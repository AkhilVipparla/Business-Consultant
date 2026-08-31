"""SSE endpoint that triggers and streams the LangGraph workflow.

Per anchor.md/ARCHITECTURE.md, this is the one exception to the standard
{success,data,error,message} JSON envelope — it returns text/event-stream,
one JSON-encoded VentureStreamEvent per line (see frontend/types/venture.ts).

Route handler stays thin; the actual run/persist orchestration is in
_run_and_stream() below (still this file, not services/, since it's tightly
coupled to the SSE event shape — but the graph itself has zero business logic
per graph/workflow.py's own rule).
"""

import json
from collections.abc import AsyncGenerator
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from core.config import settings
from core.logging import logger
from db.session import SessionLocal, get_db
from graph.workflow import graph
from models import AgentRun, ImprovementIteration, Report, ResearchFinding, Venture
from models.enums import AgentRunStatus, VentureStatus
from services import venture_service
from state.schema import VentureState

router = APIRouter(prefix="/ventures", tags=["validate"])

# Must match graph/workflow.py's node names exactly, and models.enums.AgentName's
# values — both true by construction (see ARCHITECTURE.md Decision 011).
KNOWN_NODES = {
    "planner",
    "market_research",
    "competitor",
    "customer",
    "financial_risk",
    "executive_decision",
    "report_generator",
}


def _json_safe(value):
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    return value


def _sse(agent: str, status: str, state_delta: dict) -> str:
    payload = {"agent": agent, "status": status, "state_delta": _json_safe(state_delta)}
    return f"data: {json.dumps(payload)}\n\n"


def _next_report_version(db: Session, venture_id: str) -> int:
    latest = venture_service.get_latest_report(db, venture_id)
    return (latest.version + 1) if latest else 1


def _persist_final_report(db: Session, venture_id: str, final_state: VentureState) -> None:
    # Replace findings wholesale with the current accumulated set — simplest
    # correct behavior for a venture that gets re-validated from scratch.
    db.query(ResearchFinding).filter(ResearchFinding.venture_id == venture_id).delete()
    all_findings = (
        final_state.market_findings
        + final_state.competitor_findings
        + final_state.customer_findings
        + final_state.financial_findings
        + final_state.marketing_findings
        + final_state.risk_findings
    )
    for finding in all_findings:
        db.add(
            ResearchFinding(
                venture_id=venture_id,
                category=finding.category,
                source_type=finding.source_type,
                source_url=finding.source_url,
                title=finding.title,
                content=finding.content,
            )
        )

    db.add(
        Report(
            venture_id=venture_id,
            version=_next_report_version(db, venture_id),
            venture_score=final_state.venture_score or 0.0,
            summary=final_state.summary or "",
            sections=final_state.sections,
            recommendations=final_state.recommendations,
        )
    )


async def _run_and_stream(venture_id: str) -> AsyncGenerator[str, None]:
    # A fresh session — the route handler's request-scoped session (from
    # Depends(get_db)) closes before this generator body actually runs.
    db = SessionLocal()
    try:
        venture = db.get(Venture, venture_id)
        initial_state = VentureState(
            venture_id=venture.id,
            title=venture.title,
            one_liner=venture.one_liner,
            description=venture.description,
            target_market=venture.target_market,
            industry=venture.industry,
        )

        started_at: dict[str, datetime] = {}
        previous_score: float | None = None
        current_iteration = 1
        final_state: VentureState | None = None

        try:
            async for event in graph.astream_events(initial_state, version="v2"):
                name = event.get("name")
                kind = event["event"]

                if name == "LangGraph" and kind == "on_chain_end":
                    final_state = VentureState(**event["data"]["output"])
                    continue

                if name not in KNOWN_NODES:
                    continue

                if kind == "on_chain_start":
                    started_at[name] = datetime.now(UTC)
                    yield _sse(name, "running", {})

                elif kind == "on_chain_end":
                    output = event["data"]["output"] or {}
                    yield _sse(name, "completed", output)

                    db.add(
                        AgentRun(
                            venture_id=venture_id,
                            agent_name=name,
                            iteration_number=current_iteration,
                            status=AgentRunStatus.COMPLETED,
                            output_state=_json_safe(output),
                            started_at=started_at.get(name),
                            completed_at=datetime.now(UTC),
                        )
                    )

                    if name == "executive_decision":
                        new_score = output.get("venture_score")
                        db.add(
                            ImprovementIteration(
                                venture_id=venture_id,
                                iteration_number=current_iteration,
                                previous_score=previous_score,
                                new_score=new_score,
                                feedback=output.get("decision_feedback") or "",
                            )
                        )
                        previous_score = new_score
                        venture.venture_score = new_score
                        venture.iteration_count = output.get("iteration_count", venture.iteration_count)
                        current_iteration += 1

                    db.commit()

            if final_state is None:
                raise RuntimeError("Workflow finished without producing a final state")

            _persist_final_report(db, venture_id, final_state)
            venture.status = VentureStatus.COMPLETED
            db.commit()

        except Exception as exc:  # noqa: BLE001 — a failed run must still update venture.status
            logger.error("Workflow run failed for venture {}: {}", venture_id, exc)
            venture.status = VentureStatus.FAILED
            db.commit()
            yield _sse("workflow", "failed", {"error": str(exc)})
    finally:
        db.close()


@router.get("/{venture_id}/validate")
def validate_venture(venture_id: str, db: Session = Depends(get_db)):
    venture = venture_service.get_venture(db, venture_id)
    if venture is None:
        raise HTTPException(status_code=404, detail="Venture not found")
    if venture.status == VentureStatus.RUNNING:
        # venture.updated_at is a naive UTC timestamp (models/venture.py's
        # DateTime column has no timezone) — compare against a naive UTC
        # "now" rather than datetime.now(UTC) directly, or the aware/naive
        # subtraction below raises.
        now_naive_utc = datetime.now(UTC).replace(tzinfo=None)
        stale_cutoff = now_naive_utc - timedelta(seconds=settings.stale_run_timeout_seconds)
        if venture.updated_at > stale_cutoff:
            raise HTTPException(
                status_code=409, detail="A validation run is already in progress for this venture"
            )
        logger.warning(
            "Venture {} stuck in RUNNING since {} (>{}s ago) — treating as a dead run and restarting",
            venture_id,
            venture.updated_at,
            settings.stale_run_timeout_seconds,
        )

    venture.status = VentureStatus.RUNNING
    db.commit()

    return StreamingResponse(_run_and_stream(venture_id), media_type="text/event-stream")
