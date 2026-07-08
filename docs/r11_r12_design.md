# R11 / R12 Stub Design

> Shared with Ayesha for frontend stub design — Week 3
>
> **Update — both rules moved past the stub design below.** R11
> (`check_color_only_info`) now flags checkable-state widgets (CheckBox/
> Switch/ToggleButton/RadioButton) with no text and no content_desc — a
> real, data-grounded check using fields this pipeline actually has, scoped
> to the "no non-visual state indicator exists at all" case. It does **not**
> do true before/after color-diffing (a *changing* color on an otherwise-
> labeled element) — that part of the original design below (paired
> snapshots / cross-capture screenshot diffing) is still unimplemented; see
> the TODO in `check_color_only_info`'s docstring. R12 (`check_missing_captions`)
> now also checks `parent_id`-based sibling adjacency (not just bounds-
> proximity) — the "components.json is a flat list with no adjacency" premise
> below is now out of date; `parent_id` has been on every component for a
> while. The rest of this document is kept as-is for historical context on
> why these two were originally scoped as stubs.

**Status (original, Week 3):** both rules are implemented in `src/rules.py` as documented stubs
(`check_color_only_info` for R11, `check_missing_captions` for R12), wired
into `check()` after R10. Neither is feature-complete yet — see "Known
limitations" below for exactly what's missing and why.

---

## R11 — Color-only information

| Field | Value |
|---|---|
| Rule ID | `R11` |
| Issue name | `Color-Only Info` |
| Guideline | `G11 — Information conveyed by color alone` |
| Severity | `High` |
| WCAG | 1.4.1 |
| User group | Color Blind |

**Guideline text** (from `docs/accessibility_guidelines_report.md`): *"Color
must not be the only indicator of state or meaning."*

**Detection logic** (from the same doc): *"State change only via color, no
icon/text → Color-Only Info."*

In plain terms: this rule is about elements whose state (on/off, valid/
invalid, selected/unselected, success/error) is communicated **purely by a
color change**, with no accompanying icon, text, or shape difference. A red
vs. green border on a text field with no error message next to it is the
canonical example.

### What data this needs

A single static UIAutomator XML dump is a **snapshot**, not a state
transition — it has no concept of "this element used to be blue and is now
red." Real detection needs one of:

1. **Two component snapshots of the same screen** (before/after a state-
   changing interaction, e.g. before/after form submission), diffed by
   `resource_id` so the rule can check whether a color-coded delta is
   accompanied by a `text`/`content_desc`/class change. `components.json`
   does not currently carry this — it would need an optional paired-snapshot
   field, or a second `components_json` argument to a future rule function.
2. **Screenshot pixel analysis** (same category of work as R09's contrast
   check) to detect same-position/same-shape elements that only differ in
   color across two captures.

Neither exists in the pipeline today, so `check_color_only_info()` is a
documented no-op — it always returns `[]`.

### Example violation dict (once implemented)

```json
{
  "rule_id": "R11",
  "issue": "Color-only information",
  "component_id": "c_014",
  "class": "android.widget.EditText",
  "bounds": [40, 300, 600, 360],
  "guideline": "G11 — Information conveyed by color alone",
  "severity": "High",
  "recommendation": "Add a non-color indicator (icon, text, or pattern) alongside the color change so colorblind users can perceive the state.",
  "related_component": "c_013"
}
```

(`related_component` would point at the "before" snapshot of the same
element, mirroring how R03/R08 already use it for pair-based rules.)

### Known limitations / open questions

- **No temporal data.** The core blocker: this rule fundamentally needs
  "before vs. after," and the pipeline only ever sees one moment in time per
  XML file. Until Stage 1 (or a new capture step) supplies paired snapshots,
  this cannot fire on real data.
- **Open question:** should before/after diffing live in the rule checker
  (Stage 2) at all, or is this more naturally a screenshot/vision-based check
  bolted onto the same future stage that would eventually implement R09's
  real contrast analysis? Recommend deciding this before either R09 or R11
  gets real implementation work, since they'd likely share infrastructure
  (screenshot loading, pixel sampling).
- **Open question:** what counts as "close enough" to call two components
  "the same element" across snapshots — `resource_id` match alone, or also
  bounds/class agreement? `resource_id` is frequently empty in real MASC/Rico
  data, which would leave this rule blind on a large fraction of screens.

---

## R12 — Missing captions

| Field | Value |
|---|---|
| Rule ID | `R12` |
| Issue name | `Missing Captions` |
| Guideline | `G12 — Missing captions on video` |
| Severity | `High` |
| WCAG | 1.2.2 |
| User group | Deaf / Hard of Hearing |

**Guideline text** (from `docs/accessibility_guidelines_report.md`): *"Video
with spoken audio must provide captions/subtitles."*

**Detection logic** (from the same doc): *"VideoView present AND no caption
toggle → Missing Captions."*

### What data this needs

- **What exists today:** `class` (to detect `VideoView`/`MediaPlayer`
  widgets) — this part is fully implemented and working.
- **What's missing:** confirming there is *no* caption/CC toggle **nearby**
  requires adjacency information — either the original XML parent/sibling
  tree structure, or at minimum a bounds-proximity heuristic — neither of
  which `components.json` currently exposes. The parser flattens the XML
  tree into a single list (`parse_xml_tree()` in `src/parser.py` walks
  `root.iter()`), discarding parent/child relationships entirely.

Because of this gap, the current stub takes the conservative fallback
position: it flags **every** `VideoView`/`MediaPlayer` component it finds,
unconditionally, rather than trying (and likely getting wrong) an adjacency
check with data it doesn't have.

### Example violation dict (current stub behavior — this already fires)

```json
{
  "rule_id": "R12",
  "issue": "Missing captions",
  "component_id": "c_021",
  "class": "android.widget.VideoView",
  "bounds": [0, 400, 1080, 1000],
  "guideline": "G12 — Missing captions",
  "severity": "High",
  "recommendation": "Add a caption/CC toggle control near the video player."
}
```

### Known limitations / open questions

- **Over-flagging risk:** because adjacency isn't available, this rule will
  flag a `VideoView` even if a real caption toggle exists right next to it in
  the UI — it currently cannot tell the difference. This is a known false-
  positive source until the parser preserves tree structure.
- **Open question:** should the parser add a lightweight `parent_id` (or
  `sibling_ids`) field to each component to unblock this (and future
  adjacency-dependent rules like R15's focus order or R17's spacing), or is a
  purely bounds-based "nearby" heuristic (e.g. within N px) good enough and
  simpler to ship first? Bounds-proximity is easier to add without touching
  the parser's core tree-walk, but is less precise than real tree adjacency.
- **Open question:** what resource_id/content_desc/text substrings should
  count as "a caption toggle" once adjacency is available — `"cc"`,
  `"caption"`, `"subtitle"` are the obvious candidates, but this list should
  probably be reviewed against real MASC/Rico video screens before locking it
  in, to avoid both false positives (matching unrelated text) and false
  negatives (missing a real toggle labeled something else).
