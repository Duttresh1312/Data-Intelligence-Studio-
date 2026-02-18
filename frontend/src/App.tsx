import { useEffect, useState } from "react"
import { Moon, Sun } from "lucide-react"
import ChatInterface from "./components/ChatInterface"
import DatasetSummary from "./components/DatasetSummary"
import LandingPage from "./components/LandingPage"
import { SessionProvider, useSession } from "./context/SessionContext"
import "./index.css"

function ThemeToggle() {
  const [isDark, setIsDark] = useState<boolean>(() => localStorage.getItem("studio_theme") === "dark")

  useEffect(() => {
    const root = document.documentElement
    if (isDark) root.classList.add("dark")
    else root.classList.remove("dark")
    localStorage.setItem("studio_theme", isDark ? "dark" : "light")
  }, [isDark])

  return (
    <button
      type="button"
      onClick={() => setIsDark((value) => !value)}
      className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
    >
      {isDark ? <Sun size={16} /> : <Moon size={16} />}
      {isDark ? "Light" : "Dark"}
    </button>
  )
}

function PhaseContent() {
  const { currentPhase } = useSession()

  switch (currentPhase) {
    case "LANDING":
    case "DATA_UPLOADED":
      return <LandingPage />
    case "PROFILE_READY":
      return <DatasetSummary />
    case "WAITING_FOR_INTENT":
    case "INTENT_PARSED":
    case "TARGET_VALIDATION_REQUIRED":
    case "INVESTIGATING":
    case "DRIVER_RANKED":
    case "ANSWER_READY":
    case "PLAN_READY":
    case "EXECUTING":
    case "COMPLETED":
      return <ChatInterface />
    default:
      return <LandingPage />
  }
}

function Shell() {
  const { currentPhase, sessionId, goBackPhase, clearSession } = useSession()
  const canGoBack = currentPhase !== "LANDING"
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-slate-100 to-indigo-50 text-slate-900 transition-colors dark:from-slate-950 dark:via-slate-900 dark:to-slate-950 dark:text-slate-100">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/70">
        <div className="mx-auto flex w-full max-w-7xl items-center justify-between px-4 py-3 md:px-6">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-teal-600 dark:text-teal-400">Agentic Data Intelligence Studio</p>
            <h1 className="text-xl font-semibold tracking-tight md:text-2xl">Progressive Conversational Flow</h1>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Phase: {currentPhase} {sessionId ? `| Session: ${sessionId.slice(0, 12)}...` : ""}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={goBackPhase}
              disabled={!canGoBack}
              className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-200 dark:hover:bg-slate-800"
            >
              Back
            </button>
            <button
              type="button"
              onClick={clearSession}
              className="rounded-xl bg-rose-600 px-3 py-2 text-sm font-semibold text-white transition hover:bg-rose-500"
            >
              Start Over
            </button>
            <ThemeToggle />
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-7xl px-4 py-6 md:px-6">
        <PhaseContent />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <SessionProvider>
      <Shell />
    </SessionProvider>
  )
}
