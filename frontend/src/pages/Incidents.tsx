import { useEffect, useState, useRef, FormEvent } from "react";
import api from "@/hooks/useApi";
import type { Incident, DocumentItem, Conversation, Message } from "@/types";
import {
  AlertTriangle, Plus, X, Sparkles, ShieldAlert, FileText,
  Upload, Loader2, Trash2, MessageSquare, Send, ChevronDown, ChevronRight,
  Link as LinkIcon, PlusCircle, MessageCircle, Clock, CheckCircle2
} from "lucide-react";
import DocumentSelector from "@/components/DocumentSelector";

const severityStyles: Record<Incident["severity"], { bg: string; border: string; text: string }> = {
  mineur: { bg: "bg-blue-50", border: "border-blue-200", text: "text-blue-700" },
  majeur: { bg: "bg-amber-50", border: "border-amber-200", text: "text-amber-700" },
  critique: { bg: "bg-red-50", border: "border-red-200", text: "text-red-700" },
};

const statusOptions: { value: Incident["status"]; label: string; bg: string; text: string; activeBg: string }[] = [
  { value: "ouvert", label: "Ouvert", bg: "bg-red-50 text-red-700 border-red-200", text: "text-red-700", activeBg: "bg-red-600 text-white border-red-600" },
  { value: "en_cours", label: "En attente / En cours", bg: "bg-amber-50 text-amber-700 border-amber-200", text: "text-amber-700", activeBg: "bg-amber-500 text-white border-amber-500" },
  { value: "resolu", label: "Résolu", bg: "bg-emerald-50 text-emerald-700 border-emerald-200", text: "text-emerald-700", activeBg: "bg-emerald-600 text-white border-emerald-600" },
  { value: "ferme", label: "Fermé", bg: "bg-slate-100 text-slate-700 border-slate-300", text: "text-slate-700", activeBg: "bg-slate-700 text-white border-slate-700" },
];

interface IncidentChatState {
  conversationId?: string;
  messages: Message[];
  input: string;
  loading: boolean;
}

export default function Incidents() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<Incident["severity"]>("mineur");
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>(undefined);
  const [submitting, setSubmitting] = useState(false);

  // Panels: "documents" | "chat" | null
  const [expandedPanel, setExpandedPanel] = useState<Record<string, "documents" | "chat" | null>>({});

  // Documents per incident
  const [incidentDocs, setIncidentDocs] = useState<Record<string, DocumentItem[]>>({});
  const [loadingDocs, setLoadingDocs] = useState<Record<string, boolean>>({});
  const [libraryDocs, setLibraryDocs] = useState<DocumentItem[]>([]);
  const [selectedLibDoc, setSelectedLibDoc] = useState<Record<string, string>>({});
  const [uploadingDoc, setUploadingDoc] = useState<Record<string, boolean>>({});
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Conversations & Chat per incident
  const [incidentConvs, setIncidentConvs] = useState<Record<string, Conversation[]>>({});
  const [loadingConvs, setLoadingConvs] = useState<Record<string, boolean>>({});
  const [chats, setChats] = useState<Record<string, IncidentChatState>>({});
  const chatEndRef = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    api.get<Incident[]>("/incidents").then((res) => setIncidents(res.data));
    api.get<DocumentItem[]>("/documents").then((res) => setLibraryDocs(res.data)).catch(() => {});
  }, []);

  // ── Status update ─────────────────────────────────────────────────────────

  async function handleStatusChange(incidentId: string, newStatus: Incident["status"]) {
    try {
      const res = await api.patch<Incident>(`/incidents/${incidentId}`, { status: newStatus });
      setIncidents((prev) => prev.map((inc) => (inc.id === incidentId ? res.data : inc)));
    } catch {
      alert("Échec de la mise à jour du statut.");
    }
  }

  // ── Create incident ───────────────────────────────────────────────────────

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post<Incident>("/incidents", {
        title,
        description,
        severity,
        document_id: selectedDocumentId,
      });
      setIncidents((prev) => [res.data, ...prev]);
      setTitle("");
      setDescription("");
      setSeverity("mineur");
      setSelectedDocumentId(undefined);
      setShowForm(false);
    } finally {
      setSubmitting(false);
    }
  }

  // ── Panel toggle ──────────────────────────────────────────────────────────

  function togglePanel(incidentId: string, panel: "documents" | "chat") {
    setExpandedPanel((prev) => {
      const current = prev[incidentId];
      const next = current === panel ? null : panel;
      if (next === "documents") loadIncidentDocs(incidentId);
      if (next === "chat") loadIncidentConversations(incidentId);
      return { ...prev, [incidentId]: next };
    });
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  async function loadIncidentDocs(incidentId: string) {
    if (loadingDocs[incidentId]) return;
    setLoadingDocs((prev) => ({ ...prev, [incidentId]: true }));
    try {
      const res = await api.get<DocumentItem[]>(`/incidents/${incidentId}/documents`);
      setIncidentDocs((prev) => ({ ...prev, [incidentId]: res.data }));
    } finally {
      setLoadingDocs((prev) => ({ ...prev, [incidentId]: false }));
    }
  }

  async function attachLibraryDoc(incidentId: string) {
    const docId = selectedLibDoc[incidentId];
    if (!docId) return;
    try {
      const res = await api.post<DocumentItem>(`/incidents/${incidentId}/documents`, { document_id: docId });
      setIncidentDocs((prev) => ({
        ...prev,
        [incidentId]: [res.data, ...(prev[incidentId] || [])],
      }));
      setSelectedLibDoc((prev) => ({ ...prev, [incidentId]: "" }));
    } catch {
      alert("Impossible d'attacher ce document.");
    }
  }

  async function handleFileUpload(incidentId: string, file: File) {
    setUploadingDoc((prev) => ({ ...prev, [incidentId]: true }));
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post<DocumentItem>(
        `/incidents/${incidentId}/documents/upload`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setIncidentDocs((prev) => ({
        ...prev,
        [incidentId]: [res.data, ...(prev[incidentId] || [])],
      }));
      api.get<DocumentItem[]>("/documents").then((r) => setLibraryDocs(r.data)).catch(() => {});
    } catch {
      alert("Échec de l'upload.");
    } finally {
      setUploadingDoc((prev) => ({ ...prev, [incidentId]: false }));
      if (fileInputRefs.current[incidentId]) fileInputRefs.current[incidentId]!.value = "";
    }
  }

  async function detachDoc(incidentId: string, docId: string) {
    await api.delete(`/incidents/${incidentId}/documents/${docId}`);
    setIncidentDocs((prev) => ({
      ...prev,
      [incidentId]: (prev[incidentId] || []).filter((d) => d.id !== docId),
    }));
  }

  // ── Conversations & Chat ──────────────────────────────────────────────────

  async function loadIncidentConversations(incidentId: string) {
    setLoadingConvs((prev) => ({ ...prev, [incidentId]: true }));
    try {
      const res = await api.get<Conversation[]>(`/incidents/${incidentId}/conversations`);
      setIncidentConvs((prev) => ({ ...prev, [incidentId]: res.data }));
      
      if (res.data.length > 0 && !chats[incidentId]?.conversationId) {
        selectConversation(incidentId, res.data[0]);
      } else if (!chats[incidentId]) {
        startNewChat(incidentId);
      }
    } finally {
      setLoadingConvs((prev) => ({ ...prev, [incidentId]: false }));
    }
  }

  function startNewChat(incidentId: string) {
    setChats((prev) => ({
      ...prev,
      [incidentId]: { conversationId: undefined, messages: [], input: "", loading: false },
    }));
  }

  async function selectConversation(incidentId: string, conv: Conversation) {
    try {
      const res = await api.get<Conversation>(`/chat/conversations/${conv.id}`);
      setChats((prev) => ({
        ...prev,
        [incidentId]: {
          conversationId: res.data.id,
          messages: res.data.messages || [],
          input: prev[incidentId]?.input || "",
          loading: false,
        },
      }));
    } catch {
      setChats((prev) => ({
        ...prev,
        [incidentId]: {
          conversationId: conv.id,
          messages: conv.messages || [],
          input: prev[incidentId]?.input || "",
          loading: false,
        },
      }));
    }
  }

  function setChatInput(incidentId: string, input: string) {
    setChats((prev) => ({
      ...prev,
      [incidentId]: { ...(prev[incidentId] || { messages: [], loading: false }), input },
    }));
  }

  async function sendChatMessage(incidentId: string) {
    const chat = chats[incidentId];
    if (!chat || !chat.input.trim() || chat.loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: chat.input.trim(),
      created_at: new Date().toISOString(),
    };

    setChats((prev) => ({
      ...prev,
      [incidentId]: {
        ...prev[incidentId],
        messages: [...prev[incidentId].messages, userMsg],
        input: "",
        loading: true,
      },
    }));

    try {
      const res = await api.post<{ conversation_id: string; message: Message; sources: string[] }>(
        `/incidents/${incidentId}/chat`,
        { message: userMsg.content, conversation_id: chat.conversationId },
      );

      setChats((prev) => ({
        ...prev,
        [incidentId]: {
          ...prev[incidentId],
          conversationId: res.data.conversation_id,
          messages: [...prev[incidentId].messages, res.data.message],
          loading: false,
        },
      }));

      loadIncidentConversations(incidentId);

      setTimeout(() => {
        chatEndRef.current[incidentId]?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch {
      setChats((prev) => ({
        ...prev,
        [incidentId]: { ...prev[incidentId], loading: false },
      }));
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-emerald-700 mb-1">
            <AlertTriangle className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Suivi des anomalies</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Gestion des Incidents</h1>
          <p className="mt-1 text-xs text-slate-500">
            Déclarez et gérez le statut des incidents, joignez vos fichiers et échangez via l'assistant IA.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800"
        >
          {showForm ? <><X size={16} /><span>Annuler</span></> : <><Plus size={16} /><span>Déclarer un incident</span></>}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-md">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3">Nouveau signalement d'incident</h3>
          
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Titre de l'incident</label>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="ex: Latence élevée sur la base de données principale"
              required
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description détaillée</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Décrivez les symptômes, le système impacté et le comportement constaté..."
              required
              rows={4}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Niveau de sévérité</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value as Incident["severity"])}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            >
              <option value="mineur">Mineur — Impact limité sans arrêt de service</option>
              <option value="majeur">Majeur — Dégradation significative de performance</option>
              <option value="critique">Critique — Interruption totale de service</option>
            </select>
          </div>

          <DocumentSelector
            selectedDocumentId={selectedDocumentId}
            onSelectDocument={setSelectedDocumentId}
          />

          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50"
          >
            <Sparkles size={15} />
            {submitting ? "Analyse IA en cours..." : "Lancer l'analyse automatique"}
          </button>
        </form>
      )}

      {/* Incidents List */}
      <div className="space-y-4">
        {incidents.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
            <ShieldAlert className="mx-auto h-10 w-10 text-slate-300 mb-3" />
            <p className="text-sm font-semibold text-slate-700">Aucun incident enregistré</p>
            <p className="mt-1 text-xs text-slate-400">Tous les systèmes sont opérationnels.</p>
          </div>
        ) : (
          incidents.map((i) => {
            const sev = severityStyles[i.severity] || severityStyles.mineur;
            const panel = expandedPanel[i.id] || null;
            const docs = incidentDocs[i.id] || [];
            const convs = incidentConvs[i.id] || [];
            const chat = chats[i.id];

            return (
              <div key={i.id} className="rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition">
                {/* Header */}
                <div className="p-5">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h2 className="text-sm font-bold text-slate-900">{i.title}</h2>
                      {i.document && (
                        <span className="inline-flex items-center gap-1.5 mt-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800 border border-emerald-200">
                          <FileText size={12} className="text-emerald-600" />
                          Document principal : {i.document.original_filename}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <span className={`inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wider ${sev.bg} ${sev.border} ${sev.text}`}>
                        {i.severity}
                      </span>
                    </div>
                  </div>

                  {/* Status buttons */}
                  <div className="mt-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-50 p-3 rounded-xl border border-slate-100">
                    <span className="text-xs font-bold text-slate-700 flex items-center gap-1.5">
                      <CheckCircle2 size={14} className="text-emerald-600" /> Statut de traitement :
                    </span>

                    <div className="flex flex-wrap items-center gap-1.5">
                      {statusOptions.map((opt) => {
                        const isActive = i.status === opt.value;
                        return (
                          <button
                            key={opt.value}
                            onClick={() => handleStatusChange(i.id, opt.value)}
                            className={`rounded-lg border px-3 py-1 text-xs font-semibold transition ${
                              isActive ? opt.activeBg : `${opt.bg} hover:opacity-80`
                            }`}
                          >
                            {opt.label}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Analysis */}
                  {i.analysis && (
                    <div className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-3.5 text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                      <span className="font-bold text-emerald-800 block mb-1">Analyse IA & Recommandations :</span>
                      {i.analysis}
                    </div>
                  )}

                  {/* Panel Toggles */}
                  <div className="mt-4 pt-3 border-t border-slate-100 flex items-center justify-end gap-2">
                    <button
                      onClick={() => togglePanel(i.id, "documents")}
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                        panel === "documents"
                          ? "bg-emerald-600 text-white border-emerald-600"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      <FileText size={13} />
                      <span>Fichiers</span>
                      {panel === "documents" ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </button>

                    <button
                      onClick={() => togglePanel(i.id, "chat")}
                      className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-semibold transition ${
                        panel === "chat"
                          ? "bg-emerald-600 text-white border-emerald-600"
                          : "bg-white text-slate-700 border-slate-300 hover:bg-slate-50"
                      }`}
                    >
                      <MessageSquare size={13} />
                      <span>Discussions</span>
                      {panel === "chat" ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                    </button>
                  </div>
                </div>

                {/* ── Documents Panel ─────────────────────────────────── */}
                {panel === "documents" && (
                  <div className="border-t border-slate-100 bg-slate-50/60 p-5 space-y-4">
                    <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <FileText size={14} className="text-emerald-600" /> Fichiers de l'incident
                    </h3>

                    <div className="flex gap-2">
                      <select
                        value={selectedLibDoc[i.id] || ""}
                        onChange={(e) => setSelectedLibDoc((prev) => ({ ...prev, [i.id]: e.target.value }))}
                        className="flex-1 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs text-slate-900 outline-none focus:border-emerald-500"
                      >
                        <option value="">-- Ajouter depuis la bibliothèque --</option>
                        {libraryDocs
                          .filter((ld) => !docs.find((d) => d.id === ld.id))
                          .map((ld) => (
                            <option key={ld.id} value={ld.id}>
                              📄 {ld.original_filename}
                            </option>
                          ))}
                      </select>
                      <button
                        onClick={() => attachLibraryDoc(i.id)}
                        disabled={!selectedLibDoc[i.id]}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-40 transition"
                      >
                        <LinkIcon size={13} /> Attacher
                      </button>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRefs.current[i.id]?.click()}
                        disabled={uploadingDoc[i.id]}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
                      >
                        {uploadingDoc[i.id] ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} className="text-emerald-600" />}
                        <span>{uploadingDoc[i.id] ? "Upload..." : "Uploader un nouveau fichier"}</span>
                      </button>
                      <input
                        ref={(el) => { fileInputRefs.current[i.id] = el; }}
                        type="file"
                        accept=".pdf,.docx,.txt,.md"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleFileUpload(i.id, f);
                        }}
                      />
                    </div>

                    {loadingDocs[i.id] ? (
                      <div className="flex justify-center py-4">
                        <Loader2 size={18} className="animate-spin text-emerald-500" />
                      </div>
                    ) : docs.length === 0 ? (
                      <p className="text-center text-xs text-slate-400 py-4">Aucun fichier attaché à cet incident.</p>
                    ) : (
                      <ul className="space-y-2">
                        {docs.map((doc) => (
                          <li key={doc.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-xs">
                            <div className="flex items-center gap-2 min-w-0">
                              <FileText size={14} className="text-emerald-600 shrink-0" />
                              <span className="truncate font-medium text-slate-800">{doc.original_filename}</span>
                            </div>
                            <button
                              onClick={() => detachDoc(i.id, doc.id)}
                              className="ml-3 shrink-0 text-slate-400 hover:text-red-500 transition"
                              title="Détacher ce fichier"
                            >
                              <Trash2 size={14} />
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* ── Discussions Panel ───────────────────────────────── */}
                {panel === "chat" && (
                  <div className="border-t border-slate-100 bg-slate-50/60 p-5">
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      
                      {/* Conversations Sidebar */}
                      <div className="md:col-span-1 border-b md:border-b-0 md:border-r border-slate-200 pr-0 md:pr-4 pb-4 md:pb-0 space-y-3">
                        <div className="flex items-center justify-between">
                          <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                            <MessageCircle size={14} className="text-emerald-600" />
                            <span>Discussions ({convs.length})</span>
                          </h3>
                          <button
                            onClick={() => startNewChat(i.id)}
                            className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-100 transition"
                            title="Démarrer une nouvelle discussion sur cet incident"
                          >
                            <PlusCircle size={12} />
                            <span>Nouvelle</span>
                          </button>
                        </div>

                        {loadingConvs[i.id] ? (
                          <div className="flex justify-center py-4">
                            <Loader2 size={16} className="animate-spin text-emerald-600" />
                          </div>
                        ) : convs.length === 0 ? (
                          <p className="text-xs text-slate-400 italic">Aucune discussion enregistrée.</p>
                        ) : (
                          <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                            {convs.map((conv) => {
                              const isSelected = chat?.conversationId === conv.id;
                              const dateStr = new Date(conv.updated_at).toLocaleDateString("fr-FR", {
                                day: "2-digit",
                                month: "2-digit",
                                hour: "2-digit",
                                minute: "2-digit",
                              });

                              return (
                                <button
                                  key={conv.id}
                                  onClick={() => selectConversation(i.id, conv)}
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

                      {/* Chat Messages */}
                      <div className="md:col-span-2 flex flex-col gap-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <span className="text-xs font-bold text-slate-800">
                            {chat?.conversationId
                              ? convs.find((c) => c.id === chat.conversationId)?.title || "Discussion courante"
                              : "Nouvelle discussion"}
                          </span>
                        </div>

                        <div className="flex flex-col gap-2 min-h-48 max-h-72 overflow-y-auto pr-1 bg-white border border-slate-200 p-3 rounded-xl">
                          {(!chat || chat.messages.length === 0) && (
                            <p className="text-center text-xs text-slate-400 my-auto py-6">
                              Posez vos questions sur la résolution ou le diagnostic de cet incident.
                            </p>
                          )}
                          {chat?.messages.map((msg, idx) => (
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
                          {chat?.loading && (
                            <div className="self-start bg-slate-100 rounded-xl px-3 py-2 text-xs text-slate-500">
                              <Loader2 size={13} className="animate-spin inline mr-1" /> Réponse en cours...
                            </div>
                          )}
                          <div ref={(el) => { chatEndRef.current[i.id] = el; }} />
                        </div>

                        {/* Input bar */}
                        <div className="flex gap-2">
                          <input
                            value={chat?.input || ""}
                            onChange={(e) => setChatInput(i.id, e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChatMessage(i.id)}
                            placeholder="Échangez sur l'incident avec l'assistant..."
                            className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                          />
                          <button
                            onClick={() => sendChatMessage(i.id)}
                            disabled={!chat?.input?.trim() || chat?.loading}
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
          })
        )}
      </div>
    </div>
  );
}