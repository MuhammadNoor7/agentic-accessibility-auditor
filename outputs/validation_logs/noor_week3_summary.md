# Noor Week 3 Validation Summary

**Date:** 2026-07-03  
**Branch:** noor  
**Owner:** Muhammad Noor

---

## Scope of this validation

This run validates **Noor's Week 3 deliverables** on top of Salar's R01–R12 rule engine:

| Deliverable | What was tested |
|-------------|-----------------|
| FastAPI audit stub | `POST /api/v1/audit` → parse → rules → `GET .../violations` |
| Agent scaffold | `src/agent.py` score formula + template enrichment (unit tests only; **not** wired to API yet) |
| CLI parity | `test_run.py` on R01 fixture vs API output |
| Docs / ownership | Progress report §12–§13, SRS §9 cleanup (manual review) |
| Frontend sync | Ayesha `frontend/` tree present (UI-only; no backend calls yet) |

**Out of scope this week:** report API, live LLM agent calls, auth/records endpoints.

Full terminal output: `noor_week3_validation_log.txt`  
Re-run: `python scripts/noor_week3_validate.py`

---

## Test results

| Step | Command / check | Result |
|------|-----------------|--------|
| 1 | `pytest tests/test_rules.py` | **23 passed** (R01–R12 regression) |
| 2 | `pytest tests/test_agent.py` | **2 passed** (score formula + enrich scaffold) |
| 3 | `pytest tests/test_audit.py` | **2 passed** (API pipeline + report endpoint absent) |
| 4 | `test_run.py` R01 fixture | **1 violation** written to `outputs/violations/` |
| 5 | API smoke (TestClient) | POST `202`, status `complete`, violations `1 × R01`, `/report` → **404** |
| 6 | CLI vs API cross-check | **MATCH** — same count and rule_ids |
| 7 | `scripts/validate_output.py` | **16/16 passed** schema checks |
| 8 | Direct schema on R01 output | **PASS** (0 errors) |

**Combined pytest (Noor tests):** 27 passed (23 rules + 2 agent + 2 audit)

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
| `GET /api/v1/audit/{id}/violations` | violations JSON | Pass — matches CLI |
| `GET /api/v1/audit/{id}/report` | Not implemented | **404** (correct) |

Upload field name for multipart: **`xml`**

---

## Schema validation results

- **`validate_output.py`:** 16 files sampled (MASC components + existing violations + Noor R01 components) — **16 passed, 0 failed**
- **Direct check** on `r01_missing_label_fail_violations.json` against `docs/schemas/auditor_schema.json` — **PASS**

## Files that failed and why

**None.** All automated checks passed.

---

## Agent scaffold note

`src/agent.py` is validated by unit tests only:

- Score formula (TBD-02): `100 − (Critical×20 + High×10 + Medium×5 + Low×2)`
- Template fields: `agent_explanation`, `agent_why_it_matters`, `agent_developer_fix`

Live LLM wiring and report generation are **Week 4+** work.

---

## Relation to Salar's Week 3 validation

Salar's log (`week3_validation_log.txt`) covers **20 real MASC screens** through Stage 2 rules (1,740 violations).  
Noor's log covers **API/agent integration** and **CLI↔API parity** on the R01 fixture, confirming the new FastAPI layer produces the same violations JSON shape as `test_run.py` / Streamlit.
