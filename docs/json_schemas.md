# System JSON Schemas
**Project:** Agentic Accessibility Auditor  
**Schema version:** 1.0  
**Author:** Muhammad Noor (schema review)

This document defines the data structures passed between the different modules of the system. Ensuring these schemas are strict allows Interns 1, 2, and 3 to work independently.

**Pipeline flow:** Parser → Rules → Agent → Report

| Stage | Output file | Consumer |
|-------|-------------|----------|
| 1 | `components.json` | Rules engine |
| 2 | `violations.json` | Agent (LLM) |
| 3 | `report.json` | HTML/PDF report, React UI |

Formal machine-readable schemas live in [`schemas/`](schemas/).  
Guidelines and rule-to-guideline mapping: [`accessibility_guidelines_report.md`](accessibility_guidelines_report.md).

---
## Schema Review

Two formats were compared:

1. **Teammate format** — screen-level wrapper (`screen_id`, `image_path`, `xml_path`) around `components[]` and `violations[]`; violations include denormalized `class` and `bounds`.
2. **Original format** — bare arrays for stages 1–2; screen metadata and agent fields only in the final report.

### Verdict

Adopt the **teammate's screen wrapper** for stages 1 and 2, and keep the **original report schema** for stage 3. This is the best of both:

| Decision | Rationale |
|----------|-----------|
| Screen wrapper on all file outputs | One file per screen; paths travel with the data; interns can work on disk artifacts independently |
| Denormalize `class` + `bounds` on violations | Reports and Slack reviews can highlight issues without re-joining `components.json` |
| Keep `recommendation` on raw violations | Rules engine already emits fixes; agent adds deeper explanation later |
| Keep `summary` + agent fields only in `report.json` | Clear separation between deterministic rules output and LLM-enriched output |
| Add `schema_version` | Safe evolution without breaking downstream consumers |

---

## Required Fields — UI Components

### Screen level (`components.json`)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `schema_version` | Recommended | string | `"1.0"` — omit only in legacy files |
| `screen_id` | **Yes** | string | Unique screen identifier, e.g. `screen_001` |
| `image_path` | **Yes** | string | Relative path to screenshot |
| `xml_path` | **Yes** | string | Relative path to UIAutomator XML |
| `components` | **Yes** | array | Parsed UI elements (may be empty) |

### Per component (`components[]`)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `component_id` | **Yes** | string | Stable ID, pattern `c_NNN` (e.g. `c_001`) |
| `class` | **Yes** | string | Android widget class |
| `text` | **Yes** | string | Visible text; use `""` if none |
| `content_desc` | **Yes** | string | Accessibility label; use `""` if none |
| `resource_id` | **Yes** | string | Android resource ID; use `""` if none |
| `clickable` | **Yes** | boolean | Whether the element is clickable |
| `enabled` | **Yes** | boolean | Whether the element is enabled |
| `focusable` | **Yes** | boolean | Whether the element is focusable |
| `bounds` | **Yes** | `[int,int,int,int]` | `[left, top, right, bottom]` in pixels |

**Bounds note:** Format is `[x1, y1, x2, y2]` to check touch target size (R4), detect overlap (R8), measure spacing (R16), and draw bounding boxes in reports.

---

## Required Fields — Accessibility Violations

### Screen level (`violations.json`)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `schema_version` | Recommended | string | `"1.0"` |
| `screen_id` | **Yes** | string | Must match paired `components.json` |
| `image_path` | **Yes** | string | Same screenshot as components file |
| `xml_path` | **Yes** | string | Same XML as components file |
| `total_violations` | **Yes** | integer | Must equal `violations.length` |
| `violations` | **Yes** | array | Detected issues (may be empty) |

### Per violation (`violations[]`)

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `rule_id` | **Yes** | string | `R1`–`R30` (see accessibility rules tables below) |
| `issue` | **Yes** | string | Short problem title |
| `component_id` | **Yes** | string | Links to `components[].component_id` |
| `class` | **Yes** | string | Widget class at detection time |
| `bounds` | **Yes** | `[int,int,int,int]` | Element bounds for report highlighting |
| `guideline` | **Yes** | string | Accessibility principle violated |
| `severity` | **Yes** | enum | `Critical`, `High`, `Medium`, or `Low` |
| `recommendation` | **Yes** | string | Actionable fix from rules engine |
| `related_component` | Conditional | string | Required when a rule involves a second element (e.g. **R3**, **R8**, **R16**) |

### Guidelines (G1–G10) → rules mapping

Canonical mapping aligned with [`accessibility_guidelines_report.md`](accessibility_guidelines_report.md):

| Guideline | Topic | Rules |
|-----------|-------|-------|
| G1 | Visual accessibility (color & contrast) | R11, R13, R9 *(optional)* |
| G2 | Focus & keyboard navigation | R12 |
| G3 | Touch target & motor | R4, R16, R6 |
| G4 | Screen reader & labels | R1, R2, R3, R20, R26, R29 |
| G5 | Form & input accessibility | R5, R19, R21, R30 |
| G6 | Media & multimedia | R14, R15, R17 |
| G7 | Photosensitivity & animation | R18 |
| G8 | Navigation & structure | R7, R8, R22, R25, R27, R28 |
| G9 | Time & session | R24 |
| G10 | Language & cognitive clarity | R10 *(optional)*, R23, R21, R25, R30 |

### Core accessibility rules (R1–R10)

Deterministic rules implemented first from parsed XML/components. **R1–R8** are implemented in `src/rules.py`. **R9–R10** are optional (screenshot-based).

| Rule ID | Guideline | Issue | Detection logic | Severity |
|---------|-----------|-------|-----------------|----------|
| R1 | G4 | Missing accessible label | Clickable element has empty `text` and empty `content-desc`. | High |
| R2 | G4 | Image button without description | `ImageButton` / `ImageView` is clickable but `content-desc` is missing. | High |
| R3 | G4 | Duplicate labels | Multiple clickable elements have the same visible `text` or `content-desc`. | Medium |
| R4 | G3 | Small touch target | Clickable element width or height is below the expected threshold (preferably 48dp). | Medium / High |
| R5 | G5 | Unlabeled input field | `EditText` has no hint, no `text`, and no `content-desc`. | High |
| R6 | G3 | Disabled important control | Important clickable/control element is disabled or inaccessible without a clear reason. | Medium |
| R7 | G8 | Invisible or zero-size component | Element has invalid `bounds` or zero visible area. | Medium |
| R8 | G8 | Possible layout overlap | Two important UI elements have overlapping `bounds`. | Medium |
| R9 | G1, G10 | Low contrast *(optional)* | Estimate foreground/background contrast from screenshot crop. | Medium |
| R10 | G10 | Text overflow *(optional)* | Text component `bounds` are too small for visible text or likely clipped. | Low / Medium |

### Extended accessibility rules (R11–R30)

Additional rules for broader disability coverage and advanced checks.

| Rule ID | Guideline | Issue | Detection logic | Severity |
|---------|-----------|-------|-----------------|----------|
| R11 | G1 | No color-independent indicator | UI uses color as the only way to convey information (e.g. red = error) with no icon, text, or pattern alongside it. | High |
| R12 | G2 | No visual focus indicator | Focusable element has no visible focus ring or highlight state defined (missing `android:state_focused` drawable). | High |
| R13 | G1 | Color contrast for non-text elements | Interactive elements (buttons, icons, borders) have contrast ratio below 3:1 against adjacent colors. | Medium |
| R14 | G6 | Missing captions or transcript indicator | Media element (video/audio player) detected with no visible caption toggle, subtitle button, or transcript link nearby. | High |
| R15 | G6 | Audio-only alert or notification | Alert or notification relies solely on sound with no visible banner, badge, or vibration indicator attribute present. | High |
| R16 | G3 | Insufficient touch target spacing | Two or more clickable elements placed with a gap less than 8dp, risking accidental activation. | Medium |
| R17 | G6 | Auto-playing media without pause control | Media element auto-starts with no accessible pause/stop button reachable within first focusable elements. | Medium |
| R18 | G7 | Flashing or animated content | Element suggests rapid animation or flashing (`resource-id`/`class` contains `flash`, `blink`, `strobe`) that may trigger photosensitive seizures. | Critical |
| R19 | G5 | Form field with no programmatic label association | `EditText` exists alongside a `TextView` label but not programmatically linked (no `labelFor` attribute set). | High |
| R20 | G4 | Redundant or meaningless content description | Element's `content-desc` contains generic text like `image`, `icon`, or `button` rather than describing the actual action or meaning. | Medium |
| R21 | G5, G10 | Missing error suggestion on input field | `EditText` that has a validation error but no `errorMessage` or hint describing what valid input looks like. | Medium |
| R22 | G8 | Scrollable content with no scroll announcement | `ScrollView` or `RecyclerView` present but has no `contentDescription` indicating scrollable region for screen reader users. | Medium |
| R23 | G10 | Language not set on text content | App-level or element-level locale/language attribute is missing, preventing screen readers from reading text in the correct language. | Medium |
| R24 | G9 | Timed content with no extension option | Screen contains a countdown or session timer with no detectable option to extend or disable the time limit. | High |
| R25 | G8, G10 | Missing skip navigation option | Long repeated navigation blocks (e.g. sidebars, menus) have no skip link or shortcut to jump to main content. | Medium |
| R26 | G4 | Interactive element not announced as interactive | A clickable element has no role or class indicating it is a button/control, so screen readers treat it as plain text. | High |
| R27 | G8 | Modal or dialog not trapping focus | Dialog/popup is present but focus is not confined within it, allowing screen reader to navigate behind the overlay. | High |
| R28 | G8 | Missing loading or progress state announcement | Progress bar or loading spinner has no `contentDescription` or live region attribute to announce state to screen readers. | Medium |
| R29 | G4 | Icon-only button with no label | Button contains only an icon drawable with no text and no `content-desc`, giving screen reader users no context. | High |
| R30 | G5, G10 | Placeholder text used as only label | `EditText` relies solely on `android:hint` as its label with no separate visible or programmatic label linked to it. | Medium |

### Coverage by disability

| Disability | Rules |
|------------|-------|
| Color blindness | R11, R13 |
| Low vision / contrast | R9 *(optional)*, R13 |
| Hearing impairment | R14, R15, R17 |
| Photosensitivity | R18 |
| Motor / physical | R4, R6, R16, R24 |
| Screen reader / blind | R1, R2, R3, R5, R12, R19, R20, R21, R22, R25, R26, R27, R28, R29, R30 |
| Cognitive | R10 *(optional)*, R21, R23, R25, R30 |

### Agent-enriched fields (`report.json` only)

Added after the agent stage; not present in raw `violations.json`:

| Field | Required | Type |
|-------|----------|------|
| `agent_explanation` | **Yes** | string |
| `agent_why_it_matters` | **Yes** | string |
| `agent_developer_fix` | **Yes** | string |

---

## Suggested Improvements

1. **Add `schema_version: "1.0"`** to every JSON file for forward compatibility.
2. **Validate with JSON Schema** — use [`schemas/auditor_schema.json`](schemas/auditor_schema.json) in CI or at pipeline startup.
3. **Enforce `total_violations === violations.length`** when writing `violations.json`.
4. **Emit `class` and `bounds` in rules output** — implemented in `rules.py` via `_make_violation()`; wrap with `build_violations_document()` when saving `violations.json`.
5. **Document `related_component`** for pair-based rules (e.g. R3 duplicate labels, R8 overlap, R16 touch spacing).
6. **Use empty strings, not `null`** for missing `text`, `content_desc`, and `resource_id`.
7. **Add severity `summary`** in `report.json` including `critical` count for R18 and other Critical-severity rules.
8. **Constrain enums** — `severity`: `Critical | High | Medium | Low`; `rule_id`: `R1`–`R30`.
9. **Validate bounds** — exactly 4 integers; for visible components require `right > left` and `bottom > top`.

---

## 1. Parsed Components Schema
**File:** `components.json`  
**Producer:** Parser (`src/parser.py`)  
**Consumer:** Rules engine (`src/rules.py`)

```json
{
  "schema_version": "1.0",
  "screen_id": "screen_001",
  "image_path": "data/screenshots/screen_001.png",
  "xml_path": "data/xml/window_001.xml",
  "components": [
    {
      "component_id": "c_001",
      "class": "android.widget.ImageButton",
      "text": "",
      "content_desc": "",
      "resource_id": "com.app:id/back",
      "clickable": true,
      "enabled": true,
      "focusable": true,
      "bounds": [32, 50, 80, 98]
    },
    {
      "component_id": "c_002",
      "class": "android.widget.EditText",
      "text": "",
      "content_desc": "",
      "resource_id": "com.app:id/username",
      "clickable": true,
      "enabled": true,
      "focusable": true,
      "bounds": [32, 120, 400, 168]
    },
    {
      "component_id": "c_003",
      "class": "android.widget.Button",
      "text": "Login",
      "content_desc": "",
      "resource_id": "com.app:id/login_btn",
      "clickable": true,
      "enabled": true,
      "focusable": true,
      "bounds": [32, 200, 400, 248]
    }
  ]
}
```

---

## 2. Violations Schema
**File:** `violations.json`  
**Producer:** Rules engine (`src/rules.py`)  
**Consumer:** Agent (`src/agent.py`)

```json
{
  "schema_version": "1.0",
  "screen_id": "screen_001",
  "image_path": "data/screenshots/screen_001.png",
  "xml_path": "data/xml/window_001.xml",
  "total_violations": 2,
  "violations": [
    {
      "rule_id": "R2",
      "issue": "Image button without description",
      "component_id": "c_001",
      "class": "android.widget.ImageButton",
      "bounds": [32, 50, 80, 98],
      "guideline": "ImageButtons must have a content description that describes their action.",
      "severity": "High",
      "recommendation": "Add android:contentDescription with the action name, such as Back."
    },
    {
      "rule_id": "R5",
      "issue": "Unlabeled input field",
      "component_id": "c_002",
      "class": "android.widget.EditText",
      "bounds": [32, 120, 400, 168],
      "guideline": "All input fields must have a visible label, hint, or content description.",
      "severity": "High",
      "recommendation": "Add android:hint or a programmatic label linked via labelFor."
    }
  ]
}
```

---

## 3. Final Report Schema
**File:** `report.json`  
**Producer:** Agent + report generator  
**Consumer:** HTML/PDF report, React UI

```json
{
  "schema_version": "1.0",
  "screen_id": "screen_001",
  "image_path": "data/screenshots/screen_001.png",
  "xml_path": "data/xml/window_001.xml",
  "summary": {
    "total_issues": 2,
    "critical": 0,
    "high": 2,
    "medium": 0,
    "low": 0
  },
  "violations": [
    {
      "rule_id": "R2",
      "issue": "Image button without description",
      "component_id": "c_001",
      "class": "android.widget.ImageButton",
      "bounds": [32, 50, 80, 98],
      "severity": "High",
      "guideline": "ImageButtons must have a content description that describes their action.",
      "recommendation": "Add android:contentDescription with the action name, such as Back.",
      "agent_explanation": "This ImageButton acts as a back button but has no text alternative.",
      "agent_why_it_matters": "Screen reader users will only hear 'button, unlabelled' and won't know what it does.",
      "agent_developer_fix": "In your XML layout, add android:contentDescription=\"@string/back_action\" to the ImageButton."
    },
    {
      "rule_id": "R5",
      "issue": "Unlabeled input field",
      "component_id": "c_002",
      "class": "android.widget.EditText",
      "bounds": [32, 120, 400, 168],
      "severity": "High",
      "guideline": "All input fields must have a visible label, hint, or content description.",
      "recommendation": "Add android:hint or a programmatic label linked via labelFor.",
      "agent_explanation": "The username field has no hint, text, or associated label.",
      "agent_why_it_matters": "Users relying on assistive technology cannot tell what information to enter.",
      "agent_developer_fix": "Add android:hint=\"Username\" or a TextView label with android:labelFor pointing to this EditText."
    }
  ]
}
```

---

## Example files

Ready-to-use examples are in [`examples/`](examples/):

- [`examples/components.json`](examples/components.json)
- [`examples/violations.json`](examples/violations.json)
- [`examples/report.json`](examples/report.json)
