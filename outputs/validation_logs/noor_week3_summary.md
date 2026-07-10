# Noor Week 3+ Validation Summary

**Date:** 2026-07-06  
**Branch:** noor  
**Owner:** Muhammad Noor

---

## Scope of this validation

This run validates **Noor's Week 3 deliverables** plus **R13-R20 rule engine** and **parser extensions** on top of Salar's R01-R12 baseline:

| Deliverable | What was tested |
|-------------|-----------------|
| Parser extension | 13 new component fields for R13-R20 (`focus_order`, `parent_id`, `media_type`, etc.) |
| Rules R01-R20 | Unit tests + MASC full-dataset scan via `check()` |
| FastAPI audit stub | `POST /api/v1/audit` -> parse -> rules -> `GET .../violations` |
| Agent scaffold | `src/agent.py` score formula + template enrichment (unit tests only; **not** wired to API yet) |
| CLI parity | `test_run.py` on R01 fixture vs API output |
| Schema | `validate_output.py` + direct JSON Schema on R01 output |

**Out of scope this week:** report API, live LLM agent calls, auth/records endpoints.

Full terminal output: `noor_week3_validation_log.txt`  
MASC re-parse detail: `masc_reparse_log.txt`  
Re-run (re-parses all MASC XML, then validates): `python scripts/noor_week3_validate.py`

**Pipeline order:** STEP 0 full MASC re-parse (`parser.py` + `rules.py` via `test_run.py`) → pytest → `validate_output.py` (schema) → full R01-R20 scan + random 20-screen sample.

---

## Test results

| Step | Command / check | Result |
|------|-----------------|--------|
| 1 | `pytest tests/test_parser.py` | **3 passed** (extended fields + parent_id + MASC wrapper nesting) |
| 2 | `pytest tests/test_rules.py` | **31 passed** (R01-R20 regression + controlled component tests) |
| 3 | `pytest tests/test_agent.py` | **2 passed** (score formula + enrich scaffold) |
| 4 | `pytest tests/test_audit.py` | **2 passed** (API pipeline + report endpoint absent) |
| 4b | `test_run.py` R01 fixture | **1 violation** written to `outputs/violations/` |
| 5 | Parser extended fields on R01 XML | **13/13 fields present** - PASS |
| 6 | API smoke (TestClient) | POST `202`, status `complete`, violations `1 x R01`, `/report` -> **404** |
| 7 | CLI vs API cross-check | **MATCH** - same count and rule_ids |
| 8 | `scripts/validate_output.py` | **16/16 passed** schema checks |
| 9 | MASC R01-R20 full scan | 7,068 screens re-parsed; **random 20** screen sample each run |
| 11 | Direct schema on R01 output | **PASS** (0 errors) |

**Combined pytest:** **38 passed** (3 parser + 31 rules + 2 agent + 2 audit)

---

## Rules R01-R20 status

### Unit tests (controlled fixtures)

| Rule | Unit test coverage | Notes |
|------|-------------------|-------|
| R01-R10 | Pass/fail XML fixtures + edge cases | R09 needs `contrast_score` from screenshots |
| R11 | Stub test | Returns empty (Ayesha ownership; not implemented) |
| R12 | Media + caption tests | Uses `media_type` |
| R13-R20 | Parametrized controlled components | R17 spacing test; R15 uses focus-order logic |

### MASC dataset scan (7,068 screens, **fresh re-parse from XML**)

**Re-parse run (2026-07-06):** `python test_run.py --dataset masc`  
- XML source: `data/data-masc/xml` (junction to full MASC dataset)  
- **640,563 components** parsed, **462,542 violations** written  
- **0 stale** files (all include extended parser fields)

Parser fix: MASC widgets live inside `<wrapper>` nodes; the walker now descends into wrappers (previously only 1 component/screen was extracted).

| Rule | Violations | Screens (>=1 hit) | Status |
|------|------------|-------------------|--------|
| R01 | 60,112 | 6,185 | Working |
| R02 | 11,123 | 2,788 | Working |
| R03 | 12,578 | 1,901 | Working |
| R04 | 739 | 408 | Working |
| R05 | 3,797 | 1,591 | Working |
| R06 | 1,448 | 865 | Working |
| R07 | 266,393 | 7,051 | Working |
| R08 | 75,718 | 3,699 | Working |
| R09 | 0 | 0 | Expected zero (needs screenshot contrast) |
| R10 | 24 | 21 | Working |
| R11 | 0 | 0 | Expected zero (stub) |
| R12 | 79 | 40 | Working |
| R13 | 1,055 | 118 | Working |
| R14 | 1,873 | 667 | Working |
| R15 | 3,860 | 3,860 | Working |
| R16 | 130 | 115 | Working |
| R17 | 9,327 | 1,697 | Working |
| R18 | 13,529 | 3,945 | Working (was 10 hits on stale 1-component parses) |
| R19 | 758 | 416 | Working |
| R20 | 0 | 0 | No hint-only inputs in MASC |

**Zero-hit rules on MASC:** R09, R11, R20 (all expected given implementation limits / dataset).

---

## Parser extension (R13-R20 support)

When XML fixtures are parsed fresh, components include:

`focus_order`, `parent_id`, `long_clickable`, `scrollable`, `selected`, `checked`, `password`, `text_all_caps`, `input_type`, `important_for_accessibility`, `media_type`, `is_dialog`, `label_for`

R01 fixture: **13/13 fields present**, **1 component with `parent_id`**.

---

## Fixture exercised

**Primary end-to-end fixture:** `tests/fixtures/rules/r01_missing_label_fail.xml`

| Output | Path | Key result |
|--------|------|------------|
| `components.json` | `data/parsed/rules/r01_missing_label_fail_components.json` | 2 components parsed |
| `violations.json` | `outputs/violations/r01_missing_label_fail_violations.json` | `total_violations: 1`, `rule_id: R01` |

---

## API contract verified (Week 3)

| Endpoint | Expected | Observed |
|----------|----------|----------|
| `GET /health` | `200`, `status: healthy` | Pass |
| `POST /api/v1/audit` | `202`, `status: complete` | Pass |
| `GET /api/v1/audit/{id}/status` | `complete` | Pass |
| `GET /api/v1/audit/{id}/violations` | violations JSON | Pass - matches CLI |
| `GET /api/v1/audit/{id}/report` | Not implemented | **404** (correct) |

Upload field name for multipart: **`xml`**

---

## Schema validation results

- **`validate_output.py`:** 16 files sampled - **16 passed, 0 failed**
- **Direct check** on `r01_missing_label_fail_violations.json` - **PASS**

## Files that failed and why

**None.** All automated checks passed.

---

## Agent scaffold note

`src/agent.py` is validated by unit tests only:

- Score formula (TBD-02): `100 - (Critical x 20 + High x 10 + Medium x 5 + Low x 2)`
- Template fields: `agent_explanation`, `agent_why_it_matters`, `agent_developer_fix`

Live LLM wiring and report generation are **Week 4+** work.

---

## Relation to Salar's Week 3 validation

Salar's log (`week3_validation_log.txt`) covers **20 real MASC screens** through Stage 2 rules (R01-R12).  
Noor's log extends coverage to **R01-R20**, parser extensions, API/agent integration, and **CLI<->API parity** on the R01 fixture.

**MASC re-parse:** completed 2026-07-06 via `python test_run.py --dataset masc`. Requires `data/data-masc/xml` + `screenshots` (junction-linked to full dataset in this workspace).
