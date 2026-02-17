import { useEffect, useRef, useState } from "react"
import { Send } from "lucide-react"
import { applyMissingValueSolution, sendChatMessage } from "../api/client"
import { useSession } from "../context/SessionContext"
import DatasetIntelligencePanel from "./DatasetIntelligencePanel"
import MessageBubble from "./MessageBubble"

interface ChatInterfaceProps {
  onRequestModifyPlan?: () => void
}

export default function ChatInterface({ onRequestModifyPlan }: ChatInterfaceProps) {
  const {
    sessionId,
    conversationHistory,
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
  const endRef = useRef<HTMLDivElement | null>(null)

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

  const showApprovalActions = false
  const showIntelligencePanel = !!datasetSummaryReport

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

  return (
    <div>
      {showIntelligencePanel && (
        <DatasetIntelligencePanel
          domainClassification={domainClassification}
          datasetProfile={datasetProfile}
          report={datasetSummaryReport}
          missingValueSolutions={missingValueSolutions}
          lastMissingTreatmentResult={lastMissingTreatmentResult}
          applyingSolutionId={applyingSolutionId}
          onApplyMissingValueSolution={applySolution}
          onSuggestionClick={(suggestion) => setInput(suggestion)}
        />
      )}

      <section className="rounded-3xl border border-slate-200 bg-white shadow-sm dark:border-slate-800 dark:bg-slate-900">
        <div className="border-b border-slate-200 px-5 py-3 dark:border-slate-800">
          <h3 className="text-lg font-semibold">Analysis Chat</h3>
        </div>

        <div className="h-[420px] space-y-3 overflow-y-auto px-5 py-4">
          {conversationHistory.length === 0 && (
            <p className="text-sm text-slate-500 dark:text-slate-400">Start by describing your analysis goal.</p>
          )}
          {conversationHistory.map((message, idx) => (
            <MessageBubble key={`${message.timestamp}-${idx}`} message={message} />
          ))}
          {typing && (
            <div className="flex justify-start">
              <div className="rounded-2xl bg-slate-100 px-4 py-2 text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-300">
                Assistant is typing...
              </div>
            </div>
          )}
          <div ref={endRef} />
        </div>

        {showApprovalActions && (
          <div className="flex flex-wrap gap-2 border-t border-slate-200 px-5 py-3 dark:border-slate-800">
            <button
              type="button"
              onClick={() => submitMessage("approve")}
              disabled={loading}
              className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => {
                onRequestModifyPlan?.()
                setInput("Please modify the plan: ")
              }}
              disabled={loading}
              className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Modify
            </button>
          </div>
        )}

        <div className="border-t border-slate-200 px-5 py-3 dark:border-slate-800">
          <div className="flex items-end gap-2">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              className="min-h-12 w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800"
              placeholder={showApprovalActions ? "Approve or request changes..." : "Type your analysis goal..."}
            />
            <button
              type="button"
              onClick={() => submitMessage()}
              disabled={loading || !input.trim()}
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
    </div>
  )
}
