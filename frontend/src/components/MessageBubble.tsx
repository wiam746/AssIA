import { useState } from "react";
import type { Message } from "@/types";
import { User, Bot, Copy, Check } from "lucide-react";

export default function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback si navigator.clipboard est restreint
      const textarea = document.createElement("textarea");
      textarea.value = message.content;
      document.body.appendChild(textarea);
      textarea.select();
      document.execCommand("copy");
      document.body.removeChild(textarea);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }

  return (
    <div className={`group relative flex items-start gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
          isUser
            ? "bg-slate-900 text-white"
            : "bg-emerald-600 text-white shadow-sm"
        }`}
      >
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      
      <div className="relative max-w-[75%]">
        <div
          className={`rounded-2xl px-4 py-3 text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? "bg-emerald-600 text-white shadow-sm rounded-tr-none"
              : "bg-white text-slate-800 border border-slate-200/80 shadow-sm rounded-tl-none pr-9"
          }`}
        >
          {message.content}
        </div>

        {/* Bouton Copier */}
        <button
          onClick={handleCopy}
          title={copied ? "Copié !" : "Copier la réponse"}
          className={`absolute top-2.5 right-2.5 flex h-7 w-7 items-center justify-center rounded-lg transition-all duration-200 ${
            isUser
              ? "opacity-0 group-hover:opacity-100 text-white/80 hover:bg-white/20 hover:text-white"
              : "opacity-0 group-hover:opacity-100 bg-slate-50 text-slate-400 hover:bg-slate-100 hover:text-slate-700 border border-slate-200/60"
          } ${copied ? "!opacity-100 bg-emerald-50 text-emerald-600 border-emerald-200" : ""}`}
        >
          {copied ? (
            <Check size={14} className="text-emerald-600 animate-in zoom-in-50" />
          ) : (
            <Copy size={14} />
          )}
        </button>
      </div>
    </div>
  );
}