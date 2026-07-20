# Week 7 — Guideline Coverage Summary (G01–G30)

**Generated:** 2026-07-20 10:46 UTC  
**Source:** `src/guidelines.py` RULE_GUIDELINES mapping  
**Sample:** MASC n=40 (Week 6 stratified eval)

| Guideline | Screens hit | % | Violation refs | Description |
|-----------|------------:|--:|---------------:|-------------|
| G07 | 40 | 100% | 1127 | Zero-area or invalid bounds must be removed from focus tree. |
| G25 | 40 | 100% | 1127 | Animation/auto-update must be pausable/stoppable. |
| G15 | 30 | 75% | 650 | Focus order must follow natural top-to-bottom reading sequen |
| G08 | 24 | 60% | 629 | Elements must not overlap in ways that hide content or break |
| G30 | 37 | 92% | 502 | Icon-only buttons must have content-desc describing the acti |
| G01 | 37 | 92% | 418 | Every interactive element must have a visible or programmati |
| G02 | 37 | 92% | 413 | ImageButton and clickable ImageView must have a content desc |
| G18 | 25 | 62% | 102 | All functionality must work with a single pointer. |
| G03 | 10 | 25% | 66 | No two interactive elements should share identical text/cont |
| G17 | 14 | 35% | 46 | Adjacent targets need >=8 dp spacing to prevent mis-taps. |
| G11 | 6 | 15% | 25 | Color must not be the only indicator of state or meaning. |
| G16 | 21 | 52% | 23 | Decorative elements must be excluded from accessibility focu |
| G05 | 11 | 28% | 17 | Every EditText must have a programmatic label (hint, labelFo |
| G20 | 11 | 28% | 17 | Labels must remain visible while typing. |
| G19 | 4 | 10% | 13 | Irreversible actions must require confirmation. |
| G24 | 6 | 15% | 6 | Every screen needs a visible title or heading. |
| G06 | 3 | 8% | 5 | Critical controls must not be disabled without explanation o |
| G14 | 4 | 10% | 5 | Alerts must include visual indicators, not sound alone. |
| G23 | 1 | 2% | 5 | Back, home, close, menu buttons must have descriptive labels |
| G26 | 3 | 8% | 5 | Timed sessions must warn >=20s before expiry with extend opt |
| G04 | 2 | 5% | 2 | Tappable elements must meet minimum size (48x48 dp). |
| G21 | 1 | 2% | 1 | Errors must identify the field and how to fix it. |
| G09 | 0 | 0% | 0 | Text and UI components must meet minimum contrast ratios. |
| G10 | 0 | 0% | 0 | Text bounds must fit full content without clipping. |
| G12 | 0 | 0% | 0 | Video with spoken audio must provide captions/subtitles. |
| G13 | 0 | 0% | 0 | Audio-only content must have a text transcript in the UI. |
| G22 | 0 | 0% | 0 | Password fields should offer reveal/hide control. |
| G27 | 0 | 0% | 0 | Use plain, simple language in labels and hints. |
| G28 | 0 | 0% | 0 | Text must remain readable at 200% system font size. |
| G29 | 0 | 0% | 0 | All-caps must not be used for paragraph or instruction text. |

## Zero-hit guidelines

- **G09** — Text and UI components must meet minimum contrast ratios.
- **G10** — Text bounds must fit full content without clipping.
- **G12** — Video with spoken audio must provide captions/subtitles.
- **G13** — Audio-only content must have a text transcript in the UI.
- **G22** — Password fields should offer reveal/hide control.
- **G27** — Use plain, simple language in labels and hints.
- **G28** — Text must remain readable at 200% system font size.
- **G29** — All-caps must not be used for paragraph or instruction text.
