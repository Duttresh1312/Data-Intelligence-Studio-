import type {
  ApplyMissingValueSolutionResponse,
  ApprovePlanResponse,
  ChatResponse,
  SetPhaseResponse,
  StartAnalysisResponse,
  StateResponse,
  StudioPhase,
  UploadResponse,
} from "../types"

const API_BASE = "/api/v1"

function getDetail(error: unknown): string {
  if (typeof error === "string") return error
  const e = error as { detail?: string | { msg?: string }[] }
  if (typeof e?.detail === "string") return e.detail
  if (Array.isArray(e?.detail)) return e.detail.map((d) => d?.msg ?? "").filter(Boolean).join(", ") || "Unknown error"
  return "Unknown error"
}

export async function uploadDataset(file: File): Promise<UploadResponse> {
  const form = new FormData()
  form.append("file", file)
  const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: form })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function startAnalysis(sessionId: string): Promise<StartAnalysisResponse> {
  const res = await fetch(`${API_BASE}/start-analysis`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function sendChatMessage(sessionId: string, message: string): Promise<ChatResponse> {
  const res = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, message }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function approvePlan(sessionId: string): Promise<ApprovePlanResponse> {
  const res = await fetch(`${API_BASE}/approve-plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function setSessionPhase(sessionId: string, phase: StudioPhase): Promise<SetPhaseResponse> {
  const res = await fetch(`${API_BASE}/set-phase`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, phase }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function applyMissingValueSolution(
  sessionId: string,
  solutionId: string
): Promise<ApplyMissingValueSolutionResponse> {
  const res = await fetch(`${API_BASE}/apply-missing-solution`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, solution_id: solutionId }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function getSessionState(sessionId: string): Promise<StateResponse> {
  const res = await fetch(`${API_BASE}/state/${sessionId}`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(getDetail(err))
  }
  return res.json()
}

export async function healthCheck(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`)
  if (!res.ok) throw new Error("API unhealthy")
  return res.json()
}

export function createExecutionSocket(sessionId: string): WebSocket {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws"
  const host = window.location.host
  return new WebSocket(`${protocol}://${host}/ws/${sessionId}`)
}

export const phaseOrder: StudioPhase[] = [
  "LANDING",
  "DATA_UPLOADED",
  "PROFILE_READY",
  "WAITING_FOR_INTENT",
  "PLAN_READY",
  "EXECUTING",
  "COMPLETED",
]
