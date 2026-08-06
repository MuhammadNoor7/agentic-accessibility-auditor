"""Per-rule confusion matrices + P/R/F1/PR curves for the crop-violation
classifier, mirroring what Ultralytics auto-generates for the YOLO detector
(BoxP/R/F1/PR_curve.png, confusion_matrix.png) - our custom training loop
doesn't get these for free, so this script builds them after the fact.

Self-contained: loads whatever checkpoint is currently at
models/crop_violation_classifier_best.pt, and reuses the already-built
MASC test + Rico holdout crop sets (runs/crop_violation_classifier/). No
training, no retraining - pure inference + plotting on an existing model.

Only plots R08/R17/R04 - the rules with real positive examples. R09/R10/R28
have zero positive examples in both MASC and Rico, so their curves would be
degenerate (see docs/crop_classifier_comparison_findings.md).

WARNING - CPU is slow for this: the full run (~14,900 crops across both
splits) took 190+ CPU-minutes for swin_tiny_patch4_window7_224 locally.
Strongly prefer running this on a GPU (Colab or otherwise) for any
transformer-family backbone; lightweight CNN backbones (mobilenet_v3_small
etc.) are fast enough to run locally.

Usage:
    python scripts/plot_crop_classifier_curves.py
    python scripts/plot_crop_classifier_curves.py --checkpoint path/to/other.pt
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import torch
import torch.nn as nn
import pandas as pd
import matplotlib.pyplot as plt
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from sklearn.metrics import confusion_matrix, precision_recall_curve

try:
    import timm
except ImportError:
    timm = None

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUTPUT_ROOT = ROOT / "runs" / "crop_violation_classifier"
DEFAULT_CKPT = ROOT / "models" / "crop_violation_classifier_best.pt"
PLOTS_DIR = OUTPUT_ROOT / "crop_classifier"

REAL_SIGNAL_RULES = ["R08", "R17", "R04"]  # only rules with real positive examples
THRESHOLD = 0.5

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


class CropViolationDataset(Dataset):
    def __init__(self, manifest_df, rule_classes, output_root, transform):
        self.df = manifest_df.reset_index(drop=True)
        self.rule_classes = rule_classes
        self.output_root = output_root
        self.transform = transform

    def __len__(self):
        return len(self.df)

    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        crop_path = str(row["crop_path"]).replace("\\", "/")  # tolerate Windows-written manifests
        img = Image.open(self.output_root / crop_path).convert("RGB")
        img = self.transform(img)
        label = torch.tensor([row[r] for r in self.rule_classes], dtype=torch.float32)
        return img, label


def build_model(backbone: str, num_classes: int) -> nn.Module:
    if timm is None:
        raise ImportError("pip install timm")
    return timm.create_model(backbone, pretrained=False, num_classes=num_classes)


def get_probs_labels(model, device, transform, rule_classes, manifest_path, batch_size=64):
    manifest = pd.read_csv(manifest_path)
    ds = CropViolationDataset(manifest, rule_classes, OUTPUT_ROOT, transform)
    loader = DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=0)
    all_probs, all_labels = [], []
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            probs = torch.sigmoid(model(images)).cpu()
            all_probs.append(probs)
            all_labels.append(labels)
    return torch.cat(all_probs).numpy(), torch.cat(all_labels).numpy()


def plot_confusion_matrices(masc, rico, rule_idx, prefix: str, out_dir: Path):
    masc_probs, masc_labels = masc
    rico_probs, rico_labels = rico
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for col, rule in enumerate(REAL_SIGNAL_RULES):
        i = rule_idx[rule]
        for row, (name, probs, labels) in enumerate([
            ("MASC test", masc_probs, masc_labels),
            ("Rico holdout", rico_probs, rico_labels),
        ]):
            preds = (probs[:, i] >= THRESHOLD).astype(int)
            cm = confusion_matrix(labels[:, i].astype(int), preds, labels=[0, 1])
            ax = axes[row, col]
            ax.imshow(cm, cmap="Blues")
            for r in range(2):
                for c in range(2):
                    ax.text(c, r, str(cm[r, c]), ha="center", va="center",
                            color="white" if cm[r, c] > cm.max() / 2 else "black", fontsize=11)
            ax.set_xticks([0, 1]); ax.set_xticklabels(["clean", "violation"])
            ax.set_yticks([0, 1]); ax.set_yticklabels(["clean", "violation"])
            ax.set_xlabel("Predicted"); ax.set_ylabel("True")
            ax.set_title(f"{rule} — {name}", fontsize=11)
    plt.tight_layout()
    path = out_dir / f"{prefix}_confusion_matrices.png"
    plt.savefig(path, dpi=110)
    plt.close()
    print(f"Saved {path}")


def plot_pr_curve(masc, rico, rule_idx, prefix: str, out_dir: Path):
    masc_probs, masc_labels = masc
    rico_probs, rico_labels = rico
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for col, rule in enumerate(REAL_SIGNAL_RULES):
        i = rule_idx[rule]
        ax = axes[col]
        for name, probs, labels, color in [
            ("MASC test", masc_probs, masc_labels, "tab:blue"),
            ("Rico holdout", rico_probs, rico_labels, "tab:orange"),
        ]:
            precision, recall, _ = precision_recall_curve(labels[:, i].astype(int), probs[:, i])
            ax.plot(recall, precision, label=name, color=color)
        ax.set_xlabel("Recall"); ax.set_ylabel("Precision")
        ax.set_title(rule); ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
        ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    path = out_dir / f"{prefix}_pr_curves.png"
    plt.savefig(path, dpi=110)
    plt.close()
    print(f"Saved {path}")


def plot_metric_vs_threshold(masc, rico, rule_idx, metric_name, compute_fn, prefix, suffix, out_dir: Path):
    masc_probs, masc_labels = masc
    rico_probs, rico_labels = rico
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    for col, rule in enumerate(REAL_SIGNAL_RULES):
        i = rule_idx[rule]
        ax = axes[col]
        for name, probs, labels, color in [
            ("MASC test", masc_probs, masc_labels, "tab:blue"),
            ("Rico holdout", rico_probs, rico_labels, "tab:orange"),
        ]:
            precision, recall, thresholds = precision_recall_curve(
                labels[:, i].astype(int), probs[:, i]
            )
            values = compute_fn(precision[:-1], recall[:-1])
            ax.plot(thresholds, values, label=name, color=color)
        ax.axvline(0.5, color="gray", linestyle="--", linewidth=1, alpha=0.6)
        ax.set_xlabel("Confidence threshold"); ax.set_ylabel(metric_name)
        ax.set_title(rule); ax.set_xlim(0, 1); ax.set_ylim(0, 1.02)
        ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    path = out_dir / f"{prefix}_{suffix}.png"
    plt.savefig(path, dpi=110)
    plt.close()
    print(f"Saved {path}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CKPT)
    parser.add_argument("--out-dir", type=Path, default=PLOTS_DIR)
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device: {device}")
    if device.type == "cpu":
        print("WARNING: CPU run. Transformer-family backbones (swin/vit/mobilevit) "
              "took 190+ minutes locally for the full crop set - consider Colab/GPU.")

    ckpt = torch.load(args.checkpoint, map_location=device, weights_only=False)
    rule_classes = ckpt["rule_classes"]
    crop_size = ckpt["crop_size"]
    backbone = ckpt["backbone"]
    prefix = backbone  # filenames auto-follow whatever model is actually deployed
    print(f"Loaded {backbone} (epoch {ckpt['epoch']}, val_f1={ckpt['val_f1']:.4f})")

    model = build_model(backbone, num_classes=len(rule_classes))
    model.load_state_dict(ckpt["model_state"])
    model = model.to(device).eval()

    eval_transform = transforms.Compose([
        transforms.Resize((crop_size, crop_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])

    args.out_dir.mkdir(parents=True, exist_ok=True)

    print("Running inference on MASC test set...")
    masc = get_probs_labels(model, device, eval_transform, rule_classes,
                             OUTPUT_ROOT / "manifests" / "test.csv")
    print(f"  {len(masc[0])} crops")

    print("Running inference on Rico holdout set...")
    rico = get_probs_labels(model, device, eval_transform, rule_classes,
                             OUTPUT_ROOT / "rico_manifest" / "holdout.csv")
    print(f"  {len(rico[0])} crops")

    rule_idx = {r: rule_classes.index(r) for r in REAL_SIGNAL_RULES}

    plot_confusion_matrices(masc, rico, rule_idx, prefix, args.out_dir)
    plot_pr_curve(masc, rico, rule_idx, prefix, args.out_dir)
    plot_metric_vs_threshold(masc, rico, rule_idx, "Precision", lambda p, r: p,
                              prefix, "p_curve", args.out_dir)
    plot_metric_vs_threshold(masc, rico, rule_idx, "Recall", lambda p, r: r,
                              prefix, "r_curve", args.out_dir)
    plot_metric_vs_threshold(masc, rico, rule_idx, "F1",
                              lambda p, r: (2 * p * r) / (p + r + 1e-12),
                              prefix, "f1_curve", args.out_dir)

    print("\nAt threshold 0.5 (cross-check against classification_report):")
    for name, (probs, labels) in [("MASC", masc), ("Rico", rico)]:
        for rule in REAL_SIGNAL_RULES:
            i = rule_idx[rule]
            preds = (probs[:, i] >= THRESHOLD).astype(int)
            tn, fp, fn, tp = confusion_matrix(labels[:, i].astype(int), preds, labels=[0, 1]).ravel()
            prec = tp / (tp + fp) if (tp + fp) else 0
            rec = tp / (tp + fn) if (tp + fn) else 0
            print(f"  {name} {rule}: TP={tp} FP={fp} FN={fn} TN={tn}  precision={prec:.2f} recall={rec:.2f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
