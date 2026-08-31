# VentureMind AI

VentureMind AI is an AI-powered venture studio that validates, critiques, and improves startup ideas using a team of specialized AI agents orchestrated with **LangGraph**. Submit a raw business idea and watch a graph of single-responsibility agents research the market, competitors, customers, and financial/risk profile, score the venture, and — if the score is weak — automatically loop back with feedback to improve the research before producing a final, cited executive report.

It's built primarily as a demonstration of graph-based multi-agent orchestration (parallel/sequential execution, shared state, conditional routing, iterative self-improvement loops) rather than as a general-purpose chatbot.

## How it works

1. You submit a venture idea (title, one-liner, description, target market, industry) through the frontend intake form.
2. The backend creates a `venture` record and opens a live Server-Sent Events (SSE) stream that runs a LangGraph workflow:

   ```
   Planner
     → [Market Research, Competitor, Customer]   (parallel)
     → Financial/Risk
     → Executive Decision Agent (scores the venture)
         ├─ score < threshold AND iterations remain → loop back to research, with feedback
         └─ otherwise → Report Generator → done
   ```

3. Each research agent gathers real evidence via an LLM (for query planning) plus **Tavily** (web search) and **Firecrawl** (page scraping), and writes cited findings into a shared state object.
4. The Executive Decision Agent scores the venture 0–100. Below the configured threshold, the graph loops back to research with specific feedback on what's weak — up to a capped number of extra passes.
5. The Report Generator synthesizes everything into a final report: summary, six per-category sections, and concrete recommendations.
6. The frontend renders every step live as it streams in, and shows the finished report on the same page the moment it's ready — no extra click, no extra request.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS |
| Backend | FastAPI, LangGraph, LangChain, LiteLLM |
| Database | SQLite via SQLAlchemy + Alembic migrations |
| LLM providers | Groq and/or Gemini, routed through LiteLLM — swappable via config, no code changes |
| Research | Tavily (search), Firecrawl (scraping) |
| Auth | None — single local user, v1 has no accounts/login |

## Repository layout

```
Business-Consultant/
├── anchor.md/              Living design docs (architecture, decisions, security, schema...)
├── backend/                FastAPI + LangGraph service
│   ├── main.py              App entrypoint, CORS, router mounting
│   ├── api/v1/               REST + SSE route handlers
│   ├── agents/                One file per agent (single responsibility each)
│   ├── graph/workflow.py      LangGraph wiring only — no business logic
│   ├── state/schema.py        Shared Pydantic VentureState
│   ├── prompts/                Prompt templates (never inlined in agent code)
│   ├── services/                LLM/Tavily/Firecrawl/DB service wrappers
│   ├── models/                   SQLAlchemy ORM models
│   ├── db/migrations/             Alembic migrations
│   └── core/                       Env-driven settings + logging
└── frontend/                Next.js App Router UI
    ├── app/                  Pages (intake form, live pipeline view, report view)
    ├── components/            UI components (pipeline stepper, report cards, forms)
    ├── hooks/useVentureStream.ts  SSE client — accumulates live agent state
    └── lib/api.ts              REST API client
```

## Prerequisites

- **Python 3.11+**
- **Node.js 20.x** and **npm 10.x+**
- API keys for the services you intend to use (all have a free tier):
  - [Groq](https://console.groq.com/keys) and/or [Google AI Studio (Gemini)](https://aistudio.google.com/apikey) — at least one LLM provider
  - [Tavily](https://app.tavily.com/) — web search
  - [Firecrawl](https://www.firecrawl.dev/) — page scraping

## Installation

### 1. Backend (FastAPI)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt

copy .env.example .env              # macOS/Linux: cp .env.example .env
# then open .env and fill in your API keys (see "Environment variables" below)
```

Apply database migrations (creates `venturemind.db` and its schema):

```powershell
alembic upgrade head
```

Run the server:

```powershell
uvicorn main:app --reload --port 8000
```

Confirm it's up: open `http://localhost:8000/health` — should return `{"status": "ok"}`.

### 2. Frontend (Next.js)

In a separate terminal:

```powershell
cd frontend
npm install

copy .env.example .env.local        # macOS/Linux: cp .env.example .env.local
# .env.local just needs NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1 (already the default)

npm run dev
```

Open `http://localhost:3000`. Both servers need to be running at the same time — the frontend talks to the backend over plain REST for CRUD and over SSE for the live validation stream.

## Environment variables

Set these in `backend/.env` (see `backend/.env.example` for the template):

| Variable | Required | Default | Purpose |
|---|---|---|---|
| `DATABASE_URL` | No | `sqlite:///./venturemind.db` | SQLAlchemy connection string |
| `LLM_PROVIDER` | No | `groq` | Provider used by most agents: `groq` or `gemini` |
| `GROQ_API_KEY` | If using Groq | — | Groq API key |
| `GROQ_MODEL` | No | `openai/gpt-oss-120b` | LiteLLM model id (no `groq/` prefix — added automatically) |
| `GEMINI_API_KEY` | If using Gemini | — | Gemini API key |
| `GEMINI_MODEL` | No | `gemini-2.0-flash` | LiteLLM model id (no `gemini/` prefix) |
| `HEAVY_LLM_PROVIDER` | No | `gemini` | Provider used only by the two agents that aggregate *all* research findings into one prompt (Executive Decision, Report Generator) — kept separate since those prompts are much larger and can exceed a small model's per-minute token budget on their own |
| `TAVILY_API_KEY` | Yes | — | Tavily search API key |
| `FIRECRAWL_API_KEY` | Yes | — | Firecrawl scraping API key |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated allowed origins |
| `LOG_LEVEL` | No | `INFO` | Loguru log level |
| `SCORE_THRESHOLD` | No | `70.0` | Score (0–100) at/above which the graph proceeds straight to the report |
| `MAX_ITERATIONS` | No | `2` | Extra research passes allowed beyond the first before the report is forced regardless of score |
| `STALE_RUN_TIMEOUT_SECONDS` | No | `600` | How long a venture can sit at `status=running` (e.g. after a server restart mid-run) before `/validate` treats it as dead and allows a fresh run instead of returning 409 forever |

And in `frontend/.env.local`:

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000/api/v1` | Base URL the frontend calls |

## API overview

Base URL: `http://localhost:8000/api/v1`

| Method & path | Description |
|---|---|
| `POST /ventures` | Create a venture (title, one_liner, description, target_market, industry) |
| `GET /ventures` | List all ventures |
| `GET /ventures/{id}` | Fetch one venture's status/score/metadata |
| `GET /ventures/{id}/validate` | **SSE** — triggers and streams the LangGraph agent workflow live |
| `GET /ventures/{id}/report` | Fetch the latest generated report (404 until one exists) |

All JSON responses use a standard envelope: `{"success": bool, "data": ..., "error": ..., "message": ...}`. `/validate` is the one exception — it returns `text/event-stream`, one JSON payload per line: `{"agent": "...", "status": "...", "state_delta": {...}}`.

## Architectural rules worth knowing

These are enforced by convention, not by tooling — keep them in mind if you're modifying the backend:

- Agents only ever read/write the shared `VentureState` — never call each other directly.
- `graph/workflow.py` contains *only* node/edge wiring, no business logic.
- Prompt templates live only in `prompts/`, never as inline strings in agent code.
- All LLM calls go through `services/llm_service.py` (LiteLLM) — never a provider SDK called directly from an agent.
- No auth in v1 — every route is open; there's a single implicit local user.

See `anchor.md/ARCHITECTURE.md`, `anchor.md/DECISIONS.md`, and `anchor.md/DATABASE_SCHEMA.md` for the full design rationale.

## Troubleshooting

- **`litellm.RateLimitError` / 429s**: your active model's free-tier token-per-minute or request-per-minute cap was exceeded. Check the error message for whether it's a per-minute or per-day limit, and consider a lighter model or `HEAVY_LLM_PROVIDER` split (already applied to the two heaviest prompts by default).
- **`GET /ventures/{id}/report` returns 404**: either the venture hasn't finished validating yet, or its last run failed/was interrupted before a report was persisted. Check `GET /ventures/{id}` for its `status`.
- **`GET /ventures/{id}/validate` returns 409**: a run is already in progress for that venture. If you're sure it isn't (e.g. the server restarted mid-run), it will self-recover after `STALE_RUN_TIMEOUT_SECONDS` (10 minutes by default) — or restart sooner by lowering that setting.
- **Import/module errors on backend startup**: make sure the virtual environment is activated and `pip install -r requirements.txt` completed without errors.

## Current status

Zero-budget, local-first, solo-built v1 — no hosting/deployment configured yet, no authentication, and SQLite as the only datastore (kept Postgres-portable via SQLAlchemy for a future migration). See `anchor.md/TODO.md` and `anchor.md/CONTEXT_MEMORY.md` for what's in progress.
