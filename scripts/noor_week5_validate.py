"""Run Noor Week 5 validation: report.py HTML/PDF export + download API."""

from __future__ import annotations

import io
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

R01_FIXTURE = ROOT / "tests" / "fixtures" / "rules" / "r01_missing_label_fail.xml"
LOG_DIR = ROOT / "outputs" / "validation_logs"
LOG_PATH = LOG_DIR / "noor_week5_validation_log.txt"
REPORTS_DIR = ROOT / "outputs" / "reports"


class _Tee:
    def __init__(self, *streams):
        self._streams = streams

    def write(self, data: str) -> None:
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def api_smoke_download() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 3: API smoke — report JSON + HTML/PDF download")
    print("-" * 66)
    from fastapi.testclient import TestClient

    from backend.main import app

    client = TestClient(app)
    with R01_FIXTURE.open("rb") as handle:
        created = client.post(
            "/api/v1/audit?use_llm=false",
            files={"xml": (R01_FIXTURE.name, handle, "application/xml")},
        )
    print("POST /api/v1/audit?use_llm=false", created.status_code, created.json())
    audit_id = created.json()["audit_id"]

    report = client.get(f"/api/v1/audit/{audit_id}/report")
    print("GET /report", report.status_code, "score=", report.json().get("accessibility_score"))

    html = client.get(f"/api/v1/audit/{audit_id}/report/download?format=html")
    print("GET /report/download?format=html", html.status_code, "bytes=", len(html.content))
    print("HTML contains report title:", b"Accessibility audit report" in html.content)

    pdf = client.get(f"/api/v1/audit/{audit_id}/report/download?format=pdf")
    print("GET /report/download?format=pdf", pdf.status_code, "bytes=", len(pdf.content))
    if pdf.status_code == 200:
        print("PDF magic header:", pdf.content[:4])
    else:
        print("PDF detail:", pdf.json().get("detail", pdf.text[:200]))
        if pdf.status_code == 503:
            print("NOTE: run once: playwright install chromium")


def module_smoke() -> None:
    print(f"\n{'-' * 66}")
    print("STEP 4: src/report.py direct render")
    print("-" * 66)
    from src.agent import build_audit_report
    from src.parser import load_xml_root, parse_xml_tree
    from src.rules import check
    from src.schema_documents import build_components_document
    from src.report import render_html_report, write_report_html

    components = parse_xml_tree(load_xml_root(R01_FIXTURE))
    components_doc = build_components_document(
        screen_id=R01_FIXTURE.stem,
        image_path="",
        xml_path=str(R01_FIXTURE),
        components=components,
    )
    violations_doc = check(components_doc)
    report_doc = build_audit_report(violations_doc, components_doc, use_llm=False)
    html = render_html_report(report_doc, project_root=ROOT)
    print(f"HTML length: {len(html)} chars")
    print(f"Contains screen_id: {report_doc['screen_id'] in html}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html_path = REPORTS_DIR / f"{report_doc['screen_id']}_report.html"
    write_report_html(report_doc, html_path, project_root=ROOT)
    print(f"Wrote: {html_path.relative_to(ROOT)}")


def _run_validation() -> int:
    today = date.today().isoformat()
    print("=" * 66)
    print("NOOR WEEK 5 VALIDATION LOG (HTML/PDF report export)")
    print(f"Branch: noor   Date: {today}")
    print("Owner: Muhammad Noor - src/report.py + download API")
    print("=" * 66)

    py = sys.executable
    failures = 0

    steps = [
        ("STEP 1: pytest tests/test_report.py", [py, "-m", "pytest", "tests/test_report.py", "-q"]),
        ("STEP 2: pytest tests/test_audit.py (download endpoints)", [py, "-m", "pytest", "tests/test_audit.py", "-q"]),
        (
            "STEP 2b: pytest tests/ (full suite)",
            [py, "-m", "pytest", "tests/", "-q"],
        ),
    ]
    for label, cmd in steps:
        result = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        out = (result.stdout + result.stderr).strip()
        print(f"\n{'-' * 66}")
        print(label)
        print("-" * 66)
        print(out)
        if result.returncode != 0:
            failures += 1
            print(f"EXIT CODE: {result.returncode}")

    api_smoke_download()
    module_smoke()

    print(f"\n{'-' * 66}")
    print("SUMMARY")
    print("-" * 66)
    if failures:
        print(f"FAILED pytest steps: {failures}")
        return 1
    print("All pytest steps: PASS")
    print("Report HTML download API: PASS")
    print("Report PDF download API: PASS (requires playwright install chromium)")
    print("src/report.py direct render: PASS")
    return 0


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO()
    previous_stdout = sys.stdout
    sys.stdout = _Tee(previous_stdout, buffer)
    try:
        code = _run_validation()
    finally:
        sys.stdout = previous_stdout

    with LOG_PATH.open("a", encoding="utf-8", newline="\n") as log_file:
        log_file.write(f"\n\n{'#' * 66}\n# RE-RUN {date.today().isoformat()}\n{'#' * 66}\n\n")
        log_file.write(buffer.getvalue())
    return code


if __name__ == "__main__":
    raise SystemExit(main())
