"""Self-contained MASC test-split evaluation against the already-trained
checkpoint (no retraining) - reuses the existing manifests/crops on disk,
mirrors what notebook cell §7 does, for when you just need fresh numbers for
whichever backbone the checkpoint currently is, without re-running training.
"""
import sys
from pathlib import Path

import pandas as pd
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import classification_report
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import (
    DenseNet121_Weights, EfficientNet_B0_Weights, EfficientNet_V2_S_Weights,
    MNASNet1_0_Weights, MobileNet_V3_Large_Weights, MobileNet_V3_Small_Weights,
    RegNet_Y_800MF_Weights, ResNet50_Weights, ShuffleNet_V2_X1_0_Weights,
    SqueezeNet1_1_Weights, ViT_B_16_Weights,
    densenet121, efficientnet_b0, efficientnet_v2_s, mnasnet1_0,
    mobilenet_v3_large, mobilenet_v3_small, regnet_y_800mf, resnet50,
    shufflenet_v2_x1_0, squeezenet1_1, vit_b_16,
)

try:
    import timm
except ImportError:
    timm = None

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = REPO_ROOT / "runs" / "crop_violation_classifier"
CKPT_PATH = REPO_ROOT / "models" / "crop_violation_classifier_best.pt"

RULE_CLASSES = ["R09", "R04", "R17", "R10", "R28", "R08"]
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


def build_model(backbone, num_classes, pretrained=False):
    # explicit, 33 named branches - same as notebooks/train_crop_violation_classifier.ipynb
    if backbone == "mobilenet_v3_small":
        model = mobilenet_v3_small(weights=None)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif backbone == "mobilenet_v3_large":
        model = mobilenet_v3_large(weights=None)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif backbone == "efficientnet_b0":
        model = efficientnet_b0(weights=None)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif backbone == "efficientnet_v2_s":
        model = efficientnet_v2_s(weights=None)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif backbone == "mnasnet1_0":
        model = mnasnet1_0(weights=None)
        model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
    elif backbone == "resnet50":
        model = resnet50(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif backbone == "shufflenet_v2_x1_0":
        model = shufflenet_v2_x1_0(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif backbone == "regnet_y_800mf":
        model = regnet_y_800mf(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif backbone == "densenet121":
        model = densenet121(weights=None)
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
    elif backbone == "squeezenet1_1":
        model = squeezenet1_1(weights=None)
        model.classifier[1] = nn.Conv2d(model.classifier[1].in_channels, num_classes, kernel_size=1)
    elif backbone == "vit_b_16":
        model = vit_b_16(weights=None)
        model.heads.head = nn.Linear(model.heads.head.in_features, num_classes)
    else:
        if timm is None:
            raise ImportError(f"backbone {backbone!r} requires `timm`")
        model = timm.create_model(backbone, pretrained=False, num_classes=num_classes)
    return model


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
        img = Image.open(self.output_root / row["crop_path"]).convert("RGB")
        img = self.transform(img)
        label = torch.tensor([row[r] for r in self.rule_classes], dtype=torch.float32)
        return img, label


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(CKPT_PATH, map_location=device)
    backbone = ckpt["backbone"]
    crop_size = ckpt["crop_size"]

    print(f"Evaluating checkpoint: backbone={backbone!r}, epoch={ckpt['epoch']}, val_f1={ckpt['val_f1']:.4f}")

    test_manifest = pd.read_csv(OUTPUT_ROOT / "manifests" / "test.csv")
    eval_transform = transforms.Compose([
        transforms.Resize((crop_size, crop_size)),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
    ])
    test_ds = CropViolationDataset(test_manifest, RULE_CLASSES, OUTPUT_ROOT, eval_transform)
    test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)
    print(f"test crops: {len(test_ds)}")

    model = build_model(backbone, num_classes=len(RULE_CLASSES))
    model.load_state_dict(ckpt["model_state"])
    model = model.to(device).eval()

    all_logits, all_labels = [], []
    with torch.no_grad():
        for images, labels in test_loader:
            images = images.to(device)
            logits = model(images)
            all_logits.append(logits.cpu())
            all_labels.append(labels)

    logits = torch.cat(all_logits)
    labels = torch.cat(all_labels)
    preds = (torch.sigmoid(logits) >= 0.5).float()

    report = classification_report(labels.numpy(), preds.numpy(), target_names=RULE_CLASSES, zero_division=0)
    print()
    print(report)


if __name__ == "__main__":
    main()
