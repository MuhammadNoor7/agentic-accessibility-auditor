# Progress reports (team)

This folder holds the **living supplementary progress report** for the Agentic Accessibility Auditor internship.

## Files

| File | Purpose |
|------|---------|
| `Supplementary_Progress_Report_v1.0.md` | **Edit this** — markdown source; team adds weekly updates below (current: **v1.9**, 13 Jul 2026) |
| `Internship_Progress_Report_v1.8.docx` | **Submit this** — Word export for supervisor (regenerate with `scripts/md_to_docx.py`) |

## How to update (all interns)

1. Open `Supplementary_Progress_Report_v1.0.md`
2. Add your entry under **§15 Team weekly updates** (newest week at top)
3. Update **§2 Executive summary** if your work changes pipeline status
4. Push to your branch, then notify Noor for merge coordination
5. Regenerate DOCX: `python scripts/md_to_docx.py docs/progress/Supplementary_Progress_Report_v1.0.md -o docs/progress/Internship_Progress_Report_v1.8.docx`

## Branch ownership

| Person | Branch | What to log |
|--------|--------|-------------|
| Salar | `salar` | Parser, rules, Docker, datasets |
| Ayesha | `ayesha` | Schemas, Figma, React UI |
| Noor | `noor` | Agent, reports, SRS/SDS, QA, coordination |

## Canonical specs (in this repo)

| Document | Path |
|----------|------|
| SRS v2.0 (markdown) | `srs/SRS_Agentic_Accessibility_Auditor_v2.0.md` |
| SRS v2.0 (formatted) | `srs/SRS_Agentic_Accessibility_Auditor_v2.0_formatted.docx` / `.pdf` |
| SDS v2.0 (markdown) | `sds/SDS_Agentic_Accessibility_Auditor_v2.0.md` |
| SDS v2.0 (formatted) | `sds/SDS_Agentic_Accessibility_Auditor_v2.0_formatted.docx` / `.pdf` |
| 8-week plan | `updated_plan.md` |
| Figma screenshots | `docs/assets/figma/` |
