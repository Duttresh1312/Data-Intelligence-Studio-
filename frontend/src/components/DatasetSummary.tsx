import { useState } from "react"
import { startAnalysis } from "../api/client"
import { useSession } from "../context/SessionContext"

export default function DatasetSummary() {
  const { sessionId, datasetProfile, setStartAnalysisState, setErrors } = useSession()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onStart = async () => {
    if (!sessionId) return
    setLoading(true)
    setError(null)
    try {
      const response = await startAnalysis(sessionId)
      setStartAnalysisState({
        phase: response.phase,
        domainClassification: response.domain_classification ?? null,
        datasetSummaryReport: response.dataset_summary_report ?? null,
        missingValueSolutions: response.missing_value_solutions ?? [],
        lastMissingTreatmentResult: response.last_missing_treatment_result ?? null,
        conversationHistory: response.conversation_history,
      })
      setErrors([])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to start analysis"
      setError(message)
      setErrors([message])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="mx-auto max-w-4xl space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h2 className="text-2xl font-semibold tracking-tight">Dataset Profile Ready</h2>
      <p className="text-sm text-slate-600 dark:text-slate-300">
        Ingestion and profiling are complete. Start analysis to generate the dataset intelligence summary.
      </p>

      {datasetProfile && (
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <div className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
            <p className="text-xs text-slate-500">Rows</p>
            <p className="font-semibold">{datasetProfile.total_rows}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
            <p className="text-xs text-slate-500">Columns</p>
            <p className="font-semibold">{datasetProfile.total_columns}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
            <p className="text-xs text-slate-500">Numeric</p>
            <p className="font-semibold">{datasetProfile.numeric_columns.length}</p>
          </div>
          <div className="rounded-xl bg-slate-50 p-3 text-sm dark:bg-slate-800">
            <p className="text-xs text-slate-500">Categorical</p>
            <p className="font-semibold">{datasetProfile.categorical_columns.length}</p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={onStart}
        disabled={loading}
        className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Starting..." : "Start Analysis"}
      </button>
    </section>
  )
}
