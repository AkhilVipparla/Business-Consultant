"use client";

import { useEffect, useState } from "react";

import type { AgentName, AgentRunStatus, VentureState, VentureStreamEvent } from "@/types/venture";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

interface UseVentureStreamResult {
  steps: Partial<Record<AgentName, AgentRunStatus>>;
  state: Partial<VentureState>;
  isDone: boolean;
  error: string | null;
}

// Folds one agent's state_delta into the accumulated VentureState, mirroring
// state/schema.py's own reducers: the six *_findings lists use operator.add
// (each node's delta only carries ITS OWN new findings, so accumulate them),
// every other field is last-write-wins (only the node that owns it ever
// includes it in a delta, so a plain overwrite can't clobber another agent's
// field).
function mergeStateDelta(
  prev: Partial<VentureState>,
  delta: Partial<VentureState>,
): Partial<VentureState> {
  return {
    ...prev,
    ...delta,
    market_findings: [...(prev.market_findings ?? []), ...(delta.market_findings ?? [])],
    competitor_findings: [...(prev.competitor_findings ?? []), ...(delta.competitor_findings ?? [])],
    customer_findings: [...(prev.customer_findings ?? []), ...(delta.customer_findings ?? [])],
    financial_findings: [...(prev.financial_findings ?? []), ...(delta.financial_findings ?? [])],
    marketing_findings: [...(prev.marketing_findings ?? []), ...(delta.marketing_findings ?? [])],
    risk_findings: [...(prev.risk_findings ?? []), ...(delta.risk_findings ?? [])],
  };
}

// Connects to GET /ventures/{id}/validate (SSE), tracks each agent's latest
// status, and accumulates the venture's state as deltas arrive — so the
// final report (score, sections, recommendations) is available the moment
// the stream finishes, no separate GET /report round trip needed. Auto-starts
// on mount — this hook's only real use case is "the user just landed on the
// live pipeline view for a venture," so there is no separate "start" trigger
// to wire up.
export function useVentureStream(ventureId: string): UseVentureStreamResult {
  const [steps, setSteps] = useState<Partial<Record<AgentName, AgentRunStatus>>>({});
  const [state, setState] = useState<Partial<VentureState>>({});
  const [isDone, setIsDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const source = new EventSource(`${API_URL}/ventures/${ventureId}/validate`);

    source.onmessage = (event: MessageEvent<string>) => {
      const parsed = JSON.parse(event.data) as VentureStreamEvent;

      if (parsed.agent === "workflow" && parsed.status === "failed") {
        setError(parsed.state_delta.error ?? "The workflow failed.");
        setIsDone(true);
        source.close();
        return;
      }

      setSteps((prev) => ({ ...prev, [parsed.agent]: parsed.status }));

      if (parsed.status === "completed") {
        setState((prev) => mergeStateDelta(prev, parsed.state_delta));
      }

      if (parsed.agent === "report_generator" && parsed.status === "completed") {
        setIsDone(true);
        source.close();
      }
    };

    source.onerror = () => {
      setError((prev) => prev ?? "Connection to the live pipeline was lost.");
      setIsDone(true);
      source.close();
    };

    return () => {
      source.close();
    };
  }, [ventureId]);

  return { steps, state, isDone, error };
}
