# Agentic Accessibility Auditor (Intern 1)

Automated accessibility auditing for Android mobile UIs.

## Project structure

```
agentic-accessibility-auditor/
├── app.py                  # Streamlit demo
├── test_run.py             # Batch parser + rule checker
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── src/
│   ├── parser.py           # Hybrid Android UI XML → components.json
│   ├── rules.py            # Rule checker (R01–R30 planned; partial now)
│   └── schema_documents.py
├── scripts/
│   └── validate_output.py  # Validate JSON against auditor_schema.json
├── data/
│   ├── data-masc/          # Training/dev dataset (local only)
│   ├── data-rico-holdout/  # Unseen final eval (local only)
│   ├── xml/                # Generic uploaded XML (any app)
│   ├── screenshots/        # Optional screenshots for uploads
│   └── parsed/             # Generic upload output
├── outputs/
│   ├── violations/         # Stage 2 output: {screen}_violations.json
│   └── reports/            # Stage 4 HTML/PDF (planned)
└── docs/
    ├── json_schemas.md
    └── schemas/auditor_schema.json
```

## Quick start

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Parse MASC (default dataset)
python test_run.py

# Parse Rico holdout (smoke test — use --max-files 4)
python test_run.py --dataset rico --max-files 4

# Parse generic uploaded XML (any Android UI dump in data/xml/)
python test_run.py --dataset upload

# Parse one arbitrary file
python test_run.py path\to\screen.xml

# Validate outputs against JSON Schema
python scripts/validate_output.py
```

## Team

- **Intern 1:** Data collection, XML parsing, rules, Docker
- **Intern 2:** JSON schemas, Figma, React dashboard
- **Intern 3:** LLM agent, report generation
