import { useEffect, useState, useRef, FormEvent } from "react";
import api from "@/hooks/useApi";
import type { Conversation, DocumentItem, Projet, Message } from "@/types";
import {
  Briefcase, Plus, X, Sparkles, FolderGit2, ArrowRight,
  FileText, Upload, Loader2, Trash2, MessageSquare, Send,
  ChevronDown, ChevronRight, Link as LinkIcon, PlusCircle, MessageCircle, Clock,
} from "lucide-react";

// ── types ──────────────────────────────────────────────────────────────────

interface ProjectChatState {
  conversationId?: string;
  messages: Message[];
  input: string;
  loading: boolean;
}

// ── component ──────────────────────────────────────────────────────────────

export default function Projects() {
  const [projets, setProjets] = useState<Projet[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Expanded project panels: "documents" | "chat" | null
  const [expandedPanel, setExpandedPanel] = useState<Record<string, "documents" | "chat" | null>>({});

  // Suggestions
  const [suggestions, setSuggestions] = useState<Record<string, string>>({});
  const [loadingSuggestions, setLoadingSuggestions] = useState<Record<string, boolean>>({});

  // Per-project documents
  const [projectDocs, setProjectDocs] = useState<Record<string, DocumentItem[]>>({});
  const [loadingDocs, setLoadingDocs] = useState<Record<string, boolean>>({});
  const [libraryDocs, setLibraryDocs] = useState<DocumentItem[]>([]);
  const [selectedLibDoc, setSelectedLibDoc] = useState<Record<string, string>>({});
  const [uploadingDoc, setUploadingDoc] = useState<Record<string, boolean>>({});
  const fileInputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  // Per-project conversations & chat state
  const [projectConvs, setProjectConvs] = useState<Record<string, Conversation[]>>({});
  const [loadingConvs, setLoadingConvs] = useState<Record<string, boolean>>({});
  const [chats, setChats] = useState<Record<string, ProjectChatState>>({});
  const chatEndRef = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    api.get<Projet[]>("/projets").then((res) => setProjets(res.data));
    api.get<DocumentItem[]>("/documents").then((res) => setLibraryDocs(res.data)).catch(() => {});
  }, []);

  // ── Create project ────────────────────────────────────────────────────────

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post<Projet>("/projets", { name, description });
      setProjets((prev) => [res.data, ...prev]);
      setName("");
      setDescription("");
      setShowForm(false);
    } finally {
      setSubmitting(false);
    }
  }

  // ── Suggestions ───────────────────────────────────────────────────────────

  async function handleSuggest(projetId: string) {
    setLoadingSuggestions((prev) => ({ ...prev, [projetId]: true }));
    try {
      const res = await api.post(`/projets/${projetId}/suggestions`);
      setSuggestions((prev) => ({ ...prev, [projetId]: res.data.suggestions }));
    } finally {
      setLoadingSuggestions((prev) => ({ ...prev, [projetId]: false }));
    }
  }

  // ── Panel toggle ──────────────────────────────────────────────────────────

  function togglePanel(projetId: string, panel: "documents" | "chat") {
    setExpandedPanel((prev) => {
      const current = prev[projetId];
      const next = current === panel ? null : panel;
      if (next === "documents") loadProjectDocs(projetId);
      if (next === "chat") loadProjectConversations(projetId);
      return { ...prev, [projetId]: next };
    });
  }

  // ── Documents ─────────────────────────────────────────────────────────────

  async function loadProjectDocs(projetId: string) {
    if (loadingDocs[projetId]) return;
    setLoadingDocs((prev) => ({ ...prev, [projetId]: true }));
    try {
      const res = await api.get<DocumentItem[]>(`/projets/${projetId}/documents`);
      setProjectDocs((prev) => ({ ...prev, [projetId]: res.data }));
    } finally {
      setLoadingDocs((prev) => ({ ...prev, [projetId]: false }));
    }
  }

  async function attachLibraryDoc(projetId: string) {
    const docId = selectedLibDoc[projetId];
    if (!docId) return;
    try {
      const res = await api.post<DocumentItem>(`/projets/${projetId}/documents`, { document_id: docId });
      setProjectDocs((prev) => ({
        ...prev,
        [projetId]: [res.data, ...(prev[projetId] || [])],
      }));
      setSelectedLibDoc((prev) => ({ ...prev, [projetId]: "" }));
    } catch {
      alert("Impossible d'attacher ce document.");
    }
  }

  async function handleFileUpload(projetId: string, file: File) {
    setUploadingDoc((prev) => ({ ...prev, [projetId]: true }));
    const formData = new FormData();
    formData.append("file", file);
    try {
      const res = await api.post<DocumentItem>(
        `/projets/${projetId}/documents/upload`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } },
      );
      setProjectDocs((prev) => ({
        ...prev,
        [projetId]: [res.data, ...(prev[projetId] || [])],
      }));
      api.get<DocumentItem[]>("/documents").then((r) => setLibraryDocs(r.data)).catch(() => {});
    } catch {
      alert("Échec de l'upload.");
    } finally {
      setUploadingDoc((prev) => ({ ...prev, [projetId]: false }));
      if (fileInputRefs.current[projetId]) fileInputRefs.current[projetId]!.value = "";
    }
  }

  async function detachDoc(projetId: string, docId: string) {
    await api.delete(`/projets/${projetId}/documents/${docId}`);
    setProjectDocs((prev) => ({
      ...prev,
      [projetId]: (prev[projetId] || []).filter((d) => d.id !== docId),
    }));
  }

  // ── Conversations & Chat ──────────────────────────────────────────────────

  async function loadProjectConversations(projetId: string) {
    setLoadingConvs((prev) => ({ ...prev, [projetId]: true }));
    try {
      const res = await api.get<Conversation[]>(`/projets/${projetId}/conversations`);
      setProjectConvs((prev) => ({ ...prev, [projetId]: res.data }));
      
      // Auto-select the first conversation if available, or stay ready for a new chat
      if (res.data.length > 0 && !chats[projetId]?.conversationId) {
        selectConversation(projetId, res.data[0]);
      } else if (!chats[projetId]) {
        startNewChat(projetId);
      }
    } finally {
      setLoadingConvs((prev) => ({ ...prev, [projetId]: false }));
    }
  }

  function startNewChat(projetId: string) {
    setChats((prev) => ({
      ...prev,
      [projetId]: { conversationId: undefined, messages: [], input: "", loading: false },
    }));
  }

  async function selectConversation(projetId: string, conv: Conversation) {
    try {
      const res = await api.get<Conversation>(`/chat/conversations/${conv.id}`);
      setChats((prev) => ({
        ...prev,
        [projetId]: {
          conversationId: res.data.id,
          messages: res.data.messages || [],
          input: prev[projetId]?.input || "",
          loading: false,
        },
      }));
    } catch {
      setChats((prev) => ({
        ...prev,
        [projetId]: {
          conversationId: conv.id,
          messages: conv.messages || [],
          input: prev[projetId]?.input || "",
          loading: false,
        },
      }));
    }
  }

  function setChatInput(projetId: string, input: string) {
    setChats((prev) => ({
      ...prev,
      [projetId]: { ...(prev[projetId] || { messages: [], loading: false }), input },
    }));
  }

  async function sendChatMessage(projetId: string) {
    const chat = chats[projetId];
    if (!chat || !chat.input.trim() || chat.loading) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: "user",
      content: chat.input.trim(),
      created_at: new Date().toISOString(),
    };

    setChats((prev) => ({
      ...prev,
      [projetId]: {
        ...prev[projetId],
        messages: [...prev[projetId].messages, userMsg],
        input: "",
        loading: true,
      },
    }));

    try {
      const res = await api.post<{ conversation_id: string; message: Message; sources: string[] }>(
        `/projets/${projetId}/chat`,
        { message: userMsg.content, conversation_id: chat.conversationId },
      );

      setChats((prev) => ({
        ...prev,
        [projetId]: {
          ...prev[projetId],
          conversationId: res.data.conversation_id,
          messages: [...prev[projetId].messages, res.data.message],
          loading: false,
        },
      }));

      // Refresh project conversations list
      loadProjectConversations(projetId);

      setTimeout(() => {
        chatEndRef.current[projetId]?.scrollIntoView({ behavior: "smooth" });
      }, 50);
    } catch {
      setChats((prev) => ({
        ...prev,
        [projetId]: { ...prev[projetId], loading: false },
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
            <Briefcase className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Suivi & Roadmap</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Projets & Initiations</h1>
          <p className="mt-1 text-xs text-slate-500">
            Pilotez vos projets, gagnez en clarté avec les documents associés et retrouvez toutes vos discussions IA.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800"
        >
          {showForm ? <><X size={16} /><span>Annuler</span></> : <><Plus size={16} /><span>Nouveau projet</span></>}
        </button>
      </div>

      {/* Create form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-md">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3">Création d'un nouveau projet</h3>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Nom du projet</label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="ex: Migration Cloud AWS"
              required
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Description / Objectifs</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Objectifs clés, périmètre fonctionnel..."
              rows={3}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 disabled:opacity-50"
          >
            {submitting ? "Création..." : "Enregistrer le projet"}
          </button>
        </form>
      )}

      {/* Projects list */}
      <div className="space-y-4">
        {projets.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
            <FolderGit2 className="mx-auto h-10 w-10 text-slate-300 mb-3" />
            <p className="text-sm font-semibold text-slate-700">Aucun projet en cours</p>
            <p className="mt-1 text-xs text-slate-400">Créez votre premier projet pour bénéficier du suivi intelligent.</p>
          </div>
        ) : (
          projets.map((p) => {
            const panel = expandedPanel[p.id] || null;
            const docs = projectDocs[p.id] || [];
            const convs = projectConvs[p.id] || [];
            const chat = chats[p.id];

            return (
              <div key={p.id} className="rounded-2xl border border-slate-200 bg-white shadow-sm hover:shadow-md transition">
                {/* Project header */}
                <div className="p-5">
                  <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                    <div>
                      <h2 className="text-sm font-bold text-slate-900">{p.name}</h2>
                      <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600 border border-slate-200 mt-1 inline-block">
                        {p.status || "actif"}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      {/* Documents tab */}
                      <button
                        onClick={() => togglePanel(p.id, "documents")}
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

                      {/* Chat / Discussions tab */}
                      <button
                        onClick={() => togglePanel(p.id, "chat")}
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

                  {p.description && <p className="mt-3 text-xs text-slate-600 leading-relaxed">{p.description}</p>}

                  {/* AI suggestions */}
                  <div className="mt-4 pt-2 border-t border-slate-100 flex items-center justify-between">
                    <button
                      onClick={() => handleSuggest(p.id)}
                      disabled={loadingSuggestions[p.id]}
                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800 transition disabled:opacity-50"
                    >
                      <Sparkles size={14} />
                      <span>{loadingSuggestions[p.id] ? "Génération..." : "Suggérer les prochaines étapes IA"}</span>
                      <ArrowRight size={13} />
                    </button>
                  </div>

                  {suggestions[p.id] && (
                    <div className="mt-3 rounded-xl border border-emerald-100 bg-emerald-50/60 p-4 text-xs text-slate-700 leading-relaxed whitespace-pre-wrap">
                      <span className="font-bold text-emerald-800 block mb-1">Recommandations stratégiques :</span>
                      {suggestions[p.id]}
                    </div>
                  )}
                </div>

                {/* ── Documents panel ────────────────────────────────── */}
                {panel === "documents" && (
                  <div className="border-t border-slate-100 bg-slate-50/60 p-5 space-y-4">
                    <h3 className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                      <FileText size={14} className="text-emerald-600" /> Fichiers du projet
                    </h3>

                    {/* Add existing library doc */}
                    <div className="flex gap-2">
                      <select
                        value={selectedLibDoc[p.id] || ""}
                        onChange={(e) => setSelectedLibDoc((prev) => ({ ...prev, [p.id]: e.target.value }))}
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
                        onClick={() => attachLibraryDoc(p.id)}
                        disabled={!selectedLibDoc[p.id]}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-300 bg-emerald-50 px-3 py-1.5 text-xs font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-40 transition"
                      >
                        <LinkIcon size={13} /> Attacher
                      </button>
                    </div>

                    {/* Upload new file */}
                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => fileInputRefs.current[p.id]?.click()}
                        disabled={uploadingDoc[p.id]}
                        className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
                      >
                        {uploadingDoc[p.id] ? <Loader2 size={13} className="animate-spin" /> : <Upload size={13} className="text-emerald-600" />}
                        <span>{uploadingDoc[p.id] ? "Upload..." : "Uploader un nouveau fichier"}</span>
                      </button>
                      <input
                        ref={(el) => { fileInputRefs.current[p.id] = el; }}
                        type="file"
                        accept=".pdf,.docx,.txt,.md"
                        className="hidden"
                        onChange={(e) => {
                          const f = e.target.files?.[0];
                          if (f) handleFileUpload(p.id, f);
                        }}
                      />
                    </div>

                    {/* Files list */}
                    {loadingDocs[p.id] ? (
                      <div className="flex justify-center py-4">
                        <Loader2 size={18} className="animate-spin text-emerald-500" />
                      </div>
                    ) : docs.length === 0 ? (
                      <p className="text-center text-xs text-slate-400 py-4">Aucun fichier attaché à ce projet.</p>
                    ) : (
                      <ul className="space-y-2">
                        {docs.map((doc) => (
                          <li key={doc.id} className="flex items-center justify-between rounded-xl border border-slate-200 bg-white p-3 text-xs">
                            <div className="flex items-center gap-2 min-w-0">
                              <FileText size={14} className="text-emerald-600 shrink-0" />
                              <span className="truncate font-medium text-slate-800">{doc.original_filename}</span>
                              <span className={`shrink-0 rounded px-1.5 py-0.5 text-[10px] font-semibold ${
                                doc.status === "indexed"
                                  ? "bg-emerald-100 text-emerald-800"
                                  : "bg-amber-100 text-amber-800"
                              }`}>
                                {doc.status === "indexed" ? "✓ Indexé" : doc.status}
                              </span>
                            </div>
                            <button
                              onClick={() => detachDoc(p.id, doc.id)}
                              className="ml-3 shrink-0 text-slate-400 hover:text-red-500 transition"
                              title="Détacher ce fichier du projet"
                            >
                              <Trash2 size={14} />
                            </button>
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                )}

                {/* ── Discussions panel ─────────────────────────────────── */}
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
                            onClick={() => startNewChat(p.id)}
                            className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-2 py-1 text-[11px] font-semibold text-emerald-700 hover:bg-emerald-100 transition"
                            title="Démarrer une nouvelle discussion sur ce projet"
                          >
                            <PlusCircle size={12} />
                            <span>Nouvelle</span>
                          </button>
                        </div>

                        {loadingConvs[p.id] ? (
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
                                  onClick={() => selectConversation(p.id, conv)}
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

                      {/* Chat Messages & Input */}
                      <div className="md:col-span-2 flex flex-col gap-3">
                        <div className="flex items-center justify-between border-b border-slate-200 pb-2">
                          <span className="text-xs font-bold text-slate-800">
                            {chat?.conversationId
                              ? convs.find((c) => c.id === chat.conversationId)?.title || "Discussion courante"
                              : "Nouvelle discussion"}
                          </span>
                        </div>

                        {/* Messages box */}
                        <div className="flex flex-col gap-2 min-h-48 max-h-72 overflow-y-auto pr-1 bg-white border border-slate-200 p-3 rounded-xl">
                          {(!chat || chat.messages.length === 0) && (
                            <p className="text-center text-xs text-slate-400 my-auto py-6">
                              Posez une question sur ce projet. L'IA utilisera les fichiers et le contexte associés.
                            </p>
                          )}
                          {chat?.messages.map((msg, i) => (
                            <div
                              key={i}
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
                          <div ref={(el) => { chatEndRef.current[p.id] = el; }} />
                        </div>

                        {/* Input bar */}
                        <div className="flex gap-2">
                          <input
                            value={chat?.input || ""}
                            onChange={(e) => setChatInput(p.id, e.target.value)}
                            onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && sendChatMessage(p.id)}
                            placeholder="Posez votre question sur ce projet..."
                            className="flex-1 rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
                          />
                          <button
                            onClick={() => sendChatMessage(p.id)}
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