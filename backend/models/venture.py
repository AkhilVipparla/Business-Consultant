import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import VentureStatus, db_enum


class Venture(Base):
    __tablename__ = "ventures"
    __table_args__ = (
        CheckConstraint(
            "venture_score IS NULL OR (venture_score >= 0 AND venture_score <= 100)",
            name="ck_ventures_score_range",
        ),
    )

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    one_liner: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    target_market: Mapped[str | None] = mapped_column(Text, nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[VentureStatus] = mapped_column(
        db_enum(VentureStatus, length=20),
        nullable=False,
        default=VentureStatus.DRAFT,
        server_default=VentureStatus.DRAFT.value,
        index=True,
    )
    venture_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    iteration_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    agent_runs: Mapped[list["AgentRun"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
    research_findings: Mapped[list["ResearchFinding"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
    reports: Mapped[list["Report"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
    improvement_iterations: Mapped[list["ImprovementIteration"]] = relationship(
        back_populates="venture", cascade="all, delete-orphan"
    )
