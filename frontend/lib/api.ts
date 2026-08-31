// REST API client — the ONLY place frontend code should call the backend
// from directly, per anchor.md/ARCHITECTURE.md's frontend API Communication
// section. SSE (lib/sse.ts) is separate and doesn't exist yet — it needs the
// backend's GET /ventures/{id}/validate endpoint, which is blocked.

import type {
  ApiResponse,
  VentureCreateInput,
  VentureRecord,
  VentureReport,
} from "@/types/venture";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    // This app's data changes via direct DB writes and, soon, a live agent
    // pipeline — never let Next.js cache a GET across requests/deploys.
    cache: "no-store",
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  const body: ApiResponse<T> = await res.json();
  if (!body.success || body.data === null) {
    throw new Error(body.error ?? `Request failed with status ${res.status}`);
  }
  return body.data;
}

export function createVenture(input: VentureCreateInput): Promise<VentureRecord> {
  return request<VentureRecord>("/ventures", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function listVentures(): Promise<VentureRecord[]> {
  return request<VentureRecord[]>("/ventures");
}

export function getVenture(id: string): Promise<VentureRecord> {
  return request<VentureRecord>(`/ventures/${id}`);
}

export function getVentureReport(id: string): Promise<VentureReport> {
  return request<VentureReport>(`/ventures/${id}/report`);
}
