# Software Design Specification

## Agentic Accessibility Auditor (Axion)
### for Android Mobile Application UIs

| Field | Value |
|-------|-------|
| **Document version** | 2.2 |
| **Status** | Implementation reference |
| **Prepared by** | Muhammad Noor (Lead), Salar (Parser/Rules/Docker), Ayesha (Frontend/Schemas) |
| **Institution** | FAST-NUCES |
| **Related SRS** | `SRS_Agentic_Accessibility_Auditor_v2.0.md` (v2.0) |
| **Repository** | [MuhammadNoor7/agentic-accessibility-auditor](https://github.com/MuhammadNoor7/agentic-accessibility-auditor) |

---

## Document history

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026 | Team | Initial SDS from merged SRS v1.x |
| **2.0** | 2026 | Team | Aligned to SRS v2.0 with embedded Figma screenshots; auth, Records, Dashboard flows |
| **2.1** | 2026-07-06 | Noor / Salar | Parser R13–R20 fields; rules R01–R20; MASC re-parse sign-off; audit API violations-only |
| **2.2** | 2026-07-09 | Noor / Salar | Rules R01–R30; explainer + agent API wiring; `GET …/report`; visibility filter |

---

## Table of contents

1. [Introduction](#1-introduction)
2. [System architecture](#2-system-architecture)
3. [Module design](#3-module-design)
4. [Data design](#4-data-design)
5. [API design](#5-api-design)
6. [Rule engine design](#6-rule-engine-design)
7. [Agentic layer design](#7-agentic-layer-design)
8. [Report generator design](#8-report-generator-design)
9. [Frontend design (Axion)](#9-frontend-design-axion)
10. [Authentication and Records design](#10-authentication-and-records-design)
11. [Deployment design](#11-deployment-design)
12. [Security design](#12-security-design)
13. [Testing design](#13-testing-design)
14. [SRS traceability](#14-srs-traceability)
- [Appendix A: OpenAPI specification](#appendix-a-openapi-specification)
- [Appendix B: File and directory map](#appendix-b-file-and-directory-map)
- [Appendix C: Sequence diagrams](#appendix-c-sequence-diagrams)
- [Appendix D: UI component map (Figma)](#appendix-d-ui-component-map-figma)

---

## 1. Introduction

### 1.1 Purpose

This Software Design Specification (SDS) describes **how** the Agentic Accessibility Auditor is designed and implemented. It is the technical companion to **SRS v2.0**, which defines **what** the system must do.

This document provides:

- Architecture and module boundaries
- Class/function design and algorithms
- Normative JSON schema usage
- REST API contracts (OpenAPI)
- Frontend component structure (Axion)
- Auth and per-user Records storage design
- Deployment, security, and test design

### 1.2 Design scope

| In scope | Out of scope |
|----------|--------------|
| Parser, rule engine, agent, report generator | Business case / internship planning |
| FastAPI orchestrator + Axion React UI | Clinical accessibility research |
| Auth + Records persistence | Production HIPAA / enterprise SSO |
| Docker Compose topology | Play Store / APK crawling |
| R01–R20 rule pseudocode + parser extensions | Full R21–R30 implementation detail |

### 1.3 Design principles

| ID | Principle | Rationale |
|----|-----------|-----------|
| D1 | Pipeline isolation via JSON artefacts | Interns integrate through agreed files/API |
| D2 | Deterministic rule engine | Same input → same `violations.json` |
| D3 | LLM explains only | Agent never creates violations |
| D4 | Schema-first contracts | `auditor_schema.json` validated in CI |
| D5 | Hybrid parser, single traversal | UIAutomator + MASC + Rico in one pass |
| D6 | Fail gracefully | Bad XML, LLM timeout → structured errors |
| D7 | User-scoped Records | Each audit linked to authenticated `user_id` |

### 1.4 Implementation status

| Module | Path | Owner | Status |
|--------|------|-------|--------|
| Hybrid XML parser | `src/parser.py` | Salar / Noor | **Done** (R13–R20 fields + visibility) |
| Schema helpers | `src/schema_documents.py` | Salar | **Done** |
| JSON Schema | `docs/schemas/auditor_schema.json` | Ayesha / Noor | **Done** |
| Validation scripts | `scripts/validate_output.py`, `scripts/noor_week3_validate.py`, `scripts/masc_parse_signoff.py` | Noor / Salar | **Done** |
| FastAPI audit API | `backend/routers/audit.py` | Noor | **Partial** (violations + report; no auth/records/download) |
| Rule engine | `src/rules.py` | Salar / Noor | **Done** (R01–R30; R09/R28 limited without colors/text-size) |
| Agent layer | `src/agent.py`, `src/explainer.py`, `src/llm_providers.py` | Noor / Salar | **Done** (API-wired; template + live LLM) |
| Report generator | `src/report.py` | Noor | Planned |
| Auth service | `backend/services/auth.py` | Salar | Planned |
| Records store | `backend/services/records.py` | Salar / Ayesha | Planned |
| Axion React UI | `frontend/` | Ayesha | **Partial** (UI scaffold; no live API) |
| Docker Compose | `docker-compose.yml` | Salar | **Partial** (deferred on `noor`) |

---

## 2. System architecture

### 2.1 Logical architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    Axion React Dashboard (frontend/)                      │
│  Auth │ Upload │ Dashboard │ Report │ Records │ Generate Report Modal    │
└───────────────────────────────┬──────────────────────────────────────────┘
                                │ HTTPS + JWT
┌───────────────────────────────▼──────────────────────────────────────────┐
│                   FastAPI Orchestrator (backend/)                           │
│  /auth/* │ /audit/* │ /records/* │ PipelineService │ RecordsService        │
└───┬─────────┬──────────┬──────────┬──────────┬─────────────────────────────┘
    │         │          │          │          │
    ▼         ▼          ▼          ▼          ▼
 Parser   RuleEngine   Agent    ReportGen   RecordsStore
 src/     src/rules    src/     src/report  outputs/records/
          agent
    │         │          │          │
    ▼         ▼          ▼          ▼
components  violations  report.json  audit_record.json
  .json       .json                  + HTML/PDF paths
```

### 2.2 Pipeline data flow

```
Screenshot + UIAutomator XML
  → Parser          → components.json
  → Rule Engine     → violations.json
  → Agent           → report.json
  → Report Generator → audit_report.html / .pdf
  → Records Service  → outputs/records/{user_id}/{record_id}/
  → Axion UI         → Dashboard + Records list
```

### 2.3 Physical deployment (Docker Compose)

| Service | Image | Port | Role |
|---------|-------|------|------|
| `frontend` | `./frontend/Dockerfile` | 5173 | Axion React (Vite) |
| `backend` | `./backend/Dockerfile` | 8000 | FastAPI + pipeline |
| `auditor` | `./Dockerfile` | — | Batch parser worker |

Network: `auditor-network` (bridge). Repo root mounted at `/app`.

### 2.4 Per-audit run directory

```
outputs/runs/{audit_id}/
├── input/
│   ├── screenshot.png
│   └── window.xml
├── components.json
├── violations.json
├── report.json
├── audit_report.html
└── audit_report.pdf
```

### 2.5 Per-user Records directory

```
outputs/records/{user_id}/
├── index.json                 # list of record summaries
└── {record_id}/
    ├── metadata.json          # screen_id, score, dates, paths
    ├── report.json
    ├── audit_report.html
    └── audit_report.pdf
```

---

## 3. Module design

### 3.1 Parser module (`src/parser.py`)

**SRS:** FR-PS.1–FR-PS.9 | **Owner:** Salar | **Status:** Implemented

#### 3.1.1 Responsibilities

- Sanitize XML (strip `\x00`)
- Traverse hierarchy; emit flat `components[]`
- Infer `screen_id`, `image_path`, `xml_path`
- Write schema-compliant `components.json`

#### 3.1.2 Public API

| Function | Input | Output |
|----------|-------|--------|
| `load_xml_root(path)` | Path | lxml root |
| `parse_xml_tree(root)` | Element | `list[dict]` |
| `build_screen_document(...)` | paths + components | JSON dict |
| `parse_xml_file(xml_path, ...)` | Path | output Path |
| `parse_dataset_folder(...)` | dataset root | batch stats |

#### 3.1.3 Bounds parsing algorithm

```
parse_bounds(raw):
  if matches "[l,t][r,b]" → return [l,t,r,b]      # UIAutomator
  if matches "l t r b"    → return [l,t,r,b]      # Rico
  return None

extract_bounds(element):
  b = parse_bounds(element.@bounds)
  if b: return b
  b = parse_masc_wrapper_bounds(element)
  if b: return b
  if is_uiautomator_node(element):
    return [0,0,0,0]                               # TC-01
  return None
```

#### 3.1.5 Extended component fields (R13–R20)

Depth-first traversal preserves `parent_id` and assigns `focus_order` in document order. MASC `<wrapper>` nodes are descended into (widgets are nested inside wrappers).

| Field | Used by | Notes |
|-------|---------|-------|
| `focus_order` | R15 | 1-based traversal index |
| `parent_id` | R15, hierarchy | `component_id` of parent or `""` |
| `long_clickable`, `scrollable` | R18 | Gesture heuristics |
| `media_type` | R12, R13 | `""`, `video`, `audio`, `animation` |
| `is_dialog` | R19 | Confirmation dialog detection |
| `label_for`, `hint`, `input_type`, `password` | R05, R20 | Input labelling |
| `important_for_accessibility` | R16 | Decorative vs focusable |

Also emitted: `selected`, `checked`, `text_all_caps`, `device_info.dpi` on screen document.

#### 3.1.4 Screenshot pairing

Mirror XML path under `screenshots/` with same stem; try `.jpg`, `.jpeg`, `.png`.

---

### 3.2 Rule engine module (`src/rules.py`)

**SRS:** FR-RU.1–FR-RU.30 | **Owner:** Salar / Noor | **Status:** Implemented (R01–R30)

#### 3.2.1 Public API

| Function | Input | Output |
|----------|-------|--------|
| `check(components_json)` | `components.json` dict | `violations.json` dict |
| `check_*` per rule | `list[dict]` components | `list[dict]` violations |

Implementation uses plain functions (not a `RuleEngine` class). Entry point `check()` filters hidden components (`visibility`), then chains R01–R30 checkers, reads `device_info.dpi` for dp rules (R04, R17, R28), and returns schema-shaped output.

#### 3.2.2 Processing flow

1. Load `components[]` and `device_info.dpi` (default 160)
2. Drop components with `visibility=false` (MASC `gone` / `visible-to-user=False`)
3. Run R01–R30 check functions in order
4. Each violation includes denormalized `class`, `bounds`; pair rules add `related_component` (R03, R08, R17)
5. Return dict with `total_violations == len(violations)` plus component/hidden counts

#### 3.2.3 Rule status (Week 4)

| Rules | Status |
|-------|--------|
| R01–R08, R10–R30 | Implemented |
| R09 | Implemented when declared colors present; otherwise inactive |
| R28 | Implemented when declared text size present; otherwise inactive |

#### 3.2.4 dp conversion

```
width_dp  = (bounds[2] - bounds[0]) / density
height_dp = (bounds[3] - bounds[1]) / density
```

Default `dpi = 160` when `device_info` absent (TBD-03).

#### 3.2.5 Severity mapping (engine → UI)

| Engine | Axion badge |
|--------|-------------|
| Critical | Critical |
| High | Serious |
| Medium | Moderate |
| Low | Minor |

---

### 3.3 Agent module (`src/agent.py` + `src/explainer.py`)

**SRS:** FR-AG.1–FR-AG.8 | **Owner:** Noor / Salar | **Status:** Done (API-wired Week 4)

```python
def build_audit_report(
    violations_doc: dict,
    components_doc: dict | None = None,
    *,
    use_llm: bool | None = None,
) -> dict: ...

class AgenticEnricher:
    def enrich(self, violations_doc: dict, components_doc: dict | None = None) -> dict: ...
```

- `build_audit_report()` produces `report.json` with `accessibility_score`, `summary`, and per-violation agent fields
- Live path: `src/explainer.py` → `src/llm_providers.py` (Anthropic / OpenAI / Gemini / Groq), batched, anti-hallucination match
- Fallback: template enrichment when no API key or `use_llm=false` (FR-AG.6)
- Wired in `backend/routers/audit.py` → `GET /api/v1/audit/{id}/report`

---

### 3.4 Report module (`src/report.py` — planned)

**SRS:** FR-RP.1–FR-RP.7 | **Owner:** Noor

- Jinja2 HTML template
- PIL bounding-box annotation
- WeasyPrint or pdfkit for PDF
- Accessibility score (see §8.2)

---

### 3.5 API orchestrator (`backend/`)

**Owner:** Salar + Noor

```
backend/
├── main.py                 # FastAPI app, CORS, routers
├── config.py               # env settings
├── routers/
│   ├── auth.py
│   ├── audit.py
│   └── records.py
├── services/
│   ├── pipeline.py         # stage orchestration
│   ├── auth.py             # JWT, OTP
│   └── records.py          # user-scoped persistence
├── models/
│   ├── auth.py             # Pydantic models
│   ├── audit.py
│   └── records.py
└── dependencies.py         # get_current_user
```

#### 3.5.1 Pipeline service

```python
async def run_audit(audit_id: str, user_id: str) -> None:
    set_status(audit_id, "parsing")
    components = parse_xml_file(...)
    set_status(audit_id, "checking")
    violations = rule_engine.run(components)
    set_status(audit_id, "explaining")
    report = agent.enrich(violations, components)
    set_status(audit_id, "reporting")
    paths = report_gen.render(report, run_dir)
    set_status(audit_id, "complete")
    records_service.save(user_id, audit_id, report, paths)
```

Statuses: `pending` → `parsing` → `checking` → `explaining` → `reporting` → `complete` | `error`

---

## 4. Data design

Normative schema: `docs/schemas/auditor_schema.json`

### 4.1 Entity relationship

```
User (user_id)
  └── has many AuditRecord (record_id)
        ├── has one Screen (screen_id, image_path, xml_path)
        ├── has many Violations
        └── has report artefacts (json, html, pdf)
```

### 4.2 components.json

| Field | Type | Required |
|-------|------|----------|
| `schema_version` | string `"1.0"` | Recommended |
| `screen_id` | string | Yes |
| `image_path` | string | Yes |
| `xml_path` | string | Yes |
| `components` | array | Yes |

**Component (required):** `component_id`, `class`, `text`, `content_desc`, `resource_id`, `clickable`, `enabled`, `focusable`, `bounds[4]`

**Component (optional, R13–R20):** `hint`, `focus_order`, `parent_id`, `long_clickable`, `scrollable`, `selected`, `checked`, `password`, `text_all_caps`, `input_type`, `important_for_accessibility`, `media_type`, `is_dialog`, `label_for`

**Screen:** optional `device_info` with `dpi`, `width_px`, `height_px`

Pattern: `component_id` matches `^c_\d{3,}$`

### 4.3 violations.json

**Screen level:** `schema_version`, `screen_id`, `image_path`, `xml_path`, `total_violations`, `violations[]`

**Violation:** `rule_id`, `issue`, `component_id`, `class`, `bounds`, `guideline`, `severity`, `recommendation`, optional `related_component`

**Invariant:** `total_violations == len(violations)`

### 4.4 report.json

Adds `summary` object and agent fields per violation:

- `agent_explanation`
- `agent_why_it_matters`
- `agent_developer_fix`

### 4.5 records metadata (`metadata.json`)

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | string | UUID |
| `user_id` | string | Owner |
| `audit_id` | string | Pipeline run ID |
| `screen_id` | string | e.g. `screen_014` |
| `score` | int | 0–100 |
| `total_issues` | int | Violation count |
| `severity_summary` | object | `{critical, high, medium, low}` |
| `created_at` | ISO datetime | Audit timestamp |
| `report_html_path` | string | Relative path |
| `report_pdf_path` | string | Relative path |

### 4.6 index.json (per user)

```json
{
  "user_id": "u_001",
  "records": [
    {
      "record_id": "rec_abc123",
      "screen_id": "screen_014",
      "score": 78,
      "total_issues": 7,
      "created_at": "2026-07-01T12:00:00Z"
    }
  ]
}
```

### 4.7 Validation

```bash
python test_run.py --dataset masc          # batch parse + rules → parsed/ + outputs/violations/
python scripts/validate_output.py          # JSON Schema spot-check
python scripts/masc_parse_signoff.py       # train/val/test parse sign-off + R13–R20 counts
python scripts/noor_week3_validate.py      # full pipeline: re-parse, pytest, API smoke, MASC scan
```

MASC artefacts:

| Path | Purpose |
|------|---------|
| `data/data-masc/parsed/*_components.json` | Re-parsed components (all categories) |
| `data/data-masc/parsed/batch_parse_masc_full.log` | Full batch parse terminal log |
| `data/data-masc/parsed/masc_parse_signoff_report.json` | Parse sign-off + R01–R20 aggregate counts |
| `outputs/violations/*_violations.json` | Per-screen rule output |
| `outputs/validation_logs/noor_week3_validation_log.txt` | Noor validation run log (appended) |

Run after each pipeline stage or via `python scripts/noor_week3_validate.py`.

---

## 5. API design

Base URL: `http://localhost:8000`  
Prefix: `/api/v1`  
Auth: `Authorization: Bearer <JWT>` (except auth endpoints)

### 5.1 Auth endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/auth/signup` | Email + password (≥ 8 chars) |
| POST | `/auth/login` | Returns JWT |
| POST | `/auth/google` | Google OAuth token exchange |
| POST | `/auth/forgot-password` | Send 6-digit OTP |
| POST | `/auth/verify-otp` | Validate OTP |
| POST | `/auth/reset-password` | Set new password |

### 5.2 Audit endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/audit` | Upload XML (multipart field `xml`); optional `use_llm` query; start pipeline |
| GET | `/audit/{audit_id}/status` | Pipeline status (`pending` → `parsing` → `checking` → `explaining` → `complete`) |
| GET | `/audit/{audit_id}/violations` | Violations JSON (**implemented**) |
| GET | `/audit/{audit_id}/report` | Report JSON with score + agent fields (**implemented** Week 4) |
| GET | `/audit/{audit_id}/report/download?format=html\|pdf` | File download (**planned** Week 5) |
| POST | `/audit/batch` | Batch over dataset path (Should) |

### 5.3 Records endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/records` | List current user's audits |
| GET | `/records/{record_id}` | Record detail + artefact paths |
| GET | `/records/{record_id}/download?format=html\|pdf` | Re-download report |
| DELETE | `/records/{record_id}` | Delete record (Stretch) |

### 5.4 Example: POST /audit

**Request:** `multipart/form-data` — `screenshot`, `xml`

**Response 201:**

```json
{
  "audit_id": "a1b2c3d4",
  "record_id": "rec_xyz789",
  "status": "pending",
  "screen_id": "screen_014"
}
```

### 5.5 Example: GET /audit/{id}/status

```json
{
  "audit_id": "a1b2c3d4",
  "status": "checking",
  "stage_progress": {
    "parsing": "complete",
    "checking": "in_progress",
    "explaining": "pending",
    "reporting": "pending"
  },
  "error": null
}
```

### 5.6 Example: GET /records

```json
{
  "user_id": "u_001",
  "records": [
    {
      "record_id": "rec_xyz789",
      "screen_id": "screen_014",
      "score": 78,
      "total_issues": 7,
      "severity_summary": {"critical": 4, "high": 3, "medium": 0, "low": 0},
      "created_at": "2026-07-01T12:00:00Z"
    }
  ]
}
```

---

## 6. Rule engine design

Pseudocode for **MVP rules R01–R10**. Full catalogue: SRS §7.2.

### 6.1 Shared helpers

```python
def is_empty(s: str) -> bool:
    return not s or not s.strip()

def is_clickable(c: dict) -> bool:
    return c["clickable"] is True
```

### 6.2 R01 — Missing accessible label

```
for c in components:
  if c.clickable and is_empty(c.text) and is_empty(c.content_desc):
    emit(R01, c, severity=High, guideline=G01)
```

### 6.3 R02 — Image button without description

```
for c in components:
  if is_image_class(c.class) and c.clickable and is_empty(c.content_desc):
    emit(R02, c, severity=High, guideline=G02)
```

### 6.4 R03 — Duplicate labels

Group clickable components by `(text or content_desc)`; flag groups with ≥ 2 distinct component IDs.

### 6.5 R04 — Small touch target

```
if width_dp < 48 or height_dp < 48:
  emit(R04, c, severity=High, guideline=G04)
```

### 6.6 R05 — Unlabeled input

```
if "EditText" in c.class and all empty(text, content_desc, hint):
  emit(R05, c, severity=High, guideline=G05)
```

### 6.7 R06 — Disabled important control

`clickable and not enabled` without nearby explanation TextView.

### 6.8 R07 — Zero-size element

`width <= 0 or height <= 0 or invalid rect`

### 6.9 R08 — Layout overlap

Pairwise overlap ratio > 0.5 over smaller element area.

### 6.10 R09 — Low contrast (Stretch)

Screenshot crop + WCAG contrast ratio; requires `src/contrast.py`.

### 6.11 R10 — Text overflow

Heuristic: TextView height < estimated text height (MVP: height < 24px with non-empty text).

### 6.12 R11 — Color-only information (stub)

`check_color_only_info()` returns `[]` until before/after snapshots or screenshot colour diff is available.

### 6.13 R12 — Missing captions

`media_type in (video, audio)` and no nearby caption/subtitle token in sibling text.

### 6.14 R13 — Audio without transcript

`media_type == audio` and no transcript/caption affordance nearby.

### 6.15 R14 — Audio-only notification

Notification-style text with no visible icon/banner nearby.

### 6.16 R15 — Bad focus order

Focusable components: `focus_order` traversal disagrees with top-to-bottom `bounds` order.

### 6.17 R16 — Decorative in focus tree

Likely decorative `ImageView` (no text/desc) remains `focusable`.

### 6.18 R17 — Insufficient spacing

Adjacent clickables with edge gap `< 8dp`; emit `related_component` for the paired control.

### 6.19 R18 — Multi-gesture only

Text/content describes pinch/zoom/multi-touch-only interaction without single-finger alternative.

### 6.20 R19 — Destructive without confirmation

Clickable destructive token (delete/remove) and no `is_dialog` / confirm text on screen.

### 6.21 R20 — Hint-only label

`EditText` with `hint` but no `text`, `content_desc`, `label_for`, or nearby label TextView.

---

## 7. Agentic layer design

### 7.1 LLM configuration

| Setting | Default | Env var |
|---------|---------|---------|
| Model | `gpt-4o-mini` | `OPENAI_MODEL` |
| Timeout | 30s | `OPENAI_TIMEOUT` |
| Temperature | 0.2 | — |
| Retries | 2 | — |

### 7.2 Prompt template (per violation)

```
System: Explain accessibility violations only. Never invent new violations.

User:
  rule_id: {rule_id}
  issue: {issue}
  component: {class, bounds, resource_id}
  guideline: {guideline}
  recommendation: {recommendation}

Return JSON: {agent_explanation, agent_why_it_matters, agent_developer_fix}
```

### 7.3 Fallback on failure

Use `issue` + `recommendation` as template fields; log API error.

---

## 8. Report generator design

### 8.1 HTML sections

1. Cover — screen ID, date, score, total issues
2. Summary — severity counts
3. Annotated screenshot — PIL boxes colour-coded by severity
4. Violation details — grouped Critical → High → Medium → Low
5. Footer — schema version, WCAG 2.2 AA

### 8.2 Accessibility score formula

```
score = 100
score -= critical * 20 + high * 10 + medium * 5 + low * 2
score = clamp(score, 0, 100)
```

Maps to Axion score gauge on Dashboard (SRS FR-UI.21).

### 8.3 PDF generation

Primary: WeasyPrint from HTML. Fallback: pdfkit + wkhtmltopdf.

---

## 9. Frontend design (Axion)

**Owner:** Ayesha | **SRS:** FR-UI.*, Appendix F

### 9.1 Technology stack

| Layer | Choice |
|-------|--------|
| Framework | React 18 + Vite |
| Styling | Tailwind CSS |
| Routing | React Router v6 |
| HTTP | axios + JWT interceptor |
| State | React Context (MVP) |

### 9.2 Directory structure

```
frontend/src/
├── api/
│   ├── authClient.ts
│   ├── auditClient.ts
│   └── recordsClient.ts
├── components/
│   ├── layout/          # Sidebar, Header, FloatingActionBar
│   ├── auth/            # SignUp, Login, ForgotPassword, OTP, Reset
│   ├── upload/          # UploadZone, ValidationPanel, FilesMatchedModal
│   ├── dashboard/       # ScoreCards, PriorityChart, ViolationsTable
│   ├── report/          # IssueCard, DownloadModal
│   └── records/         # RecordsTable, EmptyState
├── pages/
│   ├── UploadPage.tsx
│   ├── DashboardPage.tsx
│   ├── ReportPage.tsx
│   └── RecordsPage.tsx
└── theme/tokens.ts      # #0b1929, #1bc99a
```

### 9.3 Key UI flows

| Flow | Route | Components |
|------|-------|--------------|
| Auth | `/login`, `/signup` | Auth forms per Figma |
| Upload | `/upload` | Sequential upload → Files Matched → Start Audit |
| Audit progress | modal overlay | Audit Complete step checklist |
| Dashboard | `/dashboard/:auditId` | Score cards, table, Issue Detail drawer |
| Report | `/report/:auditId` | Guideline breakdown, Generate Report |
| Records | `/records` | User audit history, search, re-download |

### 9.4 TypeScript interfaces

Mirror JSON schema types: `Component`, `Violation`, `ReportSummary`, `AuditRecord`.

### 9.6 Figma reference screenshots

Visual source of truth: SRS Appendix F. Screenshots live in `docs/assets/figma/` (same paths as SRS).

| Screen group | Asset file | React route(s) |
|--------------|------------|----------------|
| Sign Up + Log In | `figma-01-signup-login.png` | `/signup`, `/login` |
| Forgot + OTP | `figma-02-forgot-verify-otp.png` | `/forgot-password`, `/verify-otp` |
| Reset + Success | `figma-03-reset-password-success.png` | `/reset-password`, `/reset-success` |
| Upload states | `figma-04-upload-progress-states.png` | `/upload` |
| Files Matched | `figma-08-upload-files-matched.png` | modal on `/upload` |
| Audit Complete + Dashboard | `figma-05-audit-complete-dashboard.png` | modal; `/dashboard/:id` |
| Detail drawer + Report | `figma-06-dashboard-detail-report.png` | drawer; `/report/:id` |
| Generate modal + PDF | `figma-07-generate-report-modal-pdf.png` | modal; PDF template |
| Records | *(no screenshot — match Dashboard styling)* | `/records` |

![Sign Up and Log In — implementation reference](../docs/assets/figma/figma-01-signup-login.png)

![Upload and Dashboard — implementation reference](../docs/assets/figma/figma-05-audit-complete-dashboard.png)

---

## 10. Authentication and Records design

**SRS:** FR-AUTH.*, FR-REC.*, FR-UI.40–45

### 10.1 Auth model (prototype)

| Component | Design |
|-----------|--------|
| Password storage | bcrypt hash in `data/users.json` or SQLite |
| Session | JWT (HS256), 24h expiry |
| OTP | 6-digit code, 5 min TTL, stored in memory or Redis (prototype: JSON file) |
| Google OAuth | Verify ID token server-side; create/link user |

### 10.2 Records lifecycle

1. User completes audit pipeline
2. `RecordsService.save(user_id, audit_artifacts)` copies HTML/PDF + metadata
3. Append summary to `outputs/records/{user_id}/index.json`
4. Records page reads index; detail view loads `metadata.json` + report

### 10.3 Access control

- All `/records/*` queries filter by JWT `user_id`
- No cross-user record access
- File paths validated to stay under `outputs/records/{user_id}/`

---

## 11. Deployment design

### 11.1 docker-compose.yml (target)

```yaml
services:
  frontend:
    build: ./frontend
    ports: ["5173:5173"]
    environment:
      VITE_API_BASE: http://backend:8000
    depends_on: [backend]

  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    volumes: [".:/app"]
    working_dir: /app/backend

  auditor:
    build: .
    command: python /app/test_run.py
    environment:
      DATASET_ROOT: /app/data/data-masc
```

### 11.2 Environment variables

| Variable | Service | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | backend | LLM |
| `JWT_SECRET` | backend | Token signing |
| `CORS_ORIGINS` | backend | `http://localhost:5173` |
| `DATASET_ROOT` | auditor | Batch parse path |

### 11.3 Startup

```bash
docker-compose up --build
# Frontend: http://localhost:5173
# API docs:  http://localhost:8000/docs
# Health:    http://localhost:8000/health
```

---

## 12. Security design

| Threat | Mitigation |
|--------|------------|
| API key exposure | LLM calls server-side only |
| JWT theft | httpOnly cookie option (Stretch); HTTPS in prod |
| XXE | Safe XML parsing; no external entities |
| Upload abuse | 20 MB limit, MIME validation |
| Path traversal | Sanitize paths in Records service |
| Cross-user access | JWT `user_id` scoping on all records |
| OTP brute force | Rate limit + expiry countdown (Figma: 04:50) |

---

## 13. Testing design

| Layer | Tool | Scope |
|-------|------|-------|
| Unit | pytest | Parser (incl. MASC wrappers), R01–R20 |
| Schema | `validate_output.py` | `components.json` / `violations.json` artefacts |
| API | pytest + TestClient | Audit violations + report (`test_audit.py`) |
| Integration | `noor_week3_validate.py`, `masc_parse_signoff.py` | Full MASC re-parse + R01–R20 scan |
| E2E | Manual / Playwright | Axion upload → Records (planned) |
| Evaluation | MASC train/val/test splits | 7,068 screens, sign-off JSON |

### 13.1 Golden files

```
tests/fixtures/rules/
├── r01_missing_label_fail.xml / r01_missing_label_pass.xml
├── r02_image_button_fail.xml / …
├── … (R03–R10 fail/pass fixtures)
└── clean_no_violations.xml

tests/test_parser.py     # extended fields + MASC wrapper nesting
tests/test_rules.py        # R01–R10 fixtures + R11/R12 stubs + R13–R20 unit cases
tests/test_audit.py        # API parse→rules parity on R01
tests/test_agent.py        # score formula scaffold
```

### 13.2 Sign-off tests (from SRS §10)

- TC-01: missing bounds → no crash
- R01–R30 on controlled fail/pass fixtures
- R13–R20 on controlled component dicts + MASC full-dataset scan (Week 3+)
- `masc_parse_signoff_report.json` → PASS (7,068 screens, 0 extended-field misses)
- API `POST /audit` → `GET .../violations` matches CLI on R01 fixture
- API `GET .../report` returns score + agent fields (`enrichment_mode`: `template` or `llm`)
- Explainer unit tests mock LLM; anti-hallucination guard covered in `tests/test_explainer.py`

---

## 14. SRS traceability

| SRS requirement | SDS section | Implementation |
|-----------------|-------------|----------------|
| FR-PS.1–9 | §3.1, §4 | `src/parser.py` |
| FR-RU.1–20 | §3.2, §6 | `src/rules.py` |
| FR-AG.1–8 | §7 | `src/agent.py`, `src/explainer.py` (**Done**; API-wired) |
| FR-RP.1–7 | §8 | `src/report.py` |
| FR-UI.* | §9, Appendix D | `frontend/` |
| FR-AUTH.* | §10.1, §5.1 | `backend/routers/auth.py` (planned) |
| FR-REC.* | §10.2, §5.3 | `backend/services/records.py` (planned) |
| Audit API (violations + report) | §5.2 | `backend/routers/audit.py` |
| FR-DK.* | §11 | `docker-compose.yml` |
| NFR-1–20 | §2, §7, §11, §12 | Cross-cutting |
| §8 JSON schemas | §4 | `auditor_schema.json` |
| §9 REST API | §5, Appendix A | `backend/routers/` |

---

## Appendix A: OpenAPI specification

```yaml
openapi: 3.0.3
info:
  title: Agentic Accessibility Auditor API
  version: 2.0.0
servers:
  - url: http://localhost:8000/api/v1

paths:
  /auth/login:
    post:
      summary: Login and receive JWT
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email: { type: string, format: email }
                password: { type: string, minLength: 8 }
      responses:
        "200":
          description: JWT token

  /audit:
    post:
      summary: Upload screenshot + XML and start audit
      security: [{ bearerAuth: [] }]
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              required: [screenshot, xml]
              properties:
                screenshot: { type: string, format: binary }
                xml: { type: string, format: binary }
      responses:
        "201": { description: Audit created }

  /audit/{audit_id}/status:
    get:
      summary: Get pipeline status
      security: [{ bearerAuth: [] }]
      parameters:
        - name: audit_id
          in: path
          required: true
          schema: { type: string }
      responses:
        "200": { description: Status object }

  /records:
    get:
      summary: List user's saved audits
      security: [{ bearerAuth: [] }]
      responses:
        "200": { description: Records list }

  /records/{record_id}:
    get:
      summary: Get record detail
      security: [{ bearerAuth: [] }]
      parameters:
        - name: record_id
          in: path
          required: true
          schema: { type: string }
      responses:
        "200": { description: Record detail }

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
```

---

## Appendix B: File and directory map

| Path | Role |
|------|------|
| `src/parser.py` | Hybrid XML parser (**Done**) |
| `src/schema_documents.py` | JSON envelope builders |
| `src/rules.py` | Rule engine R01–R30 (**Done**; R09/R28 limited without colors/text-size) |
| `src/agent.py` | Score + `build_audit_report` (**Done**; API-wired) |
| `src/explainer.py` | Live LLM recommendations (**Done**) |
| `src/llm_providers.py` | Multi-provider LLM client |
| `src/guidelines.py` | G01–G30 + R→G mapping |
| `src/report.py` | HTML/PDF generator (planned) |
| `backend/main.py` | FastAPI entry |
| `backend/routers/audit.py` | Violations + report audit API (**Partial** — no auth/records/download) |
| `backend/routers/` | Auth, records (planned) |
| `scripts/noor_week3_validate.py` | Full validation pipeline |
| `scripts/masc_parse_signoff.py` | MASC parse sign-off |
| `scripts/run_explainer_sample.py` | Stage 3 LLM sample runner |
| `tests/test_parser.py` | Parser unit tests |
| `tests/test_rules.py` | Rules R01–R30 unit tests |
| `tests/test_audit.py` | Audit API tests (violations + report) |
| `tests/test_explainer.py` | Explainer anti-hallucination tests |
| `frontend/src/` | Axion React app (**Partial** — mock data) |
| `docs/schemas/auditor_schema.json` | Normative JSON Schema |
| `docs/json_schemas.md` | Schema documentation |
| `outputs/reports/` | Agent-enriched `*_report.json` |
| `outputs/records/` | Per-user saved audits (planned) |
| `data/data-masc/` | Primary dataset |
| `data/data-rico-holdout/` | Unseen evaluation |

---

## Appendix C: Sequence diagrams

### C.1 Authenticated audit with Records save

```mermaid
sequenceDiagram
    participant U as User
    participant A as Axion UI
    participant API as FastAPI
    participant P as Pipeline
    participant R as RecordsStore

    U->>A: Login
    A->>API: POST /auth/login
    API-->>A: JWT

    U->>A: Upload screenshot + XML
    A->>API: POST /audit (JWT)
    API->>P: run_audit()
    P-->>API: complete + artefacts
    API->>R: save(user_id, record)
    API-->>A: audit_id, record_id
    A-->>U: Dashboard + saved to Records
```

### C.2 View past audit from Records

```mermaid
sequenceDiagram
    participant U as User
    participant A as Axion UI
    participant API as FastAPI

    U->>A: Open Reports page
    A->>API: GET /records (JWT)
    API-->>A: records list
    U->>A: Open record
    A->>API: GET /records/{id}
    API-->>A: metadata + report paths
    A-->>U: Report view / download
```

---

## Appendix D: UI component map (Figma)

Maps Figma frames to React components (SRS Appendix F). Screenshot assets in `docs/assets/figma/`.

| Figma frame | Screenshot | Route / trigger | React component(s) |
|-------------|------------|-----------------|-------------------|
| Sign Up | `figma-01-signup-login.png` | `/signup` | `SignUpPage` |
| Log In | `figma-01-signup-login.png` | `/login` | `LoginPage` |
| Forgot Password | `figma-02-forgot-verify-otp.png` | `/forgot-password` | `ForgotPasswordPage` |
| Verify Code | `figma-02-forgot-verify-otp.png` | `/verify-otp` | `OtpVerificationPage` |
| Set Password | `figma-03-reset-password-success.png` | `/reset-password` | `ResetPasswordPage` |
| Password Reset Success | `figma-03-reset-password-success.png` | `/reset-success` | `ResetSuccessPage` |
| Upload (progress) | `figma-04-upload-progress-states.png` | `/upload` | `UploadPage`, `UploadZone` |
| Files Matched Modal | `figma-08-upload-files-matched.png` | after validation | `FilesMatchedModal` |
| Audit Complete Modal | `figma-05-audit-complete-dashboard.png` | after pipeline | `AuditCompleteModal` |
| Dashboard | `figma-05-audit-complete-dashboard.png` | `/dashboard/:id` | `DashboardPage`, `ViolationsTable`, `ScoreGauge` |
| Issue Detail Drawer | `figma-06-dashboard-detail-report.png` | View action | `IssueDetailDrawer` |
| Audit Report | `figma-06-dashboard-detail-report.png` | `/report/:id` | `ReportPage` |
| Generate Report Modal | `figma-07-generate-report-modal-pdf.png` | footer CTA | `DownloadModal` |
| PDF layout | `figma-07-generate-report-modal-pdf.png` | export | `report.py` HTML template |
| Records / Reports | — | `/records` | `RecordsPage`, `RecordsTable` |

Design tokens: background `#0b1929`, primary `#1bc99a`, sidebar nav **Upload | Dashboard | Reports**.

---

**— End of Software Design Specification v2.0 —**
