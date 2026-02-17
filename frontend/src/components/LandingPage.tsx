import { useState } from "react"
import { UploadCloud } from "lucide-react"
import { uploadDataset } from "../api/client"
import { useSession } from "../context/SessionContext"

const ACCEPTED_TYPES = ".csv,.xlsx,.xls,.html"

export default function LandingPage() {
  const { setUploadState, setErrors } = useSession()
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onUpload = async () => {
    if (!file) return
    setLoading(true)
    setError(null)
    try {
      const data = await uploadDataset(file)
      setUploadState({
        sessionId: data.session_id,
        phase: data.phase,
        datasetProfile: data.dataset_profile ?? null,
      })
      setErrors([])
      setFile(null)
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed"
      setError(message)
      setErrors([message])
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="mx-auto max-w-3xl rounded-3xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-900">
      <p className="text-xs uppercase tracking-[0.2em] text-teal-600 dark:text-teal-400">Phase-Driven Experience</p>
      <h2 className="mt-2 text-3xl font-semibold tracking-tight">Welcome to Agentic Data Intelligence Studio</h2>
      <p className="mt-3 text-sm text-slate-600 dark:text-slate-300">
        Upload your dataset to start a progressive analysis conversation.
      </p>

      <div className="mt-6 rounded-2xl border-2 border-dashed border-slate-300 bg-slate-50 p-6 text-center dark:border-slate-700 dark:bg-slate-800/50">
        <input
          id="landing-upload"
          type="file"
          className="hidden"
          accept={ACCEPTED_TYPES}
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
        <label htmlFor="landing-upload" className="cursor-pointer">
          <UploadCloud className="mx-auto mb-2 text-indigo-500" size={24} />
          <p className="text-sm font-medium">Drop file or click to browse</p>
          <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">CSV, XLSX, XLS, HTML up to 100MB</p>
        </label>
      </div>

      {file && (
        <div className="mt-4 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm dark:border-slate-700 dark:bg-slate-800">
          {file.name} ({(file.size / (1024 * 1024)).toFixed(2)} MB)
        </div>
      )}
      {error && (
        <div className="mt-4 rounded-xl border border-rose-300 bg-rose-50 px-3 py-2 text-sm text-rose-700 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-300">
          {error}
        </div>
      )}

      <button
        type="button"
        onClick={onUpload}
        disabled={!file || loading}
        className="mt-5 rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "Uploading..." : "Upload Dataset"}
      </button>
    </section>
  )
}
