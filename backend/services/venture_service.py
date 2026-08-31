"""Venture business logic — DB read/write orchestration.

Per anchor.md/ARCHITECTURE.md's Request Flow, API route handlers stay thin
and call into this module; this module never imports from api/.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import Report, ResearchFinding, Venture


def create_venture(
    db: Session,
    *,
    title: str,
    one_liner: str,
    description: str,
    target_market: str | None,
    industry: str | None,
) -> Venture:
    venture = Venture(
        title=title,
        one_liner=one_liner,
        description=description,
        target_market=target_market,
        industry=industry,
    )
    db.add(venture)
    db.commit()
    db.refresh(venture)
    return venture


def list_ventures(db: Session) -> list[Venture]:
    stmt = select(Venture).order_by(Venture.created_at.desc())
    return list(db.scalars(stmt))


def get_venture(db: Session, venture_id: str) -> Venture | None:
    return db.get(Venture, venture_id)


def get_latest_report(db: Session, venture_id: str) -> Report | None:
    stmt = (
        select(Report)
        .where(Report.venture_id == venture_id)
        .order_by(Report.version.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def get_findings(db: Session, venture_id: str) -> list[ResearchFinding]:
    """All research findings for a venture — the citations behind its report's
    sections. Not filtered by report version; a venture has one evolving set
    of findings, not per-report-version findings (see DATABASE_SCHEMA.md)."""
    stmt = (
        select(ResearchFinding)
        .where(ResearchFinding.venture_id == venture_id)
        .order_by(ResearchFinding.created_at)
    )
    return list(db.scalars(stmt))
