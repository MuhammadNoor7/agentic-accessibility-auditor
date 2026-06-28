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

**Bounds note:** Format is `[x1, y1, x2, y2]` to check touch target size (R04), detect overlap (R08), measure spacing (R17), and draw bounding boxes in reports.

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
| `rule_id` | **Yes** | string | `R01`–`R30` (see accessibility rules tables below) |
| `issue` | **Yes** | string | Short problem title |
| `component_id` | **Yes** | string | Links to `components[].component_id` |
| `class` | **Yes** | string | Widget class at detection time |
| `bounds` | **Yes** | `[int,int,int,int]` | Element bounds for report highlighting |
| `guideline` | **Yes** | string | Accessibility principle violated |
| `severity` | **Yes** | enum | `Critical`, `High`, `Medium`, or `Low` |
| `recommendation` | **Yes** | string | Actionable fix from rules engine |
| `related_component` | Conditional | string | Required when a rule involves a second element (e.g. **R03**, **R08**, **R17**) |

### Guidelines (G01–G30) → rules mapping

Canonical mapping aligned with [`accessibility_guidelines_report.md`](accessibility_guidelines_report.md):

| Guideline | Topic | Rules |
|-----------|-------|-------|
| G01 | Missing accessible label | R01, R23, R30 |
| G02 | Image button without description | R01, R02 |
| G03 | Duplicate labels | R03 |
| G04 | Small touch target | R04 |
| G05 | Unlabeled input field | R05, R20 |
| G06 | Disabled important control | R06 |
| G07 | Invisible or zero-size component | R07 |
| G08 | Possible layout overlap | R08 |
| G09 | Low contrast | R09 *(optional)* |
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

### All detection rules (R01–R30)

Rules are detected from parsed XML/components. **R09** is optional (screenshot-based). Rule checker module is planned for Week 3+.

| Rule ID | Guidelines | Issue (flag) | Severity |
|---------|------------|--------------|----------|
| R01 | G01,G02,G30 | Missing Label | High |
| R02 | G02,G30 | No Image Desc | High |
| R03 | G03 | Duplicate Label | Medium |
| R04 | G04,G17 | Small Touch Target | High |
| R05 | G05,G20 | Unlabeled Input | High |
| R06 | G06,G26 | Disabled Control | Medium |
| R07 | G07,G25 | Zero-Size Element | Medium |
| R08 | G08,G15 | Layout Overlap | Medium |
| R09 | G09,G11 | Low Contrast *(optional)* | Medium |
| R10 | G10,G28,G29 | Text Overflow | Low/Medium |
| R11 | G11 | Color-Only Info | High |
| R12 | G12 | Missing Captions | High |
| R13 | G13 | No Transcript | High |
| R14 | G14 | Audio-Only Notification | Medium |
| R15 | G15,G16 | Bad Focus Order | Medium |
| R16 | G16 | Decorative In Focus Tree | Low |
| R17 | G17 | Insufficient Spacing | Medium |
| R18 | G18 | Multi-Gesture Only | High |
| R19 | G19 | No Confirmation | Medium |
| R20 | G05,G20 | Hint-Only Label | Medium |
| R21 | G21 | Vague Error Message | High |
| R22 | G22 | No Password Toggle | Medium |
| R23 | G01,G23 | Unlabeled Nav Control | High |
| R24 | G24 | Missing Screen Title | Medium |
| R25 | G25 | Uncontrolled Animation | Medium |
| R26 | G26 | No Timeout Warning | Medium |
| R27 | G27 | Complex Label Language | Low |
| R28 | G10,G28 | Font Scale Overflow | Medium |
| R29 | G29 | All-Caps Body Text | Low |
| R30 | G01,G30 | Icon-Only No Label | High |

### Coverage by disability

| Disability | Rules |
|------------|-------|
| Blind / Screen Reader | R01,R02,R03,R15,R16,R23,R24,R30 |
| Low Vision | R09,R10,R28 |
| Color Blind | R09,R11 |
| Deaf / Hard of Hearing | R12,R13,R14 |
| Motor Impaired | R04,R06,R17,R18,R19 |
| Elderly | R04,R09,R10,R28 |
| Cognitive / Memory | R03,R20,R21,R22,R27 |
| ADHD / Epilepsy | R25,R26 |
| Dyslexia / Low Literacy | R27,R29 |
| All Users | R06,R07,R08 |

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
4. **Emit `class` and `bounds` in rule-checker output** — denormalize on each violation when saving `violations.json`.
5. **Document `related_component`** for pair-based rules (R03 duplicate labels, R08 overlap, R17 spacing).
6. **Use empty strings, not `null`** for missing `text`, `content_desc`, and `resource_id`.
7. **Add severity `summary`** in `report.json` with counts per severity level.
8. **Constrain enums** — `severity`: `Critical | High | Medium | Low`; `rule_id`: `R01`–`R30`.
9. **Validate bounds** — exactly 4 integers; for visible components require `right > left` and `bottom > top`.

---

## 1. Parsed Components Schema
**File:** `components.json`  
**Producer:** XML parser (planned)  
**Consumer:** Rule checker (planned)

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
**Producer:** Rule checker (planned)  
**Consumer:** Agent explanation module (planned)

```json
{
  "schema_version": "1.0",
  "screen_id": "screen_001",
  "image_path": "data/screenshots/screen_001.png",
  "xml_path": "data/xml/window_001.xml",
  "total_violations": 2,
  "violations": [
    {
      "rule_id": "R02",
      "issue": "Image button without description",
      "component_id": "c_001",
      "class": "android.widget.ImageButton",
      "bounds": [32, 50, 80, 98],
      "guideline": "G02 — Image button without description",
      "severity": "High",
      "recommendation": "Add android:contentDescription with the action name, such as Back."
    },
    {
      "rule_id": "R05",
      "issue": "Unlabeled input field",
      "component_id": "c_002",
      "class": "android.widget.EditText",
      "bounds": [32, 120, 400, 168],
      "guideline": "G05 — Unlabeled input field",
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
      "rule_id": "R02",
      "issue": "Image button without description",
      "component_id": "c_001",
      "class": "android.widget.ImageButton",
      "bounds": [32, 50, 80, 98],
      "severity": "High",
      "guideline": "G02 — Image button without description",
      "recommendation": "Add android:contentDescription with the action name, such as Back.",
      "agent_explanation": "This ImageButton acts as a back button but has no text alternative.",
      "agent_why_it_matters": "Screen reader users will only hear 'button, unlabelled' and won't know what it does.",
      "agent_developer_fix": "In your XML layout, add android:contentDescription=\"@string/back_action\" to the ImageButton."
    },
    {
      "rule_id": "R05",
      "issue": "Unlabeled input field",
      "component_id": "c_002",
      "class": "android.widget.EditText",
      "bounds": [32, 120, 400, 168],
      "severity": "High",
      "guideline": "G05 — Unlabeled input field",
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
