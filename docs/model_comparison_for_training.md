# Model Comparison — Alternatives to YOLO for CV Training

**Author:** Ayesha Naveed
**Context:** Current pipeline uses YOLO for visual UI element detection. This compares alternatives for two distinct sub-tasks:
- **(A)** detecting/locating UI elements in a screenshot
- **(B)** classifying a specific violation type from a cropped region (contrast, overflow, touch-target size — see `docs/user_coverage_for_training.md`)

---

## Task A — Object Detection (locating elements on the full screenshot)

| Model | Speed | Accuracy | Model Size | Training Data Needs | Notes |
|---|---|---|---|---|---|
| **YOLOv8/v11 (current)** | Very fast | Good | Small–medium | Moderate | Real-time capable, easy to deploy, current baseline |
| **YOLOv6** | Very fast (fastest GPU throughput of the group on legacy hardware like T4) | Comparable to YOLOv8 at similar scale, slightly behind at same param count | Small–medium (needs more params/FLOPs than YOLOv8 for comparable accuracy) | Moderate | Built by Meituan specifically for industrial/hardware-constrained deployment; strong choice if targeting fixed inference hardware, but smaller ecosystem and less actively developed than YOLOv8/v11 |
| **Faster R-CNN** | Slow | Higher (esp. small objects) | Large | High | Two-stage, better for small/dense UI elements but much slower — not ideal for a live audit tool |
| **SSD (MobileNet backbone)** | Fast | Lower than YOLO | Small | Moderate | Similar speed class to YOLO, generally less accurate on small objects |
| **EfficientDet** | Medium | Good, scales with size (D0–D7) | Small–large (tunable) | Moderate–High | Good accuracy/speed tradeoff, more complex to tune than YOLO |
| **RT-DETR** | Fast | Good, no NMS post-processing needed | Medium | High | Newer transformer-based option, simpler pipeline, less community tooling than YOLO |

> **Verdict:** YOLO remains the right choice for detection — real-time speed matters for an interactive audit tool, and UI screenshots are visually simpler (higher contrast, less clutter) than natural images, so YOLO's small-object weakness matters less here. Between YOLO variants, **stick with YOLOv8/v11**: YOLOv6 is optimized for fixed industrial hardware and needs a larger model to match YOLOv8's accuracy, which doesn't help us since we're not deploying to dedicated inference hardware — YOLOv8/v11's better accuracy-per-parameter and larger community/tooling base make it the more practical fit.

---

## Task B — Crop Classification (given a region, is it a violation?)

The more useful direction per earlier findings (R09 contrast, R04/R17 touch-target, R10/R28 overflow, R08 overlap) — these need to classify a small crop, not detect objects across a whole screen.

| Model | Speed to Train | Accuracy on Small Crops | Model Size | Notes |
|---|---|---|---|---|
| **MobileNetV3** | Fast | Good | Very small (~5MB) | Best fit — designed for small, fast, mobile-scale classification, exactly the crop size we're working with |
| **EfficientNet-B0** | Fast | Good, slightly better than MobileNetV3 | Small (~20MB) | Close second, marginally more accurate but heavier |
| **ResNet-50** | Slower | Higher, especially with more data | Large (~100MB) | Overkill for small crops unless MobileNetV3/EfficientNet-B0 plateaus on validation |
| **ViT (Vision Transformer)** | Slow, needs more data | Can be very high with enough data | Large | Needs significantly more training data than we're likely to have (25–40 screens); not recommended yet |

---

## Recommendation

| Decision | Rationale |
|---|---|
| **Keep YOLO** for element detection | It's the right tool for that job — no reason to switch |
| **Start with MobileNetV3 or EfficientNet-B0** for crop-level violation classification (R09, R04/R17, R10/R28, R08) | Fast to train on our small dataset, lightweight to deploy |
| **Escalate to ResNet-50** | Only if validation accuracy plateaus with the lighter models |
| **Avoid ViT for now** | Needs more training data than a 25–40 screen dataset can realistically provide |

This aligns with Noor's earlier direction (EfficientNet-B0/MobileNetV3 first, ResNet-50 as fallback) — this doc adds the object-detection-alternatives comparison to make the reasoning explicit for the supervisor/team.