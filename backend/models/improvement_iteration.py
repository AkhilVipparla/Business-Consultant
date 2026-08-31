import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base


class ImprovementIteration(Base):
    __tablename__ = "improvement_iterations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    venture_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("ventures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    iteration_number: Mapped[int] = mapped_column(Integer, nullable=False)
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_score: Mapped[float] = mapped_column(Float, nullable=False)
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    venture: Mapped["Venture"] = relationship(back_populates="improvement_iterations")
