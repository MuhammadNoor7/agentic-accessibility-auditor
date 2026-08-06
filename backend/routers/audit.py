"""Audit pipeline API — parse → rules → agent report (SRS §9)."""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from lxml import etree
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models.audit import AuditCreateResponse, AuditStatusResponse
from src.agent import build_audit_report
from src.crop_violation_classifier import confirm_violations
from src.parser import build_screen_document
from src.report import render_report_bytes
from src.rules import check as check_rules
from src.yolo_ui_detector import detect_ui, detections_to_components

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

VIOLATIONS_OUTPUT_ROOT = ROOT / "outputs" / "violations"
REPORTS_OUTPUT_ROOT = ROOT / "outputs" / "reports"
RUNS_OUTPUT_ROOT = ROOT / "outputs" / "runs"
ALLOWED_SCREENSHOT_SUFFIXES = {".png", ".jpg", ".jpeg"}

# In-memory job store for MVP stub (Week 5+: persist to outputs/records/)
_AUDIT_JOBS: dict[str, dict] = {}


def _path_for_report(path: Path) -> str:
    """Store repo-relative paths so HTML/PDF export can resolve files later."""
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


async def _persist_upload_pair(
    audit_id: str,
    screenshot: UploadFile,
    xml: UploadFile | None,
) -> tuple[Path, Path | None]:
    """Save screenshot (+ XML, if provided) under outputs/runs/{audit_id}/input/
    (survives download). xml is None for a screenshot-only, YOLO-fallback upload."""
    run_dir = RUNS_OUTPUT_ROOT / audit_id / "input"
    run_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = run_dir / Path(screenshot.filename).name
    screenshot_path.write_bytes(await screenshot.read())

    xml_path: Path | None = None
    if xml is not None:
        xml_path = run_dir / Path(xml.filename).name
        xml_path.write_bytes(await xml.read())
    return screenshot_path, xml_path


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


def _build_components_doc_via_yolo(screenshot_path: Path) -> dict:
    """Build a components.json-shaped doc from pixels alone (FR-CV.4-7), used
    when no XML was uploaded, or it's missing/malformed/parses to zero
    components. Every component is tagged inferred: true."""
    detections = detect_ui(screenshot_path)
    with Image.open(screenshot_path) as im:
        width_px, height_px = im.size
    return {
        "schema_version": "1.0",
        "screen_id": screenshot_path.stem,
        "image_path": "",
        "xml_path": "",
        "device_info": {"dpi": 160, "width_px": width_px, "height_px": height_px},
        "components": detections_to_components(detections),
    }


def _run_pipeline(
    audit_id: str,
    xml_path: Path | None,
    screenshot_path: Path,
    *,
    use_llm: bool | None,
) -> None:
    """Synchronous pipeline: parsing → checking → explaining → complete.

    Falls back to the screenshot-only YOLO detector (FR-CV.4) when xml_path
    is None, the XML is missing/malformed, or parses to zero components.
    """
    try:
        _set_status(audit_id, "parsing")
        components_doc = None
        if xml_path is not None:
            try:
                candidate = build_screen_document(
                    xml_path,
                    xml_root_dir=xml_path.parent,
                    dataset_root=None,
                )
                if candidate["components"]:
                    components_doc = candidate
            except (OSError, etree.XMLSyntaxError):
                components_doc = None

        used_xml = components_doc is not None
        if not used_xml:
            components_doc = _build_components_doc_via_yolo(screenshot_path)

        # Point at durable upload copies so report HTML/PDF can embed them.
        # xml_path stays "" (already set by the YOLO builder) unless the XML
        # branch was actually the one used - a malformed/empty XML upload
        # still has a real xml_path parameter, but its content was discarded.
        components_doc["image_path"] = _path_for_report(screenshot_path)
        if used_xml:
            components_doc["xml_path"] = _path_for_report(xml_path)
        job = _AUDIT_JOBS[audit_id]
        job["components"] = components_doc
        job["screenshot_path"] = components_doc["image_path"]
        job["xml_path"] = components_doc["xml_path"]

        _set_status(audit_id, "checking")
        violations_doc = check_rules(components_doc)
        confirm_violations(violations_doc, screenshot_path)
        job["violations"] = violations_doc
        _write_violations(components_doc, violations_doc)

        _set_status(audit_id, "explaining")
        report_doc = build_audit_report(violations_doc, components_doc, use_llm=use_llm)
        report_doc["image_path"] = components_doc["image_path"]
        report_doc["xml_path"] = components_doc["xml_path"]
        job["report"] = report_doc
        _write_report(report_doc)

        _set_status(audit_id, "complete", "Pipeline finished")
    except Exception as exc:
        _set_status(audit_id, "error", f"{type(exc).__name__}: {exc}")


@router.post("", response_model=AuditCreateResponse, status_code=202)
async def create_audit(
    screenshot: UploadFile = File(...),
    xml: UploadFile | None = File(
        None,
        description="UIAutomator XML. Optional - if omitted, malformed, or empty, "
        "the audit falls back to the screenshot-only YOLO UI detector (FR-CV.4).",
    ),
    use_llm: bool | None = Query(
        default=None,
        description="Use live LLM for explanations (default: auto-detect API key; "
        "falls back to templates when no key is set).",
    ),
) -> AuditCreateResponse:
    """Upload a screenshot (+ optional UIAutomator XML) and run parse → rules → report (R01–R30)."""
    if not screenshot.filename:
        raise HTTPException(status_code=400, detail="Screenshot file is required")

    screenshot_suffix = Path(screenshot.filename).suffix.lower()
    if screenshot_suffix not in ALLOWED_SCREENSHOT_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail="Screenshot must be a PNG or JPG image",
        )

    if xml is not None and xml.filename:
        if not xml.filename.lower().endswith(".xml"):
            raise HTTPException(status_code=400, detail="Upload must include a .xml file")
        if not _files_match_pair(screenshot.filename, xml.filename):
            raise HTTPException(
                status_code=400,
                detail="Screenshot and XML filenames do not match as a pair",
            )
    else:
        xml = None

    audit_id = str(uuid.uuid4())
    _AUDIT_JOBS[audit_id] = {
        "status": "pending",
        "message": None,
        "components": None,
        "violations": None,
        "report": None,
        "use_llm": use_llm,
        "screenshot_filename": screenshot.filename,
        "xml_filename": xml.filename if xml is not None else None,
    }

    screenshot_path, xml_path = await _persist_upload_pair(audit_id, screenshot, xml)
    _run_pipeline(audit_id, xml_path, screenshot_path, use_llm=use_llm)

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
