# Week 3 Validation Summary

**Date:** 2026-07-02
**Branch:** salar

---

## Deviation from the literal run command (read this first)

The task asked to run `python test_run.py --dataset masc --max-files 20`.
Raw MASC XML is **not present locally** — only `data/data-masc/parsed/*.json`
(7,071 files, already parsed in an earlier session) exists under
`data/data-masc/`; there is no `data/data-masc/xml/` directory to re-parse
from. Running the literal command confirmed this: `processed_files: 0`.

Since Stage 1 (the parser) couldn't be exercised against real XML here, this
run instead took the **first 20 real, already-parsed MASC `components.json`
files** (genuine MASC screens from the `chat` category, not synthetic
fixtures) and ran them through the **current `src.rules.check()`** — the
part of the pipeline actually under test this week. Violations were written
to `outputs/violations/` exactly as `test_run.py`'s `write_violations()`
already does. Full terminal output for both the literal attempt and this
substitute run is in `week3_validation_log.txt`.

---

## Screens processed

**20** real MASC screens (category: `chat`), selected as the first 20 files
(sorted) under `data/data-masc/parsed/`:

`chat_1054, chat_10560, chat_11382, chat_11389, chat_11390, chat_11396,
chat_11728, chat_11729, chat_12607, chat_13416, chat_14305, chat_14551,
chat_14555, chat_15164, chat_15168, chat_15172, chat_15175, chat_15178,
chat_15179, chat_15180`

## Schema validation results

Two passes were run (see `week3_validation_log.txt` for full output):

1. **`scripts/validate_output.py`** (as instructed) — this script only
   samples the first 5 files per directory, so it did not give full coverage
   of all 20 screens on its own. Everything it checked passed:
   - `components.json`: 14 files checked (across all tracked datasets), **14 passed, 0 failed**
   - `violations.json`: 5 files checked (4 from Rico holdout + 1 from this run's MASC set — `chat_1054`), **5 passed, 0 failed**
2. **Supplementary direct validation** (full coverage, added to close the gap
   left by the 5-file sample) — every one of the 20 screens' files checked
   directly against `docs/schemas/auditor_schema.json`:
   - `components.json`: **20 checked, 20 passed, 0 failed**
   - `violations.json`: **20 checked, 20 passed, 0 failed**

## Files that failed and why

**None.** All 40 files checked (20 `components.json` + 20 `violations.json`)
passed schema validation with zero errors.

## Rules that fired most frequently (across the 20 screens)

| Rule | Count | Issue |
|---|---|---|
| R07 | 1,130 | Invisible or zero-size component |
| R08 | 271 | Possible layout overlap |
| R01 | 261 | Missing accessible label |
| R02 | 28 | Image button without description |
| R03 | 27 | Duplicate labels |
| R05 | 9 | Unlabeled input field |
| R06 | 9 | Disabled important control |
| R04 | 3 | Small touch target |
| R12 | 2 | Missing captions |

**Total violations across all 20 screens: 1,740**

**R07 (zero-size components) dominates**, accounting for ~65% of all
violations. This is worth investigating separately — it's likely a mix of
(a) genuinely invisible/collapsed elements in real chat-UI screens (common in
messaging apps with conditionally-rendered elements) and (b) the parser's
`[0,0,0,0]` fallback bounds (see `src/parser.py::_element_to_component`)
firing on UIAutomator nodes whose bounds couldn't be parsed. Distinguishing
these two cases isn't possible from `violations.json` alone and would need a
targeted look at the source XML once it's available locally.

R09 (low contrast) and R10 (text overflow) did not fire on this sample —
consistent with R09 being an MVP placeholder (no `contrast_score` data
exists) and R10's threshold apparently not being crossed by any TextView in
this particular 20-screen sample. R11 (color-only info) is a documented
no-op stub and never fires on any input.
