# Noor Week 4 Validation Summary

**Date:** 2026-07-09  
**Branch:** noor  
**Owner:** Muhammad Noor

---

## Scope of this validation

This run validates **Noor's Week 4 deliverables** on top of the Week 3 baseline (R01–R20 parser/rules/API):

| Deliverable | What was tested |
|-------------|-----------------|
| Salar sync | Stage 3 LLM layer (`explainer.py`, `guidelines.py`, `llm_providers.py`); rules **R01–R30** + visibility filter |
| Agent API wiring | `build_audit_report()` in `src/agent.py`; full pipeline `parse → checking → explaining → complete` |
| Report endpoint | `GET /api/v1/audit/{id}/report` returns enriched `report.json` (template mode) |
| Explainer layer | 21 unit tests (mocked LLM, anti-hallucination guard, batching) |
| LLM SDKs | Lazy imports for anthropic, openai, google-genai, groq |
| Full pytest | **94 tests** across parser, rules, agent, audit, explainer |
| MASC scan | R01–R30 violation counts on 7,069 parsed screens (random 20-screen sample) |

**Out of scope this week:** HTML/PDF report download, auth/records API, frontend↔API wiring, live LLM prompt experiments (TBD-01).

Full terminal output: `noor_week4_validation_log.txt`  
Re-run: `python scripts/noor_week4_validate.py`

---

## Test results

| Step | Command / check | Result |
|------|-----------------|--------|
| 1 | `pytest tests/test_parser.py` | **10 passed** (visibility + MASC bounds) |
| 2 | `pytest tests/test_rules.py` | **57 passed** (R01–R30 + visibility filter) |
| 3 | `pytest tests/test_agent.py` | **2 passed** (score formula + template enrich) |
| 4 | `pytest tests/test_audit.py` | **4 passed** (violations + report API) |
| 4b | `pytest tests/test_explainer.py` | **21 passed** (anti-hallucination, batching) |
| 4c | `pytest tests/` (full suite) | **94 passed** |
| 4d | `test_run.py` R01 fixture | **SKIP/FAIL** — fixture path outside MASC `xml/` root when dataset root is inferred (API path works) |
| 5 | LLM SDK import check | **4/4 PASS** (anthropic, openai, google-genai, groq) |
| 6 | API smoke (`use_llm=false`) | POST `202`, status `complete`, violations `1×R01`, **report `200`** template mode, score `90` |
| 7 | CLI vs API cross-check | **MATCH** — same violation count and rule_ids; report has agent fields |
| 8 | `scripts/validate_output.py` | **16/16 passed** schema checks |
| 9 | MASC R01–R30 full scan | 7,069 screens; see table below |
| 11 | Direct schema on API output | **Note** — API violations include `component_count`/`hidden_component_count`; report includes `accessibility_score`/`enrichment_mode` (not yet in `auditor_schema.json` oneOf) |

**Combined pytest:** **94 passed** (10 parser + 57 rules + 2 agent + 4 audit + 21 explainer)

---

## Rules R01–R30 status (MASC dataset, 7,069 screens)

| Rule | Violations | Screens (≥1 hit) | Status |
|------|------------|------------------|--------|
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
| R11 | 3,276 | 940 | Working (implemented Week 4 sync) |
| R12 | 79 | 40 | Working |
| R13 | 1,055 | 118 | Working |
| R14 | 1,873 | 667 | Working |
| R15 | 3,860 | 3,860 | Working |
| R16 | 130 | 115 | Working |
| R17 | 9,327 | 1,697 | Working |
| R18 | 13,529 | 3,945 | Working |
| R19 | 758 | 416 | Working |
| R20 | 0 | 0 | Expected zero (no hint-only inputs in MASC) |
| R21 | 313 | 167 | Working (Week 4 sync) |
| R22 | 0 | 0 | Fixture-tested; 0 MASC hits |
| R23 | 582 | 302 | Working |
| R24 | 526 | 526 | Working |
| R25 | 34 | 23 | Working |
| R26 | 16 | 11 | Working |
| R27 | 8 | 8 | Working |
| R28 | 0 | 0 | Needs declared text size |
| R29 | 0 | 0 | Fixture-tested; 0 MASC hits |
| R30 | 11,265 | 2,818 | Working |

**Zero-hit rules on MASC:** R09, R20, R22, R28, R29 (expected given dataset/implementation limits).

---

## API contract verified (Week 4)

| Endpoint | Expected | Observed |
|----------|----------|----------|
| `GET /health` | `200`, `status: healthy` | Pass |
| `POST /api/v1/audit?use_llm=false` | `202`, `status: complete` | Pass |
| `GET /api/v1/audit/{id}/status` | `complete` (includes `explaining` stage) | Pass |
| `GET /api/v1/audit/{id}/violations` | violations JSON | Pass — matches CLI |
| `GET /api/v1/audit/{id}/report` | enriched report JSON | **Pass — 200** (was 404 in Week 3) |

Upload field name for multipart: **`xml`**

Report fields verified: `enrichment_mode`, `accessibility_score`, `summary`, `violations[].agent_*`

---

## Agent layer note

- **Template mode** (`use_llm=false` or no API key): `agent_explanation`, `agent_why_it_matters`, `agent_developer_fix` populated from templates
- **Live LLM mode**: `src/explainer.py` + `src/llm_providers.py` (Groq/Gemini/Anthropic/OpenAI); explainer tests mock the LLM call
- **Gemini SDK**: migrated to `google-genai` (commit `790354554`)
- **TBD-01** (default LLM provider): still open — Ayesha prompt experiments pending

---

## Relation to Week 3 validation

Week 3 (`noor_week3_summary.md`) covered R01–R20, violations-only API, and full MASC re-parse.  
Week 4 extends to **R01–R30**, **report API**, **explainer layer**, and **94 pytest** (up from 38).

---

## Files that failed and why

| Check | Result | Reason |
|-------|--------|--------|
| `test_run.py` on R01 fixture | Fail | Dataset root inferred to MASC; fixture XML not under `data/data-masc/xml/` |
| Direct schema on API-generated report | Fail | `accessibility_score` / `enrichment_mode` not yet in `auditor_schema.json` report branch |

All pytest and API integration checks passed.
