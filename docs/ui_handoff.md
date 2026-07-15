# UI Handoff — How to Run & API Map

**For:** Supervisor / new contributor onboarding
**Author:** Ayesha Naveed

## Running the frontend locally

1. Backend (from repo root, with `.env` set up and venv active):
uvicorn backend.main:app --port 8000
2. Frontend (separate terminal):
cd frontend
npm install   # first time only
npm run dev
3. Open `http://localhost:5173` — you'll land on the Login page first.

## Page → API map

| Page | File | Talks to |
|---|---|---|
| Login | `frontend/src/pages/auth/Login.jsx` | `POST /auth/login` |
| Sign Up | `frontend/src/pages/auth/SignUp.jsx` | `POST /auth/register` |
| Upload | `frontend/src/pages/Upload.jsx` | `POST /api/v1/audit` (sends screenshot + xml) |
| Dashboard | `frontend/src/pages/Dashboard.jsx` | `GET /api/v1/audit/{id}/report` |
| Report | `frontend/src/pages/Report.jsx` | `GET /api/v1/audit/{id}/report`, `GET /api/v1/audit/{id}/report/download?format=html\|pdf`, `GET /records/{id}/report` (when reopening a past record) |
| Records | `frontend/src/pages/Records.jsx` | `GET /records` (per-user, requires login) |

## Helper files

- `frontend/src/api.js` — audit endpoints (create/status/report/download)
- `frontend/src/utils/api.js` — auth-related requests
- `frontend/src/utils/auth.js` — stores/reads the JWT token
- `frontend/src/state/auditFiles.js` — in-memory store so the uploaded screenshot/xml and current `audit_id` survive page navigation

## Local setup notes

- PDF export needs a one-time `playwright install chromium` per machine
- Groq is the only fully free-to-test LLM provider right now (see `docs/agent_prompt_experiments.md`) — set `LLM_PROVIDER=groq` and `GROQ_API_KEY` in `.env`
- JWT auth works locally without setting `JWT_SECRET` (falls back to a dev default) — should be set explicitly for any shared/demo deployment