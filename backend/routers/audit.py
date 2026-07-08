"""Audit pipeline API — parse → rules → violations (SRS §9, Week 3)."""

from __future__ import annotations

import json
import sys
import tempfile
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.models.audit import AuditCreateResponse, AuditStatusResponse
from src.parser import build_screen_document
from src.rules import check as check_rules

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])

VIOLATIONS_OUTPUT_ROOT = ROOT / "outputs" / "violations"

# In-memory job store for MVP stub (Week 5+: persist to outputs/records/)
_AUDIT_JOBS: dict[str, dict] = {}


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


def _run_pipeline(audit_id: str, xml_path: Path) -> None:
    """Synchronous pipeline: parsing → checking → complete."""
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

        _set_status(audit_id, "complete", "Pipeline finished")
    except Exception as exc:
        _set_status(audit_id, "error", f"{type(exc).__name__}: {exc}")


@router.post("", response_model=AuditCreateResponse, status_code=202)
async def create_audit(xml: UploadFile = File(...)) -> AuditCreateResponse:
    """Upload a UIAutomator XML file and run parse + rules (R01–R30)."""
    if not xml.filename or not xml.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="Upload must be a .xml file")

    audit_id = str(uuid.uuid4())
    _AUDIT_JOBS[audit_id] = {
        "status": "pending",
        "message": None,
        "components": None,
        "violations": None,
    }

    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / xml.filename
        xml_path.write_bytes(await xml.read())
        _run_pipeline(audit_id, xml_path)

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
