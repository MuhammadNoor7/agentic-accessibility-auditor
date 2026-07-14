"""Per-user audit record persistence (SDS §10.2-10.3)."""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.auth import User, get_current_user

router = APIRouter(prefix="/records", tags=["records"])

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RECORDS_DB_PATH = DATA_DIR / "records.db.json"
REPORTS_OUTPUT_ROOT = ROOT / "outputs" / "reports"


@dataclass
class AuditRecord:
    record_id: str
    user_id: str
    screen_id: str
    created_at: str
    total_violations: int
    violations_by_severity: dict
    components_path: str
    violations_path: str
    accessibility_score: int | None = None
    screenshot_name: str | None = None
    xml_name: str | None = None


def load_records() -> dict[str, AuditRecord]:
    if not RECORDS_DB_PATH.exists():
        return {}
    raw = json.loads(RECORDS_DB_PATH.read_text(encoding="utf-8") or "{}")
    records: dict[str, AuditRecord] = {}
    for record_id, data in raw.items():
        # Older DB rows may omit optional Week-6 fields — fill defaults.
        records[record_id] = AuditRecord(
            record_id=data["record_id"],
            user_id=data["user_id"],
            screen_id=data["screen_id"],
            created_at=data["created_at"],
            total_violations=data["total_violations"],
            violations_by_severity=data.get("violations_by_severity") or {},
            components_path=data.get("components_path") or "",
            violations_path=data.get("violations_path") or "",
            accessibility_score=data.get("accessibility_score"),
            screenshot_name=data.get("screenshot_name"),
            xml_name=data.get("xml_name"),
        )
    return records


def save_records(records: dict[str, AuditRecord]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    raw = {record_id: asdict(record) for record_id, record in records.items()}
    RECORDS_DB_PATH.write_text(json.dumps(raw, indent=2), encoding="utf-8")


class RecordCreateRequest(BaseModel):
    screen_id: str
    total_violations: int
    violations_by_severity: dict
    components_path: str
    violations_path: str
    accessibility_score: int | None = None
    screenshot_name: str | None = None
    xml_name: str | None = None


@router.post("")
async def create_record(
    body: RecordCreateRequest,
    current_user: User = Depends(get_current_user),
) -> dict:
    records = load_records()
    record = AuditRecord(
        record_id=str(uuid.uuid4()),
        user_id=current_user.user_id,
        screen_id=body.screen_id,
        created_at=datetime.now(timezone.utc).isoformat(),
        total_violations=body.total_violations,
        violations_by_severity=body.violations_by_severity,
        components_path=body.components_path,
        violations_path=body.violations_path,
        accessibility_score=body.accessibility_score,
        screenshot_name=body.screenshot_name,
        xml_name=body.xml_name,
    )
    records[record.record_id] = record
    save_records(records)
    return asdict(record)


@router.get("")
async def list_records(current_user: User = Depends(get_current_user)) -> dict:
    own_records = [
        record for record in load_records().values() if record.user_id == current_user.user_id
    ]
    own_records.sort(key=lambda record: record.created_at, reverse=True)
    return {"records": [asdict(record) for record in own_records], "total": len(own_records)}


@router.get("/{record_id}")
async def get_record(record_id: str, current_user: User = Depends(get_current_user)) -> dict:
    record = load_records().get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this record")
    return asdict(record)


@router.get("/{record_id}/report")
async def get_record_report(record_id: str, current_user: User = Depends(get_current_user)) -> dict:
    """Re-open a past audit's full report, read straight from the persisted
    outputs/reports/{screen_id}_report.json — independent of the audit
    pipeline's in-memory job store, so it survives backend restarts."""
    record = load_records().get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this record")
    report_path = REPORTS_OUTPUT_ROOT / f"{record.screen_id}_report.json"
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report file not found on disk")
    return json.loads(report_path.read_text(encoding="utf-8"))


@router.delete("/{record_id}")
async def delete_record(record_id: str, current_user: User = Depends(get_current_user)) -> dict:
    records = load_records()
    record = records.get(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Record not found")
    if record.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="You do not have access to this record")
    del records[record_id]
    save_records(records)
    return {"message": "deleted"}
