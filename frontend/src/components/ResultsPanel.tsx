import DriverAnalysisPanel from "./DriverAnalysisPanel"
import type { DriverInsightReport, DriverRanking, ExecutionResult } from "../types"

interface ResultsPanelProps {
  executionResults: ExecutionResult[]
  driverRanking: DriverRanking | null
  driverInsightReport: DriverInsightReport | null
}

function renderMetricValue(value: unknown): string {
  if (value === null || value === undefined) return "N/A"
  if (typeof value === "number") return Number.isFinite(value) ? value.toFixed(4).replace(/\.?0+$/, "") : "N/A"
  if (typeof value === "string" || typeof value === "boolean") return String(value)
  return "Object"
}

export default function ResultsPanel({ executionResults, driverRanking, driverInsightReport }: ResultsPanelProps) {
  return (
    <div className="space-y-4">
      <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-xl font-semibold tracking-tight">Execution Results</h3>
        {executionResults.length === 0 && (
          <p className="text-sm text-slate-500 dark:text-slate-400">No execution results were generated.</p>
        )}

        {executionResults.map((result) => (
          <article key={result.step_id} className="rounded-2xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800/60">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-semibold">Step: {result.step_id}</h4>
              <span
                className={`rounded-full px-2 py-1 text-xs font-semibold ${
                  result.status === "SUCCESS"
                    ? "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/40 dark:text-emerald-300"
                    : "bg-rose-100 text-rose-800 dark:bg-rose-900/40 dark:text-rose-300"
                }`}
              >
                {result.status}
              </span>
            </div>
            <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{result.result_summary}</p>
            {result.metrics && (
              <div className="mt-3 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
                {Object.entries(result.metrics).map(([key, value]) => (
                  <div key={key} className="rounded-xl border border-slate-200 bg-white p-2 dark:border-slate-700 dark:bg-slate-900">
                    <p className="text-[11px] uppercase tracking-wide text-slate-500">{key}</p>
                    <p className="text-sm font-medium">{renderMetricValue(value)}</p>
                  </div>
                ))}
              </div>
            )}
          </article>
        ))}
      </section>

      <DriverAnalysisPanel ranking={driverRanking} report={driverInsightReport} />
    </div>
  )
}
