# Agentic Accessibility Auditor
# Accessibility Guidelines & Rule Mapping Report

**FAST University 2025 — Summer Internship**  
**Prepared by:** Muhammad Noor (schema & mapping) · Ayesha Naveed (original guidelines, revised)  
**Schema version:** 1.0  
**Related docs:** [`json_schemas.md`](json_schemas.md) · [`schemas/auditor_schema.json`](schemas/auditor_schema.json)

---

## 1. Introduction

This document defines all **30 accessibility guidelines (G01–G30)** and **30 detection rules (R01–R30)** for the Agentic Accessibility Auditor. Guidelines describe *what* must be accessible; rules describe *how* violations are detected from UIAutomator XML (and optional screenshot analysis).

The pipeline maps each detected violation to one or more guideline IDs, a severity, and a developer recommendation.

> **Important:** Each rule ID is unique (R01–R30). Each guideline ID is unique (G01–G30). A rule may enforce multiple guidelines; a guideline may be covered by multiple rules.

---

## 2. All 30 Accessibility Guidelines (G01–G30)

| ID | Issue / Guideline | Description | User Group | WCAG |
|----|-------------------|-------------|------------|------|
| G01 | Missing accessible label | Every interactive element must have a visible or programmatic label for screen readers. | Blind / Low Vision | 4.1.2 |
| G02 | Image button without description | ImageButton and clickable ImageView must have a content description. | Blind | 1.1.1 |
| G03 | Duplicate labels | No two interactive elements should share identical text/content-desc unless same action. | Blind / Cognitive | 4.1.2 |
| G04 | Small touch target | Tappable elements must meet minimum size (48×48 dp). | Motor / Elderly | 2.5.5 |
| G05 | Unlabeled input field | Every EditText must have a programmatic label (hint, labelFor, or content-desc). | Blind / Cognitive | 1.3.1 |
| G06 | Disabled important control | Critical controls must not be disabled without explanation or alternative. | All Users | 2.1.1 |
| G07 | Invisible or zero-size component | Zero-area or invalid bounds must be removed from focus tree. | All / Blind | 1.3.1 |
| G08 | Possible layout overlap | Elements must not overlap in ways that hide content or break focus order. | All / Blind | 1.3.2 |
| G09 | Low contrast | Text and UI components must meet minimum contrast ratios. | Low Vision / Color Blind | 1.4.3 |
| G10 | Text overflow | Text bounds must fit full content without clipping. | Low Vision / Cognitive | 1.4.4 |
| G11 | Information conveyed by color alone | Color must not be the only indicator of state or meaning. | Color Blind | 1.4.1 |
| G12 | Missing captions on video | Video with spoken audio must provide captions/subtitles. | Deaf / Hard of Hearing | 1.2.2 |
| G13 | Audio-only without transcript | Audio-only content must have a text transcript in the UI. | Deaf / Hard of Hearing | 1.2.1 |
| G14 | Notification uses audio only | Alerts must include visual indicators, not sound alone. | Deaf / Hard of Hearing | 1.3.3 |
| G15 | Logical focus / reading order | Focus order must follow natural top-to-bottom reading sequence. | Blind / Motor | 1.3.2 / 2.4.3 |
| G16 | Non-interactive elements in focus tree | Decorative elements must be excluded from accessibility focus. | Blind | 1.3.1 |
| G17 | Insufficient touch target spacing | Adjacent targets need ≥8 dp spacing to prevent mis-taps. | Motor Impaired | 2.5.5 |
| G18 | Multi-finger gesture required | All functionality must work with a single pointer. | Motor / Single Hand | 2.1.1 |
| G19 | No confirmation for destructive action | Irreversible actions must require confirmation. | Motor / Cognitive | 3.3.4 |
| G20 | Input label disappears on focus | Labels must remain visible while typing. | Cognitive / Memory | 3.3.2 |
| G21 | Vague or missing error messages | Errors must identify the field and how to fix it. | Cognitive / Blind | 3.3.1 / 3.3.3 |
| G22 | Password field lacks show/hide toggle | Password fields should offer reveal/hide control. | Cognitive / Motor | 3.3.1 |
| G23 | Navigation control not labeled | Back, home, close, menu buttons must have descriptive labels. | Blind | 2.4.6 |
| G24 | Screen has no descriptive title | Every screen needs a visible title or heading. | Blind / Cognitive | 2.4.2 |
| G25 | Uncontrolled auto-updating content | Animation/auto-update must be pausable/stoppable. | Cognitive / Epilepsy / ADHD | 2.2.2 |
| G26 | Session timeout without warning | Timed sessions must warn ≥20 s before expiry with extend option. | Cognitive / Slow Readers | 2.2.1 |
| G27 | Complex or jargon-heavy labels | Use plain, simple language in labels and hints. | Cognitive / Low Literacy | 3.1.5 |
| G28 | Text does not scale with system font | Text must remain readable at 200% system font size. | Low Vision / Elderly | 1.4.4 |
| G29 | All-caps body content | All-caps must not be used for paragraph or instruction text. | Cognitive / Dyslexia | 3.1.5 |
| G30 | Icon-only button with no text alternative | Icon-only buttons must have content-desc describing the action. | Blind / Low Literacy | 1.1.1 |

---

## 3. All 30 Detection Rules (R01–R30)

| Rule | Detection logic (XML condition → flag) | Severity | Guidelines |
|------|----------------------------------------|----------|------------|
| R01 | `clickable=true` AND `text=''` AND `content-desc=''` → Missing Label | High | G01, G02, G30 |
| R02 | `ImageButton` OR clickable `ImageView` AND `content-desc=''` → No Image Desc | High | G02, G30 |
| R03 | Two+ clickable elements share identical text/content-desc → Duplicate Label | Medium | G03 |
| R04 | `clickable=true` AND (width < 48dp OR height < 48dp) → Small Touch Target | High | G04, G17 |
| R05 | `EditText` AND `hint=''` AND `text=''` AND `content-desc=''` → Unlabeled Input | High | G05, G20 |
| R06 | `clickable=true` AND `enabled=false` AND no explanation TextView → Disabled Control | Medium | G06, G26 |
| R07 | bounds width=0 OR height=0 OR invalid rect → Zero-Size Element | Medium | G07, G25 |
| R08 | Two elements overlap >50% of smaller area → Layout Overlap | Medium | G08, G15 |
| R09 | Contrast ratio < 4.5:1 (text) or < 3:1 (icons) *(optional, screenshot)* → Low Contrast | Medium | G09, G11 |
| R10 | TextView bounds height < estimated text height → Text Overflow | Low/Medium | G10, G28, G29 |
| R11 | State change only via color, no icon/text → Color-Only Info | High | G11 |
| R12 | VideoView present AND no caption toggle → Missing Captions | High | G12 |
| R13 | Audio-only media AND no transcript link → No Transcript | High | G13 |
| R14 | Alert/notification AND no visible icon/banner → Audio-Only Notification | Medium | G14 |
| R15 | Focus order ≠ visual top-bottom order → Bad Focus Order | Medium | G15, G16 |
| R16 | Decorative element `focusable=true` → Decorative In Focus Tree | Low | G16 |
| R17 | Gap between clickable elements < 8dp → Insufficient Spacing | Medium | G17 |
| R18 | Feature only via multi-touch gesture → Multi-Gesture Only | High | G18 |
| R19 | Destructive button text AND no confirmation dialog → No Confirmation | Medium | G19 |
| R20 | EditText hint-only, no paired label TextView → Hint-Only Label | Medium | G05, G20 |
| R21 | Error TextView empty or vague → Vague Error Message | High | G21 |
| R22 | Password EditText AND no show/hide toggle → No Password Toggle | Medium | G22 |
| R23 | Nav ImageButton (`back`/`close`/`home`/`menu`) AND `content-desc=''` → Unlabeled Nav Control | High | G01, G23 |
| R24 | Toolbar title TextView empty → Missing Screen Title | Medium | G24 |
| R25 | AnimationView/auto-play media AND no pause control → Uncontrolled Animation | Medium | G25 |
| R26 | Countdown dialog AND no Extend/OK button → No Timeout Warning | Medium | G26 |
| R27 | content-desc/hint overly technical (long words) → Complex Label Language | Low | G27 |
| R28 | TextView bounds don't fit 200% font scale → Font Scale Overflow | Medium | G10, G28 |
| R29 | `textAllCaps=true` AND word count > 3 → All-Caps Body Text | Low | G29 |
| R30 | `clickable=true` AND `text=''` AND icon-only class → Icon-Only No Label | High | G01, G30 |

Pair-based rules may include `related_component`: **R03**, **R08**, **R17**.

**Implementation notes (R21, R30):** `src/rules.py` deliberately diverges from
this table's shorthand in two places, both to avoid false positives:

- **R21** flags only when an error label's `text` AND `content_desc` are
  *both* empty (matching R01/R05's own empty-label convention), not when
  *either* is empty. A plain error TextView that sets `text` and leaves
  `content_desc` unset (the normal, correct way to label a TextView) is not
  vague — flagging on content_desc alone would misfire on nearly every
  correctly-implemented error message.
- **R30** additionally requires `content_desc==''` (not just `text==''`), so
  it doesn't flag an icon-only control that already carries a real
  content_desc. This keeps R30's stated intent ("no text alternative")
  consistent with R01/R02's own AND-both-empty convention for the same
  underlying "unlabeled control" case.

---

## 4. Guideline → Rule Mapping (quick reference)

| G-ID | Guidelines | Rules |
|------|------------|-------|
| G01 | Missing accessible label | R01, R23, R30 |
| G02 | Image button without description | R01, R02 |
| G03 | Duplicate labels | R03 |
| G04 | Small touch target | R04 |
| G05 | Unlabeled input field | R05, R20 |
| G06 | Disabled important control | R06 |
| G07 | Invisible or zero-size component | R07 |
| G08 | Possible layout overlap | R08 |
| G09 | Low contrast | R09 |
| G10 | Text overflow | R10, R28 |
| G11 | Color-only information | R09, R11 |
| G12 | Missing captions | R12 |
| G13 | Audio-only without transcript | R13 |
| G14 | Audio-only notification | R14 |
| G15 | Logical focus order | R08, R15 |
| G16 | Decorative in focus tree | R15, R16 |
| G17 | Insufficient spacing | R04, R17 |
| G18 | Multi-finger gesture | R18 |
| G19 | No destructive confirmation | R19 |
| G20 | Label disappears on focus | R05, R20 |
| G21 | Vague error messages | R21 |
| G22 | Password show/hide toggle | R22 |
| G23 | Unlabeled navigation | R23 |
| G24 | Missing screen title | R24 |
| G25 | Uncontrolled animation | R07, R25 |
| G26 | Session timeout warning | R06, R26 |
| G27 | Complex label language | R27 |
| G28 | Font scale overflow | R10, R28 |
| G29 | All-caps body text | R10, R29 |
| G30 | Icon-only no label | R01, R02, R30 |

---

## 5. User Group Coverage

| User / Disability Group | Guidelines | Primary Rules |
|-------------------------|------------|---------------|
| Blind / Screen Reader | G01,G02,G03,G05,G15,G16,G23,G24,G30 | R01,R02,R03,R15,R16,R23,R24,R30 |
| Low Vision | G09,G10,G28 | R09,R10,R28 |
| Color Blind | G09,G11 | R09,R11 |
| Deaf / Hard of Hearing | G12,G13,G14 | R12,R13,R14 |
| Motor Impaired / Switch | G04,G06,G17,G18,G19 | R04,R06,R17,R18,R19 |
| Elderly | G04,G09,G10,G28 | R04,R09,R10,R28 |
| Cognitive / Memory | G03,G20,G21,G22,G27 | R03,R20,R21,R22,R27 |
| ADHD / Epilepsy | G25,G26 | R25,R26 |
| Dyslexia / Low Literacy | G27,G29 | R27,R29 |
| All Users | G06,G07,G08 | R06,R07,R08 |

---

## 6. JSON schema alignment

Violations use `rule_id` (R01–R30), `guideline` (human-readable text referencing G-ID), `severity`, and `recommendation` per [`json_schemas.md`](json_schemas.md). Formal validation: [`schemas/auditor_schema.json`](schemas/auditor_schema.json).

**Pipeline (planned):** Parser → `components.json` → Rule checker → `violations.json` → Agent → `report.json` → HTML/PDF report.

The agent layer receives **only** rule-detected violations and must not invent new issues.

---

*Canonical source for the guidelines PDF. Regenerate HTML via export script or Print → PDF from `docs/Accessibility_Guidelines_Report.html`.*
