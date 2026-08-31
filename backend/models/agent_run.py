import uuid
from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import AgentName, AgentRunStatus, db_enum


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    venture_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("ventures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_name: Mapped[AgentName] = mapped_column(db_enum(AgentName, length=50), nullable=False)
    iteration_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    status: Mapped[AgentRunStatus] = mapped_column(
        db_enum(AgentRunStatus, length=20),
        nullable=False,
        default=AgentRunStatus.PENDING,
        server_default=AgentRunStatus.PENDING.value,
    )
    input_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    output_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    venture: Mapped["Venture"] = relationship(back_populates="agent_runs")
