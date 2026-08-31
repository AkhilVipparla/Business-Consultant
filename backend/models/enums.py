import enum

from sqlalchemy import Enum as SAEnum


def db_enum(enum_cls: type[enum.Enum], length: int) -> SAEnum:
    """A non-native (CHECK-constrained) Enum column that stores each member's
    lowercase `.value` (matching anchor.md/DATABASE_SCHEMA.md's enum tables),
    not SQLAlchemy's default of the uppercase Python `.name`."""
    return SAEnum(
        enum_cls,
        native_enum=False,
        validate_strings=True,
        length=length,
        values_callable=lambda cls: [member.value for member in cls],
    )


class VentureStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentName(str, enum.Enum):
    PLANNER = "planner"
    MARKET_RESEARCH = "market_research"
    COMPETITOR = "competitor"
    CUSTOMER = "customer"
    FINANCIAL_RISK = "financial_risk"
    EXECUTIVE_DECISION = "executive_decision"
    REPORT_GENERATOR = "report_generator"


class AgentRunStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class FindingCategory(str, enum.Enum):
    MARKET = "market"
    COMPETITOR = "competitor"
    CUSTOMER = "customer"
    FINANCIAL = "financial"
    MARKETING = "marketing"
    RISK = "risk"


class FindingSourceType(str, enum.Enum):
    TAVILY = "tavily"
    FIRECRAWL = "firecrawl"
    LLM = "llm"
