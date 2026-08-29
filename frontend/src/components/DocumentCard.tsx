import { useState, useRef } from "react";
import api from "@/hooks/useApi";
import {
  FileText, Trash2, CheckCircle2, Clock, AlertCircle, MessageSquare,
  ChevronDown, ChevronRight, PlusCircle, MessageCircle, Send, Loader2
} from "lucide-react";
import type { DocumentItem, Conversation, Message } from "@/types";

const statusLabels: Record<DocumentItem["status"], string> = {
  pending: "En attente",
  processing: "Traitement...",
  indexed: "Indexé",
  error: "Erreur",
};

const statusBadgeStyles: Record<DocumentItem["status"], { bg: string; text: string; icon: any }> = {
  pending: { bg: "bg-amber-50 border-amber-200 text-amber-700", text: "text-amber-700", icon: Clock },
  processing: { bg: "bg-blue-50 border-blue-200 text-blue-700", text: "text-blue-700", icon: Clock },
  indexed: { bg: "bg-emerald-50 border-emerald-200 text-emerald-700", text: "text-emerald-700", icon: CheckCircle2 },
  error: { bg: "bg-red-50 border-red-200 text-red-700", text: "text-red-700", icon: AlertCircle },
};

interface DocumentCardProps {
  document: DocumentItem;
  onDelete: (id: string) => void;
}

interface ChatState {
  conversationId?: string;
  messages: Message[];
  input: string;
  loading: boolean;
}

export default function DocumentCard({ document, onDelete }: DocumentCardProps) {
  const badge = statusBadgeStyles[document.status] || statusBadgeStyles.pending;
  const BadgeIcon = badge.icon;

  const [expanded, setExpanded] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loadingConvs, setLoadingConvs] = useState(false);
  const [chat, setChat] = useState<ChatState>({ messages: [], input: "", loading: false });
  const chatEndRef = useRef<HTMLDivElement | null>(null);

  function toggleChatPanel() {
    const next = !expanded;
    setExpanded(next);
    if (next) {
      loadConversations();
    }
  }

  async function loadConversations() {
    setLoadingConvs(true);
    try {
      const res = await api.get<Conversation[]>(`/documents/${document.id}/conversations`);
      setConversations(res.data);

      if (res.data.length > 0 && !chat.conversationId) {
        selectConversation(res.data[0]);
      } else if (!chat.conversationId) {
        startNewChat();
      }
    } finally {
      setLoadingConvs(false);
    }
  }

  function startNewChat() {
    setChat({ conversationId: undefined, messages: [], input: "", loading: false });
  }

  async function selectConversation(conv: Conversation) {
    try {
      const res = await api.get<Conversation>(`/chat/conversations/${conv.id}`);
      setChat({
        conversationId: res.data.id,
        messages: res.data.messages || [],
        input: "",
        loading: false,
      });
    } catch {
      setChat({
        conversationId: conv.id,
        messages: conv.messages || [],
        input: "",
        loading: false,
      });
    }
  }

  async function sendChatMessage() {
    if (!chat.input.trim() || chat.loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: chat.input.trim(),
      created_at: new Date().toISOString(),
    };

    setChat((prev) => ({
      ...prev,
      messages: [...prev.messages, userMsg],
      input: "",
      loading: true,
    }));

    try {
      const res = await api.post<{ conversation_id: string; message: Message; sources: string[] }>(
        `/documents/${document.id}/chat`,
        { message: userMsg.content, conversation_id: chat.conversationId },
      );

      setChat((prev) => ({
        ...prev,
        conversationId: res.data.conversation_id,
        messages: [...prev.messages, res.data.message],
        loading: false,
      }));

      loadConversations();

      setTimeout(() => {
        chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch {
      setChat((prev) => ({ ...prev, loading: false }));
    }
  }

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition overflow-hidden">
      {/* Main card row */}
      <div className="flex items-center justify-between p-4">
        <div className="flex items-center gap-3.5 overflow-hidden">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600 border border-emerald-100">
            <FileText size={20} />
          </div>
          <div className="overflow-hidden">
            <p className="truncate text-sm font-semibold text-slate-800">{document.original_filename}</p>
            <div className="mt-1 flex items-center gap-2">
              <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[11px] font-medium ${badge.bg}`}>
                <BadgeIcon size={12} />
                {statusLabels[document.status]}
              </span>
              {document.error_message && (
                <span className="truncate text-xs text-red-500">{document.error_message}</span>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Chat discussion button */}
          <button
            onClick={toggleChatPanel}
            className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
              expanded
                ? "bg-emerald-600 text-white border-emerald-600"
                : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
            }`}
          >
            <MessageSquare size={14} />
            <span>Discuter</span>
            {expanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          </button>

          {/* Delete button */}
          <button
            onClick={() => onDelete(document.id)}
            className="rounded-lg p-2 text-slate-400 hover:bg-red-50 hover:text-red-600 transition"
            title="Supprimer"
          >
            <Trash2 size={17} />
          </button>
        </div>
      </div>

      {/* Expandable Document Chat Panel */}
      {expanded && (
        <div className="border-t border-slate-100 bg-slate-50/60 p-5">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            
            {/* Conversations Sidebar */}
            <div className="md:col-span-1 border-b md:border-b-0 md:border-r border-slate-200 pr-0 md:pr-4 pb-4 md:pb-0 space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                  <MessageCircle size={14} className="text-emerald-600" />
                  <span>Discussions ({conversations.length})</span>
                </h4>
                <button
                  onClick={startNewChat}
                  className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-100 transition"
                  title="Démarrer une nouvelle discussion"
                >
                  <PlusCircle size={12} />
                  <span>Nouvelle</span>
                </button>
              </div>

              {loadingConvs ? (
                <div className="flex justify-center py-4">
                  <Loader2 size={16} className="animate-spin text-emerald-600" />
                </div>
              ) : conversations.length === 0 ? (
                <p className="text-xs text-slate-400 italic">Aucune discussion sur ce document.</p>
              ) : (
                <div className="space-y-1.5 max-h-60 overflow-y-auto pr-1">
                  {conversations.map((conv) => {
                    const isSelected = chat.conversationId === conv.id;
                    const dateStr = new Date(conv.updated_at).toLocaleDateString("fr-FR", {
                      day: "2-digit",
                      month: "2-digit",
                      hour: "2-digit",
                      minute: "2-digit",
                    });

                    return (
                      <button
                        key={conv.id}
                        onClick={() => selectConversation(conv)}
                        className={`w-full text-left p-2.5 rounded-xl text-xs transition flex flex-col gap-0.5 border ${
                          isSelected
                            ? "bg-emerald-50 border-emerald-300 text-emerald-900 font-semibold"
                            : "bg-white border-slate-200 text-slate-700 hover:bg-slate-100"
                        }`}
                      >
                        <span className="truncate">{conv.title || "Discussion sans titre"}</span>
                        <span className="text-[10px] text-slate-400 flex items-center gap-1">
                          <Clock size={10} /> {dateStr}
                        </span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Chat Box */}
            <div className="md:col-span-2 flex flex-col gap-3">
              <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                <span className="text-xs font-bold text-slate-800">
                  {chat.conversationId
                    ? conversations.find((c) => c.id === chat.conversationId)?.title || "Discussion courante"
                    : "Nouvelle discussion"}
                </span>
              </div>

              <div className="flex flex-col gap-2 min-h-48 max-h-64 overflow-y-auto pr-1 bg-white border border-slate-200 p-3 rounded-xl">
                {chat.messages.length === 0 && (
                  <p className="text-center text-xs text-slate-400 my-auto py-6">
                    Posez vos questions sur le contenu du document «{document.original_filename}».
                  </p>
                )}
                {chat.messages.map((msg, idx) => (
                  <div
                    key={idx}
                    className={`rounded-xl px-3 py-2 text-xs leading-relaxed whitespace-pre-wrap max-w-[88%] ${
                      msg.role === "user"
                        ? "self-end bg-emerald-600 text-white"
                        : "self-start bg-slate-100 text-slate-800"
                    }`}
                  >
                    {msg.content}
                  </div>
                ))}
                {chat.loading && (
                  <div className="self-start bg-slate-100 rounded-xl px-3 py-2 text-xs text-slate-500">
                    <Loader2 size={13} className="animate-spin inline mr-1" /> Réponse en cours...
                  </div>
                )}
                <div ref={chatEndRef} />
              </div>

              {/* Input bar */}
              <div className="flex gap-2">
                <input
                  value={chat.input}
                  onChange={(e) => setChat((prev) => ({ ...prev, input: e.target.value }))}
                  onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChatMessage()}
                  placeholder={`Question sur ${document.original_filename}...`}
                  className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                />
                <button
                  onClick={sendChatMessage}
                  disabled={!chat.input.trim() || chat.loading}
                  className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 disabled:opacity-50 transition"
                >
                  <Send size={14} />
                </button>
              </div>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}