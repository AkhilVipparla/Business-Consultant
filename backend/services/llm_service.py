"""LLM access — the ONLY place agent code may call an LLM from.

Per anchor.md/DECISIONS.md Decision 009, every LLM call goes through LiteLLM
(never a direct `google-generativeai` call), so swapping or adding a provider
later only touches this file and core.config — no agent code changes.
"""

import threading
import time
from typing import Callable, TypeVar

import litellm
from pydantic import BaseModel

from core.config import settings
from core.logging import logger

T = TypeVar("T", bound=BaseModel)

# Ignore kwargs a given provider doesn't support instead of raising — keeps
# this wrapper stable if the default model/provider ever changes.
litellm.drop_params = True

# Free-tier LLM APIs are rate-limited, and independent per-call retries from
# parallel agents can still collide on a shared quota — discovered via real
# end-to-end runs against Gemini's free tier (5 req/min, then a 20 req/DAY
# cap — see anchor.md/DECISIONS.md Decision 013). Two layers of defense: a
# proactive process-wide throttle (below) that spaces EVERY call at least
# MIN_SECONDS_BETWEEN_CALLS apart, serialized across threads via a lock, plus
# a reactive retry-on-429 as a safety net. Groq's free tier (current
# provider) has a much higher per-minute cap than Gemini's did, so this can
# stay small — raise it if 429s show up in practice.
MIN_SECONDS_BETWEEN_CALLS = 2.0
MAX_RATE_LIMIT_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 20

_throttle_lock = threading.Lock()
_last_call_at = 0.0


def _throttle() -> None:
    """Block until it's been at least MIN_SECONDS_BETWEEN_CALLS since the
    last LLM call from ANY thread in this process."""
    global _last_call_at
    with _throttle_lock:
        wait = MIN_SECONDS_BETWEEN_CALLS - (time.monotonic() - _last_call_at)
        if wait > 0:
            time.sleep(wait)
        _last_call_at = time.monotonic()


def _with_rate_limit_retry(call: Callable[[], T]) -> T:
    for attempt in range(MAX_RATE_LIMIT_RETRIES + 1):
        _throttle()
        try:
            return call()
        except litellm.RateLimitError:
            if attempt == MAX_RATE_LIMIT_RETRIES:
                raise
            wait = RATE_LIMIT_BACKOFF_SECONDS * (attempt + 1)
            logger.warning(
                "LLM rate limit hit, retrying in {}s (attempt {}/{})",
                wait,
                attempt + 1,
                MAX_RATE_LIMIT_RETRIES,
            )
            time.sleep(wait)
    raise AssertionError("unreachable")  # loop always returns or raises


class LLMError(RuntimeError):
    """Raised when an LLM call fails or the active provider's API key is missing."""


def _active_model_id(provider: str) -> str:
    return settings.groq_model if provider == "groq" else settings.gemini_model


def _active_api_key(provider: str) -> str:
    return settings.groq_api_key if provider == "groq" else settings.gemini_api_key


def _model_name(provider: str) -> str:
    return f"{provider}/{_active_model_id(provider)}"


def _build_messages(prompt: str, system: str | None) -> list[dict[str, str]]:
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    return messages


def _require_api_key(provider: str) -> None:
    if not _active_api_key(provider):
        env_var = "GROQ_API_KEY" if provider == "groq" else "GEMINI_API_KEY"
        raise LLMError(
            f"{env_var} is not set — copy backend/.env.example to backend/.env and fill it in"
        )


def complete(
    prompt: str,
    system: str | None = None,
    temperature: float = 0.3,
    provider: str | None = None,
) -> str:
    """Plain-text completion — for free-form output (research plans, summaries).

    `provider` defaults to settings.llm_provider; pass "groq"/"gemini" to
    route a specific call elsewhere (see settings.heavy_llm_provider).
    """
    provider = provider or settings.llm_provider
    _require_api_key(provider)
    logger.debug("LLM call (text) model={}", _model_name(provider))
    try:
        response = _with_rate_limit_retry(
            lambda: litellm.completion(
                model=_model_name(provider),
                messages=_build_messages(prompt, system),
                api_key=_active_api_key(provider),
                temperature=temperature,
            )
        )
    except Exception as exc:  # noqa: BLE001 — normalize every provider error the same way
        logger.error("LLM text completion failed: {}", exc)
        raise LLMError(f"LLM completion failed: {exc}") from exc
    return response.choices[0].message.content or ""


def complete_structured(
    prompt: str,
    response_model: type[T],
    system: str | None = None,
    temperature: float = 0.2,
    provider: str | None = None,
) -> T:
    """Structured completion — returns a validated `response_model` instance.

    Use this whenever an agent needs the LLM's output as data (e.g. the
    Executive Decision Agent's score + feedback) rather than prose.

    `provider` defaults to settings.llm_provider; pass "groq"/"gemini" to
    route a specific call elsewhere (see settings.heavy_llm_provider).
    """
    provider = provider or settings.llm_provider
    _require_api_key(provider)
    logger.debug("LLM call (structured: {}) model={}", response_model.__name__, _model_name(provider))
    try:
        response = _with_rate_limit_retry(
            lambda: litellm.completion(
                model=_model_name(provider),
                messages=_build_messages(prompt, system),
                api_key=_active_api_key(provider),
                temperature=temperature,
                response_format=response_model,
            )
        )
    except Exception as exc:  # noqa: BLE001
        logger.error("LLM structured completion ({}) failed: {}", response_model.__name__, exc)
        raise LLMError(f"LLM structured completion failed: {exc}") from exc

    content = response.choices[0].message.content or ""
    try:
        return response_model.model_validate_json(content)
    except Exception as exc:  # noqa: BLE001
        logger.error("LLM returned invalid {}: {}", response_model.__name__, exc)
        raise LLMError(f"LLM response did not match {response_model.__name__}: {exc}") from exc
