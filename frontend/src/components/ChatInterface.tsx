import { useEffect, useMemo, useRef, useState } from "react"
import { Send } from "lucide-react"
import { applyMissingValueSolution, confirmTarget, sendChatMessage } from "../api/client"
import { useSession } from "../context/SessionContext"
import DatasetIntelligencePanel from "./DatasetIntelligencePanel"
import MessageBubble from "./MessageBubble"

function formatMetric(value?: number | null, digits = 3): string {
  if (value === undefined || value === null || Number.isNaN(value)) return "-"
  return value.toFixed(digits)
}

export default function ChatInterface() {
  const {
    sessionId,
    currentPhase,
    conversationHistory,
    parsedIntent,
    targetColumn,
    targetType,
    rankedDrivers,
    finalAnswer,
    setChatState,
    setMissingTreatmentState,
    setErrors,
    domainClassification,
    datasetProfile,
    datasetSummaryReport,
    missingValueSolutions,
    lastMissingTreatmentResult,
  } = useSession()

  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [typing, setTyping] = useState(false)
  const [applyingSolutionId, setApplyingSolutionId] = useState<string | null>(null)
  const [selectedTarget, setSelectedTarget] = useState<string>("")
  const [intentWorkspaceOpen, setIntentWorkspaceOpen] = useState(false)
  const endRef = useRef<HTMLDivElement | null>(null)

  const candidateTargets = useMemo(() => parsedIntent?.target_candidates ?? [], [parsedIntent])

  useEffect(() => {
    if (candidateTargets.length > 0 && !selectedTarget) {
      setSelectedTarget(candidateTargets[0])
    }
  }, [candidateTargets, selectedTarget])

  useEffect(() => {
    if (currentPhase !== "WAITING_FOR_INTENT") {
      setIntentWorkspaceOpen(true)
    }
  }, [currentPhase])

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [conversationHistory, loading, typing])

  const submitMessage = async (messageOverride?: string) => {
    const msg = (messageOverride ?? input).trim()
    if (!sessionId || !msg) return

    setLoading(true)
    setTyping(true)
    setError(null)
    try {
      const response = await sendChatMessage(sessionId, msg)
      setChatState({
        phase: response.phase,
        conversationHistory: response.conversation_history,
        parsedIntent: response.parsed_intent ?? null,
        targetColumn: response.target_column ?? null,
        targetType: response.target_type ?? null,
        generatedHypotheses: response.generated_hypotheses ?? null,
        statisticalResults: response.statistical_results ?? null,
        rankedDrivers: response.ranked_drivers ?? null,
        finalAnswer: response.final_answer ?? null,
        intentClassification: response.intent_classification ?? null,
        analysisPlan: response.analysis_plan ?? null,
      })
      setErrors([])
      setInput("")
    } catch (err) {
      const message = err instanceof Error ? err.message : "Chat request failed"
      setError(message)
      setErrors([message])
    } finally {
      setTyping(false)
      setLoading(false)
    }
  }

  const submitTargetConfirmation = async () => {
    if (!sessionId || !selectedTarget) return
    setLoading(true)
    setError(null)
    try {
      const response = await confirmTarget(sessionId, selectedTarget)
      setChatState({
        phase: response.phase,
        conversationHistory: response.conversation_history,
        parsedIntent: response.parsed_intent ?? null,
        targetColumn: response.target_column ?? null,
        targetType: response.target_type ?? null,
        generatedHypotheses: response.generated_hypotheses ?? null,
        statisticalResults: response.statistical_results ?? null,
        rankedDrivers: response.ranked_drivers ?? null,
        finalAnswer: response.final_answer ?? null,
        intentClassification: null,
        analysisPlan: null,
      })
      setErrors([])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Target confirmation failed"
      setError(message)
      setErrors([message])
    } finally {
      setLoading(false)
    }
  }

  const applySolution = async (solutionId: string) => {
    if (!sessionId) return
    setApplyingSolutionId(solutionId)
    setError(null)
    try {
      const response = await applyMissingValueSolution(sessionId, solutionId)
      setMissingTreatmentState({
        phase: response.phase,
        datasetProfile: response.dataset_profile ?? null,
        datasetSummaryReport: response.dataset_summary_report ?? null,
        missingValueSolutions: response.missing_value_solutions ?? [],
        lastMissingTreatmentResult: response.last_missing_treatment_result ?? null,
      })
      setErrors([])
    } catch (err) {
      const message = err instanceof Error ? err.message : "Missing-value treatment failed"
      setError(message)
      setErrors([message])
    } finally {
      setApplyingSolutionId(null)
    }
  }

  const showIntelligencePanel = !!datasetSummaryReport

  return (
    <div>
      {showIntelligencePanel && !intentWorkspaceOpen && (
        <DatasetIntelligencePanel
          domainClassification={domainClassification}
          datasetProfile={datasetProfile}
          report={datasetSummaryReport}
          missingValueSolutions={missingValueSolutions}
          lastMissingTreatmentResult={lastMissingTreatmentResult}
          applyingSolutionId={applyingSolutionId}
          onApplyMissingValueSolution={applySolution}
        />
      )}

      {!intentWorkspaceOpen && (
        <section className="mb-4 rounded-3xl border border-indigo-200 bg-white p-5 shadow-sm dark:border-indigo-900 dark:bg-slate-900">
          <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Ready for Goal-Driven Investigation</h3>
          <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">
            Dataset intelligence is prepared. Continue to the intent workspace and ask any analysis question.
          </p>
          <button
            type="button"
            onClick={() => setIntentWorkspaceOpen(true)}
            className="mt-4 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500"
          >
            Continue to Intent Workspace
          </button>
        </section>
      )}

      {intentWorkspaceOpen && currentPhase === "ANSWER_READY" && finalAnswer && (
        <section className="mb-4 rounded-3xl border border-indigo-200 bg-white p-5 shadow-sm dark:border-indigo-900 dark:bg-slate-900">
          <h3 className="text-xl font-semibold text-slate-900 dark:text-slate-100">AI Strategy Report</h3>
          <article className="mt-3 rounded-2xl bg-indigo-50 p-4 dark:bg-indigo-950/40">
            <p className="text-xs font-semibold uppercase tracking-wide text-indigo-700 dark:text-indigo-300">Direct Answer</p>
            <p className="mt-1 text-sm text-indigo-950 dark:text-indigo-100">{finalAnswer.direct_answer}</p>
            <p className="mt-2 text-xs text-indigo-700 dark:text-indigo-300">Confidence: {(finalAnswer.confidence_score * 100).toFixed(0)}%</p>
          </article>

          <div className="mt-4 overflow-hidden rounded-2xl border border-slate-200 dark:border-slate-700">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-100 text-xs uppercase tracking-wide text-slate-600 dark:bg-slate-800 dark:text-slate-300">
                <tr>
                  <th className="px-3 py-2">Feature</th>
                  <th className="px-3 py-2">Strength</th>
                  <th className="px-3 py-2">P-value</th>
                  <th className="px-3 py-2">Effect size</th>
                  <th className="px-3 py-2">Importance</th>
                </tr>
              </thead>
              <tbody>
                {(rankedDrivers ?? []).slice(0, 8).map((driver) => (
                  <tr key={driver.feature} className="border-t border-slate-200 dark:border-slate-700">
                    <td className="px-3 py-2 font-medium text-slate-900 dark:text-slate-100">{driver.feature}</td>
                    <td className="px-3 py-2">{formatMetric(driver.strength_score, 2)}</td>
                    <td className="px-3 py-2">{formatMetric(driver.p_value, 4)}</td>
                    <td className="px-3 py-2">{formatMetric(driver.effect_size, 3)}</td>
                    <td className="px-3 py-2">{formatMetric(driver.feature_importance, 3)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <article className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Evidence Points</p>
              <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-slate-700 dark:text-slate-300">
                {finalAnswer.evidence_points.map((point) => (
                  <li key={point}>{point}</li>
                ))}
              </ul>
            </article>
            <article className="rounded-2xl border border-slate-200 p-4 dark:border-slate-700">
              <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">Business Impact</p>
              <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{finalAnswer.business_impact}</p>
              <p className="mt-3 text-xs font-semibold uppercase tracking-wide text-slate-500">Recommended Next Step</p>
              <p className="mt-1 text-sm text-slate-700 dark:text-slate-300">{finalAnswer.recommended_next_step}</p>
            </article>
          </div>

          <p className="mt-3 text-xs text-slate-500 dark:text-slate-400">
            Target analyzed: <span className="font-semibold">{targetColumn ?? "N/A"}</span> ({targetType ?? "N/A"})
          </p>
        </section>
      )}

      {intentWorkspaceOpen && currentPhase === "TARGET_VALIDATION_REQUIRED" && candidateTargets.length > 0 && (
        <section className="mb-4 rounded-3xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-900 dark:bg-amber-950/30">
          <p className="text-sm font-semibold text-amber-900 dark:text-amber-200">Target Validation Required</p>
          <p className="mt-1 text-xs text-amber-800 dark:text-amber-300">
            Multiple target candidates were detected. Select one to continue the driver investigation.
          </p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <select
              value={selectedTarget}
              onChange={(event) => setSelectedTarget(event.target.value)}
              className="min-w-[260px] rounded-xl border border-amber-300 bg-white px-3 py-2 text-sm dark:border-amber-800 dark:bg-slate-900"
            >
              {candidateTargets.map((target) => (
                <option key={target} value={target}>{target}</option>
              ))}
            </select>
            <button
              type="button"
              onClick={submitTargetConfirmation}
              disabled={loading || !selectedTarget}
              className="rounded-xl bg-amber-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-amber-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Confirm Target
            </button>
          </div>
        </section>
      )}

      {intentWorkspaceOpen && (
      <section className="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <div className="flex items-center justify-between gap-3">
            <h3 className="text-lg font-semibold">Intent Workspace</h3>
            <button
              type="button"
              onClick={() => setIntentWorkspaceOpen(false)}
              className="rounded-xl border border-slate-300 px-3 py-1.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Back to Dataset Summary
            </button>
          </div>
        </div>

        <div className="h-[420px] space-y-3 overflow-y-auto px-5 py-4">
          {conversationHistory.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Start by describing your analysis question.</p>
          )}
          {conversationHistory.map((message, idx) => (
            <MessageBubble key={`${message.timestamp}-${idx}`} message={message} />
          ))}
          {typing && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-slate-100 px-4 py-2 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                Assistant is analyzing...
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        <div className="border-t border-slate-200 px-5 py-3 dark:border-slate-800">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
              placeholder={currentPhase === "TARGET_VALIDATION_REQUIRED" ? "Target confirmation is required above." : "Ask your investigation question..."}
              disabled={currentPhase === "TARGET_VALIDATION_REQUIRED"}
            />
            <button
              type="button"
              onClick={() => submitMessage()}
              disabled={loading || !input.trim() || currentPhase === "TARGET_VALIDATION_REQUIRED"}
              className="rounded-xl bg-indigo-600 px-3 py-3 text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Send size={16} />
            </button>
          </div>
          {error && (
            <div className="mt-2 rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
              {error}
            </div>
          )}
        </div>
      </section>
      )}
    </div>
  )
}
