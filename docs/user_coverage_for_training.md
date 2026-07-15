# User Coverage for Model Training

**Author:** Ayesha Naveed
**Source:** `docs/accessibility_guidelines_report.md` §5 (User Group Coverage)
**Purpose:** Identify which user groups' rules are good candidates for CV/visual model training, vs which are already solved by XML-based rule checks.

## The source table (for reference)

| User / Disability Group | Rules |
|---|---|
| Blind / Screen Reader | R01,R02,R03,R15,R16,R23,R24,R30 |
| Low Vision | R09,R10,R28 |
| Color Blind | R09,R11 |
| Deaf / Hard of Hearing | R12,R13,R14 |
| Motor Impaired / Switch | R04,R06,R17,R18,R19 |
| Elderly | R04,R09,R10,R28 |
| Cognitive / Memory | R03,R20,R21,R22,R27 |
| ADHD / Epilepsy | R25,R26 |
| Dyslexia / Low Literacy | R27,R29 |
| All Users | R06,R07,R08 |

## Key distinction: XML-detectable vs visual-only

Most rules (R01, R02, R03, R05, R06, R12, R13, R15, R16, R19, R20, R21, R22, R23, R24, R27, R29, R30) are **already fully solved by the XML parser + rule checker** — they check `text`, `content-desc`, `clickable`, `bounds`, etc. directly from the UI hierarchy. **No model training needed for these** — they're deterministic and already working.

The genuinely useful CV/model training candidates are the ones that need to look at the **rendered screenshot itself**, not just XML structure:

## Good CV training candidates

| Group affected | Rules | Why it needs a visual model |
|---|---|---|
| Low Vision, Elderly, Color Blind | **R09** (low contrast) | Needs actual pixel color analysis between foreground/background — can't be read from XML alone |
| Low Vision, Elderly | **R10, R28** (text overflow / font scale) | Needs to see if rendered text is visually clipped or overlapping |
| Motor Impaired, Elderly | **R04, R17** (small touch target, spacing) | XML gives raw bounds, but visual crop training helps confirm actual tap-target size against real screen density |
| All Users | **R08** (layout overlap) | Bounding-box math catches some cases, but visual confirmation reduces false positives |
| Blind (indirectly) | **R02, R30** (icon-only buttons) | A CV model could help flag "this looks like an icon with no visible text" even before checking content-desc, useful as a cross-check |

## Recommendation

Prioritize training data collection for: **R09 (contrast), R04/R17 (touch target size), R10/R28 (text overflow/scale), R08 (layout overlap)** — these are the rules where a screenshot crop actually adds detection power beyond what the XML parser already gives us for free.

