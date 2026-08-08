# Progress reports (team)

This folder holds the **living supplementary progress report** for the Agentic Accessibility Auditor internship.

## Files

| File | Purpose |
|------|---------|
| `Supplementary_Progress_Report_v1.29.md` | **Edit this** — markdown source; team adds weekly updates below (current: **v1.29**, 08 Aug 2026) |
| `Supplementary_Progress_Report_v1.29.docx` | **Submit this** — Word export for supervisor (regenerate with `scripts/md_to_docx.py`) |

Older versions are kept in this folder for version-history reference (see §16 Document history in the report itself); only the highest-numbered `.md`/`.docx` pair is current.

## How to update (all interns)

1. Open the current `Supplementary_Progress_Report_v1.29.md`
2. Add your entry under **§15 Team weekly updates** (newest week at top)
3. Update **§2 Executive summary** if your work changes pipeline status
4. Push to your branch, then notify Noor for merge coordination
5. Bump the version: `git mv` the `.md` (and `.docx`, once regenerated) to the next version number, add a row to **§16 Document history**
6. Regenerate DOCX: `python scripts/md_to_docx.py docs/progress/Supplementary_Progress_Report_v1.29.md -o docs/progress/Supplementary_Progress_Report_v1.29.docx`

## Branch ownership

| Person | Branch | What to log |
|--------|--------|-------------|
| Salar | `salar` | Parser, rules, Docker, datasets |
| Ayesha | `ayesha` | Schemas, Figma, React UI |
| Noor | `noor` | Agent, reports, SRS/SDS, QA, coordination |

## Canonical specs (in this repo)

| Document | Path |
|----------|------|
| SRS v2.12 (markdown) | `srs/SRS_Agentic_Accessibility_Auditor_v2.12.md` |
| SRS v2.12 (Word) | `srs/SRS_Agentic_Accessibility_Auditor_v2.12.docx` |
| SDS v2.16 (markdown) | `sds/SDS_Agentic_Accessibility_Auditor_v2.16.md` |
| SDS v2.16 (Word) | `sds/SDS_Agentic_Accessibility_Auditor_v2.16.docx` |
| Final Internship Report (IEEE) | `docs/final-report/Final_Internship_Report.tex` · `.pdf` |
| 8-week plan | `updated_plan.md` |
| Figma screenshots | `docs/assets/figma/` (11 images — do not re-create a mirror under `docs/progress/assets/`; this report's images link to the canonical folder via `../assets/figma/`) |
