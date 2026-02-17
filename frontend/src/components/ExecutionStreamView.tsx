import { useEffect, useMemo, useState } from "react"
import { Loader2 } from "lucide-react"
import { createExecutionSocket, getSessionState } from "../api/client"
import { useSession } from "../context/SessionContext"
import type { DriverInsightReport, DriverRanking, ExecutionResult, ExecutionStreamEvent } from "../types"

interface TimelineEvent {
  id: string
  type: "step_started" | "step_completed" | "step_failed"
  stepId: string
  message: string
}

export default function ExecutionStreamView() {
  const { sessionId, executionResults, setExecutionState, setErrors } = useSession()
  const [events, setEvents] = useState<TimelineEvent[]>([])
  const [connected, setConnected] = useState(false)
  const [activeStepId, setActiveStepId] = useState<string | null>(null)

  useEffect(() => {
    if (!sessionId) return
    const ws = createExecutionSocket(sessionId)
    ws.onopen = () => setConnected(true)
    ws.onmessage = (evt) => {
      try {
        const event = JSON.parse(evt.data) as ExecutionStreamEvent
        if (event.type === "heartbeat") return
        if (event.type === "step_started") {
          const stepId = String(event.payload.step_id ?? "unknown")
          setActiveStepId(stepId)
          setEvents((prev) => [
            ...prev,
            {
              id: `${stepId}-started-${prev.length}`,
              type: "step_started",
              stepId,
              message: `Step ${stepId} started`,
            },
          ])
          return
        }
        if (event.type === "step_completed") {
          const stepId = String(event.payload.step_id ?? "unknown")
          setActiveStepId(null)
          setEvents((prev) => [
            ...prev,
            {
              id: `${stepId}-completed-${prev.length}`,
              type: "step_completed",
              stepId,
              message: `Step ${stepId} completed: ${String(event.payload.summary ?? "Done")}`,
            },
          ])
          return
        }
        if (event.type === "step_failed") {
          const stepId = String(event.payload.step_id ?? "unknown")
          const error = String(event.payload.error ?? "Unknown execution error")
          setActiveStepId(null)
          setEvents((prev) => [
            ...prev,
            {
              id: `${stepId}-failed-${prev.length}`,
              type: "step_failed",
              stepId,
              message: `Step ${stepId} failed: ${error}`,
            },
          ])
          setErrors([error])
          return
        }
        if (event.type === "analysis_completed") {
          const results = (event.payload.execution_results as ExecutionResult[]) ?? []
          setExecutionState({
            phase: "COMPLETED",
            executionResults: results,
            driverRanking: (event.payload.driver_ranking as DriverRanking | null) ?? null,
            driverInsightReport: (event.payload.driver_insight_report as DriverInsightReport | null) ?? null,
          })
        }
      } catch {
        // Ignore malformed stream payloads
      }
    }
    ws.onclose = () => setConnected(false)
    return () => ws.close()
  }, [sessionId, setErrors, setExecutionState])

  useEffect(() => {
    if (!sessionId) return
    const interval = window.setInterval(async () => {
      try {
        const snapshot = await getSessionState(sessionId)
        if (snapshot.phase === "COMPLETED") {
          setExecutionState({
            phase: "COMPLETED",
            executionResults: snapshot.execution_results ?? [],
            hypothesisSet: snapshot.hypothesis_set ?? null,
            statisticalResults: snapshot.statistical_results ?? [],
            driverRanking: snapshot.driver_ranking ?? null,
            driverInsightReport: snapshot.driver_insight_report ?? null,
          })
        }
      } catch {
        // Ignore polling errors during active execution stream.
      }
    }, 2000)

    return () => window.clearInterval(interval)
  }, [sessionId, setExecutionState])

  const successCount = useMemo(() => executionResults.filter((item) => item.status === "SUCCESS").length, [executionResults])
  const failedCount = useMemo(() => executionResults.filter((item) => item.status === "FAILED").length, [executionResults])

  return (
    <section className="mx-auto max-w-4xl rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-2xl font-semibold tracking-tight">Execution Stream</h2>
      <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
        Deterministic analysis steps are executing live. Each step event is streamed from the backend.
      </p>
      <div className="mt-4 rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800">
        <p className="text-xs uppercase tracking-wide text-slate-500 dark:text-slate-400">
          Connection: {connected ? "LIVE" : "CONNECTING"}
        </p>
        {activeStepId && (
          <p className="mt-2 inline-flex items-center gap-2 rounded-lg bg-indigo-50 px-3 py-1 text-xs text-indigo-700 dark:bg-indigo-950/40 dark:text-indigo-300">
            <Loader2 size={14} className="animate-spin" />
            Executing step: {activeStepId}
          </p>
        )}
        <div className="mt-3 max-h-72 space-y-2 overflow-y-auto">
          {events.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Awaiting stream events...</p>
          )}
          {events.map((event, idx) => (
            <div key={`${event.id}-${idx}`} className="rounded-xl bg-white px-3 py-2 text-sm shadow-sm dark:bg-slate-900">
              <p>{event.message}</p>
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
          <p className="text-xs text-slate-500">Total Steps</p>
          <p className="text-lg font-semibold">{executionResults.length}</p>
        </div>
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-900 dark:bg-emerald-950/30">
          <p className="text-xs text-emerald-700 dark:text-emerald-300">Completed</p>
          <p className="text-lg font-semibold text-emerald-800 dark:text-emerald-200">{successCount}</p>
        </div>
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 dark:border-rose-900 dark:bg-rose-950/30">
          <p className="text-xs text-rose-700 dark:text-rose-300">Failed</p>
          <p className="text-lg font-semibold text-rose-800 dark:text-rose-200">{failedCount}</p>
        </div>
      </div>
    </section>
  )
}
