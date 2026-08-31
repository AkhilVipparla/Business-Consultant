import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.enums import FindingCategory, FindingSourceType, db_enum


class ResearchFinding(Base):
    __tablename__ = "research_findings"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    venture_id: Mapped[str] = mapped_column(
        String(32), ForeignKey("ventures.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category: Mapped[FindingCategory] = mapped_column(
        db_enum(FindingCategory, length=20),
        nullable=False,
        index=True,
    )
    source_type: Mapped[FindingSourceType] = mapped_column(
        db_enum(FindingSourceType, length=20), nullable=False
    )
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    venture: Mapped["Venture"] = relationship(back_populates="research_findings")
