import type { ConversationMessage } from "../types"

interface MessageBubbleProps {
  message: ConversationMessage
}

export default function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user"
  const isAssistant = message.role === "assistant"

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[82%] rounded-2xl px-4 py-2 text-sm shadow-sm ${
          isUser
            ? "bg-indigo-600 text-white"
            : isAssistant
              ? "bg-white text-slate-800 dark:bg-slate-800 dark:text-slate-100"
              : "bg-slate-100 text-slate-700 dark:bg-slate-700 dark:text-slate-100"
        }`}
      >
        <p className="whitespace-pre-wrap">{message.content}</p>
        <p className={`mt-1 text-[10px] ${isUser ? "text-indigo-100" : "text-slate-400"}`}>
          {new Date(message.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
        </p>
      </div>
    </div>
  )
}
