import type { AnalysisPlan } from "../types"

interface PlanPreviewCardProps {
  plan: AnalysisPlan | null
  onApprove: () => void
  onModify: () => void
  disabled?: boolean
}

export default function PlanPreviewCard({ plan, onApprove, onModify, disabled = false }: PlanPreviewCardProps) {
  return (
    <article className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <h3 className="text-lg font-semibold">Plan Preview</h3>
      {!plan ? (
        <p className="mt-2 text-sm text-slate-600 dark:text-slate-300">No plan available yet.</p>
      ) : (
        <>
          <p className="mt-2 text-sm">
            <span className="font-semibold">Intent Type:</span> {plan.intent_type}
          </p>
          <ol className="mt-3 space-y-2">
            {plan.steps.map((step, index) => (
              <li key={step.step_id} className="rounded-xl border border-slate-200 p-3 text-sm dark:border-slate-700">
                <p className="font-medium">{index + 1}. {step.description}</p>
                <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{step.operation_type}</p>
              </li>
            ))}
          </ol>
        </>
      )}

      <div className="mt-4 flex gap-2">
        <button
          type="button"
          onClick={onApprove}
          disabled={disabled || !plan}
          className="rounded-xl bg-emerald-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Approve
        </button>
        <button
          type="button"
          onClick={onModify}
          disabled={disabled}
          className="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-700 dark:text-slate-200 dark:hover:bg-slate-800"
        >
          Modify
        </button>
      </div>
    </article>
  )
}
