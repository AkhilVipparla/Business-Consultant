from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """App configuration loaded from environment variables.

    Every field here must stay in sync with the env var list in
    anchor.md/TECH_STACK.md and anchor.md/SECURITY.md.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite:///./venturemind.db"

    # Which LiteLLM provider prefix to use — see anchor.md/DECISIONS.md Decision 013.
    # Switching provider is a config-only change (services/llm_service.py reads this),
    # nothing else in the codebase needs to change per Decision 009.
    llm_provider: str = "groq"

    # Provider used only by the two agents that aggregate ALL research
    # findings into a single prompt (Executive Decision, Report Generator).
    # Those prompts are far larger than the rest of the graph's calls and can
    # exceed a small model's per-request token-per-minute cap on their own —
    # kept as a separate setting so just those two calls can run against a
    # bigger-budget provider without moving the whole app off llm_provider.
    heavy_llm_provider: str = "gemini"

    gemini_api_key: str = ""
    # LiteLLM model id (without the "gemini/" provider prefix — services/llm_service.py
    # adds that). No live key to verify against yet — if this model gets deprecated,
    # update it here only, nothing else needs to change.
    gemini_model: str = "gemini-2.0-flash"

    groq_api_key: str = ""
    # LiteLLM model id (without the "groq/" provider prefix). Groq's free tier has a
    # much higher daily request cap than Gemini's (see Decision 013) — chosen to get
    # unblocked on real end-to-end runs. Verify this is still current before relying
    # on it — Groq's hosted model lineup moves.
    groq_model: str = "openai/gpt-oss-120b"

    tavily_api_key: str = ""
    firecrawl_api_key: str = ""
    cors_origins: str = "http://localhost:3000"
    log_level: str = "INFO"

    # Executive Decision Agent loop — see anchor.md/DECISIONS.md Decision 012.
    # Score below this loops back to research with feedback; at/above it goes
    # straight to the report. Tunable here without touching graph/workflow.py.
    score_threshold: float = 60.0
    # How many EXTRA research passes are allowed beyond the first (so 2 means
    # up to 3 evaluation passes total) before the report is forced regardless
    # of score.
    max_iterations: int = 1

    # If a venture is stuck at status=RUNNING (e.g. the server restarted or the
    # client disconnected mid-stream, so _run_and_stream() never reached its
    # COMPLETED/FAILED write) for longer than this, /validate treats it as
    # dead and allows a fresh run instead of returning 409 forever.
    stale_run_timeout_seconds: int = 600

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()
