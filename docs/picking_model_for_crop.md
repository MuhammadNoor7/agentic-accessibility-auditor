# Picking a Model for Crop-Level Accessibility Classification

| Field | Value |
|-------|-------|
| Project | Agentic Accessibility Auditor — Task B (Crop Classification) |
| Notebook | `notebooks/train_crop_violation_classifier.ipynb` |
| Source doc | `model-comparison-cv-training (1).docx` |
| Owner | Muhammad Noor |
| Date | 2026-07-28 |

---

## 1. Why this model exists at all

`docs/user_coverage_for_training.md` splits the 30 accessibility rules into two buckets. Most rules (R01, R02, R03, R05, R06, R12, R13, R15, R16, R19–R27, R29, R30, ...) are already fully solved by the XML parser + rule checker (`src/rules.py`) — they read `text`, `content-desc`, `clickable`, `bounds` straight from the UI hierarchy. No model needed.

A handful of rules need to look at the **rendered pixels**, not just the XML, because the thing that makes them a violation (a color contrast ratio, clipped/overlapping text, a screen-density-relative touch target) only exists once the layout is rendered:

| Rule | Violation | Why it needs pixels |
|---|---|---|
| **R09** | Low contrast (text/background ratio) | Needs actual foreground/background pixel colors |
| **R04** | Small touch target (< 48dp) | XML gives raw bounds; a visual crop confirms real on-screen tap size |
| **R17** | Insufficient spacing between clickable elements (< 8dp) | Visual crop confirms actual rendered gap |
| **R10** | Text overflow (text taller than its box) | Needs to see if rendered text is visually clipped |
| **R28** | Font-scale overflow (200% scale wouldn't fit) | Visual confirmation of clipping |
| **R08** | Layout overlap between elements | Bounding-box math catches some cases; a crop reduces false positives |

This notebook builds a **multi-label crop classifier** over exactly these 6 rules: given a crop, predict which (if any) of `[R09, R04, R17, R10, R28, R08]` apply. A crop can trigger more than one rule at once (e.g. a button that is both too small *and* too close to its neighbor), hence multi-label rather than a single softmax over classes.

---

## 2. Dataset size — the number that drives every decision below

- **Training screens:** `data-masc/splits/train.csv` = 4,943 screens (val = 1,056, test = 1,069). Each screen contributes however many positive-violation crops exist, plus `negatives_per_screen=3`. Nowhere near ImageNet scale (1.2M images) that these backbones were pretrained on.
- **Class imbalance:** 6 rule classes, each independently imbalanced. `pos_weight` is capped at 20 in the loss, meaning some rules have as few as ~1 positive crop per 20 negatives — so the rarer rules (e.g. R28 font-scale overflow) likely have only low hundreds of positive examples, not thousands.
- **Augmentation is light:** horizontal flip (p=0.3) + color jitter only. No mixup, cutout, or dropout to counteract memorization.
- **Notebook's own documented risk (cell 18):** *"crops are small and this dataset is tiny, so overfitting is the main risk, not underfitting."* This single sentence flips the usual "bigger model = better" intuition for this task.

---

## 3. Backbone comparison table

Per `model-comparison-cv-training (1).docx`, Task B — Crop Classification:

| Model | Speed to train | Accuracy on small crops | Size | Verdict |
|---|---|---|---|---|
| **MobileNetV3** | Fast | Good | ~5MB | **Best fit** — designed for small, fast, mobile-scale classification |
| MobileNetV3-Large | Fast (~2x slower than Small) | Good, higher ImageNet ceiling | ~9MB | Extra capacity not needed here — see §5 |
| EfficientNet-B0 | Fast, slightly slower than Small | Good, slightly better | ~20MB | Close second, marginally more accurate but heavier |
| ResNet-50 | Slower | Higher, with more data | ~100MB | Overkill unless the lighter models plateau |
| ViT | Slow, needs more data | Can be high with enough data | Large | Not recommended yet — needs more data than we have |

---

## 4. MobileNetV3-Small vs. MobileNetV3-Large

| Property | MobileNetV3-Small | MobileNetV3-Large |
|---|---|---|
| Parameters | ~2.5M | ~5.4M |
| ImageNet top-1 accuracy | ~67.5% | ~75.2% |
| Relative speed / latency | Fastest | ~2x slower than Small |
| Memory / compute footprint | Lowest | Higher (more channels + layers) |
| Target use case | Mobile/edge, fast iteration | Higher-accuracy mobile/edge deployment |
| Depth (inverted residual blocks) | Fewer, narrower blocks | More, wider blocks |
| Good fit for `LOCAL_MODE` smoke tests | Yes — trains fast on CPU | Slower, less ideal for quick debugging |
| Good fit for full training run | OK if crop dataset is small | Better if you want max accuracy and have GPU time |
| torchvision weights used | `MobileNet_V3_Small_Weights.DEFAULT` | `MobileNet_V3_Large_Weights.DEFAULT` |
| Both pretrained on | ImageNet only (no UI/accessibility knowledge) | ImageNet only (no UI/accessibility knowledge) |

For reference, `efficientnet_b0` (the third option in `CFG["backbone"]`) sits above both — ~5.3M params, ~77.7% ImageNet top-1 — a bit slower than MobileNetV3-Large but typically a stronger accuracy ceiling for the same fine-tuning effort, on paper.

---

## 5. Why MobileNetV3-Large is the wrong pick here

- More than double MobileNetV3-Small's ~2.5M params, with nothing in this dataset that requires the extra representational power — UI crops are simple geometric/color patterns (contrast ratios, spacing gaps, bounding-box overlap), not the fine-grained texture discrimination (dog breeds, bird species) that Large's extra capacity was built to help ImageNet with.
- Its ImageNet-accuracy edge (75.2% vs 67.5%) is a natural-image benchmark number — it doesn't reliably transfer to a domain-shifted, class-imbalanced, low-positive-count fine-tuning task. The extra capacity is more likely to just memorize the few hundred positive crops per rare rule than generalize from them.
- Roughly 2x slower per epoch than Small for no demonstrated benefit — iteration speed lost while the crop-extraction/label pipeline itself is still being validated.

---

## 6. Why EfficientNet-B0 is also the wrong pick here (for now)

- Same capacity-vs-data mismatch as Large, arguably worse: EfficientNet's compound scaling (depth + width + resolution together) is specifically known to need more data to pay off — its advantage over MobileNet shows up in data-rich fine-tuning, not sparse-label regimes like this one.
- It is more BatchNorm-sensitive, and with `batch_size=32` and rare positives, some batches may contain zero positive examples for a given rule — unstable BN statistics under-serve an architecture tuned assuming large, well-populated batches.
- Same ~2x epoch cost as Large, again without a task-specific reason to expect it pays off.
- **Escalation path:** if training shows true underfitting — train F1 *and* val F1 both low/plateaued together (not just val lagging behind train, which signals overfitting instead) — switch `CFG["backbone"] = "efficientnet_b0"` and re-run.

---

## 7. Why ViT was ruled out

- ViTs have no built-in convolutional inductive bias (locality, translation-equivariance). A CNN's early layers already "know" that nearby pixels are related and that a pattern shifted in the image is still the same pattern. A ViT has to learn that spatial structure from scratch purely through attention over patches — which is why the original ViT paper only beat CNNs once pretrained on JFT-300M / ImageNet-21k scale data. From-scratch or lightly fine-tuned ViTs underperform CNNs on small datasets.
- This project's dataset (4,943 train screens, sparse positives per rule) is nowhere near that scale. The notebook's own "Next steps" cell is explicit: *"Avoid ViT for now... it needs more training data than a dataset this size can realistically provide."*
- Even the smallest practical ViT variants are large relative to MobileNetV3-Small and would compound the same overfitting risk already flagged for EfficientNet-B0/Large — but worse, since ViT's data requirement is higher, not just its parameter count.

---

## 8. Why legacy CNNs (ResNet-50 and older) weren't picked either

- ResNet-50 (~25M params, ~100MB) is the one legacy-style option the source doc actually evaluated, and its own verdict caps it: higher accuracy only shows up "with more data," and it's explicitly reserved as a fallback — *"escalate to ResNet-50... only if validation accuracy plateaus"* — not a starting choice.
- Older architectures like VGG or Inception-v3 weren't even in the comparison because they predate the efficiency techniques (depthwise-separable convolutions, inverted residuals, compound scaling) that MobileNetV3 / EfficientNet-B0 / ResNet-50 all use. They would cost more compute and memory for worse accuracy-per-parameter than ResNet-50 already gives — strictly dominated by an option already ruled out as premature.

---

## 9. Decision

**MobileNetV3-Small is the default backbone** (`CFG["backbone"] = "mobilenet_v3_small"`). T4 GPU compute is not the bottleneck at `batch_size=32` / `crop_size=224` for any of the candidate models — the deciding factor is dataset size, and this crop dataset is small with overfitting as the documented risk, not underfitting. MobileNetV3-Small's lower capacity acts as a built-in regularizer against that, it is the fastest to train/iterate, and no config change is needed.

---

## 10. Escalation ladder (only if needed)

MobileNetV3-Small (default) → EfficientNet-B0 (one-line config swap, `CFG["backbone"] = "efficientnet_b0"`, try if train+val F1 plateau together) → ResNet-50 (documented fallback if the lighter models plateau, not yet wired into `build_model()`) → ViT (explicitly deferred until there is more data).

Practical rule of thumb: run MobileNetV3-Small first, watch the train-vs-val macro-F1 gap in the training history log, and let that gap — not intuition — decide whether escalating backbones is worth it.

---

## References

- `notebooks/train_crop_violation_classifier.ipynb` (cells 0, 6, 18, 21, 22, 34)
- `model-comparison-cv-training (1).docx` — Task B backbone comparison table
- `docs/user_coverage_for_training.md` — rule taxonomy / pixel-dependent rule bucket
- `data/data-masc/splits/{train,val,test}.csv` — dataset size figures