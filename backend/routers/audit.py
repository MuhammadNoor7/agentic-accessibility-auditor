"""Audit pipeline API — parse → rules → agent report (SRS §9)."""

from __future__ import annotations

import json
import re
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models.audit import AuditCreateResponse, AuditStatusResponse
from src.agent import build_audit_report
from src.parser import build_screen_document
from src.report import render_report_bytes
from src.rules import check as check_rules

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

VIOLATIONS_OUTPUT_ROOT = ROOT / "outputs" / "violations"
REPORTS_OUTPUT_ROOT = ROOT / "outputs" / "reports"
ALLOWED_SCREENSHOT_SUFFIXES = {".png", ".jpg", ".jpeg"}

# In-memory job store for MVP stub (Week 5+: persist to outputs/records/)
_AUDIT_JOBS: dict[str, dict] = {}


def _file_stem(filename: str) -> str:
    return Path(filename).stem.lower()


def _extract_number(filename: str) -> str | None:
    matches = re.findall(r"\d+", filename)
    return matches[-1] if matches else None


def _files_match_pair(screenshot_filename: str, xml_filename: str) -> bool:
    """Mirror frontend filesMatch() in Upload.jsx."""
    stem1 = _file_stem(screenshot_filename)
    stem2 = _file_stem(xml_filename)
    if stem1 == stem2:
        return True

    n1 = _extract_number(screenshot_filename)
    n2 = _extract_number(xml_filename)
    if n1 is None or n2 is None or n1 != n2:
        return False

    prefix1 = re.sub(r"\d+$", "", stem1)
    prefix2 = re.sub(r"\d+$", "", stem2)
    return prefix1 == prefix2


def _set_status(audit_id: str, status: str, message: str | None = None) -> None:
    job = _AUDIT_JOBS[audit_id]
    job["status"] = status
    if message is not None:
        job["message"] = message


def _write_violations(components_doc: dict, violations_doc: dict) -> None:
    """Persist violations.json under outputs/violations/ (same as test_run/app)."""
    VIOLATIONS_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output_file = VIOLATIONS_OUTPUT_ROOT / f"{components_doc['screen_id']}_violations.json"
    output_file.write_text(json.dumps(violations_doc, indent=2), encoding="utf-8")


def _write_report(report_doc: dict) -> None:
    """Persist report.json under outputs/reports/."""
    REPORTS_OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_OUTPUT_ROOT / f"{report_doc['screen_id']}_report.json"
    output_file.write_text(json.dumps(report_doc, indent=2), encoding="utf-8")


def _run_pipeline(audit_id: str, xml_path: Path, *, use_llm: bool | None) -> None:
    """Synchronous pipeline: parsing → checking → explaining → complete."""
    try:
        _set_status(audit_id, "parsing")
        components_doc = build_screen_document(
            xml_path,
            xml_root_dir=xml_path.parent,
            dataset_root=None,
        )
        job = _AUDIT_JOBS[audit_id]
        job["components"] = components_doc

        _set_status(audit_id, "checking")
        violations_doc = check_rules(components_doc)
        job["violations"] = violations_doc
        _write_violations(components_doc, violations_doc)

        _set_status(audit_id, "explaining")
        report_doc = build_audit_report(violations_doc, components_doc, use_llm=use_llm)
        job["report"] = report_doc
        _write_report(report_doc)

        _set_status(audit_id, "complete", "Pipeline finished")
    except Exception as exc:
        _set_status(audit_id, "error", f"{type(exc).__name__}: {exc}")


@router.post("", response_model=AuditCreateResponse, status_code=202)
async def create_audit(
    screenshot: UploadFile = File(...),
    xml: UploadFile = File(...),
    use_llm: bool | None = Query(
        default=None,
        description="Use live LLM for explanations (default: auto-detect API key; "
        "falls back to templates when no key is set).",
    ),
) -> AuditCreateResponse:
    """Upload a screenshot + UIAutomator XML pair and run parse → rules → report (R01–R30)."""
    if not screenshot.filename:
        raise HTTPException(status_code=400, detail="Screenshot file is required")
    if not xml.filename or not xml.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="Upload must include a .xml file")

    screenshot_suffix = Path(screenshot.filename).suffix.lower()
    if screenshot_suffix not in ALLOWED_SCREENSHOT_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Screenshot must be a PNG or JPG image",
        )

    if not _files_match_pair(screenshot.filename, xml.filename):
        raise HTTPException(
            status_code=400,
            detail="Screenshot and XML filenames do not match as a pair",
        )

    audit_id = str(uuid.uuid4())
    _AUDIT_JOBS[audit_id] = {
        "status": "pending",
        "message": None,
        "components": None,
        "violations": None,
        "report": None,
        "use_llm": use_llm,
        "screenshot_filename": screenshot.filename,
    }

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        xml_path = tmp_dir / Path(xml.filename).name
        screenshot_path = tmp_dir / Path(screenshot.filename).name
        xml_path.write_bytes(await xml.read())
        screenshot_path.write_bytes(await screenshot.read())
        _run_pipeline(audit_id, xml_path, use_llm=use_llm)

    job = _AUDIT_JOBS[audit_id]
    if job["status"] == "error":
        raise HTTPException(status_code=500, detail=job.get("message", "Pipeline failed"))

    return AuditCreateResponse(audit_id=audit_id, status=job["status"])


@router.get("/{audit_id}/status", response_model=AuditStatusResponse)
async def get_audit_status(audit_id: str) -> AuditStatusResponse:
    job = _AUDIT_JOBS.get(audit_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    return AuditStatusResponse(
        audit_id=audit_id,
        status=job["status"],
        message=job.get("message"),
    )


@router.get("/{audit_id}/violations")
async def get_audit_violations(audit_id: str) -> dict:
    job = _AUDIT_JOBS.get(audit_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    if job["violations"] is None:
        raise HTTPException(status_code=409, detail="Violations not ready")
    return job["violations"]


@router.get("/{audit_id}/report")
async def get_audit_report(audit_id: str) -> dict:
    """Return agent-enriched report.json for a completed audit."""
    return _load_report_doc(audit_id)


def _load_report_doc(audit_id: str) -> dict:
    job = _AUDIT_JOBS.get(audit_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Audit not found")
    if job["report"] is None:
        if job["violations"] is None or job["components"] is None:
            raise HTTPException(status_code=409, detail="Report not ready")
        report_doc = build_audit_report(
            job["violations"],
            job["components"],
            use_llm=job.get("use_llm"),
        )
        job["report"] = report_doc
        _write_report(report_doc)
    return job["report"]


@router.get("/{audit_id}/report/download")
def download_audit_report(
    audit_id: str,
    format: str = Query(..., pattern="^(html|pdf)$", description="Export format"),
) -> Response:
    """Download agent-enriched audit report as HTML or PDF."""
    report_doc = _load_report_doc(audit_id)
    try:
        content, media_type, filename = render_report_bytes(
            report_doc,
            format,  # type: ignore[arg-type]
            project_root=ROOT,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    artifact_path = REPORTS_OUTPUT_ROOT / filename
    artifact_path.write_bytes(content)

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
