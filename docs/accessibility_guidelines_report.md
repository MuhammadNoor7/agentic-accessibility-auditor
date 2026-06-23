# Agentic Accessibility Auditor
# Accessibility Guidelines & Rule Mapping Report

**Summer Internship 2026 | Android Mobile UI Accessibility**  
**Prepared by:** Ayesha Naveed (revised for rule alignment)  
**Schema version:** 1.0  
**Related docs:** [`json_schemas.md`](json_schemas.md) · [`schemas/auditor_schema.json`](schemas/auditor_schema.json)

---

## 1. Introduction

This document defines the accessibility **guidelines** followed by the Agentic Accessibility Auditor and maps each guideline to the specific **rules** implemented in the rule-checking engine.

The system audits Android mobile UI screens by accepting a screenshot and UIAutomator XML hierarchy, detecting accessibility violations, and generating developer-friendly fix recommendations.

### Rule numbering (canonical)

| Tier | Rule IDs | Description | Implementation status |
|------|----------|-------------|------------------------|
| **Core** | **R1–R10** | Detectable from parsed XML/components first; R9–R10 optional (screenshot) | R1–R8 in `rules.py`; R9–R10 planned |
| **Extended** | **R11–R30** | Broader WCAG/disability coverage; advanced checks | Documented; implementation planned |

> **Important:** Each rule ID is unique. Core rules use R1–R10. Extended rules use R11–R30. Do not reuse the same ID for two different checks.

---

## 2. Accessibility Guidelines

Guidelines are broad principles (G1–G10). Rules in Section 3 are specific, measurable checks derived from these guidelines.

### Guideline G1 — Visual Accessibility (Color & Contrast)

UI elements must not rely on color alone to convey information. Interactive elements must meet minimum contrast ratios so users with color blindness or low vision can perceive and operate them.

- **Applies to:** Color blindness, Low vision  
- **WCAG:** 1.4.1 (Use of Color), 1.4.3 (Contrast Minimum), 1.4.11 (Non-text Contrast)  
- **Rules:** R11, R13, R9 *(optional)*

### Guideline G2 — Focus & Keyboard Navigation

All interactive elements must have a clearly visible focus indicator so users navigating by keyboard or switch access can identify which element is focused.

- **Applies to:** Motor/physical disabilities, Screen reader users  
- **WCAG:** 2.4.7 (Focus Visible), 2.4.3 (Focus Order)  
- **Rules:** R12

### Guideline G3 — Touch Target & Motor Accessibility

Interactive elements must be large enough and spaced far enough apart to be tapped without accidental activation. Minimum recommended touch target is 48×48 dp with at least 8 dp spacing between targets.

- **Applies to:** Motor/physical disabilities, Elderly users  
- **WCAG:** 2.5.5 (Target Size), 2.5.8 (Target Size Minimum)  
- **Rules:** R4, R16, R6

### Guideline G4 — Screen Reader & Label Accessibility

Every interactive and informative UI element must have a meaningful programmatic label. Labels must describe purpose or action, not only element type.

- **Applies to:** Blind users, Screen reader users  
- **WCAG:** 1.3.1 (Info and Relationships), 4.1.2 (Name, Role, Value)  
- **Rules:** R1, R2, R3, R20, R26, R29

### Guideline G5 — Form & Input Accessibility

Input fields must have visible or programmatically associated labels. Error messages must describe valid input. Placeholder text alone is not sufficient.

- **Applies to:** Screen reader users, Cognitive disabilities  
- **WCAG:** 1.3.1, 3.3.1 (Error Identification), 3.3.2 (Labels or Instructions)  
- **Rules:** R5, R19, R21, R30

### Guideline G6 — Media & Multimedia Accessibility

Audio/video must provide captions, transcripts, or visible alternatives. Alerts must not rely solely on sound. Auto-playing media must include accessible pause/stop.

- **Applies to:** Hearing impairment, Deaf users  
- **WCAG:** 1.2.1 (Audio-only), 1.2.2 (Captions), 1.4.2 (Audio Control)  
- **Rules:** R14, R15, R17

### Guideline G7 — Photosensitivity & Animation Safety

Content must not flash more than three times per second. Animations should respect reduced-motion preferences.

- **Applies to:** Photosensitivity, Epilepsy  
- **WCAG:** 2.3.1 (Three Flashes or Below Threshold)  
- **Rules:** R18

### Guideline G8 — Navigation & Structure

Repeated navigation must include skip links. Interactive elements must have correct roles. Modals must trap focus. Scrollable regions and loading states must be announced.

- **Applies to:** Screen reader users, Motor/physical disabilities  
- **WCAG:** 2.4.1 (Bypass Blocks), 4.1.2 (Name, Role, Value), 2.4.3 (Focus Order)  
- **Rules:** R25, R27, R22, R28, R7, R8

### Guideline G9 — Time & Session Accessibility

Users must be able to extend, adjust, or disable time limits on timed content or sessions.

- **Applies to:** Motor/physical disabilities, Cognitive disabilities  
- **WCAG:** 2.2.1 (Timing Adjustable)  
- **Rules:** R24

### Guideline G10 — Language & Cognitive Clarity

App/element language must be set programmatically. Instructions must be clear. Text must not be clipped; scrollable regions must be announced.

- **Applies to:** Cognitive disabilities, Screen reader users, Non-native speakers  
- **WCAG:** 3.1.1 (Language of Page), 3.1.2 (Language of Parts)  
- **Rules:** R23, R10 *(optional)*, R21, R25, R30

---

## 3. Accessibility Rules

Rules are applied to the parsed UIAutomator XML hierarchy of each Android screen.

### 3.1 Core rules (R1–R10)

Implemented first from XML/components. **R1–R8** are in `src/rules.py`. **R9–R10** are optional (require screenshot analysis).

| Rule ID | Guideline | Issue | Detection logic | Severity |
|---------|-----------|-------|-----------------|----------|
| R1 | G4 | Missing accessible label | Clickable element has empty `text` and empty `content-desc`. | High |
| R2 | G4 | Image button without description | `ImageButton` / `ImageView` is clickable but `content-desc` is missing. | High |
| R3 | G4 | Duplicate labels | Multiple clickable elements share the same visible `text` or `content-desc`. | Medium |
| R4 | G3 | Small touch target | Clickable element width or height is below 48 dp (threshold). | Medium / High |
| R5 | G5 | Unlabeled input field | `EditText` has no hint, no `text`, and no `content-desc`. | High |
| R6 | G3 | Disabled important control | Important clickable control is disabled without clear reason. | Medium |
| R7 | G8 | Invisible or zero-size component | Element has invalid `bounds` or zero visible area. | Medium |
| R8 | G8 | Possible layout overlap | Two important UI elements have overlapping `bounds`. | Medium |
| R9 | G1, G10 | Low contrast *(optional)* | Estimate foreground/background contrast from screenshot crop. | Medium |
| R10 | G10 | Text overflow *(optional)* | Text component `bounds` are too small for visible text or likely clipped. | Low / Medium |

### 3.2 Extended rules (R11–R30)

Broader disability and WCAG coverage. Documented for pipeline v1.0; implementation planned after core rules.

| Rule ID | Guideline | Issue | Detection logic | Severity |
|---------|-----------|-------|-----------------|----------|
| R11 | G1 | No color-independent indicator | UI uses color as the only way to convey information with no icon, text, or pattern. | High |
| R12 | G2 | No visual focus indicator | Focusable element has no visible focus ring (`android:state_focused` drawable). | High |
| R13 | G1 | Color contrast for non-text elements | Interactive elements have contrast below 3:1 against adjacent colors. | Medium |
| R14 | G6 | Missing captions or transcript indicator | Media element has no caption toggle, subtitle button, or transcript link nearby. | High |
| R15 | G6 | Audio-only alert or notification | Alert relies solely on sound with no visible banner, badge, or vibration indicator. | High |
| R16 | G3 | Insufficient touch target spacing | Two+ clickable elements have gap less than 8 dp. | Medium |
| R17 | G6 | Auto-playing media without pause control | Media auto-starts with no accessible pause/stop in first focusable elements. | Medium |
| R18 | G7 | Flashing or animated content | `resource-id`/`class` suggests flash/blink/strobe patterns. | Critical |
| R19 | G5 | Form field with no programmatic label association | `EditText` beside `TextView` label but no `labelFor` link. | High |
| R20 | G4 | Redundant or meaningless content description | `content-desc` is generic (`image`, `icon`, `button`) not descriptive. | Medium |
| R21 | G5, G10 | Missing error suggestion on input field | `EditText` has validation error but no `errorMessage` or helpful hint. | Medium |
| R22 | G8 | Scrollable content with no scroll announcement | `ScrollView` / `RecyclerView` lacks scrollable `contentDescription`. | Medium |
| R23 | G10 | Language not set on text content | App/element locale attribute missing for screen readers. | Medium |
| R24 | G9 | Timed content with no extension option | Countdown/session timer with no extend/disable option. | High |
| R25 | G8, G10 | Missing skip navigation option | Long repeated nav blocks with no skip link to main content. | Medium |
| R26 | G4 | Interactive element not announced as interactive | Clickable element has no role/class indicating button/control. | High |
| R27 | G8 | Modal or dialog not trapping focus | Dialog present but focus not confined; user navigates behind overlay. | High |
| R28 | G8 | Missing loading or progress state announcement | Progress/spinner has no `contentDescription` or live region. | Medium |
| R29 | G4 | Icon-only button with no label | Button has icon only; no text and no `content-desc`. | High |
| R30 | G5, G10 | Placeholder text used as only label | `EditText` relies solely on `android:hint` with no linked label. | Medium |

### 3.3 Guideline → rules quick reference

| Guideline | Rules |
|-----------|-------|
| G1 | R11, R13, R9* |
| G2 | R12 |
| G3 | R4, R16, R6 |
| G4 | R1, R2, R3, R20, R26, R29 |
| G5 | R5, R19, R21, R30 |
| G6 | R14, R15, R17 |
| G7 | R18 |
| G8 | R7, R8, R22, R25, R27, R28 |
| G9 | R24 |
| G10 | R10*, R23, R21, R25, R30 |

\* Optional rules requiring screenshot analysis.

---

## 4. Coverage by Disability Category

| Disability category | Covered by rules |
|---------------------|------------------|
| Color blindness | R11, R13 |
| Low vision / contrast | R9*, R13 |
| Hearing impairment | R14, R15, R17 |
| Photosensitivity / Epilepsy | R18 |
| Motor / physical | R4, R6, R16, R24 |
| Blind / Screen reader | R1, R2, R3, R5, R12, R19, R20, R21, R22, R25, R26, R27, R28, R29, R30 |
| Cognitive | R10*, R21, R23, R25, R30 |

---

## 5. JSON schema alignment

Violations emitted by the pipeline use `rule_id` (R1–R30) and a text `guideline` field per [`json_schemas.md`](json_schemas.md). Formal validation: [`schemas/auditor_schema.json`](schemas/auditor_schema.json).

Pair-based rules may include `related_component`: **R3**, **R8**, **R16**.

---

*Canonical source for `Accessibility_Guidelines_Report.pdf`. Export: run `python scripts/export_guidelines_html.py`, open `docs/Accessibility_Guidelines_Report.html`, then Print → Save as PDF.*
