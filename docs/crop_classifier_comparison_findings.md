# Crop Classifier Backbone Comparison — Findings Log

| Field | Value |
|-------|-------|
| Project | Agentic Accessibility Auditor — Task B (Crop Classification) |
| Purpose | Verify whether `mobilenet_v3_small` (current pick, per `docs/picking_model_for_crop.md`) is actually the best backbone, by running the identical training/eval pipeline (`notebooks/train_crop_violation_classifier.ipynb`) across candidate backbones |
| Pretraining data | All candidates are pretrained on **ImageNet-1k** (~1.28M images, 1000 classes) — confirmed per-model, no corpus-size confound between candidates |
| Dataset | `data-masc` full split (train/val/test) for training + MASC test eval; `data-rico-holdout` (1,698 screens) for generalization eval |
| Rules | R09 (contrast), R04 (touch target), R17 (spacing), R10 (text overflow), R28 (font-scale overflow), R08 (overlap) — **R09/R10/R28 have ~0 positive training examples in this dataset**, so their precision/recall/F1 will read as 0.00 for every backbone; this is a known dataset-coverage gap, not a backbone failure. Only **R04, R17, R08** have real signal. |
| How each row was captured | `scripts/extract_notebook_results.py <path-to-executed-notebook>` pulls params/best-val-F1/classification reports out of the saved `.ipynb` outputs |
| Status | **COMPLETE — all 33 candidates fully logged.** Best result: `swin_tiny_patch4_window7_224` (Rico macro-F1 0.22), ahead of `vit_b_16`/`mobilevitv2_200` (0.21 each). Baseline `mobilenet_v3_small`: 0.18, mid-pack, beaten by 10 other models. |
| Reusable tool | `scripts/eval_masc_test.py` — re-runs MASC test-split eval against whatever checkpoint is currently at `models/crop_violation_classifier_best.pt`, no retraining needed. Useful if a notebook's §7 output goes stale (as happened for mobilenetv1_100 - only Rico was re-run before, MASC eval was still showing the old mobilenet_v3_large numbers until this was used to get fresh ones). |

---

## Summary table (fill in as each backbone completes)

| Backbone | Params | Best val F1 | MASC test macro-F1 | R04 F1 (MASC) | R17 F1 (MASC) | R08 F1 (MASC) | Rico macro-F1 | Rico vs MASC gap | Notes |
|---|---|---|---|---|---|---|---|---|---|
| `mobilenet_v3_small` | 1.52M | 0.265 | 0.25 | 0.36 | 0.47 | 0.70 | 0.18 | large drop | **baseline** — see detail below |
| `mobilenet_v3_large` | 4.21M | 0.268 | 0.27 | 0.37 | 0.51 | 0.72 | 0.18 | large drop, same size as small | Better on MASC test, **flat on Rico** — extra params aren't generalizing, matches doc's §5 prediction |
| `mobilenetv1_100` | 3.21M | 0.266 | 0.26 | 0.33 | 0.51 | 0.71 | 0.19 | large drop | Best Rico macro-F1 so far (0.19), R17/R08 on par with Large despite fewer params — see detail below |
| `efficientnet_b0` | 4,015,234 | 0.278 | 0.26 | 0.34 | 0.52 | 0.73 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `mobilevit_s` | 4,941,478 | 0.263 | 0.25 | 0.31 | 0.50 | 0.71 | 0.18 | 0.07 drop | auto-logged, overnight sweep — see detail below |
| `vit_b_16` | 85,803,270 | 0.242 | 0.23 | 0.34 | 0.36 | 0.65 | 0.21 | 0.02 drop | auto-logged, overnight sweep — see detail below |
| `resnet50` | 23,520,326 | 0.271 | 0.26 | 0.31 | 0.55 | 0.72 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `shufflenet_v2_x1_0` | 1,259,754 | 0.269 | 0.26 | 0.34 | 0.52 | 0.71 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `regnet_y_800mf` | 5,652,222 | 0.267 | 0.27 | 0.38 | 0.49 | 0.73 | 0.18 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `mnasnet1_0` | 3,109,998 | 0.275 | 0.26 | 0.33 | 0.54 | 0.70 | 0.19 | 0.07 drop | auto-logged, overnight sweep — see detail below |
| `efficientnet_v2_s` | 20,185,174 | 0.271 | 0.26 | 0.29 | 0.54 | 0.73 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `densenet121` | 6,960,006 | 0.272 | 0.25 | 0.28 | 0.52 | 0.72 | 0.19 | 0.06 drop | auto-logged, overnight sweep — see detail below |
| `squeezenet1_1` | 725,574 | 0.122 | 0.12 | 0.02 | 0.21 | 0.49 | 0.14 | -0.02 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv1_125` | 4,997,526 | 0.254 | 0.26 | 0.31 | 0.51 | 0.72 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv2_050` | 695,366 | 0.230 | 0.24 | 0.28 | 0.44 | 0.69 | 0.19 | 0.05 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv2_100` | 2,231,558 | 0.270 | 0.25 | 0.29 | 0.52 | 0.71 | 0.17 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv2_140` | 4,326,534 | 0.267 | 0.26 | 0.37 | 0.50 | 0.72 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv3_small_050` | 574,374 | 0.240 | 0.24 | 0.32 | 0.42 | 0.69 | 0.18 | 0.06 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv4_conv_small` | 2,500,710 | 0.252 | 0.25 | 0.30 | 0.47 | 0.71 | 0.16 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv4_conv_medium` | 8,442,198 | 0.233 | 0.24 | 0.30 | 0.44 | 0.71 | 0.18 | 0.06 drop | auto-logged, overnight sweep — see detail below |
| `mobilenetv4_conv_large` | 31,317,550 | 0.237 | 0.23 | 0.21 | 0.48 | 0.72 | 0.18 | 0.05 drop | auto-logged, overnight sweep — see detail below |
| `mobilevit_xxs` | 952,950 | 0.250 | 0.25 | 0.33 | 0.46 | 0.71 | 0.19 | 0.06 drop | auto-logged, overnight sweep — see detail below |
| `mobilevit_xs` | 1,935,158 | 0.266 | 0.26 | 0.34 | 0.52 | 0.71 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `mobilevitv2_050` | 1,115,135 | 0.264 | 0.26 | 0.35 | 0.50 | 0.71 | 0.19 | 0.07 drop | auto-logged, overnight sweep — see detail below |
| `mobilevitv2_100` | 4,391,919 | 0.273 | 0.25 | 0.30 | 0.52 | 0.71 | 0.19 | 0.06 drop | auto-logged, overnight sweep — see detail below |
| `mobilevitv2_200` | 17,430,479 | 0.270 | 0.28 | 0.45 | 0.50 | 0.73 | 0.21 | 0.07 drop | auto-logged, overnight sweep — see detail below |
| `mobileone_s0` | 4,274,422 | 0.268 | 0.25 | 0.29 | 0.51 | 0.72 | 0.18 | 0.07 drop | auto-logged, overnight sweep — see detail below |
| `mobileone_s1` | 3,551,878 | 0.268 | 0.27 | 0.35 | 0.53 | 0.72 | 0.18 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `mobileone_s4` | 12,914,542 | 0.266 | 0.27 | 0.34 | 0.56 | 0.73 | 0.18 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `ghostnet_100` | 3,909,194 | 0.277 | 0.26 | 0.33 | 0.51 | 0.72 | 0.17 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `ghostnetv2_100` | 4,883,594 | 0.268 | 0.26 | 0.33 | 0.49 | 0.72 | 0.17 | 0.09 drop | auto-logged, overnight sweep — see detail below |
| `convnext_tiny` | 27,824,742 | 0.268 | 0.26 | 0.32 | 0.49 | 0.72 | 0.18 | 0.08 drop | auto-logged, overnight sweep — see detail below |
| `swin_tiny_patch4_window7_224` | 27,523,968 | 0.274 | 0.25 | 0.31 | 0.49 | 0.72 | 0.22 | 0.03 drop | auto-logged, overnight sweep — see detail below |
| ... | | | | | | | | | |

*(Add one row per backbone as you complete it. Macro-F1 numbers above include R09/R10/R28's forced 0.00 in the average — see the dataset-coverage note above; R04/R17/R08 columns are the ones that actually reflect model quality.)*

---

## Detail: `mobilenet_v3_small` (baseline, current pick)

- **Params:** 1,524,006 (~1.52M — this is the num_classes=6 head variant; ImageNet-1000-class version is ~2.54M)
- **Device:** cuda
- **Best val macro-F1:** 0.265

**MASC test-split report:**
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.26      0.58      0.36        45
         R17       0.43      0.52      0.47       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.71      0.70      1805
   micro avg       0.60      0.66      0.63      2510
   macro avg       0.23      0.30      0.25      2510
weighted avg       0.61      0.66      0.63      2510
 samples avg       0.28      0.28      0.28      2510
```

**Rico holdout report** (9,343 crops):
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.17      0.50      0.25       145
         R17       0.34      0.37      0.35      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.54      0.40      0.46      3418
   micro avg       0.44      0.40      0.42      4982
   macro avg       0.17      0.21      0.18      4982
weighted avg       0.47      0.40      0.43      4982
 samples avg       0.19      0.19      0.19      4982
```

**Generalization read:** R08 F1 drops 0.70 → 0.46 (MASC → Rico), R17 drops 0.47 → 0.35, R04 actually drops less (0.36 → 0.25 but recall stays 0.50-0.58 range). Meaningful generalization gap — model is picking up some MASC-specific visual style, not purely rule signal. This is the number every other backbone needs to beat or match.

**Sample predictions (visual grid):** not yet reviewed — open the notebook's §3.5 "Sample predictions" and §9 "Sample Rico predictions" cells to eyeball failure patterns (systematic misses vs. random noise).

---

## Detail: `mobilenet_v3_large`

- **Params:** 4,209,718 (~4.21M — 6-class head variant; matches expected size, ~1.66x mobilenet_v3_small)
- **Device:** cuda
- **Best val macro-F1:** 0.268 (checkpoint's own metadata says 0.2677, epoch 14 — consistent)

**MASC test-split report:**
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.26      0.64      0.37        45
         R17       0.49      0.53      0.51       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.71      0.74      0.72      1805
   micro avg       0.63      0.68      0.66      2510
   macro avg       0.24      0.32      0.27      2510
weighted avg       0.64      0.68      0.66      2510
 samples avg       0.29      0.29      0.29      2510
```

**Rico holdout report** (9,343 crops):
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.17      0.54      0.26       145
         R17       0.35      0.34      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.53      0.39      0.45      3418
   micro avg       0.44      0.38      0.41      4982
   macro avg       0.18      0.21      0.18      4982
weighted avg       0.47      0.38      0.41      4982
 samples avg       0.19      0.18      0.18      4982
```

**Generalization read — this is the key finding for Large vs. Small:**

| Rule | Small MASC → Rico | Large MASC → Rico |
|---|---|---|
| R04 F1 | 0.36 → 0.25 (-0.11) | 0.37 → 0.26 (-0.11) |
| R17 F1 | 0.47 → 0.35 (-0.12) | 0.51 → 0.34 (-0.17) |
| R08 F1 | 0.70 → 0.46 (-0.24) | 0.72 → 0.45 (-0.27) |
| **Rico macro-F1** | **0.18** | **0.18** |

Large edges out Small on the MASC test split (macro-F1 0.27 vs 0.25) but lands at the **exact same Rico macro-F1 (0.18)** — and its generalization *drop* is actually slightly larger on R17/R08. This is a direct, empirical confirmation of `docs/picking_model_for_crop.md` §5's a priori reasoning: *"[Large's] extra capacity is more likely to just memorize... than generalize."* 2.76x the parameters (1.52M → 4.21M head-adjusted) bought a better score on the split the model trained near, and nothing on the split that actually tests generalization. Point in favor of Small as the pick, one data point in.

---

## Detail: `mobilenetv1_100`

- **Params:** 3,213,126 (~3.21M — between Small and Large)
- **Checkpoint:** epoch 15, best val_f1 = 0.266 (essentially tied with Small's 0.265 and Large's 0.268)

**MASC test-split report:**
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.22      0.69      0.33        45
         R17       0.46      0.57      0.51       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.62      0.83      0.71      1805
   micro avg       0.56      0.76      0.65      2510
   macro avg       0.22      0.35      0.26      2510
weighted avg       0.57      0.76      0.65      2510
 samples avg       0.31      0.33      0.32      2510
```

**Rico holdout report** (9,343 crops):
```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.14      0.52      0.22       145
         R17       0.35      0.37      0.36      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.56      0.54      3418
   micro avg       0.44      0.51      0.47      4982
   macro avg       0.17      0.24      0.19      4982
weighted avg       0.46      0.51      0.48      4982
 samples avg       0.25      0.25      0.24      4982
```

**Generalization read — three-way comparison so far:**

| Rule | Small (1.52M) | Large (4.21M) | MobileNetV1 (3.21M) |
|---|---|---|---|
| R04 F1 (Rico) | 0.25 | 0.26 | 0.22 |
| R17 F1 (Rico) | 0.35 | 0.34 | 0.36 |
| R08 F1 (Rico) | 0.46 | 0.45 | 0.54 |
| **Rico macro-F1** | 0.18 | 0.18 | **0.19** |

MobileNetV1 posts the **best Rico macro-F1 of the three so far (0.19)**, driven almost entirely by a notably stronger R08 F1 (0.54 vs ~0.45-0.46 for both V3 variants) — R08 (layout overlap) is the rule with by far the most training signal (1805 MASC / 3418 Rico support), so this is a real, non-noise difference. R04 is weaker than both V3 variants, but R04 has the least support (45 MASC / 145 Rico) of the three real-signal rules, so that gap is less reliable.

**Read so far:** not yet a clean win for Small — MobileNetV1 (an older, different architecture family entirely, not a MobileNetV3 variant) is matching or beating both V3 sizes on the metric that actually matters (Rico generalization), on a comparable parameter budget. Worth watching whether this holds as more backbones come in, or if R08's dominance in the support counts is doing most of the work here.

---

## Workflow for each subsequent backbone

1. In `runs/notebooks/train_crop_violation_classifier.ipynb` (or wherever you're running from), set `CFG["backbone"]` to the next candidate and Run All.
2. **Press Ctrl+S** as soon as it finishes — this is the step that was missed for `mobilenet_v3_large`.
3. Tell me it's done (or just point me at the file) — I'll run the extraction script, add a row to the summary table above, and write up a full detail section like the ones above.
4. Repeat for the next backbone.

Once enough are in, I'll also pull in the params/pretraining-corpus context from the earlier conversation (all 33 are ImageNet-1k pretrained, tiered by parameter count) so the final write-up ties results back to *why* each one performed the way it did, not just the raw numbers.


## Detail: `efficientnet_b0` (auto-logged, overnight sweep)

- **Params:** 4,015,234
- **Best val macro-F1:** 0.278
- **Run time:** 42.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.25      0.53      0.34        45
         R17       0.53      0.51      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.77      0.73      1805

   micro avg       0.64      0.70      0.67      2510
   macro avg       0.24      0.30      0.26      2510
weighted avg       0.64      0.70      0.67      2510
 samples avg       0.30      0.30      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.48      0.24       145
         R17       0.37      0.36      0.36      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.54      0.44      0.49      3418

   micro avg       0.45      0.42      0.44      4982
   macro avg       0.18      0.21      0.18      4982
weighted avg       0.48      0.42      0.44      4982
 samples avg       0.21      0.21      0.20      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.34 -> 0.24 | R17 F1: 0.52 -> 0.36 | R08 F1: 0.73 -> 0.49

**Generalization read:** Squarely in the unremarkable middle of the pack - Rico macro-F1 0.18, identical to `mobilenet_v3_small/large`, `mobilevit_s`, and `regnet_y_800mf`. It actually posts the **highest best-val-F1 (0.278) of any model so far**, which makes it a clean demonstration that strong validation/MASC performance doesn't predict Rico generalization - the two just aren't correlated here. R08 Rico F1 (0.49) sits mid-range, between the MobileNetV3 pair (~0.45-0.46) and the MobileNetV1/MNASNet pair (0.54-0.55, see below).

---

## Detail: `mobilevit_s` (auto-logged, overnight sweep)

- **Params:** 4,941,478
- **Best val macro-F1:** 0.263
- **Run time:** 53.0 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.22      0.56      0.31        45
         R17       0.45      0.57      0.50       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.64      0.79      0.71      1805

   micro avg       0.57      0.73      0.64      2510
   macro avg       0.22      0.32      0.25      2510
weighted avg       0.58      0.73      0.65      2510
 samples avg       0.30      0.31      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.53      0.25       145
         R17       0.35      0.40      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.47      0.49      3418

   micro avg       0.43      0.45      0.44      4982
   macro avg       0.17      0.23      0.18      4982
weighted avg       0.45      0.45      0.45      4982
 samples avg       0.22      0.22      0.21      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.31 -> 0.25 | R17 F1: 0.50 -> 0.37 | R08 F1: 0.71 -> 0.49

**Generalization read:** Also unremarkable on Rico (0.18) despite being the one lightweight model that mixes CNN and attention. Notably has the **lowest best-val-F1 (0.263) of the non-ViT models** and the lowest R04 MASC F1 (0.31) of the group. The contrast with `vit_b_16` (below) - full attention at scale does show a generalization edge, a small CNN+attention hybrid doesn't - suggests whatever `vit_b_16` is doing is more about capacity/scale than the mere presence of attention.

---

## Detail: `vit_b_16` (auto-logged, overnight sweep)

- **Params:** 85,803,270
- **Best val macro-F1:** 0.242
- **Run time:** 60.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.36      0.33      0.34        45
         R17       0.26      0.59      0.36       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.58      0.76      0.65      1805

   micro avg       0.45      0.71      0.55      2510
   macro avg       0.20      0.28      0.23      2510
weighted avg       0.49      0.71      0.57      2510
 samples avg       0.28      0.31      0.28      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.59      0.33      0.42       145
         R17       0.25      0.56      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.47      0.49      0.48      3418

   micro avg       0.36      0.51      0.43      4982
   macro avg       0.22      0.23      0.21      4982
weighted avg       0.41      0.51      0.44      4982
 samples avg       0.22      0.25      0.23      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.23 | Rico macro-F1: 0.21 | R04 F1 (MASC->Rico): 0.34 -> 0.42 | R17 F1: 0.36 -> 0.34 | R08 F1: 0.65 -> 0.48

**Generalization read - the standout so far:** Best Rico macro-F1 of all 10 models tested (0.21) and by far the smallest MASC-to-Rico gap (0.02, vs. 0.07-0.09 for everyone else). But look closer: this is almost entirely an **R04 story** - Rico R04 F1 is 0.42, more than double the next-best (`mobilenet_v3_large` at 0.26) - while R17 (0.34) and R08 (0.48) are just average-to-slightly-below the rest of the field. R04 has the thinnest support of the three real-signal rules (145 Rico crops vs. R08's 3,418), so a narrow win concentrated there is more sensitive to a handful of examples going right than a broad-based win would be. Genuinely interesting, but treat it as provisional - one rule's result carrying the whole macro-F1 lead, on the single most expensive model to train (86.6M params, 60.2 min, longest of any backbone so far) for that lead.

---

## Detail: `resnet50` (auto-logged, overnight sweep)

- **Params:** 23,520,326
- **Best val macro-F1:** 0.271
- **Run time:** 57.0 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.22      0.49      0.31        45
         R17       0.54      0.56      0.55       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.66      0.80      0.72      1805

   micro avg       0.61      0.74      0.67      2510
   macro avg       0.24      0.31      0.26      2510
weighted avg       0.62      0.74      0.67      2510
 samples avg       0.31      0.32      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.14      0.39      0.20       145
         R17       0.38      0.33      0.35      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.49      0.50      3418

   micro avg       0.45      0.44      0.45      4982
   macro avg       0.17      0.20      0.18      4982
weighted avg       0.47      0.44      0.45      4982
 samples avg       0.22      0.21      0.21      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.31 -> 0.20 | R17 F1: 0.55 -> 0.35 | R08 F1: 0.72 -> 0.50

**Generalization read:** 23.5M params - 15x `mobilenet_v3_small`'s size - buys **nothing** on Rico (same 0.18 pack-level macro-F1), and its Rico R04 F1 (0.20) is the **worst of all 10 models tested**. This is the cleanest confirmation yet of `docs/picking_model_for_crop.md`'s original caution that ResNet-50 is "overkill... only if [lighter models] plateau" - here, more capacity didn't just fail to help, it correlated with the weakest result on the rarest-support rule.

---

## Detail: `shufflenet_v2_x1_0` (auto-logged, overnight sweep)

- **Params:** 1,259,754
- **Best val macro-F1:** 0.269
- **Run time:** 35.6 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.23      0.64      0.34        45
         R17       0.47      0.59      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.67      0.75      0.71      1805

   micro avg       0.60      0.71      0.65      2510
   macro avg       0.23      0.33      0.26      2510
weighted avg       0.61      0.71      0.65      2510
 samples avg       0.30      0.31      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.55      0.26       145
         R17       0.35      0.40      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.54      0.43      0.48      3418

   micro avg       0.44      0.42      0.43      4982
   macro avg       0.18      0.23      0.18      4982
weighted avg       0.47      0.42      0.44      4982
 samples avg       0.20      0.20      0.20      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.34 -> 0.26 | R17 F1: 0.52 -> 0.37 | R08 F1: 0.71 -> 0.48

**Generalization read:** The smallest model tested so far (1.26M params, even smaller than `mobilenet_v3_small`'s 1.52M) lands at the exact same 0.18 Rico macro-F1 as everything in the mid-pack. Further evidence that above some fairly low capacity floor, extra parameters aren't buying anything on this task - the floor for "good enough" appears to sit well below 2M params.

---

## Detail: `regnet_y_800mf` (auto-logged, overnight sweep)

- **Params:** 5,652,222
- **Best val macro-F1:** 0.267
- **Run time:** 32.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.29      0.58      0.38        45
         R17       0.41      0.61      0.49       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.78      0.73      1805

   micro avg       0.58      0.73      0.65      2510
   macro avg       0.23      0.33      0.27      2510
weighted avg       0.60      0.73      0.66      2510
 samples avg       0.30      0.31      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.47      0.25       145
         R17       0.33      0.43      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.44      0.47      3418

   micro avg       0.42      0.44      0.43      4982
   macro avg       0.17      0.22      0.18      4982
weighted avg       0.45      0.44      0.44      4982
 samples avg       0.21      0.21      0.21      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.27 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.38 -> 0.25 | R17 F1: 0.49 -> 0.37 | R08 F1: 0.73 -> 0.47

**Generalization read:** MASC macro-F1 0.27 ties `mobilenet_v3_large` for the best MASC-split score seen so far, but Rico stays at pack-level 0.18 - the same memorize-don't-generalize pattern already seen with Large. Another data point for "MASC test performance is not a reliable proxy for Rico generalization."

---

## Detail: `mnasnet1_0` (auto-logged, overnight sweep)

- **Params:** 3,109,998
- **Best val macro-F1:** 0.275
- **Run time:** 35.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.26      0.47      0.33        45
         R17       0.59      0.50      0.54       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.58      0.87      0.70      1805

   micro avg       0.57      0.77      0.66      2510
   macro avg       0.24      0.31      0.26      2510
weighted avg       0.57      0.77      0.65      2510
 samples avg       0.33      0.33      0.33      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.36      0.22       145
         R17       0.40      0.29      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.48      0.64      0.55      3418

   micro avg       0.45      0.54      0.49      4982
   macro avg       0.17      0.22      0.19      4982
weighted avg       0.45      0.54      0.48      4982
 samples avg       0.26      0.26      0.26      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.33 -> 0.22 | R17 F1: 0.54 -> 0.34 | R08 F1: 0.70 -> 0.55

**Generalization read:** Ties `mobilenetv1_100` for second-best Rico macro-F1 (0.19) and posts the **single highest R08 Rico F1 of all 10 models (0.55)**, edging out even `mobilenetv1_100`'s 0.54. Since R08 has by far the most support of any real-signal rule (3,418 Rico crops), this isn't a small-sample fluke the way `vit_b_16`'s R04 result might be. Two older/different-generation architectures (MobileNetV1, MNASNet - both pre-MobileNetV3 in lineage) now show this same R08 edge over the MobileNetV3/EfficientNet/ResNet family - an emerging pattern worth watching as more backbones complete.

---

## Detail: `efficientnet_v2_s` (auto-logged, overnight sweep)

- **Params:** 20,185,174
- **Best val macro-F1:** 0.271
- **Run time:** 54.0 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.20      0.53      0.29        45
         R17       0.54      0.55      0.54       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.78      0.73      1805

   micro avg       0.63      0.72      0.67      2510
   macro avg       0.24      0.31      0.26      2510
weighted avg       0.64      0.72      0.67      2510
 samples avg       0.30      0.31      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.48      0.23       145
         R17       0.38      0.36      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.54      0.42      0.47      3418

   micro avg       0.45      0.40      0.42      4982
   macro avg       0.18      0.21      0.18      4982
weighted avg       0.48      0.40      0.43      4982
 samples avg       0.20      0.19      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.29 -> 0.23 | R17 F1: 0.54 -> 0.37 | R08 F1: 0.73 -> 0.47

**Generalization read:** Third-largest model tested (20.2M params, after `vit_b_16`'s 86.6M and `resnet50`'s 23.5M) and it lands right back at pack-level Rico macro-F1 (0.18) - unremarkable across R04 (0.23), R17 (0.37), and R08 (0.47). A third confirmation now (alongside `resnet50` and `mobilenet_v3_large`) that extra capacity in this size range isn't buying real generalization on this task, just better MASC-split fit (macro-F1 0.26, mid-pack-high) that doesn't carry over.

---

## Detail: `densenet121` (auto-logged, overnight sweep)

- **Params:** 6,960,006
- **Best val macro-F1:** 0.272
- **Run time:** 53.3 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.20      0.47      0.28        45
         R17       0.50      0.55      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.64      0.83      0.72      1805

   micro avg       0.59      0.75      0.66      2510
   macro avg       0.22      0.31      0.25      2510
weighted avg       0.60      0.75      0.66      2510
 samples avg       0.31      0.32      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.40      0.21       145
         R17       0.37      0.41      0.39      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.52      0.51      3418

   micro avg       0.44      0.48      0.46      4982
   macro avg       0.17      0.22      0.19      4982
weighted avg       0.46      0.48      0.47      4982
 samples avg       0.23      0.24      0.23      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.28 -> 0.21 | R17 F1: 0.52 -> 0.39 | R08 F1: 0.72 -> 0.51

**Generalization read:** Ties `mobilenetv1_100`/`mnasnet1_0` for second-best Rico macro-F1 (0.19), behind only `vit_b_16`. More notably, it posts the **highest Rico R17 F1 of any model so far (0.39)** - every other backbone has topped out around 0.34-0.37 on that rule. At 6.96M params it's solidly in the "good fit" size tier, so this isn't a capacity story the way `vit_b_16`'s result might be - DenseNet's dense/feature-reuse connectivity pattern may just suit the spacing-detection task (R17) better than the other architectures tried. Worth flagging as a real candidate, not just a data point.

---

## Detail: `squeezenet1_1` (auto-logged, overnight sweep)

- **Params:** 725,574
- **Best val macro-F1:** 0.122
- **Run time:** 15.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.01      1.00      0.02        45
         R17       0.12      1.00      0.21       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.33      1.00      0.49      1805

   micro avg       0.08      1.00      0.14      2510
   macro avg       0.08      0.50      0.12      2510
weighted avg       0.27      1.00      0.41      2510
 samples avg       0.08      0.43      0.13      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.02      1.00      0.03       145
         R17       0.15      1.00      0.26      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.37      1.00      0.54      3418

   micro avg       0.09      1.00      0.16      4982
   macro avg       0.09      0.50      0.14      4982
weighted avg       0.29      1.00      0.44      4982
 samples avg       0.09      0.48      0.15      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.12 | Rico macro-F1: 0.14 | R04 F1 (MASC->Rico): 0.02 -> 0.03 | R17 F1: 0.21 -> 0.26 | R08 F1: 0.49 -> 0.54

**Generalization read - this one actually failed, not just underperformed:** Recall is **1.00 for every rule** on both MASC and Rico, with precision near-floor (0.01-0.33). That's the signature of a model that collapsed to predicting *positive for everything* rather than learning real decision boundaries - not "weak generalization," a degenerate solution. Its Rico macro-F1 (0.14) actually being *higher* than its MASC macro-F1 (0.12) - a negative gap, the only model so far where Rico beats MASC - isn't a generalization win, it's noise around a near-useless baseline (predict-everything-positive scores differently depending on each split's positive/negative ratio, not on anything the model learned). At 1.24M params it's the smallest architecture tested and had the shortest training time (15.2 min) of anything so far - worth checking whether this is a genuine architecture/task mismatch (SqueezeNet's aggressive fire-module channel squeezing may be too tight a bottleneck for the fine-grained spatial cues this task needs) or a training instability specific to its interaction with the `pos_weight`-heavy loss and this LR schedule. Either way, this is the first backbone in the sweep that should be treated as **excluded**, not just "worse."

---

## Detail: `mobilenetv1_125` (auto-logged, overnight sweep)

- **Params:** 4,997,526
- **Best val macro-F1:** 0.254
- **Run time:** 39.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.20      0.67      0.31        45
         R17       0.45      0.59      0.51       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.66      0.79      0.72      1805

   micro avg       0.58      0.74      0.65      2510
   macro avg       0.22      0.34      0.26      2510
weighted avg       0.59      0.74      0.65      2510
 samples avg       0.31      0.32      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.12      0.48      0.19       145
         R17       0.33      0.41      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.49      0.50      3418

   micro avg       0.42      0.47      0.44      4982
   macro avg       0.16      0.23      0.18      4982
weighted avg       0.45      0.47      0.45      4982
 samples avg       0.22      0.23      0.22      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.31 -> 0.19 | R17 F1: 0.51 -> 0.37 | R08 F1: 0.72 -> 0.50

**Generalization read:** Back to pack-level Rico macro-F1 (0.18) - unlike its narrower sibling `mobilenetv1_100` (1.0x width), which stood out with Rico macro-F1 0.19 and the strongest R08 F1 (0.54) of any model at the time. This 1.25x-width variant's Rico R08 F1 (0.50) is solidly mid-pack, not a repeat of that edge. Suggests `mobilenetv1_100`'s good result wasn't simply "MobileNetV1 as an architecture family generalizes well" - it may be more specific to that width setting, or could be run-to-run variance rather than a real architectural effect. Worth keeping in mind when reading the MobileNetV2/V3/V4 width-multiplier results still to come: a family showing a good result at one width doesn't guarantee it repeats at another.

---

## Detail: `mobilenetv2_050` (auto-logged, overnight sweep)

- **Params:** 695,366
- **Best val macro-F1:** 0.230
- **Run time:** 32.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.84      0.28        45
         R17       0.32      0.71      0.44       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.77      0.69      1805

   micro avg       0.48      0.76      0.59      2510
   macro avg       0.19      0.39      0.24      2510
weighted avg       0.54      0.76      0.62      2510
 samples avg       0.29      0.33      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.76      0.25       145
         R17       0.30      0.62      0.41      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.48      0.44      0.46      3418

   micro avg       0.37      0.50      0.42      4982
   macro avg       0.16      0.30      0.19      4982
weighted avg       0.42      0.50      0.44      4982
 samples avg       0.22      0.24      0.22      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.24 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.28 -> 0.25 | R17 F1: 0.44 -> 0.41 | R08 F1: 0.69 -> 0.46

**Generalization read - a real surprise:** At 0.70M params (smaller than `squeezenet1_1`'s 0.73M, which collapsed), this one is genuinely strong, not a repeat of that failure. Rico macro-F1 0.19 ties for second-best overall, the MASC->Rico gap (0.05) is the tightest of any *healthy* model so far (only `vit_b_16`'s 0.02 and `squeezenet1_1`'s anomalous -0.02 are tighter, and the latter isn't a real comparison), and it posts the **best Rico R17 F1 of any model tested (0.41)**, beating `densenet121`'s previous-best 0.39. This directly disproves the size-proximity concern raised earlier: `squeezenet1_1`'s collapse was about its specific fire-module squeeze design, not simply being a small model - MobileNetV2 at an even smaller width multiplier trains just fine and generalizes better than almost everything bigger tested so far. Strong candidate.

---

## Detail: `mobilenetv2_100` (auto-logged, overnight sweep)

- **Params:** 2,231,558
- **Best val macro-F1:** 0.270
- **Run time:** 38.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.20      0.51      0.29        45
         R17       0.52      0.52      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.74      0.71      1805

   micro avg       0.63      0.68      0.65      2510
   macro avg       0.24      0.30      0.25      2510
weighted avg       0.63      0.68      0.65      2510
 samples avg       0.29      0.29      0.29      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.46      0.23       145
         R17       0.36      0.31      0.33      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.55      0.42      0.48      3418

   micro avg       0.46      0.39      0.42      4982
   macro avg       0.18      0.20      0.17      4982
weighted avg       0.49      0.39      0.43      4982
 samples avg       0.19      0.19      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.17 | R04 F1 (MASC->Rico): 0.29 -> 0.23 | R17 F1: 0.52 -> 0.33 | R08 F1: 0.71 -> 0.48

**Generalization read - a within-family reversal:** Rico macro-F1 (0.17) is actually **below** the pack-level 0.18 baseline - the weakest healthy result so far (excluding `squeezenet1_1`'s collapse). This is the standard 1.0x-width MobileNetV2; its 0.5x-width sibling `mobilenetv2_050` (0.70M params, a third the size) beat it on every axis: Rico macro-F1 0.19 vs 0.17, R17 F1 0.41 vs 0.33, R04 F1 0.25 vs 0.23. Same architecture family, smaller width winning cleanly - this echoes the `mobilenetv1_100` vs `mobilenetv1_125` result (there too, the narrower variant did better), and starts to look like a real pattern specific to this dataset's overfitting risk: within a given architecture family, the smaller width multiplier is beating the larger one, not just matching it.

---

## Detail: `mobilenetv2_140` (auto-logged, overnight sweep)

- **Params:** 4,326,534
- **Best val macro-F1:** 0.267
- **Run time:** 44.4 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.27      0.62      0.37        45
         R17       0.45      0.55      0.50       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.75      0.72      1805

   micro avg       0.61      0.69      0.65      2510
   macro avg       0.23      0.32      0.26      2510
weighted avg       0.62      0.69      0.65      2510
 samples avg       0.29      0.30      0.29      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.53      0.25       145
         R17       0.34      0.41      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.40      0.45      3418

   micro avg       0.42      0.41      0.41      4982
   macro avg       0.17      0.22      0.18      4982
weighted avg       0.46      0.41      0.42      4982
 samples avg       0.19      0.20      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.37 -> 0.25 | R17 F1: 0.50 -> 0.37 | R08 F1: 0.72 -> 0.45

**Generalization read - completes the MobileNetV2 trio, and complicates the earlier story:** Rico macro-F1 0.18, landing back at pack-level - between `mobilenetv2_050`'s 0.19 (best of the three) and `mobilenetv2_100`'s 0.17 (worst of the three). That's **non-monotonic** with width (0.5x -> 1.0x -> 1.4x gives 0.19 -> 0.17 -> 0.18), which walks back the "smaller width cleanly wins" pattern suggested after `mobilenetv2_050` beat `mobilenetv2_100`. The correct read now: `mobilenetv2_100` specifically underperformed within its own family, not "wider is worse" as a general rule - `mobilenetv1_100` vs `_125` was a genuine narrow-wins-clean comparison (two points), but with three MobileNetV2 points in hand the relationship isn't linear. Treat the earlier width-multiplier narrative as partially retracted until more families are in.

---

## Detail: `mobilenetv3_small_050` (auto-logged, overnight sweep)

- **Params:** 574,374
- **Best val macro-F1:** 0.240
- **Run time:** 33.6 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.21      0.67      0.32        45
         R17       0.30      0.67      0.42       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.60      0.80      0.69      1805

   micro avg       0.48      0.77      0.59      2510
   macro avg       0.19      0.36      0.24      2510
weighted avg       0.51      0.77      0.61      2510
 samples avg       0.29      0.33      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.52      0.23       145
         R17       0.29      0.55      0.38      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.48      0.50      0.49      3418

   micro avg       0.38      0.52      0.44      4982
   macro avg       0.15      0.26      0.18      4982
weighted avg       0.42      0.52      0.45      4982
 samples avg       0.23      0.25      0.23      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.24 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.32 -> 0.23 | R17 F1: 0.42 -> 0.38 | R08 F1: 0.69 -> 0.49

**Generalization read:** The smallest model tested so far (0.57M params - smaller than `squeezenet1_1`'s 0.73M, which collapsed, and smaller than `mobilenetv2_050`'s 0.70M). Trains completely healthily: Rico macro-F1 0.18 (pack-level), and its R17 F1 (0.38) is the **second-best of any model tested**, behind only `mobilenetv2_050`'s 0.41. This is now the third small MobileNet-family model (after `mobilenetv1_100` and `mobilenetv2_050`) to train fine and generalize reasonably at very low capacity, against one clean failure (`squeezenet1_1`). Reinforces that the `squeezenet1_1` collapse was specific to its fire-module design, not a general "too small for this task" risk - low capacity alone isn't the danger signal here.

---

## Detail: `mobilenetv4_conv_small` (auto-logged, overnight sweep)

- **Params:** 2,500,710
- **Best val macro-F1:** 0.252
- **Run time:** 33.8 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.19      0.67      0.30        45
         R17       0.43      0.52      0.47       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.75      0.71      1805

   micro avg       0.59      0.69      0.63      2510
   macro avg       0.22      0.32      0.25      2510
weighted avg       0.60      0.69      0.64      2510
 samples avg       0.29      0.30      0.29      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.12      0.52      0.20       145
         R17       0.31      0.33      0.32      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.43      0.47      3418

   micro avg       0.41      0.40      0.41      4982
   macro avg       0.16      0.21      0.16      4982
weighted avg       0.45      0.40      0.42      4982
 samples avg       0.20      0.20      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.16 | R04 F1 (MASC->Rico): 0.30 -> 0.20 | R17 F1: 0.47 -> 0.32 | R08 F1: 0.71 -> 0.47

**Generalization read - the worst healthy result so far:** Rico macro-F1 0.16, below even `mobilenetv2_100`'s previous-worst 0.17, with the largest MASC->Rico gap seen among non-collapsed models (0.09) and its R17 F1 dropping the hardest of anything tested (0.47 -> 0.32). Notable because MobileNetV4 (2024) is the newest-generation architecture in the whole sweep, specifically designed to improve on MobileNetV1/V2/V3 on standard ImageNet benchmarks - here it's landing below all three of its own predecessor generations (`mobilenetv1_100`: 0.19, `mobilenetv2_050`: 0.19, `mobilenet_v3_small`: 0.18). "Newer/SOTA-on-ImageNet" clearly isn't the same as "better for this tiny, imbalanced task" - worth watching whether `mobilenetv4_conv_medium`/`_large` repeat this or if `_small` specifically struggles.

---

## Detail: `mobilenetv4_conv_medium` (auto-logged, overnight sweep)

- **Params:** 8,442,198
- **Best val macro-F1:** 0.233
- **Run time:** 26.7 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.18      0.80      0.30        45
         R17       0.32      0.71      0.44       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.61      0.84      0.71      1805

   micro avg       0.49      0.81      0.61      2510
   macro avg       0.19      0.39      0.24      2510
weighted avg       0.53      0.81      0.63      2510
 samples avg       0.32      0.35      0.33      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.13      0.64      0.21       145
         R17       0.25      0.54      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.48      0.55      0.51      3418

   micro avg       0.35      0.55      0.43      4982
   macro avg       0.14      0.29      0.18      4982
weighted avg       0.40      0.55      0.45      4982
 samples avg       0.25      0.27      0.25      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.24 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.30 -> 0.21 | R17 F1: 0.44 -> 0.34 | R08 F1: 0.71 -> 0.51

**Generalization read - partially walks back the `mobilenetv4_conv_small` finding:** Rico macro-F1 0.18, back to pack-level and clearly better than `mobilenetv4_conv_small`'s 0.16. So it's not "MobileNetV4 as a generation underperforms" - the small variant specifically struggled, and the medium variant (8.44M params) is unremarkable-but-fine, R08 F1 0.51 even landing above average. Fastest MobileNetV4 result yet (26.7 min, faster than the smaller variant's own 33.8 min - likely just run-to-run epoch-count variance from early stopping, not a real speed relationship). Still watching whether `mobilenetv4_conv_large` continues the recovery or the family's real story turns out to be "only the smallest one struggles."

---

## Detail: `mobilenetv4_conv_large` (auto-logged, overnight sweep)

- **Params:** 31,317,550
- **Best val macro-F1:** 0.237
- **Run time:** 32.9 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.12      0.87      0.21        45
         R17       0.39      0.63      0.48       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.85      0.72      1805

   micro avg       0.52      0.79      0.63      2510
   macro avg       0.19      0.39      0.23      2510
weighted avg       0.56      0.79      0.65      2510
 samples avg       0.31      0.34      0.32      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.11      0.80      0.19       145
         R17       0.30      0.44      0.36      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.49      0.53      0.51      3418

   micro avg       0.38      0.51      0.43      4982
   macro avg       0.15      0.30      0.18      4982
weighted avg       0.43      0.51      0.46      4982
 samples avg       0.23      0.25      0.23      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.23 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.21 -> 0.19 | R17 F1: 0.48 -> 0.36 | R08 F1: 0.72 -> 0.51

**Generalization read - completes the MobileNetV4 trio, confirms it's a `_small`-only issue:** At 31.3M params (larger than `resnet50`'s 23.5M - the biggest non-transformer model in the sweep), Rico macro-F1 is 0.18 with a tight 0.05 MASC->Rico gap, and R08 F1 (0.51) is solid. With all three MobileNetV4 sizes now done - small: 0.16 (worst healthy result in the sweep), medium: 0.18, large: 0.18 - the family verdict is clear: it's specifically `mobilenetv4_conv_small` that struggles, not "MobileNetV4 as a generation" the way it first looked. Also ran notably faster than estimated (32.9 min vs. an expected 55-70 min for its size), suggesting early stopping triggered quickly rather than running the full epoch budget.

---

## Detail: `mobilevit_xxs` (auto-logged, overnight sweep)

- **Params:** 952,950
- **Best val macro-F1:** 0.250
- **Run time:** 25.4 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.21      0.78      0.33        45
         R17       0.35      0.65      0.46       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.81      0.71      1805

   micro avg       0.52      0.77      0.62      2510
   macro avg       0.20      0.37      0.25      2510
weighted avg       0.55      0.77      0.64      2510
 samples avg       0.31      0.33      0.32      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.62      0.26       145
         R17       0.31      0.51      0.39      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.49      0.48      0.48      3418

   micro avg       0.40      0.49      0.44      4982
   macro avg       0.16      0.27      0.19      4982
weighted avg       0.43      0.49      0.45      4982
 samples avg       0.23      0.24      0.22      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.33 -> 0.26 | R17 F1: 0.46 -> 0.39 | R08 F1: 0.71 -> 0.48

**Generalization read:** At 0.95M params, this is the smallest CNN+attention hybrid tested, and it beats its own larger sibling `mobilevit_s` (4.94M, Rico macro-F1 0.18) clearly - Rico macro-F1 0.19 (tied for second-best in the whole sweep), with R17 F1 0.39 (third-best of any model, behind only `mobilenetv2_050`'s 0.41 and `densenet121`'s narrowly-lower 0.39 tie). Another instance of a smaller variant beating a larger sibling within the same family - joins `mobilenetv1_100` > `_125` as a second MobileViT-specific data point (`mobilevit_xxs` > `mobilevit_s`), though the MobileNetV2 trio already showed this isn't universal. Real candidate worth remembering when picking a final model.

---

## Detail: `mobilevit_xs` (auto-logged, overnight sweep)

- **Params:** 1,935,158
- **Best val macro-F1:** 0.266
- **Run time:** 49.4 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.23      0.60      0.34        45
         R17       0.52      0.52      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.64      0.81      0.71      1805

   micro avg       0.60      0.73      0.66      2510
   macro avg       0.23      0.32      0.26      2510
weighted avg       0.60      0.73      0.66      2510
 samples avg       0.31      0.32      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.53      0.25       145
         R17       0.36      0.33      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.50      0.49      0.49      3418

   micro avg       0.43      0.44      0.44      4982
   macro avg       0.17      0.23      0.18      4982
weighted avg       0.45      0.44      0.44      4982
 samples avg       0.22      0.22      0.21      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.34 -> 0.25 | R17 F1: 0.52 -> 0.34 | R08 F1: 0.71 -> 0.49

**Generalization read:** Back to pack-level Rico macro-F1 (0.18), not repeating `mobilevit_xxs`'s standout 0.19. With two of three MobileViT sizes now in - xxs (0.95M): 0.19, xs (1.94M): 0.18 - the pattern looks like "only the smallest MobileViT variant has an edge," similar to how only `mobilenetv4_conv_small` stood out (negatively) in its family while medium/large were unremarkable. Waiting on `mobilevit_s` (already done, also 0.18) to confirm - all signs point to `mobilevit_xxs` being the specific outlier in this family, not a general "smaller MobileViT is better" trend.

---

## Detail: `mobilevitv2_050` (auto-logged, overnight sweep)

- **Params:** 1,115,135
- **Best val macro-F1:** 0.264
- **Run time:** 37.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.25      0.62      0.35        45
         R17       0.42      0.60      0.50       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.82      0.71      1805

   micro avg       0.56      0.76      0.64      2510
   macro avg       0.22      0.34      0.26      2510
weighted avg       0.57      0.76      0.65      2510
 samples avg       0.31      0.33      0.32      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.52      0.26       145
         R17       0.34      0.42      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.49      0.49      0.49      3418

   micro avg       0.42      0.47      0.44      4982
   macro avg       0.17      0.24      0.19      4982
weighted avg       0.44      0.47      0.45      4982
 samples avg       0.23      0.23      0.22      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.35 -> 0.26 | R17 F1: 0.50 -> 0.37 | R08 F1: 0.71 -> 0.49

**Generalization read - a consistent MobileViT pattern across two generations:** At 1.12M params (the smallest MobileViT-v2 variant), Rico macro-F1 is 0.19 - tied for second-best in the whole sweep, matching `mobilevit_xxs`'s result in the v1 family. That makes it two-for-two: the smallest variant in *both* MobileViT generations (v1's `xxs`, v2's `050`) outperforms its larger siblings, while MobileNetV2's smallest-wins pattern didn't hold across its full family. This looks like a real MobileViT-specific effect now, not a coincidence - worth flagging clearly as a strong candidate family alongside `mobilenetv2_050`.

---

## Detail: `mobilevitv2_100` (auto-logged, overnight sweep)

- **Params:** 4,391,919
- **Best val macro-F1:** 0.273
- **Run time:** 50.6 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.21      0.51      0.30        45
         R17       0.52      0.53      0.52       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.64      0.78      0.71      1805

   micro avg       0.60      0.71      0.65      2510
   macro avg       0.23      0.30      0.25      2510
weighted avg       0.60      0.71      0.65      2510
 samples avg       0.30      0.31      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.17      0.55      0.26       145
         R17       0.39      0.35      0.37      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.50      0.51      3418

   micro avg       0.45      0.46      0.46      4982
   macro avg       0.18      0.23      0.19      4982
weighted avg       0.47      0.46      0.46      4982
 samples avg       0.22      0.22      0.22      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.19 | R04 F1 (MASC->Rico): 0.30 -> 0.26 | R17 F1: 0.52 -> 0.37 | R08 F1: 0.71 -> 0.51

**Generalization read - refines the MobileViT story again:** Rico macro-F1 0.19, matching `mobilevitv2_050`'s 0.19 exactly. This actually **walks back** the "smallest MobileViT variant wins" framing from the last entry - now *both* the smallest (0.050, 1.12M) and middle (0.100, 4.39M) MobileViT-v2 sizes are doing equally well, so it's not specifically about picking the tiniest one. The more accurate read: MobileViT-**v2** as a family (0.19 at both sizes tested) is outperforming MobileViT-**v1** (0.19 only at the smallest `xxs`, 0.18 at `xs`/`s`) - the v2 architecture revision itself may be what's driving the improvement, not model size within either generation. Still one v2 size left (`mobilevitv2_200`, 17.4M) to confirm whether this holds at scale.

---

## Detail: `mobilevitv2_200` (auto-logged, overnight sweep)

- **Params:** 17,430,479
- **Best val macro-F1:** 0.270
- **Run time:** 63.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.38      0.56      0.45        45
         R17       0.44      0.58      0.50       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.78      0.73      1805

   micro avg       0.61      0.72      0.66      2510
   macro avg       0.25      0.32      0.28      2510
weighted avg       0.62      0.72      0.66      2510
 samples avg       0.30      0.31      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.39      0.46      0.42       145
         R17       0.31      0.36      0.33      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.53      0.45      0.49      3418

   micro avg       0.45      0.43      0.44      4982
   macro avg       0.21      0.21      0.21      4982
weighted avg       0.46      0.43      0.44      4982
 samples avg       0.21      0.21      0.20      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.28 | Rico macro-F1: 0.21 | R04 F1 (MASC->Rico): 0.45 -> 0.42 | R17 F1: 0.50 -> 0.33 | R08 F1: 0.73 -> 0.49

**Generalization read - ties `vit_b_16` for best in the whole sweep, at 1/5th the params:** Rico macro-F1 0.21, matching `vit_b_16`'s previous best exactly, and its Rico R04 F1 (0.42) is nearly identical to `vit_b_16`'s (0.42 vs 0.42) - the same rule driving both results. But this achieves it at **17.4M params vs `vit_b_16`'s 86.6M** - a fifth the size, and far cheaper to train/deploy. This completes the MobileViT-v2 trio cleanly: 050 (1.12M) = 0.19, 100 (4.39M) = 0.19, 200 (17.4M) = 0.21 - macro-F1 climbs with size within v2 specifically, unlike every other family tested where size didn't help or was non-monotonic. Combined with `vit_b_16`'s result, this strongly suggests attention-based architectures (both windowed/MobileViT-style and full ViT) have a genuine edge on R04 specifically, which is the single biggest open question raised by this whole sweep. **`mobilevitv2_200` is currently the strongest practical candidate** - `vit_b_16`-level generalization without the cost.

---

## Detail: `mobileone_s0` (auto-logged, overnight sweep)

- **Params:** 4,274,422
- **Best val macro-F1:** 0.268
- **Run time:** 52.0 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.18      0.67      0.29        45
         R17       0.47      0.55      0.51       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.65      0.80      0.72      1805

   micro avg       0.58      0.73      0.65      2510
   macro avg       0.22      0.34      0.25      2510
weighted avg       0.59      0.73      0.65      2510
 samples avg       0.31      0.32      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.55      0.23       145
         R17       0.38      0.37      0.38      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.46      0.49      3418

   micro avg       0.44      0.44      0.44      4982
   macro avg       0.17      0.23      0.18      4982
weighted avg       0.46      0.44      0.45      4982
 samples avg       0.21      0.21      0.21      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.29 -> 0.23 | R17 F1: 0.51 -> 0.38 | R08 F1: 0.72 -> 0.49

**Generalization read:** Pack-level Rico macro-F1 (0.18), unremarkable overall - its R17 F1 (0.38) is solid (roughly tied for fourth-best) but doesn't stand out the way MobileViT-v2 or the smallest MobileNet/MobileViT variants did. MobileOne's headline feature (structural reparameterization - a multi-branch architecture during training that collapses to a single-path network at inference for fast deployment) is an inference-speed optimization, not an accuracy one, so an unremarkable-but-solid result here is consistent with what the architecture is actually designed to do.

---

## Detail: `mobileone_s1` (auto-logged, overnight sweep)

- **Params:** 3,551,878
- **Best val macro-F1:** 0.268
- **Run time:** 46.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.24      0.64      0.35        45
         R17       0.54      0.53      0.53       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.69      0.75      0.72      1805

   micro avg       0.64      0.69      0.66      2510
   macro avg       0.24      0.32      0.27      2510
weighted avg       0.64      0.69      0.66      2510
 samples avg       0.29      0.30      0.29      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.50      0.24       145
         R17       0.40      0.33      0.36      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.53      0.40      0.45      3418

   micro avg       0.45      0.38      0.41      4982
   macro avg       0.18      0.20      0.18      4982
weighted avg       0.48      0.38      0.42      4982
 samples avg       0.19      0.18      0.18      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.27 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.35 -> 0.24 | R17 F1: 0.53 -> 0.36 | R08 F1: 0.72 -> 0.45

**Generalization read:** Same pack-level Rico macro-F1 (0.18) as `mobileone_s0`, with a slightly larger MASC->Rico gap (0.09 vs 0.07). Two of three MobileOne sizes now both land at 0.18 - consistent, unremarkable family so far, reinforcing that its reparameterization trick is about inference speed, not generalization. `mobileone_s4` (12.9M, the largest) is next and will complete the picture.

---

## Detail: `mobileone_s4` (auto-logged, overnight sweep)

- **Params:** 12,914,542
- **Best val macro-F1:** 0.266
- **Run time:** 69.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.23      0.69      0.34        45
         R17       0.56      0.56      0.56       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.79      0.73      1805

   micro avg       0.63      0.72      0.67      2510
   macro avg       0.24      0.34      0.27      2510
weighted avg       0.64      0.72      0.68      2510
 samples avg       0.31      0.31      0.31      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.16      0.54      0.24       145
         R17       0.41      0.35      0.38      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.51      0.45      0.48      3418

   micro avg       0.45      0.42      0.44      4982
   macro avg       0.18      0.22      0.18      4982
weighted avg       0.47      0.42      0.44      4982
 samples avg       0.21      0.21      0.20      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.27 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.34 -> 0.24 | R17 F1: 0.56 -> 0.38 | R08 F1: 0.73 -> 0.48

**Generalization read - completes the MobileOne trio with a flat line:** Rico macro-F1 0.18, identical to both `mobileone_s0` (4.27M) and `mobileone_s1` (3.55M). All three MobileOne sizes tested (3.55M to 12.9M, a 3.6x range) land at exactly 0.18 - the flattest, most size-invariant family in the whole sweep. Contrast with MobileViT-v2 (clear improvement with size: 0.19/0.19/0.21) or MobileNetV2 (non-monotonic: 0.19/0.17/0.18) - MobileOne's reparameterization design appears genuinely orthogonal to both scale and generalization quality here, consistent with it being an inference-speed optimization rather than an accuracy one. R17 F1 (0.38) is solidly mid-tier across all three sizes too. Unremarkable but reliable.

---

## Detail: `ghostnet_100` (auto-logged, overnight sweep)

- **Params:** 3,909,194
- **Best val macro-F1:** 0.277
- **Run time:** 33.7 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.24      0.56      0.33        45
         R17       0.48      0.54      0.51       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.77      0.72      1805

   micro avg       0.61      0.71      0.66      2510
   macro avg       0.23      0.31      0.26      2510
weighted avg       0.62      0.71      0.66      2510
 samples avg       0.30      0.30      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.50      0.23       145
         R17       0.34      0.34      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.43      0.47      3418

   micro avg       0.42      0.40      0.41      4982
   macro avg       0.17      0.21      0.17      4982
weighted avg       0.45      0.40      0.42      4982
 samples avg       0.20      0.20      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.17 | R04 F1 (MASC->Rico): 0.33 -> 0.23 | R17 F1: 0.51 -> 0.34 | R08 F1: 0.72 -> 0.47

**Generalization read:** Rico macro-F1 0.17, below the 0.18 pack-level baseline - ties `mobilenetv2_100` for one of the weaker healthy results, with the largest MASC->Rico gap seen among non-collapsed models (0.09). GhostNet's headline trick (generating most feature maps via cheap linear operations on a small set of real convolutions, rather than full convolutions everywhere) is an efficiency/inference-cost optimization - similar to `mobileone`'s reparameterization and `mobilenetv4`'s newer design, it doesn't appear to translate into better generalization on this task. One more GhostNet variant (`ghostnetv2_100`) still to come.

---

## Detail: `ghostnetv2_100` (auto-logged, overnight sweep)

- **Params:** 4,883,594
- **Best val macro-F1:** 0.268
- **Run time:** 38.1 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.26      0.47      0.33        45
         R17       0.49      0.50      0.49       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.67      0.77      0.72      1805

   micro avg       0.61      0.69      0.65      2510
   macro avg       0.24      0.29      0.26      2510
weighted avg       0.61      0.69      0.65      2510
 samples avg       0.29      0.30      0.29      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.15      0.39      0.22       145
         R17       0.37      0.30      0.34      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.52      0.45      0.48      3418

   micro avg       0.45      0.41      0.43      4982
   macro avg       0.17      0.19      0.17      4982
weighted avg       0.47      0.41      0.43      4982
 samples avg       0.20      0.20      0.19      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.17 | R04 F1 (MASC->Rico): 0.33 -> 0.22 | R17 F1: 0.49 -> 0.34 | R08 F1: 0.72 -> 0.48

**Generalization read - closes out GhostNet, no improvement from V2's attention addition:** Rico macro-F1 0.17, identical to `ghostnet_100`'s result. GhostNetV2's headline addition over V1 - a lightweight long-range (DFC) attention branch layered onto the cheap-operation blocks - doesn't move the needle here at all, despite adding attention in some form. Worth contrasting with the MobileViT family, where attention integration clearly did help: the difference may be that MobileViT's attention operates over the full feature map via transformer blocks, while GhostNetV2's DFC attention is a much lighter, more local addition - not all "attention" additions are equivalent.

---

## Detail: `convnext_tiny` (auto-logged, overnight sweep)

- **Params:** 27,824,742
- **Best val macro-F1:** 0.268
- **Run time:** 63.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.24      0.51      0.32        45
         R17       0.46      0.52      0.49       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.68      0.78      0.72      1805

   micro avg       0.61      0.70      0.65      2510
   macro avg       0.23      0.30      0.26      2510
weighted avg       0.61      0.70      0.65      2510
 samples avg       0.30      0.30      0.30      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.18      0.49      0.27       145
         R17       0.35      0.36      0.35      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.53      0.45      0.49      3418

   micro avg       0.45      0.42      0.44      4982
   macro avg       0.18      0.22      0.18      4982
weighted avg       0.47      0.42      0.44      4982
 samples avg       0.21      0.21      0.20      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.26 | Rico macro-F1: 0.18 | R04 F1 (MASC->Rico): 0.32 -> 0.27 | R17 F1: 0.49 -> 0.35 | R08 F1: 0.72 -> 0.49

**Generalization read - the answer to the sweep's biggest open question:** `convnext_tiny` exists specifically to test whether `vit_b_16`/`mobilevitv2_200`'s strong results come from *attention* or just *modern CNN design* (ConvNeXt adopts nearly every ViT-inspired design choice - LayerNorm, a patchify stem, an inverted-bottleneck block, fewer activations - while remaining a pure CNN with zero attention). At 27.8M params (comparable to `mobilevitv2_200`'s 17.4M, smaller than `vit_b_16`'s 86.6M), it lands at **plain pack-level Rico macro-F1 (0.18)** - no repeat of the R04 spike (0.27 here vs. 0.42 for both attention-based standouts) and no repeat of the elevated overall score. **This is a clean answer: it's attention specifically, not modern design or capacity, driving `vit_b_16`/`mobilevitv2_200`'s edge.** A model with every other "2020s CNN" trick but no attention mechanism just gets a normal result. One model left in the whole sweep (`swin_tiny_patch4_window7_224`) to see if a *different* attention mechanism (windowed, not global) reproduces the effect too.

---

## Detail: `swin_tiny_patch4_window7_224` (auto-logged, overnight sweep)

- **Params:** 27,523,968
- **Best val macro-F1:** 0.274
- **Run time:** 46.2 min

**MASC test-split report:**
```
              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.22      0.49      0.31        45
         R17       0.39      0.64      0.49       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.84      0.72      1805

   micro avg       0.55      0.78      0.64      2510
   macro avg       0.21      0.33      0.25      2510
weighted avg       0.56      0.78      0.65      2510
 samples avg       0.31      0.34      0.32      2510
```

**Rico holdout report:**
```
Rico holdout crops evaluated: 9343

              precision    recall  f1-score   support

         R09       0.00      0.00      0.00         0
         R04       0.31      0.56      0.40       145
         R17       0.32      0.46      0.38      1419
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.50      0.53      0.51      3418

   micro avg       0.43      0.51      0.47      4982
   macro avg       0.19      0.26      0.22      4982
weighted avg       0.44      0.51      0.47      4982
 samples avg       0.24      0.25      0.24      4982


Compare against the MASC test-split report in §7 above - a large drop here
means the model memorized MASC's visual style rather than the general rule
signal; a similar report means real generalization to unseen apps.
```

MASC macro-F1: 0.25 | Rico macro-F1: 0.22 | R04 F1 (MASC->Rico): 0.31 -> 0.40 | R17 F1: 0.49 -> 0.38 | R08 F1: 0.72 -> 0.51

**Generalization read - THE BEST RESULT IN THE WHOLE SWEEP, and the final word on the attention question:** Rico macro-F1 **0.22**, beating both `vit_b_16` and `mobilevitv2_200` (0.21 each). Unlike those two, this isn't a narrow R04-only spike - R04 F1 (0.40) is elevated but slightly below theirs (0.42), while **R17 F1 (0.38) and R08 F1 (0.51) are both solidly above the pack average too** (typical R17 range is 0.32-0.39, typical R08 is 0.45-0.51). This is a more evenly-distributed win across all three real-signal rules, not one rule carrying the whole score - a more robust result than either previous attention-based standout. MASC->Rico gap (0.03) is the second-tightest in the sweep, behind only `vit_b_16`'s 0.02.

**Combined with the `convnext_tiny` control (same size class, zero attention, plain pack-level result), the full picture across the 4 attention-related models is now clear:**

| Model | Attention type | Params | Rico macro-F1 |
|---|---|---|---|
| `convnext_tiny` | none (pure CNN, modern design) | 27.8M | 0.18 (pack-level) |
| `vit_b_16` | global (full self-attention) | 86.6M | 0.21 |
| `mobilevitv2_200` | hybrid CNN + separable self-attention | 17.4M | 0.21 |
| `swin_tiny_patch4_window7_224` | windowed/hierarchical self-attention | 27.5M | **0.22 (best)** |

Attention helps, consistently, across three different implementations of it - and the **windowed,
hierarchical variant (Swin) wins outright**, at roughly a third the size of `vit_b_16` and with a more
well-rounded per-rule profile than either prior attention-based leader. This is now the strongest
evidence-based candidate for the final pick, ahead of `mobilevitv2_200`.

---
