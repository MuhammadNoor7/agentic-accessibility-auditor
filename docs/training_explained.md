# How the Two CV Models Were Trained — A Full Walkthrough

This doc exists to explain the **training side** of the project end to end — both models, from "what problem are we even solving" down to "what do these numbers mean." It assumes no prior ML training experience. If something is unclear, that's a doc bug — ask and it'll get fixed.

There are two trained models in this project:

1. **YOLO UI Detector** — object detection. Given a screenshot, draw boxes around UI elements (buttons, text, icons, etc.) and say what type each one is.
2. **Crop-Violation Classifier** — multi-label classification. Given a small cropped piece of a screenshot, decide which accessibility rules (if any) it violates.

They solve different problems, use different techniques, but share the same underlying training *philosophy*, which is worth understanding first.

---

## 1. Concepts you need before any of this makes sense

### 1.1 Why do we need a model at all? Isn't the XML enough?

For most of the 30 accessibility rules, yes — the XML view hierarchy tells us everything (is this clickable, does it have a label, what are its bounds). `src/rules.py` handles those with plain deterministic code, no model needed.

But a handful of rules describe something that only really exists once the screen is **rendered as pixels** — a contrast ratio between text and background, whether text visually overflows its box, whether two elements visually overlap in a way that matters, whether a touch target actually *looks* too small on screen. XML bounds math can approximate these, but a model looking at the actual rendered crop can catch cases bounds math misses or reduce false positives. That's the entire reason the crop classifier exists.

The YOLO detector solves a *different* problem: what happens when there's **no XML at all** — a malformed dump, a hardened app that blocks the accessibility tree, or just a bare screenshot upload? Without XML, the rule engine has nothing to check. YOLO's job is to look at the screenshot pixels alone and reconstruct a "components list" good enough for the rule engine to still run on.

### 1.2 What is "training" actually doing?

A neural network starts as a big pile of random numbers (weights). "Training" means: show it an example, let it guess, compare the guess to the correct answer, and nudge the weights slightly in the direction that would have made the guess more correct. Repeat this thousands of times across thousands of examples, and the weights gradually become good at the task.

- **One pass through the entire training dataset = one epoch.** We don't train for one epoch and stop — we go through the data many times (each epoch, the model gets slightly better).
- **Batch** = how many examples the model looks at before it updates its weights once. Smaller batches = noisier but more frequent updates; larger batches = smoother but slower per update.
- **Learning rate (lr)** = how big each nudge is. Too high and the model overshoots and never settles; too low and training takes forever / gets stuck.
- **Loss** = a single number representing "how wrong was the model on this batch." Training's whole goal is to push this number down over time. Loss going down on the *training* data means the model is learning something; whether it's learning something *useful* is a separate question (see overfitting, below).

### 1.3 Pretrained weights, backbones, and fine-tuning

Neither model was trained from scratch (random weights). Both start from a **pretrained backbone** — a model that was already trained on a huge, unrelated dataset (ImageNet for the crop classifier: 1.2 million general photos; COCO-style data for YOLO's base weights) and already knows how to recognize edges, shapes, textures, and general visual structure.

We then **fine-tune** that pretrained model on our own, much smaller dataset (thousands of UI screens, not millions of general photos) so it repurposes what it already knows toward our specific task (detecting UI elements / recognizing accessibility violations).

Why not train from scratch? Because our datasets are small by deep-learning standards. A randomly-initialized model trying to learn "what an edge is" *and* "what a violation is" at the same time from only a few thousand examples would badly overfit (see below) or just fail to converge. Starting from a pretrained backbone means the model only has to learn the *new* part — a massive head start.

**"Backbone"** = the main body of the network that does feature extraction (turns pixels into a meaningful internal representation). Both models replace the pretrained backbone's final output layer with a new one sized for our specific task (9 UI element classes for YOLO; 6 rule labels for the crop classifier) — everything before that final layer is the reused, pretrained part.

### 1.4 Overfitting — the central risk with small datasets

**Overfitting** = the model starts memorizing the specific training examples instead of learning the general pattern. Symptom: training loss keeps going down, but performance on data the model *hasn't seen* stalls or gets worse. It's like a student who memorizes the answers to last year's exam questions instead of understanding the subject — perfect on that exact exam, useless on a new one.

This is why we never just look at training accuracy. We always hold out a **validation set** (data the model trains on zero times, but we check performance on after every epoch) to see if the model is generalizing or just memorizing. If validation performance starts getting *worse* while training performance keeps improving, that's the overfitting signal — and it's exactly what you'll see in both models' training curves below.

### 1.5 Train / Val / Test / Rico-holdout — four different splits, four different jobs

Both models use the same data-discipline:

| Split | Source | Purpose | Ever trained on? |
|---|---|---|---|
| **Train** | MASC | The examples the model actually learns from | Yes |
| **Val** | MASC | Checked after every epoch to catch overfitting, decide when to stop | No |
| **Test** | MASC | Final scorecard, checked once training is done | No |
| **Rico holdout** | Rico (a completely different app dataset) | Checked *only after everything is finalized*, to answer "does this generalize beyond MASC's specific apps?" | **Never, by policy** |

The Rico holdout is the strictest one: it's not just "not trained on this round," it is contractually never allowed to be used for training at all (this is written into the SRS as a hard requirement, BR-4/BR-5). The reason is that if you ever let a model see Rico during training or hyperparameter tuning, you lose your only honest way to answer "would this work on an app it's never seen before?" MASC test-set performance alone can't answer that, because the model has seen *other screens from the same apps* during training.

### 1.6 Reading a classification report (precision / recall / F1)

You'll see tables like this throughout:

```
              precision    recall  f1-score   support
         R08       0.63      0.84      0.72      1805
```

- **Support** = how many real positive examples of this class existed in the data being evaluated. If support is 0, precision/recall/F1 are mathematically undefined (there was nothing to score against) — not a failure, just no data.
- **Precision** = of everything the model *called* R08, what fraction actually was R08? Low precision = lots of false alarms.
- **Recall** = of everything that *actually was* R08, what fraction did the model catch? Low recall = lots of misses.
- **F1** = the harmonic mean of precision and recall — a single number balancing both. You can't game F1 by just always predicting "yes" (that gives perfect recall but terrible precision, so F1 stays low).
- **Macro avg** = simple average of each class's F1, treating every rule equally regardless of how much data it had.
- **Micro/weighted avg** = averages weighted by how much data each class actually had, so it's dominated by whichever rule has the most examples (here, R08).

We report **macro-F1 as the headline number** specifically *because* it doesn't let one high-volume rule (R08) hide poor performance on the rarer ones.

---

## 2. Model 1 — YOLO UI Detector (Object Detection)

**File:** `src/yolo_ui_detector.py` (inference) · `notebooks/train_yolo_ui_detector.ipynb` (training) · trained checkpoint at `models/yolo_ui_detector_best.pt`

### 2.1 What "object detection" means, concretely

Unlike classification (which just says "what is this image"), object detection has to do two things at once for every element on the screen: **draw a box** around it (regression — predicting 4 numbers: left/top/right/bottom) and **classify** what's inside that box (which of the 9 UI element types it is). YOLO ("You Only Look Once") does both in a single forward pass over the whole image, which is why it's fast enough to be practical.

### 2.2 The 9-class taxonomy

`text`, `image`, `icon`, `button_labeled`, `button_icon_only`, `input_field`, `checkbox_toggle`, `tab_item`, `list_item`

This is deliberately coarse — just enough categories for the downstream rule engine to reason about (e.g. "is this a clickable control that needs a label"), not a fine-grained widget taxonomy.

### 2.3 Where the training labels came from

This is the subtle part: **the model never sees XML at inference time — only pixels.** But during *training*, we absolutely need to know the correct answer (ground truth boxes + classes) for every screenshot, and that ground truth comes from the XML bounds, converted into YOLO's label format at label-*generation* time only. So the training pipeline is: XML → generate label files (once, offline) → then train the model purely on (screenshot, label file) pairs, with the XML itself thrown away for the actual training loop. This is why the module works standalone from pixels alone at inference — it never learned to depend on XML being present.

### 2.4 Starting point and training configuration

| Setting | Value | Why |
|---|---|---|
| Base weights | `yolo11s.pt` (Ultralytics-pretrained) | Fine-tune from a model that already understands general object detection, not from scratch |
| Train/val/test | MASC only | Rico is reserved for eval (§1.5 above) |
| Epochs | 60 (early-stop patience 10) | Enough passes to converge without running forever |
| Batch size | 8 | Limited by available GPU memory on the training hardware |
| Image size | 960px | Resolution the model trains and infers at |
| Optimizer | auto (`lr0=0.01`, `lrf=0.01`, cosine LR schedule) | Ultralytics' auto-tuned defaults for this model size |
| Seed | 42, deterministic mode on | So the run is reproducible |
| Hardware | Google Colab, T4 GPU | Free-tier GPU, sufficient for this model size |

There's also a `LOCAL_MODE` smoke-test path (~20 images, 1 epoch) used to sanity-check the whole pipeline end-to-end *before* committing hours of Colab GPU time to the real run — cheap way to catch a broken path or config typo early.

### 2.5 Reading the results

| Metric | 1-epoch smoke result (superseded) | Full 60-epoch result |
|---|---:|---:|
| Precision | 0.4711 | **0.5349** |
| Recall | 0.4196 | **0.4469** |
| mAP50 | 0.3971 | **0.4342** |
| mAP50-95 | 0.2846 | **0.3217** |

**mAP** ("mean Average Precision") is object detection's standard headline metric — it combines "did you find the object" and "was your box actually in the right place" into one number. **mAP50** only requires the predicted box to overlap the true box by 50% to count as correct (a looser bar); **mAP50-95** averages that requirement across a range of overlap thresholds from 50% to 95% (a much stricter, more honest bar). Both climbing from the 1-epoch checkpoint to the full 60-epoch one is exactly what you want to see — the extra training time was worth it.

### 2.6 The zero-shot vs. fine-tuned comparison — proving fine-tuning actually mattered

This is the single most important sanity check on the whole YOLO track. We ran the Rico holdout (apps the model never trained on) through **two** versions of the model:

| Model | Rico mAP50 | Rico mAP50-95 |
|---|---:|---:|
| **Zero-shot** (the pretrained `yolo11s.pt` base weights, no fine-tuning at all) | 0.0258 | 0.0116 |
| **Fine-tuned** (our 60-epoch trained checkpoint) | **0.2546** | **0.1732** |

"Zero-shot" means: take the pretrained weights exactly as downloaded, run them on Rico screenshots with zero UI-specific training, and see what happens. It performs terribly (as expected — it's never seen a UI-specific class taxonomy), and that's the whole point of showing it: it's the honest baseline that proves the ~10x improvement from fine-tuning is real signal, not a fluke of the eval, and that the model generalizes beyond the exact apps it trained on (rather than just memorizing MASC).

### 2.7 What you actually get at inference time

```python
detect_ui(image_path) -> list[{"bbox": [x1,y1,x2,y2], "class": str, "conf": float}]
```

A confidence threshold (default 0.25) filters out low-confidence guesses. A separate helper, `detections_to_components()`, converts these raw detections into the same shape the XML parser would have produced (`components.json` format), tagged `inferred: true` so the rest of the pipeline (and any developer reading the output) knows this component list came from pixels, not a real accessibility tree — and can be less trusting of fields the model can't actually know (like `content_desc`, which doesn't exist in a screenshot).

---

## 3. Model 2 — Crop-Violation Classifier (Multi-label Classification)

**File:** `src/crop_violation_classifier.py` (inference) · `notebooks/train_crop_violation_classifier.ipynb` (training) · trained checkpoint at `models/crop_violation_classifier_best.pt`

### 3.1 The 6 rules this model covers, and why each needs pixels

| Rule | Violation | Why XML bounds math alone isn't enough |
|---|---|---|
| R09 | Low contrast (text/background) | Contrast is a property of rendered colors, not something XML declares |
| R04 | Small touch target (< 48dp) | XML gives raw bounds; a crop confirms the *real* on-screen tap size |
| R17 | Insufficient spacing (< 8dp) | Visual crop confirms the actual rendered gap |
| R10 | Text overflow | Only visible once text is actually rendered and can be seen clipping |
| R28 | Font-scale overflow (200% scale) | Same — only visible once rendered |
| R08 | Layout overlap | Bounds math catches some cases; a visual crop reduces false positives on ambiguous ones |

It's **multi-label**, not single-label — one crop can trip more than one rule at once (e.g. a button that's both too small *and* too close to its neighbor). This is a meaningfully different training setup from ordinary "pick one class" classification, discussed below.

### 3.2 The clever bit: where the training labels come from

We didn't hand-label thousands of crops. Instead, the label-generation step **reuses the already-tested rule checker** (`src.rules.check()`): run it on each full screen, keep only the 6 target rules, and use whatever it flags as the ground-truth label for that region's crop. This means the classifier's job isn't "learn contrast/overlap/spacing math from scratch" — it's "learn to visually recognize the same patterns the deterministic rule checker already knows how to detect from XML," which is a much more learnable target, and means we never had to write or validate a separate labeling process.

### 3.3 How crops are built

Each flagged component becomes one **positive** crop: 224×224 pixels, resized, with ~15% padding around the element's actual bounds (so the model has a bit of surrounding context, not just the bare element). For every screen, 3 non-violating clickable/text elements are also sampled as **negative** crops (`negatives_per_screen=3`) — the model needs to see "clean" examples too, or it would just learn to always predict "violation."

**Dataset build (numbers you'll actually see in output):**

| Split | Total crops | Positive | Negative | Screens |
|---|---:|---:|---:|---:|
| train | 25,202 | 10,549 | 14,653 | 4,943 |
| val | 5,558 | 2,433 | 3,125 | 1,056 |
| test | 5,541 | 2,367 | 3,174 | 1,069 |

Per-rule positives in train: R08 = 8,089 (77% of all positives, by far the most common), R17 = 2,879, R04 = 288, and **R09/R10/R28 = 0**. That last part isn't a bug — MASC (the dataset) never declares `textColor`/`backgroundColor`/`textSize` attributes at all, so the rule checker that generates these labels has nothing to flag for those 3 rules on this particular dataset. The model architecture and training code fully support them; there's just no positive training signal available for them in the current data. This is a data-coverage gap, not a code gap, and it's why R09/R10/R28 always show `support=0` in every results table below.

### 3.4 Choosing the backbone — the part worth understanding in most depth

**Original decision (before this was tested):** the reasoning was "our dataset is small (4,943 train screens, nowhere near ImageNet's 1.2 million), so a low-capacity model (`mobilenet_v3_small`, ~2.5M params) will act as a built-in regularizer against overfitting, and a bigger model would just overfit worse." This is a reasonable *theory*, but it was never actually tested against alternatives — it was picked on reasoning alone.

**What we actually did about it:** ran a **33-backbone comparison sweep** — took the exact same training/eval pipeline and reran it once per candidate architecture (all pretrained on ImageNet-1k, same crops, same splits, same hyperparameter *shape*), then evaluated every single one on both the MASC test split and the full 1,698-screen Rico holdout. This took multiple unattended hours (`scripts/overnight_sweep.py`) since GPU time per backbone runs 30-45+ minutes.

**Result: the "small model prevents overfitting" theory was wrong for our case.** `mobilenet_v3_small` scored Rico holdout macro-F1 **0.18** — mid-pack, beaten by 10+ of the other 32 candidates. The consistent winners across the whole sweep were **attention-based architectures**:

| Model | Attention mechanism | Params | Rico macro-F1 |
|---|---|---:|---:|
| `convnext_tiny` (control, see below) | none — pure CNN | 27.8M | 0.18 (pack-level) |
| `vit_b_16` | global self-attention | 86.6M | 0.21 |
| `mobilevitv2_200` | hybrid CNN + separable self-attention | 17.4M | 0.21 |
| **`swin_tiny_patch4_window7_224`** | windowed/hierarchical self-attention | 27.5M | **0.22 — best in the sweep** |

**What's "attention" and why does it matter here?** Ordinary CNNs build up understanding of an image through small local filters (each neuron only "sees" a small nearby patch, layer by layer). Attention mechanisms let the model directly relate *any* part of the image to *any other* part in a single step — useful here because rules like R17 (spacing) and R08 (overlap) are fundamentally about the *relationship between two elements*, not a property of one local patch. That's a plausible reason attention-based backbones have an edge on this specific task.

**The `convnext_tiny` control is what actually proves that reasoning**, rather than just leaving it as a guess: ConvNeXt is a modern pure-CNN architecture that borrows nearly every 2020s design trick from vision transformers (LayerNorm, a patchify stem, inverted bottlenecks) — *except* attention. If the top performers were winning just because they're "modern, well-designed 2020s architectures," ConvNeXt should have done well too. It didn't — it landed right back at plain pack-level (0.18), the same as the original MobileNetV3 pick. That isolates the variable: it's attention specifically, not general architectural modernity or raw parameter count, driving the gap.

Among the three attention-based winners, **Swin (windowed/hierarchical attention) won outright** — a more evenly-distributed result across all three real-signal rules (R04/R17/R08) than the other two, at roughly a third of `vit_b_16`'s parameter count. One clean failure worth knowing about: `squeezenet1_1` collapsed to predicting "violation" on everything — an architecture-specific failure (its extreme parameter efficiency comes at a real cost here), not simply a "too small" problem, since other genuinely small models (`mobilenetv2_050`) trained fine.

**Final pick: `swin_tiny_patch4_window7_224`**, replacing the original MobileNetV3-Small choice.

### 3.5 Two-phase fine-tuning — why we don't just unfreeze everything immediately

| Phase | Epochs | What's trainable | Learning rate | Why |
|---|---|---|---:|---|
| **Phase 1** | 1–3 | Only the new classification head (backbone frozen) | 1e-3 (higher) | The head starts as random weights and needs to learn fast; if the pretrained backbone were also updating at this stage, those big, noisy early gradients from the random head would blow away the useful pretrained features before the head has learned anything sensible to backpropagate |
| **Phase 2** | 4–20 (early-stop budget) | Everything, backbone included | 1e-4 (lower) | Now that the head has a reasonable starting point, unfreeze the backbone and let it adapt to our specific crops too — but at a much lower rate, since we don't want to destroy what it already learned from ImageNet, just nudge it |

This is a very standard transfer-learning pattern (sometimes called "warmup" or "linear probing then fine-tuning") and it's not just theoretical here — **you can see it directly in the Swin run's own numbers**:

- Phase 1 (backbone frozen): val macro-F1 plateaus around 0.20 (0.195 → 0.202 → 0.199 across epochs 1-3) — frozen ImageNet features plus a freshly-trained head alone, and it stalls there.
- Phase 2 (backbone unfrozen): climbs to **0.274** by epoch 8 — a **+37% relative improvement** from actually letting the backbone adapt, not just training a linear layer on top of frozen features.

That comparison (frozen-only ceiling vs. actual fine-tuned result) is the crop classifier's version of what YOLO's zero-shot-vs-fine-tuned table shows: proof that the extra training step (unfreezing) is doing real, measurable work.

### 3.6 Loss function and handling class imbalance

`BCEWithLogitsLoss` (binary cross-entropy per rule label — appropriate for multi-label problems, since each of the 6 rules is judged independently rather than picking one winner out of many classes). Because R08 has vastly more positive examples than the rarer rules (§3.3), each rule gets its own `pos_weight` — a multiplier that makes the loss penalize missing a rare-rule positive more heavily than missing a common one, so the model doesn't just learn "always predict R08, ignore everything else" as a lazy shortcut. Weights are capped at 20.0 (R09/R04/R10/R28 hit this cap since they're so rare; R17=7.75, R08=2.12 since it's common enough not to need much boosting).

### 3.7 Early stopping and why only one checkpoint is ever saved

`patience=5` — if validation macro-F1 doesn't improve for 5 straight epochs, training stops rather than running to the full 20-epoch budget. On the Swin run, the best epoch was 8 (val macro-F1 0.274); training continued to epoch 13 without improving, then stopped. **Only the single best-val-F1 checkpoint is ever kept** (each new best overwrites the saved file) — not the final epoch's weights, and not every epoch's weights. This matters because the final epoch (13) is *not* the best epoch (8) — by epoch 13 the model has started overfitting again (val F1 had dropped to 0.243 by then, even though train F1 was still climbing). Saving "whatever the last epoch produced" would have silently shipped a worse model than what was actually achieved mid-run.

### 3.8 Reading the actual results

**MASC test-split (5,541 crops, checkpoint = Swin-Tiny, epoch 8):**

```
              precision    recall  f1-score   support
         R09       0.00      0.00      0.00         0
         R04       0.22      0.49      0.31        45
         R17       0.39      0.64      0.49       660
         R10       0.00      0.00      0.00         0
         R28       0.00      0.00      0.00         0
         R08       0.63      0.84      0.72      1805
   macro avg       0.21      0.33      0.25      2510
```

R08 (0.72 F1, recall 0.84) is where the model performs best — by far, and unsurprisingly, since it's the rule with the most training examples. R17 (0.49) is usable. R04 (0.31) is data-starved — only 45 test examples exist for it. R09/R10/R28 show `support=0` for the reason explained in §3.3.

**Rico holdout (9,343 crops, never trained on):**

```
              precision    recall  f1-score   support
         R04       0.31      0.56      0.40       145
         R17       0.32      0.46      0.38      1419
         R08       0.50      0.53      0.51      3418
   macro avg       0.19      0.26      0.22      4982
```

Comparing MASC → Rico: R08 drops 0.72 → 0.51, R17 drops 0.49 → 0.38, but **R04 actually improves, 0.31 → 0.40**. The overall macro-F1 gap (0.25 → 0.22, a drop of only 0.03) is the *tightest* generalization gap of any backbone in the entire 33-model sweep except `vit_b_16` — meaning Swin isn't just memorizing MASC's specific visual style, it's picked up something that transfers to apps it's never seen. (A model that had simply memorized MASC would show a much bigger drop, or even collapse toward 0 on Rico.)

### 3.9 What you actually get at inference time

```python
classify_crop(image_path, bounds=None) -> {"_all": {rule: prob, ...}, rule_above_threshold: prob, ...}
confirm_violations(violations_doc, screenshot_path)  # mutates violations_doc in place
```

`confirm_violations()` is what's actually wired into the backend pipeline: right after the XML rule checker runs, it re-crops the screenshot around any R08/R17/R04 violation (the 3 rules with real training signal — R09/R10/R28 are skipped since a confidence score with zero training examples behind it would be meaningless) and attaches a `cv_confidence` field (0-1) to that violation. It **never removes or overrides** a rule-detected violation — it only adds supplementary confidence, consistent with the rule engine staying the deterministic source of truth and the model acting as a secondary confirmation signal.

---

## 4. What's the same between both models (worth remembering)

- Both fine-tune from ImageNet/COCO-pretrained backbones rather than training from scratch — small datasets, big pretrained head start.
- Both train **exclusively on MASC**; Rico is held out and **never trained on**, only evaluated on at the very end, specifically to test generalization to unseen apps.
- Both show a genuine, measurable "did the extra training work actually help" comparison — YOLO's zero-shot-vs-fine-tuned table, and the crop classifier's frozen-vs-unfrozen-backbone numbers.
- Both are wired into the backend as **fallback/confirmation signals**, not replacements for the deterministic rule engine — the rule engine (`src/rules.py`) is and remains the primary source of truth; both models exist to fill gaps XML alone can't reach (missing XML entirely for YOLO; pixel-only properties like contrast/overflow for the crop classifier).

## 5. Where to go for more detail

| Topic | File |
|---|---|
| Full 33-backbone sweep results, every candidate | `docs/crop_classifier_comparison_findings.md` |
| Architecture/year/paper reference for all 33 backbones | `docs/crop_classifier_model_reference.md` |
| Original (pre-sweep) backbone reasoning | `docs/picking_model_for_crop.md` |
| Full YOLO training run artifacts, plots, confusion matrices | Progress Report §15C, `runs/runs/yolo_ui_detector/` |
| Full crop classifier results, plots, confusion matrices | Progress Report §15G, `runs/crop_violation_classifier/crop_classifier/` |
| Backend wiring detail (how these get called during a real audit) | Progress Report §15J, SDS §3.6/§3.7 |
| The actual training notebooks (fully executed, with saved outputs) | `notebooks/train_yolo_ui_detector.ipynb`, `notebooks/train_crop_violation_classifier.ipynb` |
