"""Pydantic models for audit API (SRS §9, SDS §5)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

AuditStatus = Literal[
    "pending",
    "parsing",
    "checking",
    "complete",
    "error",
]


class AuditCreateResponse(BaseModel):
    audit_id: str
    status: AuditStatus = "pending"


class AuditStatusResponse(BaseModel):
    audit_id: str
    status: AuditStatus
    message: str | None = None


class AuditErrorResponse(BaseModel):
    detail: str
