import { useEffect, useState } from "react"
import { AlertTriangle, BarChart3, HeartPulse, Lightbulb, Sparkles, Table2 } from "lucide-react"
import type {
  DatasetProfile,
  DatasetSummaryReport,
  DomainClassification,
  MissingValueSolution,
  MissingValueTreatmentResult,
} from "../types"

interface DatasetIntelligencePanelProps {
  domainClassification: DomainClassification | null
  datasetProfile: DatasetProfile | null
  report: DatasetSummaryReport | null
  missingValueSolutions: MissingValueSolution[]
  lastMissingTreatmentResult: MissingValueTreatmentResult | null
  applyingSolutionId: string | null
  onApplyMissingValueSolution?: (solutionId: string) => void
}

interface MissingItem {
  column: string
  pct: number
}

interface MetricStatRow {
  column: string
  mean: number | null
  std: number | null
  min: number | null
  max: number | null
  range: number | null
  variabilityScore: number | null
}

interface ActionableInsight {
  id: string
  title: string
  signal: string
  analysisAction: string
  businessImpact: string
}

function toNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null
}

function formatNumber(value: number | null, digits = 2): string {
  if (value === null || !Number.isFinite(value)) return "N/A"
  return value.toFixed(digits)
}

function interpretationBadge(score: number | null): { label: string; className: string } {
  if (score === null) {
    return {
      label: "Insufficient data",
      className: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
    }
  }
  if (score >= 0.6) {
    return {
      label: "High variability",
      className: "bg-rose-100 text-rose-800 dark:bg-rose-900/30 dark:text-rose-300",
    }
  }
  if (score >= 0.3) {
    return {
      label: "Moderate variability",
      className: "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-300",
    }
  }
  return {
    label: "Stable range",
    className: "bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-300",
  }
}

function buildMetricRows(profile: DatasetProfile | null): MetricStatRow[] {
  if (!profile) return []
  const metricColumns = Object.entries(profile.column_roles)
    .filter(([, role]) => role === "NUMERIC_METRIC")
    .map(([column]) => column)

  return metricColumns
    .map((column) => {
      const summary = profile.column_summary[column] ?? {}
      const mean = toNumber(summary.mean)
      const std = toNumber(summary.std)
      const min = toNumber(summary.min)
      const max = toNumber(summary.max)
      const range = min !== null && max !== null ? max - min : null
      const denominator = mean !== null && Math.abs(mean) > 0.0000001 ? Math.abs(mean) : null
      const variabilityScore = std !== null && denominator !== null ? Math.abs(std / denominator) : null
      return { column, mean, std, min, max, range, variabilityScore }
    })
    .sort((a, b) => (b.variabilityScore ?? b.std ?? 0) - (a.variabilityScore ?? a.std ?? 0))
}

function buildActionableInsights(
  profile: DatasetProfile | null,
  rows: MetricStatRow[]
): ActionableInsight[] {
  if (!profile || rows.length === 0) return []
  const insights: ActionableInsight[] = []
  const topRows = rows.slice(0, 3)

  topRows.forEach((row, index) => {
    const variability = row.variabilityScore ?? 0
    if (variability >= 0.6) {
      insights.push({
        id: `${row.column}-${index}`,
        title: `${row.column}: Volatility Driver`,
        signal: `${row.column} shows high movement (std ${formatNumber(row.std)}, range ${formatNumber(row.range)}).`,
        analysisAction: `Run distribution diagnostics, outlier checks, and segmented variance analysis on ${row.column}.`,
        businessImpact: "Supports risk control, threshold setting, and faster detection of unstable operating conditions.",
      })
    } else if (variability >= 0.3) {
      insights.push({
        id: `${row.column}-${index}`,
        title: `${row.column}: Segmentation Signal`,
        signal: `${row.column} has moderate spread (std ${formatNumber(row.std)}, range ${formatNumber(row.range)}).`,
        analysisAction: `Use ${row.column} for cohort segmentation, benchmarking, and before/after performance comparisons.`,
        businessImpact: "Enables targeted interventions and sharper prioritization across customer, team, or regional segments.",
      })
    } else {
      insights.push({
        id: `${row.column}-${index}`,
        title: `${row.column}: Baseline KPI`,
        signal: `${row.column} is relatively stable (std ${formatNumber(row.std)}).`,
        analysisAction: `Treat ${row.column} as a control metric for baseline tracking and drift monitoring.`,
        businessImpact: "Improves measurement consistency and helps separate structural change from short-term noise.",
      })
    }
  })

  const datetimeColumns = profile.datetime_columns
  if (datetimeColumns.length > 0) {
    insights.push({
      id: "time-series-opportunity",
      title: "Time-Series Opportunity",
      signal: `${datetimeColumns[0]} introduces a usable temporal axis for trend and seasonality analysis.`,
      analysisAction: `Create weekly/monthly trends and seasonal decomposition using ${datetimeColumns[0]}.`,
      businessImpact: "Improves planning precision for demand, staffing, budget pacing, and operational timing.",
    })
  }

  const metricCount = Object.values(profile.column_roles).filter((role) => role === "NUMERIC_METRIC").length
  if (metricCount >= 3) {
    insights.push({
      id: "cross-metric-driver",
      title: "Cross-Metric Driver Discovery",
      signal: `Detected ${metricCount} metric columns, allowing multivariate driver analysis.`,
      analysisAction: "Prioritize correlation heatmaps and grouped comparisons across the top-variance metrics.",
      businessImpact: "Helps identify the few controllable levers most likely to move strategic KPIs.",
    })
  }

  return insights.slice(0, 5)
}

function buildAdvancedHighlights(profile: DatasetProfile | null): string[] {
  if (!profile) return []

  const metricColumns = Object.entries(profile.column_roles)
    .filter(([, role]) => role === "NUMERIC_METRIC")
    .map(([column]) => column)
  const identifierColumns = Object.entries(profile.column_roles)
    .filter(([, role]) => role === "IDENTIFIER")
    .map(([column]) => column)
  const highSignalMetrics = metricColumns
    .map((column) => {
      const summary = profile.column_summary[column] ?? {}
      const std = toNumber(summary.std)
      const min = toNumber(summary.min)
      const max = toNumber(summary.max)
      const range = min !== null && max !== null ? max - min : null
      return { column, std, range }
    })
    .filter((item) => item.std !== null || item.range !== null)
    .sort((a, b) => (b.std ?? b.range ?? 0) - (a.std ?? a.range ?? 0))
    .slice(0, 4)

  const usefulDimensions = profile.categorical_columns
    .map((column) => {
      const summary = profile.column_summary[column] ?? {}
      const uniqueCount = toNumber(summary.unique_count)
      return { column, uniqueCount }
    })
    .filter((item) => item.uniqueCount !== null && item.uniqueCount >= 2 && item.uniqueCount <= 30)
    .slice(0, 4)

  const highlights: string[] = []
  highlights.push(
    `Core shape: ${profile.total_rows.toLocaleString()} rows x ${profile.total_columns} columns with ${metricColumns.length} metric feature(s).`
  )
  if (highSignalMetrics.length > 0) {
    const text = highSignalMetrics
      .map((item) => {
        const stdText = item.std !== null ? `std ${item.std.toFixed(2)}` : "std n/a"
        const rangeText = item.range !== null ? `range ${item.range.toFixed(2)}` : "range n/a"
        return `${item.column} (${stdText}, ${rangeText})`
      })
      .join(", ")
    highlights.push(`Highest variability metric features: ${text}.`)
  }
  if (usefulDimensions.length > 0) {
    highlights.push(
      `Best segmentation dimensions (balanced cardinality): ${usefulDimensions
        .map((item) => `${item.column} (${item.uniqueCount} levels)`)
        .join(", ")}.`
    )
  }
  if (identifierColumns.length > 0) {
    highlights.push(`Identifier features detected: ${identifierColumns.slice(0, 6).join(", ")}.`)
  }
  if (profile.datetime_columns.length > 0) {
    highlights.push(`Time-aware analysis is possible via: ${profile.datetime_columns.slice(0, 3).join(", ")}.`)
  }
  return highlights
}

export default function DatasetIntelligencePanel({
  domainClassification,
  datasetProfile,
  report,
  missingValueSolutions,
  lastMissingTreatmentResult,
  applyingSolutionId,
  onApplyMissingValueSolution,
}: DatasetIntelligencePanelProps) {
  if (!report) return null
  const [forceShowStats, setForceShowStats] = useState(false)

  const confidencePct = Math.max(0, Math.min(100, Math.round((domainClassification?.confidence ?? 0) * 100)))
  const missingColumns: MissingItem[] = datasetProfile
    ? Object.entries(datasetProfile.missing_percentage)
        .filter(([, pct]) => pct > 0)
        .map(([column, pct]) => ({ column, pct }))
        .sort((a, b) => b.pct - a.pct)
        .slice(0, 10)
    : []
  const maxMissing = Math.max(...missingColumns.map((item) => item.pct), 1)
  const advancedHighlights = buildAdvancedHighlights(datasetProfile)
  const metricRows = buildMetricRows(datasetProfile)
  const maxVariability = Math.max(...metricRows.map((item) => item.variabilityScore ?? 0), 0.0001)
  const actionableInsights = buildActionableInsights(datasetProfile, metricRows)
  const hasMissingValues = missingColumns.length > 0
  const showStatisticalSummary = !hasMissingValues || forceShowStats

  useEffect(() => {
    if (!hasMissingValues) {
      setForceShowStats(false)
    }
  }, [hasMissingValues])

  return (
    <section className="mb-4 animate-[fadeIn_320ms_ease-out] rounded-3xl border border-white/20 bg-white/80 p-5 shadow-xl shadow-slate-900/5 backdrop-blur dark:border-slate-700/60 dark:bg-slate-900/60 dark:shadow-black/20">
      <div className="rounded-2xl bg-gradient-to-r from-indigo-600 via-indigo-500 to-teal-500 p-4 text-white">
        <div className="flex items-center gap-2 text-xs uppercase tracking-[0.2em]">
          <Sparkles size={14} />
          Dataset Intelligence Summary
        </div>
        <p className="mt-2 text-sm text-indigo-100">
          {domainClassification
            ? `Domain hypothesis: ${domainClassification.domain_label}`
            : "Domain signal loading..."}
        </p>
        <div className="mt-3 h-2 w-full rounded-full bg-indigo-300/40">
          <div className="h-2 rounded-full bg-white/90 transition-all" style={{ width: `${confidencePct}%` }} />
        </div>
        <p className="mt-2 text-xs text-indigo-100">Domain confidence: {confidencePct}%</p>
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.35fr_1fr]">
        <div className="space-y-4">
          <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
            <h4 className="flex items-center gap-2 text-sm font-semibold">
              <HeartPulse size={16} className="text-teal-500" />
              Data Health
            </h4>
            <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{report.data_health_assessment}</p>

          {missingColumns.length > 0 ? (
            <div className="mt-4 space-y-3">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Missing Value Distribution</p>
              {missingColumns.map((item) => (
                <div key={item.column}>
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="truncate pr-2 text-slate-600 dark:text-slate-300">{item.column}</span>
                    <span className="font-semibold text-rose-600 dark:text-rose-300">{item.pct.toFixed(2)}%</span>
                  </div>
                  <div className="h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                    <div
                      className="h-2 rounded-full bg-gradient-to-r from-amber-400 to-rose-500 transition-all"
                      style={{ width: `${Math.max((item.pct / maxMissing) * 100, 6)}%` }}
                    />
                  </div>
                </div>
              ))}
              <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800/50">
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                  Missing-Value Solutions (Executable)
                </p>
                <div className="mt-2 grid gap-2">
                  {missingValueSolutions.map((solution) => (
                    <button
                      key={solution.solution_id}
                      type="button"
                      disabled={applyingSolutionId !== null}
                      onClick={() => onApplyMissingValueSolution?.(solution.solution_id)}
                      className="rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-left transition hover:bg-indigo-100 disabled:cursor-not-allowed disabled:opacity-60 dark:border-indigo-900 dark:bg-indigo-950/30 dark:hover:bg-indigo-950/50"
                    >
                      <p className="text-sm font-semibold text-indigo-900 dark:text-indigo-200">
                        {solution.title}
                        {applyingSolutionId === solution.solution_id ? " (Applying...)" : ""}
                      </p>
                      <p className="mt-1 text-xs text-indigo-700 dark:text-indigo-300">{solution.description}</p>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="mt-4 rounded-xl bg-emerald-50 px-3 py-2 text-sm text-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300">
              No missing values detected across profiled columns.
            </p>
          )}

          {lastMissingTreatmentResult && (
            <div className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 p-3 dark:border-emerald-900 dark:bg-emerald-950/30">
              <p className="text-sm font-semibold text-emerald-800 dark:text-emerald-200">Latest Treatment Result</p>
              <p className="mt-1 text-xs text-emerald-700 dark:text-emerald-300">
                {lastMissingTreatmentResult.summary}
              </p>
              <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                <span>Missing Before: {lastMissingTreatmentResult.missing_before}</span>
                <span>Missing After: {lastMissingTreatmentResult.missing_after}</span>
                <span>Rows Before: {lastMissingTreatmentResult.rows_before}</span>
                <span>Rows After: {lastMissingTreatmentResult.rows_after}</span>
              </div>
            </div>
          )}

          </article>

          {showStatisticalSummary ? (
            <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
              <h4 className="flex items-center gap-2 text-sm font-semibold">
                <BarChart3 size={16} className="text-indigo-500" />
                Statistical Summary
              </h4>
            {hasMissingValues && forceShowStats && (
              <p className="mt-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
                Showing statistics with remaining missing values. Results may be biased.
              </p>
            )}
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {[...advancedHighlights, ...report.statistical_highlights]
                .filter((item, index, arr) => arr.indexOf(item) === index)
                .slice(0, 6)
                .map((highlight, index) => (
                  <div key={`${highlight}-${index}`} className="rounded-xl bg-indigo-50 px-3 py-2 text-sm leading-relaxed text-indigo-900 dark:bg-indigo-950/50 dark:text-indigo-200">
                    {highlight}
                  </div>
                ))}
            </div>

            <div className="mt-4 rounded-xl border border-teal-200 bg-teal-50 p-3 dark:border-teal-900 dark:bg-teal-950/30">
              <p className="text-xs font-semibold uppercase tracking-wide text-teal-700 dark:text-teal-300">
                Actionable Analysis Insights
              </p>
              <div className="mt-3 grid gap-3 md:grid-cols-2">
                {actionableInsights.map((insight) => (
                  <article
                    key={insight.id}
                    className="rounded-xl border border-teal-200/80 bg-white/90 p-3 shadow-sm dark:border-teal-900/50 dark:bg-slate-900/50"
                  >
                    <p className="text-sm font-semibold text-teal-800 dark:text-teal-200">{insight.title}</p>
                    <p className="mt-2 text-xs text-slate-700 dark:text-slate-300">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">Signal:</span> {insight.signal}
                    </p>
                    <p className="mt-1 text-xs text-slate-700 dark:text-slate-300">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">Recommended analysis:</span>{" "}
                      {insight.analysisAction}
                    </p>
                    <p className="mt-1 text-xs text-slate-700 dark:text-slate-300">
                      <span className="font-semibold text-slate-900 dark:text-slate-100">Business impact:</span>{" "}
                      {insight.businessImpact}
                    </p>
                  </article>
                ))}
              </div>
              <p className="mt-3 rounded-lg bg-white/70 px-2 py-2 text-xs text-teal-900 dark:bg-slate-900/40 dark:text-teal-100">
                These insights prioritize the smallest set of high-leverage analyses likely to create measurable KPI movement.
              </p>
            </div>
          </article>
          ) : (
            <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
              <h4 className="flex items-center gap-2 text-sm font-semibold">
                <BarChart3 size={16} className="text-indigo-500" />
                Statistical Summary
              </h4>
              <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">
                Statistical summary is locked until missing values are treated to avoid misleading signals.
              </p>
              <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
                Apply a missing-value solution from Data Health. It will auto-unlock when missing values are cleaned.
              </p>
              <button
                type="button"
                onClick={() => setForceShowStats(true)}
                className="mt-3 rounded-xl border border-indigo-200 bg-indigo-50 px-3 py-2 text-xs font-semibold text-indigo-700 transition hover:bg-indigo-100 dark:border-indigo-900 dark:bg-indigo-950/40 dark:text-indigo-300 dark:hover:bg-indigo-950/60"
              >
                Generate Statistics Anyway
              </button>
            </article>
          )}
        </div>

        <div className="space-y-4">
          <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
            <h4 className="flex items-center gap-2 text-sm font-semibold">
              <BarChart3 size={16} className="text-indigo-500" />
              Quick Snapshot
            </h4>
            <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
              <div className="rounded-lg bg-slate-100 px-3 py-2 dark:bg-slate-800/80">
                <p className="text-slate-500">Rows</p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {datasetProfile?.total_rows?.toLocaleString?.() ?? "N/A"}
                </p>
              </div>
              <div className="rounded-lg bg-slate-100 px-3 py-2 dark:bg-slate-800/80">
                <p className="text-slate-500">Columns</p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {datasetProfile?.total_columns ?? "N/A"}
                </p>
              </div>
              <div className="rounded-lg bg-slate-100 px-3 py-2 dark:bg-slate-800/80">
                <p className="text-slate-500">Metrics</p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">
                  {Object.values(datasetProfile?.column_roles ?? {}).filter((role) => role === "NUMERIC_METRIC").length}
                </p>
              </div>
              <div className="rounded-lg bg-slate-100 px-3 py-2 dark:bg-slate-800/80">
                <p className="text-slate-500">Missing Cols</p>
                <p className="text-sm font-semibold text-slate-800 dark:text-slate-100">{missingColumns.length}</p>
              </div>
            </div>
          </article>

          <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
            <h4 className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle size={16} className="text-amber-500" />
              Anomaly Indicators
            </h4>
            <div className="mt-3 flex flex-wrap gap-2">
              {report.anomaly_indicators.length ? (
                report.anomaly_indicators.map((signal, index) => (
                  <span
                    key={`${signal}-${index}`}
                    className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-300"
                  >
                    {signal}
                  </span>
                ))
              ) : (
                <span className="text-sm text-slate-500 dark:text-slate-400">No anomaly indicators available.</span>
              )}
            </div>
          </article>

          {(report.important_features.length > 0 || report.useful_statistics.length > 0) && (
            <article className="rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
              <h4 className="flex items-center gap-2 text-sm font-semibold">
                <Lightbulb size={16} className="text-teal-500" />
                Analysis Readiness (Post-Cleaning)
              </h4>
              {report.important_features.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Important Features
                  </p>
                  <div className="mt-2 flex flex-wrap gap-2">
                    {report.important_features.map((feature) => (
                      <span
                        key={feature}
                        className="rounded-full border border-teal-200 bg-teal-50 px-2 py-1 text-xs font-medium text-teal-800 dark:border-teal-900 dark:bg-teal-950/30 dark:text-teal-300"
                      >
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              )}
              {report.useful_statistics.length > 0 && (
                <div className="mt-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Useful Statistics
                  </p>
                  <div className="mt-2 space-y-1">
                    {report.useful_statistics.map((item) => (
                      <p key={item} className="text-xs text-slate-700 dark:text-slate-300">
                        - {item}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </article>
          )}

        </div>
      </div>

      {showStatisticalSummary && (
        <article className="mt-4 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm dark:border-slate-700 dark:bg-slate-900/80">
          <div className="mb-2 flex items-center gap-2">
            <Table2 size={14} className="text-indigo-500" />
            <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
              Metric Variability Table
            </p>
          </div>
          {metricRows.length > 0 ? (
            <div className="grid gap-2 md:grid-cols-2">
              {metricRows.slice(0, 8).map((row) => {
                const score = row.variabilityScore
                const width = `${Math.max(6, ((score ?? 0) / maxVariability) * 100)}%`
                const badge = interpretationBadge(score)
                return (
                  <div key={row.column} className="rounded-lg border border-slate-200 p-2 dark:border-slate-700">
                    <div className="flex items-center justify-between gap-2">
                      <p className="text-sm font-semibold">{row.column}</p>
                      <span className={`rounded-full px-2 py-1 text-[11px] font-semibold ${badge.className}`}>
                        {badge.label}
                      </span>
                    </div>
                    <div className="mt-2 h-2 rounded-full bg-slate-200 dark:bg-slate-700">
                      <div className="h-2 rounded-full bg-gradient-to-r from-indigo-500 to-teal-500" style={{ width }} />
                    </div>
                    <div className="mt-2 grid grid-cols-2 gap-2 text-[11px] md:grid-cols-4">
                      <span>Mean: {formatNumber(row.mean)}</span>
                      <span>Std: {formatNumber(row.std)}</span>
                      <span>Range: {formatNumber(row.range)}</span>
                      <span>Score: {formatNumber(row.variabilityScore, 3)}</span>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <p className="text-xs text-slate-500 dark:text-slate-400">No numeric metric columns available for variability analysis.</p>
          )}
        </article>
      )}

    </section>
  )
}
