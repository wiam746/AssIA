import { useEffect, useState, FormEvent } from "react";
import api from "@/hooks/useApi";
import type { Reunion } from "@/types";
import { Users, Plus, X, Sparkles, CheckSquare, FileText, Calendar, Download, FileType, CheckCircle2, Clock, Edit3, Save } from "lucide-react";
import DocumentSelector from "@/components/DocumentSelector";

export default function Meetings() {
  const [reunions, setReunions] = useState<Reunion[]>([]);
  const [showForm, setShowForm] = useState(false);
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [participants, setParticipants] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState<string | undefined>(undefined);
  const [submitting, setSubmitting] = useState(false);

  // Édit / Validation Humaine state
  const [editingReunion, setEditingReunion] = useState<Reunion | null>(null);
  const [editTitle, setEditTitle] = useState("");
  const [editParticipants, setEditParticipants] = useState("");
  const [editObjet, setEditObjet] = useState("");
  const [editSummary, setEditSummary] = useState("");
  const [editDecisions, setEditDecisions] = useState("");
  const [editActions, setEditActions] = useState("");
  const [editProchaine, setEditProchaine] = useState("");
  const [savingValidation, setSavingValidation] = useState(false);

  useEffect(() => {
    api.get<Reunion[]>("/reunions").then((res) => setReunions(res.data));
  }, []);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    try {
      const res = await api.post<Reunion>("/reunions", {
        title,
        participants: participants || undefined,
        raw_content: content,
        document_id: selectedDocumentId,
      });
      setReunions((prev) => [res.data, ...prev]);
      setTitle("");
      setParticipants("");
      setContent("");
      setSelectedDocumentId(undefined);
      setShowForm(false);
    } finally {
      setSubmitting(false);
    }
  }

  function openValidationModal(r: Reunion) {
    setEditingReunion(r);
    setEditTitle(r.title);
    setEditParticipants(r.participants || "");
    setEditObjet(r.objet || "");
    setEditSummary(r.summary || "");
    setEditDecisions(r.decisions || "");
    setEditActions(r.actions || "");
    setEditProchaine(r.prochaine_reunion || "");
  }

  async function handleSaveValidation(newStatus: "brouillon" | "valide") {
    if (!editingReunion) return;
    setSavingValidation(true);
    try {
      const res = await api.patch<Reunion>(`/reunions/${editingReunion.id}`, {
        title: editTitle,
        participants: editParticipants,
        objet: editObjet,
        summary: editSummary,
        decisions: editDecisions,
        actions: editActions,
        prochaine_reunion: editProchaine,
        status: newStatus,
      });

      setReunions((prev) => prev.map((item) => (item.id === editingReunion.id ? res.data : item)));
      setEditingReunion(null);
    } finally {
      setSavingValidation(false);
    }
  }

  function handleDownload(reunionId: string, format: "docx" | "pdf", filename: string) {
    const token = localStorage.getItem("access_token");
    const exportUrl = `/api/reunions/${reunionId}/export?format=${format}`;
    
    fetch(exportUrl, {
      headers: {
        Authorization: `Bearer ${token || ""}`,
      },
    })
      .then((response) => {
        if (!response.ok) throw new Error("Échec du téléchargement");
        return response.blob();
      })
      .then((blob) => {
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        const safeName = filename.replace(/[^a-zA-Z0-9_\-]/g, "_");
        a.download = `Proces_Verbal_${safeName}.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      })
      .catch((err) => alert(err.message || "Erreur de téléchargement"));
  }

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-8">
      {/* Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-emerald-700 mb-1">
            <Users className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Procès-Verbaux & Synthèses</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Réunions d'équipe</h1>
          <p className="mt-1 text-xs text-slate-500">
            Générez des procès-verbaux structurés, effectuez la validation humaine et téléchargez le document officiel.
          </p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800"
        >
          {showForm ? (
            <>
              <X size={16} />
              <span>Annuler</span>
            </>
          ) : (
            <>
              <Plus size={16} />
              <span>Nouveau compte-rendu</span>
            </>
          )}
        </button>
      </div>

      {/* Form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-8 space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-md">
          <h3 className="text-sm font-bold text-slate-800 border-b border-slate-100 pb-3">Saisie des notes de réunion</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Titre / Sujet de la réunion</label>
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="ex: Synchronisation hebdomadaire Direction"
                required
                className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Participants (Optionnel)</label>
              <input
                value={participants}
                onChange={(e) => setParticipants(e.target.value)}
                placeholder="ex: Alice Dupont, Bob Martin"
                className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Notes brutes / Transcription</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="Collez ou saisissez le texte brut de la réunion..."
              required
              rows={6}
              className="w-full rounded-xl border border-slate-300 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 outline-none focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20"
            />
          </div>

          {/* Document Selector */}
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
            {submitting ? "Rédaction du Procès-Verbal..." : "Générer le procès-verbal IA"}
          </button>
        </form>
      )}

      {/* Validation Humaine Modal */}
      {editingReunion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm">
          <div className="w-full max-w-3xl max-h-[90vh] overflow-y-auto rounded-2xl bg-white p-6 shadow-xl space-y-4 border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2 text-emerald-800 font-bold text-sm">
                <Edit3 size={18} />
                <span>Validation Humaine du Procès-Verbal</span>
              </div>
              <button onClick={() => setEditingReunion(null)} className="text-slate-400 hover:text-slate-600">
                <X size={18} />
              </button>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Titre</label>
                <input
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Participants</label>
                <input
                  value={editParticipants}
                  onChange={(e) => setEditParticipants(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Objet</label>
              <input
                value={editObjet}
                onChange={(e) => setEditObjet(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Points abordés</label>
              <textarea
                value={editSummary}
                onChange={(e) => setEditSummary(e.target.value)}
                rows={4}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Décisions prises</label>
              <textarea
                value={editDecisions}
                onChange={(e) => setEditDecisions(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Actions à réaliser</label>
              <textarea
                value={editActions}
                onChange={(e) => setEditActions(e.target.value)}
                rows={3}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Prochaine réunion</label>
              <input
                value={editProchaine}
                onChange={(e) => setEditProchaine(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-1.5 text-xs outline-none focus:border-emerald-500"
              />
            </div>

            <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
              <button
                type="button"
                onClick={() => handleSaveValidation("brouillon")}
                disabled={savingValidation}
                className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
              >
                <Save size={14} />
                <span>Sauvegarder brouillon</span>
              </button>

              <button
                type="button"
                onClick={() => handleSaveValidation("valide")}
                disabled={savingValidation}
                className="inline-flex items-center gap-1.5 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white hover:bg-emerald-700 transition"
              >
                <CheckCircle2 size={14} />
                <span>Valider le procès-verbal</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Meetings List */}
      <div className="space-y-4">
        {reunions.length === 0 ? (
          <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
            <Calendar className="mx-auto h-10 w-10 text-slate-300 mb-3" />
            <p className="text-sm font-semibold text-slate-700">Aucun procès-verbal enregistré</p>
            <p className="mt-1 text-xs text-slate-400">Ajoutez les notes de votre première réunion pour démarrer.</p>
          </div>
        ) : (
          reunions.map((r) => {
            const isValidated = r.status === "valide";
            return (
              <div key={r.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md transition space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between border-b border-slate-100 pb-3 gap-2">
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="text-sm font-bold text-slate-900">{r.title}</h2>
                      {isValidated ? (
                        <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 border border-emerald-300 px-2.5 py-0.5 text-[10px] font-bold text-emerald-800">
                          <CheckCircle2 size={11} /> VALIDÉ
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 border border-amber-300 px-2.5 py-0.5 text-[10px] font-bold text-amber-800">
                          <Clock size={11} /> BROUILLON (Attente validation)
                        </span>
                      )}
                    </div>

                    {r.document && (
                      <span className="inline-flex items-center gap-1.5 mt-1 rounded-md bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-800 border border-emerald-200">
                        <FileText size={12} className="text-emerald-600" />
                        Document : {r.document.original_filename}
                      </span>
                    )}
                  </div>

                  {/* Actions & Export Buttons */}
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => openValidationModal(r)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition"
                      title="Éditer et valider le procès-verbal"
                    >
                      <Edit3 size={14} className="text-emerald-600" />
                      <span>{isValidated ? "Éditer" : "Valider"}</span>
                    </button>

                    <button
                      onClick={() => handleDownload(r.id, "docx", r.title)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2.5 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition"
                      title="Télécharger en document Word (.docx)"
                    >
                      <FileType size={14} className="text-blue-600" />
                      <span>Word</span>
                    </button>

                    <button
                      onClick={() => handleDownload(r.id, "pdf", r.title)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50 px-2.5 py-1.5 text-xs font-semibold text-red-700 hover:bg-red-100 transition"
                      title="Télécharger en document PDF (.pdf)"
                    >
                      <Download size={14} className="text-red-600" />
                      <span>PDF</span>
                    </button>
                  </div>
                </div>
                
                {/* Meta details */}
                {(r.objet || r.participants) && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs bg-slate-50 p-2.5 rounded-xl border border-slate-100 text-slate-700">
                    <div><span className="font-semibold text-slate-900">Objet :</span> {r.objet || "Non précisé"}</div>
                    <div><span className="font-semibold text-slate-900">Participants :</span> {r.participants || "Non précisé"}</div>
                  </div>
                )}

                {r.summary && (
                  <div className="text-xs text-slate-700 leading-relaxed">
                    <span className="font-semibold text-slate-900 block mb-1">Points abordés :</span>
                    <p className="whitespace-pre-wrap">{r.summary}</p>
                  </div>
                )}

                {r.decisions && (
                  <div className="rounded-xl border border-slate-200 bg-slate-50/80 p-3.5 text-xs text-slate-700">
                    <span className="font-bold text-emerald-800 flex items-center gap-1.5 mb-1">
                      <CheckSquare size={14} /> Décisions prises :
                    </span>
                    <p className="leading-relaxed whitespace-pre-wrap">{r.decisions}</p>
                  </div>
                )}

                {r.actions && (
                  <div className="rounded-xl border border-emerald-100 bg-emerald-50/50 p-3.5 text-xs text-slate-700">
                    <span className="font-bold text-emerald-900 flex items-center gap-1.5 mb-1">
                      <FileText size={14} /> Actions à réaliser :
                    </span>
                    <p className="leading-relaxed whitespace-pre-wrap">{r.actions}</p>
                  </div>
                )}

                {r.prochaine_reunion && (
                  <div className="text-xs text-slate-600 italic border-t border-slate-100 pt-2">
                    <span className="font-semibold text-slate-800 not-italic">Prochaine réunion :</span> {r.prochaine_reunion}
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