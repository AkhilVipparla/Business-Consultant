"""Venture CRUD routes — thin handlers; business logic lives in
services/venture_service.py per anchor.md/ARCHITECTURE.md's Request Flow.

The SSE workflow-trigger endpoint (GET /ventures/{id}/validate) is NOT here
yet — it needs graph/workflow.py, which is blocked on the Executive Decision
Agent (see anchor.md/DECISIONS.md Open Questions).
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy.orm import Session

from db.session import get_db
from models.enums import FindingCategory, FindingSourceType, VentureStatus
from services import venture_service
from utils.responses import success

router = APIRouter(prefix="/ventures", tags=["ventures"])


class VentureCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    one_liner: str = Field(min_length=1)
    description: str = Field(min_length=1)
    target_market: str | None = None
    industry: str | None = None


class VentureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    one_liner: str
    description: str
    target_market: str | None
    industry: str | None
    status: VentureStatus
    venture_score: float | None
    iteration_count: int
    created_at: datetime
    updated_at: datetime


class FindingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    category: FindingCategory
    source_type: FindingSourceType
    source_url: str | None
    title: str | None
    content: str
    created_at: datetime


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    venture_id: str
    version: int
    venture_score: float
    summary: str
    sections: dict[str, str]
    recommendations: list[str]
    created_at: datetime
    # Not an ORM attribute — populated manually in get_venture_report() below,
    # grouped by category so the frontend can render citations per section.
    findings: dict[str, list[FindingResponse]] = Field(default_factory=dict)


@router.post("", status_code=201)
def create_venture(payload: VentureCreateRequest, db: Session = Depends(get_db)):
    venture = venture_service.create_venture(
        db,
        title=payload.title,
        one_liner=payload.one_liner,
        description=payload.description,
        target_market=payload.target_market,
        industry=payload.industry,
    )
    return success(VentureResponse.model_validate(venture).model_dump(mode="json"))


@router.get("")
def list_ventures(db: Session = Depends(get_db)):
    ventures = venture_service.list_ventures(db)
    return success([VentureResponse.model_validate(v).model_dump(mode="json") for v in ventures])


@router.get("/{venture_id}")
def get_venture(venture_id: str, db: Session = Depends(get_db)):
    venture = venture_service.get_venture(db, venture_id)
    if venture is None:
        raise HTTPException(status_code=404, detail="Venture not found")
    return success(VentureResponse.model_validate(venture).model_dump(mode="json"))


@router.get("/{venture_id}/report")
def get_venture_report(venture_id: str, db: Session = Depends(get_db)):
    venture = venture_service.get_venture(db, venture_id)
    if venture is None:
        raise HTTPException(status_code=404, detail="Venture not found")

    report = venture_service.get_latest_report(db, venture_id)
    if report is None:
        raise HTTPException(status_code=404, detail="No report has been generated for this venture yet")

    findings_by_category: dict[str, list[dict]] = {}
    for finding in venture_service.get_findings(db, venture_id):
        findings_by_category.setdefault(finding.category.value, []).append(
            FindingResponse.model_validate(finding).model_dump(mode="json")
        )

    payload = ReportResponse.model_validate(report).model_dump(mode="json")
    payload["findings"] = findings_by_category
    return success(payload)
