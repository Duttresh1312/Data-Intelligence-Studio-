import { BarChart3, ShieldCheck } from "lucide-react"
import type { DriverInsightReport, DriverRanking, StatisticalResult } from "../types"

interface DriverAnalysisPanelProps {
  ranking: DriverRanking | null
  report: DriverInsightReport | null
}

function impactValue(item: StatisticalResult): number {
  const significance = item.p_value !== null && item.p_value !== undefined ? Math.max(0, 1 - Math.min(item.p_value, 1)) : 0
  const effect = item.effect_size ? Math.abs(item.effect_size) : 0
  const importance = item.feature_importance ? Math.abs(item.feature_importance) : 0
  return Number((0.4 * significance + 0.35 * effect + 0.25 * importance).toFixed(4))
}

export default function DriverAnalysisPanel({ ranking, report }: DriverAnalysisPanelProps) {
  if (!ranking || ranking.ranked_drivers.length === 0) {
    return (
      <section className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <h3 className="text-xl font-semibold tracking-tight">Driver Analysis</h3>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
          No driver ranking signals were generated in this run.
        </p>
      </section>
    )
  }

  const maxImpact = Math.max(...ranking.ranked_drivers.map(impactValue), 0.0001)

  return (
    <section className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold tracking-tight">Driver Analysis</h3>
        {report && (
          <span className="inline-flex items-center gap-1 rounded-full bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-700 dark:bg-indigo-900/40 dark:text-indigo-300">
            <ShieldCheck size={12} />
            Confidence {Math.round(report.confidence * 100)}%
          </span>
        )}
      </div>

      {report && (
        <div className="rounded-2xl border border-indigo-200 bg-indigo-50 p-4 dark:border-indigo-900 dark:bg-indigo-950/30">
          <p className="text-sm font-medium text-indigo-900 dark:text-indigo-200">{report.executive_driver_summary}</p>
          <p className="mt-2 text-xs text-indigo-700 dark:text-indigo-300">{report.strength_assessment}</p>
          <p className="mt-2 text-xs text-indigo-700 dark:text-indigo-300">Next: {report.recommended_next_step}</p>
        </div>
      )}

      <div className="space-y-3">
        {ranking.ranked_drivers.slice(0, 10).map((item, index) => {
          const impact = impactValue(item)
          const width = `${Math.max(8, (impact / maxImpact) * 100)}%`
          return (
            <div key={`${item.predictor}-${item.target}-${index}`} className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
              <div className="flex items-center justify-between text-sm">
                <p className="font-semibold">
                  {index + 1}. {item.predictor} {item.target ? `-> ${item.target}` : ""}
                </p>
                <p className="text-slate-500 dark:text-slate-400">{item.test_type}</p>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                <div className="h-2 rounded-full bg-gradient-to-r from-teal-500 to-indigo-500 transition-all" style={{ width }} />
              </div>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs md:grid-cols-4">
                <div className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">
                  <p className="text-slate-500">Impact</p>
                  <p className="font-semibold">{impact}</p>
                </div>
                <div className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">
                  <p className="text-slate-500">Score</p>
                  <p className="font-semibold">{item.score.toFixed(4)}</p>
                </div>
                <div className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">
                  <p className="text-slate-500">P-Value</p>
                  <p className="font-semibold">{item.p_value ?? "N/A"}</p>
                </div>
                <div className="rounded-lg bg-slate-100 px-2 py-1 dark:bg-slate-800">
                  <p className="text-slate-500">Effect</p>
                  <p className="font-semibold">{item.effect_size ?? item.feature_importance ?? "N/A"}</p>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {report?.top_3_drivers?.length ? (
        <div className="rounded-2xl border border-slate-200 p-3 dark:border-slate-700">
          <p className="mb-2 inline-flex items-center gap-1 text-sm font-semibold">
            <BarChart3 size={14} />
            Top Drivers
          </p>
          <div className="flex flex-wrap gap-2">
            {report.top_3_drivers.map((driver) => (
              <span key={driver} className="rounded-full bg-teal-100 px-3 py-1 text-xs font-medium text-teal-800 dark:bg-teal-900/30 dark:text-teal-200">
                {driver}
              </span>
            ))}
          </div>
        </div>
      ) : null}
    </section>
  )
}
