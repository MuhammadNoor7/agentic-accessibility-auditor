# YOLO UI Element Detector

Screenshot-only Android UI element detector. Used as a fallback in the
accessibility auditor pipeline when a screen has **no UIAutomator XML view
hierarchy** — the detector locates and classifies UI elements from pixels
alone so the rule checker still has `components.json`-shaped input to work
with.

Trained in [`notebooks/train_yolo_ui_detector.ipynb`](../notebooks/train_yolo_ui_detector.ipynb).
Inference wrapper: [`src/yolo_ui_detector.py`](../src/yolo_ui_detector.py).

---

## Status

**Trained, evaluated, exported.** 60/60 epochs complete, evaluated on a held-out
MASC test split and on the fully unseen Rico holdout set, weights exported to
`models/yolo_ui_detector_best.pt`.

---

## Model

| | |
|---|---|
| Architecture | YOLO11**l** (25.3M params, 86.6 GFLOPs) |
| Init weights | [`macpaw-research/yolov11l-ui-elements-detection`](https://huggingface.co/macpaw-research/yolov11l-ui-elements-detection) (Screen2AX, HF) |
| Framework | Ultralytics 8.4.104, torch 2.6.0+cu124 |
| Image size | 960 (tall mobile screenshots need more vertical resolution than the usual 640 default) |
| Classes (9) | `text`, `image`, `icon`, `button_labeled`, `button_icon_only`, `input_field`, `checkbox_toggle`, `tab_item`, `list_item` |

`icon` vs `image` is split by size: an `ImageView` under 64dp is called an
`icon`, otherwise `image` — see the classification cell in the notebook.

### Why Screen2AX init weights

Screen2AX is already tuned to detect UI elements rather than generic COCO
objects, which matters a lot given per-class instance counts in this dataset.
Its backbone is YOLO11-l, which can be too heavy to train at `imgsz=960` on a
16GB-class GPU alongside batchnorm stats and gradients — in that case the
notebook falls back to COCO-pretrained `yolo11m` or `yolo11s`
(`CFG["init_weights_mode"]`, default `"auto"`, decides from available GPU
memory).

### Training hyperparameters

| | |
|---|---|
| Epochs | 60, cosine LR |
| Early stopping | patience 10 |
| Batch size | 8 (auto-halved on CUDA OOM, floor of 2) |
| Augmentation | mosaic + horizontal flip; **vertical flip and rotation disabled** — a UI screenshot is never upside down or rotated, so training on flipped/rotated UIs would teach layouts that never occur in practice |
| Seed | 42 |

**Resume-from-checkpoint:** the training cell checks whether
`weights/last.pt` already exists and resumes from it instead of starting
over — useful since the run was interrupted mid-training by a disk-full
error at epoch 52 (`save_period` was originally `1`, writing a full ~194MB
snapshot *every* epoch; changed to `-1` so only `last.pt`/`best.pt` are kept).

---

## Dataset

Built from **MASC** (`data/data-masc/`), converted from UIAutomator XML +
screenshots into YOLO-format labels via `convert_screen_to_yolo_labels()` in
the notebook.

| Split | Images |
|---|---|
| Train | 4,942 |
| Val | 1,054 |
| Test | 1,068 |

**Rico holdout** (`data/data-rico-holdout/`, 1,698 screens, MASC-disjoint) is
used *only* for final generalization evaluation — never for training or
tuning. Converting it to YOLO format for eval:

- 1,683 / 1,698 screens produced usable boxes (15 failed — zero usable boxes
  after filtering, e.g. `chat_10732`).
- Box filtering: 38,820 kept · 46,304 dropped (zero/negative area) · 41,740
  dropped (unmapped class) · 18,520 dropped (hidden) · 1,204 dropped
  (duplicate bounds).
- Rico's AX taxonomy only maps to 8 of the 9 classes (no `tab_item`).

---

## Results

### Final training validation (MASC val, 1,054 images / 20,476 instances)

| Precision | Recall | mAP50 | mAP50-95 |
|---|---|---|---|
| 0.535 | 0.449 | 0.436 | 0.323 |

### MASC test split (held out from training, 1,068 images / 20,556 instances)

**Overall: mAP50 0.4283 · mAP50-95 0.3175**

| Class | mAP50-95 |
|---|---|
| input_field | 0.496 |
| button_labeled | 0.405 |
| checkbox_toggle | 0.348 |
| text | 0.329 |
| list_item | 0.327 |
| button_icon_only | 0.301 |
| image | 0.274 |
| tab_item | 0.239 |
| icon | 0.140 |

### Rico holdout — zero-shot vs. fine-tuned (1,683 images, genuinely unseen apps)

This is the real generalization test: base Screen2AX weights (never trained
on MASC) vs. our fine-tuned `best.pt`, both evaluated on Rico.

| | mAP50 | mAP50-95 |
|---|---|---|
| Zero-shot (base Screen2AX) | 0.0258 | 0.0116 |
| **Fine-tuned** | **0.2546** | **0.1732** |

Fine-tuning gives roughly a **10x improvement in mAP50** and **15x in
mAP50-95** over the base weights on completely unseen apps — the model
generalizes well beyond its MASC training distribution, not just
memorizing it.

Per-class (fine-tuned, on Rico):

| Class | mAP50 | mAP50-95 |
|---|---|---|
| input_field | 0.326 | 0.204 |
| checkbox_toggle | 0.316 | 0.233 |
| list_item | 0.294 | 0.193 |
| text | 0.298 | 0.204 |
| image | 0.258 | 0.155 |
| button_icon_only | 0.209 | 0.156 |
| button_labeled | 0.193 | 0.151 |
| icon | 0.141 | 0.089 |

`icon` is consistently the weakest class across both eval sets — worth
checking instance counts / label quality for that class if revisiting.

**Weakest class across the board:** `icon` — lowest mAP50-95 on both MASC
test (0.140) and Rico (0.089). Likely candidate for more training instances
or a size-threshold review (`icon_max_dp`) if this detector gets revisited.

---

## Artifacts

| Path | Contents |
|---|---|
| `models/yolo_ui_detector_best.pt` | Exported weights (51.2 MB), for use via `src/yolo_ui_detector.py` |
| `runs/yolo_ui_detector/export/yolo_ui_detector_best.pt` | Same weights, run-scoped copy |
| `runs/yolo_ui_detector/runs/yolo_ui_detector/weights/{best,last}.pt` | Raw Ultralytics training checkpoints |
| `runs/yolo_ui_detector/runs/yolo_ui_detector/results.csv` | Per-epoch loss/mAP history |

---

## Usage

```python
from src.yolo_ui_detector import detect_ui

detections = detect_ui("path/to/screenshot.jpg")
# [{"bbox": [x1, y1, x2, y2], "class": "button_labeled", "conf": 0.87}, ...]
```

`detect_ui(image_path, weights_path=DEFAULT_WEIGHTS, conf=0.25)` loads
`models/yolo_ui_detector_best.pt` by default (cached across calls) and
returns one dict per detected element in the original image's pixel space.
Intended as the screenshot-only fallback when no XML hierarchy is available
for a screen.

---

## Reproducing / retraining

1. Open [`notebooks/train_yolo_ui_detector.ipynb`](../notebooks/train_yolo_ui_detector.ipynb).
2. Set `LOCAL_MODE = True` for a fast ~20-image CPU smoke test, or `False`
   for the full run (requires a CUDA GPU — developed against an RTX 4000 Ada,
   20GB).
3. Run all cells top to bottom. The training cell auto-resumes from
   `weights/last.pt` if a previous run left one — safe to re-run after an
   interruption.
4. Final cells copy `best.pt` to `models/yolo_ui_detector_best.pt` and print
   the test-split and Rico holdout metrics shown above.
