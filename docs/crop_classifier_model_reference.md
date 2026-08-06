# Crop Classifier Backbone Reference — Architecture Background

For each of the 33 backbones in `docs/crop_classifier_comparison_findings.md`'s comparison sweep: when it was
introduced, who built it, the core architectural idea, and why it's relevant to Task B (crop-level
accessibility-violation classification). Organized by architecture family, since several families contribute
more than one width/size variant to the sweep.

All 33 are pretrained on ImageNet-1k (see the findings doc) — the "year" below is the year the *architecture*
was published, not when the specific ImageNet-1k checkpoint used here was trained.

---

## MobileNetV1 — `mobilenetv1_100`, `mobilenetv1_125`

- **Year:** 2017
- **Paper:** "MobileNets: Efficient Convolutional Neural Networks for Mobile Vision Applications" (Howard et al., Google)
- **Architecture:** The original depthwise-separable-convolution CNN — splits a standard convolution into a
  depthwise convolution (one filter per input channel) followed by a 1x1 pointwise convolution, cutting
  compute/params roughly 8-9x versus a standard convolution for similar accuracy. `_100`/`_125` refer to the
  width multiplier (1.0x, 1.25x channels).
- **Relevance to this project:** The oldest, simplest architecture in the sweep — no residuals, no attention,
  no squeeze-excite. Included as a "does the newest architecture actually help on this tiny dataset" baseline.
  Result: `mobilenetv1_100` posted one of the best Rico generalization scores (0.19) in the whole sweep, while
  `mobilenetv1_125` was pack-level (0.18) — an early signal that architectural sophistication doesn't
  straightforwardly predict performance here.

## MobileNetV2 — `mobilenetv2_050`, `mobilenetv2_100`, `mobilenetv2_140`

- **Year:** 2018
- **Paper:** "MobileNetV2: Inverted Residuals and Linear Bottlenecks" (Sandler, Howard, Zhu, Zhmoginov, Chen — Google)
- **Architecture:** Introduces the inverted residual block — expand channels with a 1x1 conv, apply a
  depthwise conv, then project back down with a *linear* (no activation) 1x1 conv, with a residual connection
  when input/output shapes match. The "linear bottleneck" avoids destroying information in the low-dimensional
  representation. `_050`/`_100`/`_140` are width multipliers (0.5x, 1.0x, 1.4x).
- **Relevance to this project:** Three width points let us see how this family scales on the task.
  Non-monotonic result: 0.5x (0.19) beat both 1.0x (0.17, the family's worst) and 1.4x (0.18) — capacity within
  this family doesn't correlate cleanly with generalization here.

## MobileNetV3 — `mobilenet_v3_small`, `mobilenet_v3_large`, `mobilenetv3_small_050`

- **Year:** 2019
- **Paper:** "Searching for MobileNetV3" (Howard et al., Google)
- **Architecture:** Combines NAS (via MnasNet-style platform-aware search) and manual redesign on top of
  MobileNetV2's inverted residuals: adds squeeze-and-excite blocks (channel-wise attention) to some blocks and
  replaces ReLU6 with the h-swish activation (a hardware-friendlier approximation of swish) in the later
  layers. Small/Large are two NAS-searched configurations for different latency budgets; `_050` is a lighter
  width-multiplier variant of Small.
- **Relevance to this project:** `mobilenet_v3_small` is the project's original pick per
  `docs/picking_model_for_crop.md` — this whole 33-model sweep exists to verify whether that choice holds up.
  Result: it sits mid-pack (0.18 Rico macro-F1), beaten by 9+ other models on the same metric — the pick was
  reasonable a priori but the data doesn't show it as clearly the best.

## MobileNetV4 — `mobilenetv4_conv_small`, `mobilenetv4_conv_medium`, `mobilenetv4_conv_large`

- **Year:** 2024
- **Paper:** "MobileNetV4 - Universal Models for the Mobile Ecosystem" (Qin et al., Google)
- **Architecture:** Introduces the Universal Inverted Bottleneck (UIB) block, which generalizes MobileNetV2's
  inverted residual, MobileNetV3's squeeze-excite variant, and a couple of newer block types into one
  searchable unit, plus a NAS process co-designed for both mobile CPUs and dedicated ML accelerators
  (not just CPU latency like earlier MobileNet NAS runs).
- **Relevance to this project:** The newest, most "state of the art on ImageNet" architecture in the whole
  sweep. Result: genuinely the most interesting negative finding of the project — `_small` posted the *worst*
  healthy Rico score (0.16) of any model tested, while `_medium`/`_large` were merely pack-level. Newer/SOTA
  on standard benchmarks clearly didn't transfer to this small, imbalanced task.

## EfficientNet-B0 — `efficientnet_b0`

- **Year:** 2019
- **Paper:** "EfficientNet: Rethinking Model Scaling for Convolutional Neural Networks" (Tan & Le, Google)
- **Architecture:** Starts from a small NAS-searched base network (using MBConv blocks, essentially
  MobileNetV2-style inverted residuals + squeeze-excite) and scales depth, width, and input resolution
  together via a single compound coefficient, rather than scaling just one dimension.
- **Relevance to this project:** Named directly in `docs/model_comparison_for_training.md` as the doc's
  "close second" pick behind MobileNetV3-Small. Result: unremarkable (0.18 Rico), but notably posted the
  **highest best-val-F1 of any model at the time it ran** — a clean demonstration that strong MASC/validation
  performance doesn't predict Rico generalization here.

## EfficientNetV2-S — `efficientnet_v2_s`

- **Year:** 2021
- **Paper:** "EfficientNetV2: Smaller Models and Faster Training" (Tan & Le, Google)
- **Architecture:** Replaces some of the original EfficientNet's MBConv blocks (especially in early layers)
  with Fused-MBConv blocks (a single regular 3x3 conv instead of a separate expand + depthwise pair), which
  trains faster on modern accelerators, plus progressive learning (growing image size and regularization
  strength together during training).
- **Relevance to this project:** Deliberately included as a "does bigger/newer help" negative-control
  candidate (21.5M params, the doc predicted EfficientNet's compound scaling needs data-rich regimes to pay
  off). Result: confirmed the prediction — unremarkable 0.18 Rico, no benefit from the extra capacity.

## MNASNet — `mnasnet1_0`

- **Year:** 2019
- **Paper:** "MnasNet: Platform-Aware Neural Architecture Search for Mobile" (Tan, Chen, Pang, Vasudevan,
  Sandler, Howard, Le — Google)
- **Architecture:** One of the first NAS approaches to directly optimize for real device latency (measured on
  an actual phone) as part of the search reward, rather than just proxy metrics like FLOPs. Uses MobileNetV2-
  style inverted residual blocks as the search space's building blocks, with squeeze-excite in some variants.
- **Relevance to this project:** A NAS-searched predecessor to MobileNetV3 (which reused MnasNet's search
  methodology). Result: one of the standout performers — tied for second-best Rico macro-F1 (0.19) and posted
  the single **highest Rico R08 F1 of any model in the sweep (0.55)**.

## ResNet-50 — `resnet50`

- **Year:** 2015 (published at CVPR 2016)
- **Paper:** "Deep Residual Learning for Image Recognition" (He, Zhang, Ren, Sun — Microsoft Research)
- **Architecture:** Introduced the residual/skip connection — each block learns a residual function relative to
  its input (`output = F(x) + x`) rather than a direct mapping, which made it practical to train much deeper
  networks (50-152+ layers) than was previously stable. ResNet-50 uses "bottleneck" blocks (1x1 reduce -> 3x3
  -> 1x1 expand).
- **Relevance to this project:** The doc's own documented escalation fallback ("only if lighter models
  plateau," not a starting choice) — included specifically to test that caution. Result: confirmed it —
  15x `mobilenet_v3_small`'s size bought nothing on Rico (0.18, pack-level) and posted the **worst Rico R04 F1
  of any model tested (0.20)**.

## ShuffleNetV2 — `shufflenet_v2_x1_0`

- **Year:** 2018
- **Paper:** "ShuffleNet V2: Practical Guidelines for Efficient CNN Architecture Design" (Ma, Zhang, Zheng, Sun
  — Megvii/Face++)
- **Architecture:** Splits each block's input channels in two; one half passes through unchanged, the other
  goes through a small conv stack, and the two halves are concatenated and then "shuffled" (channels
  interleaved) so subsequent blocks can mix information across the split — designed around real measured
  hardware speed, not just FLOP counts.
- **Relevance to this project:** A different-lineage efficient-CNN comparison point (channel-split/shuffle
  instead of depthwise-separable). Result: smallest model tested at the time it ran (1.26M params) yet
  identical pack-level performance (0.18) to everything from 1.5M to 6M params — further evidence the capacity
  floor for "good enough" is very low on this task.

## RegNet — `regnet_y_800mf`

- **Year:** 2020
- **Paper:** "Designing Network Design Spaces" (Radosavovic, Kosaraju, Girshick, He, Dollár — Facebook AI Research)
- **Architecture:** Not a single hand-designed network — a *design space* generated by progressively
  constraining a broad space of possible networks based on which design choices (width/depth patterns per
  stage) empirically work well across many sampled models, then picking a specific point on that space.
  RegNetY adds squeeze-excite to the resulting blocks. "800MF" refers to its ~800 million FLOPs target.
- **Relevance to this project:** A methodologically distinct approach (search-over-design-space rather than
  NAS-over-single-network or hand design). Result: unremarkable (0.18 Rico) despite tying `mobilenet_v3_large`
  for one of the best MASC-split scores — another data point that MASC-split performance doesn't predict Rico
  generalization.

## DenseNet-121 — `densenet121`

- **Year:** 2017 (published at CVPR 2017, best paper award)
- **Paper:** "Densely Connected Convolutional Networks" (Huang, Liu, van der Maaten, Weinberger — Cornell/Facebook/Tsinghua)
- **Architecture:** Each layer receives the concatenated feature maps of *all* preceding layers within its
  block (not just the previous one, and not summed like ResNet — concatenated), encouraging feature reuse and
  requiring comparatively few new feature maps per layer ("growth rate").
- **Relevance to this project:** A genuinely different connectivity pattern than everything else in the sweep.
  Result: a real standout — tied for second-best Rico macro-F1 (0.19) and posted (at the time) the **best Rico
  R17 F1 of any model (0.39)**, later edged out by `mobilenetv2_050`'s 0.41. Its dense/feature-reuse design may
  genuinely suit the spacing-detection rule (R17) better than other architectures tried.

## SqueezeNet 1.1 — `squeezenet1_1`

- **Year:** 2016
- **Paper:** "SqueezeNet: AlexNet-level accuracy with 50x fewer parameters and <0.5MB model size" (Iandola,
  Han, Moskewicz, Ashraf, Dally, Keutzer — DeepScale/UC Berkeley/Stanford)
- **Architecture:** Built from "Fire modules" — a 1x1 "squeeze" convolution that aggressively reduces channel
  count, feeding into a mix of 1x1 and 3x3 "expand" convolutions. Version 1.1 (used here) is an efficiency
  refinement of the original with the same core idea but fewer computations for similar accuracy.
- **Relevance to this project:** The smallest, most aggressively compressed architecture in the sweep before
  the model-width variants of other families got even smaller. Result: the sweep's one clean **failure** — it
  collapsed to predicting positive for every crop on every rule (recall 1.00 across the board), not a
  generalization-quality issue but a genuine training/architecture mismatch. Later confirmed as
  SqueezeNet-specific, not a general "too small" risk, once `mobilenetv2_050` and `mobilenetv3_small_050`
  (both smaller or comparable) trained fine.

## Vision Transformer (ViT-B/16) — `vit_b_16`

- **Year:** 2020 (preprint), published at ICLR 2021
- **Paper:** "An Image is Worth 16x16 Words: Transformers for Image Recognition at Scale" (Dosovitskiy et al., Google)
- **Architecture:** Splits an image into fixed-size patches (16x16 pixels here), linearly embeds each patch as
  a token, adds a learnable class token and position embeddings, and feeds the sequence through a standard
  Transformer encoder (the same multi-head self-attention architecture used in NLP) — no convolutions, no
  built-in spatial locality bias at all.
- **Relevance to this project:** `docs/picking_model_for_crop.md` explicitly recommended *against* using ViT,
  reasoning it needs far more data than this project has. Result: the doc's caution was directionally
  right about data-hunger in general, but the actual outcome surprised — `vit_b_16` tied for the **best Rico
  macro-F1 in the whole sweep (0.21)**, driven almost entirely by a large R04 edge, at the cost of being the
  single most expensive model to train (86.6M params, longest training time).

## MobileViT v1 — `mobilevit_xxs`, `mobilevit_xs`, `mobilevit_s`

- **Year:** 2021 (preprint), published at ICLR 2022
- **Paper:** "MobileViT: Light-weight, General-purpose, and Mobile-friendly Vision Transformer" (Mehta &
  Rastegari, Apple)
- **Architecture:** A hybrid: standard MobileNetV2-style convolutional blocks for early feature extraction,
  interleaved with "MobileViT blocks" that unfold a feature map into non-overlapping patches, apply standard
  transformer self-attention across patches, then fold the result back into a feature map — combining CNN
  locality/efficiency with a transformer's global receptive field.
- **Relevance to this project:** The first attention-hybrid tested, directly comparable to plain ViT. Result:
  mixed by size — `xxs` (0.95M, smallest) tied for second-best (0.19), while `xs`/`s` (larger) were both
  pack-level (0.18) — suggesting it's not simply "attention helps," since the biggest attention-hybrid variant
  here didn't show `vit_b_16`'s edge.

## MobileViTv2 — `mobilevitv2_050`, `mobilevitv2_100`, `mobilevitv2_200`

- **Year:** 2022
- **Paper:** "Separable Self-attention for Mobile Vision Transformers" (Mehta & Rastegari, Apple)
- **Architecture:** Replaces MobileViT v1's standard (quadratic-cost) multi-head self-attention with a linear-
  complexity "separable self-attention" operation, removing the need for the expensive query-key-value
  projections of standard attention while keeping a similar hybrid CNN+attention structure.
- **Relevance to this project:** The single most important result in the whole sweep. All three sizes tested
  scored 0.19/0.19/**0.21** — climbing with size, unlike every other family — and `mobilevitv2_200` (17.4M
  params) **tied `vit_b_16`'s best-in-sweep 0.21 Rico macro-F1 at one-fifth the parameters**, with a nearly
  identical R04-driven profile. Currently the leading practical candidate for the final pick.

## MobileOne — `mobileone_s0`, `mobileone_s1`, `mobileone_s4`

- **Year:** 2022
- **Paper:** "MobileOne: An Improved One millisecond Mobile Backbone" (Vasu, Gabriel, Zhu, Tuzel, Ranjan, Apple)
- **Architecture:** Uses a multi-branch structure (parallel conv branches plus a residual branch) *only during
  training*, then mathematically "re-parameterizes" (algebraically collapses) all the branches into a single
  linear conv path for inference — gets multi-branch training benefits with single-path (fast) deployment.
- **Relevance to this project:** A structural-reparameterization approach, distinct from every other family in
  the sweep. Result: the flattest, most size-invariant family tested — all three sizes (3.55M to 12.9M, a
  3.6x range) landed at exactly 0.18 Rico macro-F1, consistent with its design being an inference-speed
  optimization rather than an accuracy one.

## GhostNet — `ghostnet_100`

- **Year:** 2020
- **Paper:** "GhostNet: More Features from Cheap Operations" (Han, Wang, Tian, Guo, Xu, Xu — Huawei Noah's Ark Lab)
- **Architecture:** Generates a smaller set of "intrinsic" feature maps with a normal convolution, then
  produces the rest of the feature maps ("ghost" features) by applying cheap linear operations (depthwise
  convs) to the intrinsic ones, instead of computing every feature map with a full convolution.
- **Relevance to this project:** Another cheap-operations efficiency design, philosophically similar to
  MobileNetV1's depthwise-separable idea taken further. Result: slightly below pack-level (0.17 Rico), the
  largest generalization gap seen among healthy (non-collapsed) models — its efficiency trick didn't translate
  to better generalization here.

## GhostNetV2 — `ghostnetv2_100`

- **Year:** 2022
- **Paper:** "GhostNetV2: Enhance Cheap Operation with Long-Range Attention" (Tang, Han, Xu, Xiao, Deng, Xu,
  Wang, Tian — Huawei Noah's Ark Lab)
- **Architecture:** Adds a lightweight "DFC" (Decoupled Fully Connected) attention branch to the original
  GhostNet's cheap-operation blocks, aiming to capture long-range spatial dependencies that the purely local
  ghost-feature generation misses.
- **Relevance to this project:** Direct sequel to `ghostnet_100`, testing whether adding a lightweight
  attention mechanism improves on the V1 result. Result: identical Rico macro-F1 (0.17) to V1 - the DFC
  attention addition made no measurable difference here, unlike MobileViT's attention integration which did
  help. Suggests not all "attention" additions are equivalent - GhostNetV2's is a much lighter, more local
  mechanism than MobileViT's full transformer blocks.

## ConvNeXt-Tiny — `convnext_tiny`

- **Year:** 2022
- **Paper:** "A ConvNet for the 2020s" (Liu, Mao, Wu, Feichtenhofer, Darrell, Xie — Meta AI/FAIR)
- **Architecture:** Takes a standard ResNet and "modernizes" it one design choice at a time by adopting ideas
  popularized by Vision Transformers (larger convolution kernels, fewer normalization/activation layers, a
  patchify stem, LayerNorm instead of BatchNorm, an inverted-bottleneck-style block) while remaining a pure
  CNN with no actual attention mechanism — a controlled test of "is it attention itself, or just modern
  training/design recipes, that make transformers competitive."
- **Relevance to this project:** Added specifically to help interpret `vit_b_16`/`mobilevitv2_200`'s strong
  results — a "modern CNN, no attention" data point. Result: **the answer**. Plain pack-level Rico macro-F1
  (0.18), no repeat of the R04 spike (0.27 vs. 0.42 for the attention-based models) despite adopting nearly
  every other 2020s CNN design trick. Confirms it's attention specifically — not modern design or capacity —
  driving the `vit_b_16`/`mobilevitv2_200` edge.

## Swin Transformer Tiny — `swin_tiny_patch4_window7_224`

- **Year:** 2021
- **Paper:** "Swin Transformer: Hierarchical Vision Transformer using Shifted Windows" (Liu, Lin, Cao, Hu, Wei,
  Zhang, Lin, Guo — Microsoft Research Asia)
- **Architecture:** Computes self-attention only within local, non-overlapping windows (7x7 patches here)
  rather than globally across the whole image like ViT, and alternates between two window layouts (regular and
  "shifted") across consecutive layers so information can still flow between windows — giving attention a
  CNN-like locality bias while staying much cheaper than full global attention, plus a hierarchical multi-stage
  structure (like a CNN's downsampling stages) that plain ViT lacks.
- **Relevance to this project:** The most direct follow-up to `vit_b_16`'s result — same attention mechanism
  family, but with a CNN-like locality/hierarchy bias ViT-B/16 doesn't have. Result: **the best result in the
  entire 33-model sweep** (Rico macro-F1 0.22, beating `vit_b_16`/`mobilevitv2_200`'s 0.21), and a more evenly
  distributed win across R04/R17/R08 rather than one rule carrying the score. Confirms attention helps broadly
  across three different implementations (global, hybrid-separable, windowed) — and the windowed/hierarchical
  variant wins outright, at roughly a third of `vit_b_16`'s size.

---

## Summary by "generation"

| Era | Models | Common thread |
|---|---|---|
| 2015-2017 (early efficient/deep CNNs) | ResNet-50, DenseNet-121, SqueezeNet1.1, MobileNetV1 | Foundational ideas (residuals, dense connections, aggressive compression, depthwise-separable convs) still underlying everything newer |
| 2018-2019 (mobile-NAS era) | MobileNetV2, MobileNetV3, MNASNet, EfficientNet-B0, ShuffleNetV2 | Neural architecture search + hand-tuned mobile efficiency tricks |
| 2020 (design-space / efficiency refinement) | RegNet, GhostNet, EfficientNetV2 (2021) | Systematic search over design choices rather than single-network NAS |
| 2020-2022 (vision transformers arrive) | ViT-B/16, MobileViT v1/v2, Swin Tiny, ConvNeXt-Tiny | Attention mechanisms (or attention-inspired CNN redesigns) enter image classification |
| 2022 (reparameterization + efficiency-attention) | MobileOne, GhostNetV2 | Deployment-time optimizations layered on earlier ideas |
| 2024 (most recent) | MobileNetV4 | Newest generation, unified block design co-optimized for accelerators |
