import sys

from loguru import logger

from core.config import settings


def configure_logging() -> None:
    """Configure loguru per anchor.md/SECURITY.md logging rules.

    Never log secrets (API keys) or raw prompt/response payloads that may
    contain them — see anchor.md/SECURITY.md > LOGGING & MONITORING.
    """
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level, backtrace=False, diagnose=False)


__all__ = ["configure_logging", "logger"]
