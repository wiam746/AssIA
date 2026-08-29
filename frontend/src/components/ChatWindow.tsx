import { useState, FormEvent, useRef, useEffect } from "react";
import { Send, Bot, Sparkles, Paperclip, Loader2, AlertCircle, FileText, X } from "lucide-react";
import MessageBubble from "./MessageBubble";
import type { Message } from "@/types";
import api from "@/hooks/useApi";

interface IndexedFile {
  id: string;
  docId?: string;
  name: string;
  type: string;
}

interface ChatWindowProps {
  messages: Message[];
  sending: boolean;
  onSend: (text: string, documentIds?: string[]) => void;
}

export default function ChatWindow({ messages, sending, onSend }: ChatWindowProps) {
  const [input, setInput] = useState("");
  const [uploading, setUploading] = useState(false);
  const [indexedFiles, setIndexedFiles] = useState<IndexedFile[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  
  const bottomRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!input.trim() || sending) return;
    const docIds = indexedFiles.map((f) => f.docId).filter((id): id is string => Boolean(id));
    onSend(input.trim(), docIds.length > 0 ? docIds : undefined);
    setInput("");
  }

  async function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const docId = res.data?.document?.id;
      const filename = res.data?.document?.original_filename || file.name;
      const ext = filename.split(".").pop()?.toUpperCase() || "DOC";
      setIndexedFiles((prev) => [
        ...prev,
        { id: `${Date.now()}`, docId, name: filename, type: ext },
      ]);
    } catch {
      setUploadError("Échec de l'upload du document. Vérifiez le format (PDF, DOCX, TXT, MD).");
      setTimeout(() => setUploadError(null), 6000);
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  return (
    <div className="flex h-full flex-col bg-slate-50">
      {/* Header Bar */}
      <div className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-4 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-emerald-100 text-emerald-700">
            <Bot size={20} />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-900">Votre Assistant IA Professionnel</h2>
            <p className="text-xs text-slate-500">Posez vos questions sur les réunions, projets et incidents</p>
          </div>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {messages.length === 0 && indexedFiles.length === 0 && (
          <div className="flex h-full flex-col items-center justify-center text-center p-8">
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-100 text-emerald-700 mb-4 shadow-sm">
              <Bot size={28} />
            </div>
            <h3 className="text-base font-bold text-slate-800">Comment puis-je vous aider aujourd'hui ?</h3>
            <p className="mt-1 text-xs text-slate-500 max-w-md">
              Vous pouvez me demander un résumé de la dernière réunion, rechercher un projet spécifique ou uploader un document ci-dessous pour l'analyser.
            </p>
          </div>
        )}

        {/* Indexed File Cards — persistent in discussion */}
        {indexedFiles.map((f) => (
          <div
            key={f.id}
            className="flex items-center gap-3 w-fit max-w-xs rounded-2xl border border-slate-200 bg-white px-4 py-3 shadow-sm"
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-100">
              <FileText size={20} className="text-red-600" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-semibold text-slate-800" title={f.name}>
                {f.name}
              </p>
              <p className="text-xs text-slate-400">{f.type}</p>
            </div>
            <button
              onClick={() => setIndexedFiles((prev) => prev.filter((x) => x.id !== f.id))}
              className="ml-1 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
              title="Retirer"
            >
              <X size={13} />
            </button>
          </div>
        ))}

        {messages.map((m) => (
          <MessageBubble key={m.id} message={m} />
        ))}
        {sending && (
          <div className="flex items-center gap-2 text-xs font-medium text-emerald-700 bg-emerald-50 w-fit px-3 py-2 rounded-lg border border-emerald-200">
            <Sparkles size={14} className="animate-spin" />
            L'assistant analyse vos données et rédige une réponse...
          </div>
        )}
        <div ref={bottomRef} />
      </div>


      {uploadError && (
        <div className="mx-4 mb-2 flex items-center justify-between rounded-xl border border-red-200 bg-red-50 p-3 text-xs text-red-700 shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{uploadError}</span>
          </div>
          <button onClick={() => setUploadError(null)} className="text-red-700 hover:text-red-900 font-bold ml-2">×</button>
        </div>
      )}

      {/* Input Form */}
      <div className="border-t border-slate-200 bg-white p-4 shadow-md">
        <form onSubmit={handleSubmit} className="flex items-center gap-2 max-w-4xl mx-auto">
          {/* File Upload Button */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx,.txt,.md"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploading}
            title="Uploader un fichier (PDF, DOCX, TXT, MD)"
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-slate-300 bg-slate-50 text-slate-600 transition hover:bg-slate-100 hover:text-emerald-700 active:bg-slate-200 disabled:opacity-50"
          >
            {uploading ? (
              <Loader2 size={18} className="animate-spin text-emerald-600" />
            ) : (
              <Paperclip size={18} />
            )}
          </button>

          {/* Message Input */}
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Posez votre question ou uploadez un fichier..."
            className="flex-1 rounded-xl border border-slate-300 bg-slate-50 px-4 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition"
          />

          {/* Send Button */}
          <button
            type="submit"
            disabled={sending || !input.trim()}
            className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-emerald-600 text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send size={16} />
          </button>
        </form>
      </div>
    </div>
  );
}