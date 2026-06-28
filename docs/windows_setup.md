# Windows Setup Guide

Onboarding guide for teammates moving from Linux (or setting up fresh on Windows) for the **Agentic Accessibility Auditor** project.

---

## Required software

| Software | Purpose | Download |
|----------|---------|----------|
| **Git** | Clone and pull the repository | [git-scm.com/download/win](https://git-scm.com/download/win) |
| **Python 3.11+** | Parser, Streamlit app, scripts, tests | [python.org/downloads](https://www.python.org/downloads/) |
| **Code editor** | Development (Cursor or VS Code) | Your preferred editor |
| **Web browser** | Streamlit UI at `http://localhost:8501` | Chrome or Edge |

During Python installation, enable **“Add Python to PATH”**.

---

## Clone the repository

```powershell
cd D:\internship
git clone <repository-url> agentic-accessibility-auditor
cd agentic-accessibility-auditor
```

Replace `<repository-url>` with your team’s actual Git remote.

---

## Python virtual environment

Open **PowerShell** or **Windows Terminal** in the project root:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
playwright install
```

### If activation is blocked

PowerShell may block script execution. Run once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate again:

```powershell
.\venv\Scripts\Activate.ps1
```

### Alternative: Command Prompt

```cmd
venv\Scripts\activate.bat
```

---

## Environment variables

### Gemini API key (LLM / agent layer)

**PowerShell (current session):**

```powershell
$env:GEMINI_API_KEY = "your_key_here"
```

**Command Prompt (current session):**

```cmd
set GEMINI_API_KEY=your_key_here
```

For a persistent local setup, create a `.env` file in the project root (do **not** commit it):

```
GEMINI_API_KEY=your_key_here
```

---

## Run the Streamlit app

```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```

Open: [http://localhost:8501](http://localhost:8501)

Upload an XML file and click **Parse XML to Components**. A screenshot is optional.

---

## Verify the parser

```powershell
python src/parser.py data/data-masc/xml/chat/49879.xml
python scripts/batch_parse_xml.py --file data/data-masc/xml/chat/49879.xml
```

Expected output includes something like:

```
Parsed 22 component(s) from data\data-masc\xml\chat\49879.xml
```

Full JSON output:

```powershell
python src/parser.py data/data-masc/xml/chat/49879.xml --json
```

Smoke test:

```powershell
python test_run.py
```

---

## Dataset (not included in Git)

Large datasets must be downloaded or copied manually.

| Dataset | Path | Notes |
|---------|------|-------|
| **MASC** | `data/data-masc/` | [Google Drive — MASC dataset](https://drive.google.com/file/d/1kx8qRbOtdQbbewZgfBTeCIj7lNvabFTF/view?usp=sharing) |
| **final_rico** | `data/final_rico/final_rico/` | Raw Rico source (2,000 screens). Not for direct eval — 302 screens overlap MASC. |
| **Rico holdout** | `data/data-rico-holdout/` | Filtered holdout (1,698 screens, zero MASC overlap). See [`rico_holdout_dataset.md`](rico_holdout_dataset.md). |

Allow **7–15 GB** free disk space for MASC. Rico holdout adds ~2–3 GB.

Regenerate train/val/test splits after MASC is in place:

```powershell
python scripts/split_masc_dataset.py
```

Build Rico holdout from `final_rico` (after both MASC and `final_rico` are on disk):

```powershell
python scripts/compare_datasets.py
python scripts/build_rico_holdout.py
python scripts/build_rico_holdout_sheet.py
```

---

## Optional software

| Software | Who needs it | Purpose |
|----------|--------------|---------|
| **Docker Desktop** | Intern 1 (Docker) | Containerized run via `docker-compose` |
| **Android Platform Tools (ADB)** | Data collection | Capture screenshots and UIAutomator XML from devices |
| **Node.js LTS** | Intern 2 | React dashboard (when that frontend is added) |
| **Figma** | Intern 2 | UI design |

### Docker (alternative to local venv)

1. Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/)
2. Enable WSL 2 if prompted during setup
3. From the project root:

```powershell
docker-compose up --build
```

App: [http://localhost:8501](http://localhost:8501)

`./data` and `./outputs` are mounted into the container so files persist on your machine.

---

## Linux vs Windows quick reference

| Task | Linux | Windows (PowerShell) |
|------|-------|-------------------------|
| Activate venv | `source venv/bin/activate` | `.\venv\Scripts\Activate.ps1` |
| Set env var | `export GEMINI_API_KEY=...` | `$env:GEMINI_API_KEY="..."` |
| Chain commands | `cmd1 && cmd2` | `cmd1; cmd2` |
| Path style | `/home/user/project` | `D:\internship\agentic-accessibility-auditor` |

---

## Role-specific checklist

### Intern 1 — Parser, rules, Docker

- [ ] Python 3.11+, venv, `pip install -r requirements.txt`
- [ ] MASC dataset in `data/data-masc/`
- [ ] Parser smoke test passes (`49879.xml`)
- [ ] Docker Desktop (if using `docker-compose`)

### Intern 2 — Schemas, React UI

- [ ] Python venv (for schema/docs alignment)
- [ ] Node.js LTS + npm (when React app is available)
- [ ] Review `docs/json_schemas.md` and `docs/examples/`

### Intern 3 (Lead) — LLM, reports

- [ ] Python venv + `playwright install`
- [ ] `GEMINI_API_KEY` configured
- [ ] `streamlit run app.py` works

---

## “Am I set up?” sanity check

Run these from the project root with venv activated:

```powershell
python --version
pip --version
git --version
streamlit --version
python src/parser.py data/data-masc/xml/chat/49879.xml
```

All commands should succeed without import errors.

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `python` not found | Reinstall Python with **Add to PATH**, or use `py -3.11` |
| `Activate.ps1` blocked | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
| Parser returns 0 components | Confirm XML has `<node>` elements with `class` and `bounds` (or MASC `<wrapper>` bounds) |
| `lxml` install fails | Upgrade pip: `pip install --upgrade pip setuptools wheel` |
| Streamlit shows no output after parse | Upload XML, click **Parse XML to Components**; results persist in session state |
| Docker build slow/fails | Ensure Docker Desktop is running; WSL 2 backend enabled |
| Missing MASC files | Download from Google Drive; paths must match `data/data-masc/xml/{category}/{id}.xml` |

---

## What not to commit

- `venv/`
- `.env` and API keys
- Full `data/data-masc/`, `data/final_rico/`, and `data/data-rico-holdout/screenshots|xml|json/` (too large for Git)
- Generated outputs under `data/parsed/`, `outputs/` (unless your team agrees otherwise)

---

## Related docs

| Doc | Description |
|-----|-------------|
| [`README.md`](../README.md) | Project overview and folder layout |
| [`json_schemas.md`](json_schemas.md) | Pipeline JSON schemas |
| [`rico_holdout_dataset.md`](rico_holdout_dataset.md) | Rico holdout filtering and regeneration |
| [`qa_test_plan.md`](qa_test_plan.md) | QA test cases |
