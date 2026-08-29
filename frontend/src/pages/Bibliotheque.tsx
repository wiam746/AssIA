import { useEffect, useState } from "react";
import api from "@/hooks/useApi";
import DocumentUploader from "@/components/DocumentUploader";
import DocumentCard from "@/components/DocumentCard";
import type { DocumentItem } from "@/types";
import { FolderOpen, Search } from "lucide-react";

export default function Bibliotheque() {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    api
      .get<DocumentItem[]>("/documents")
      .then((res) => setDocuments(res.data))
      .finally(() => setLoading(false));
  }, []);

  async function handleDelete(id: string) {
    await api.delete(`/documents/${id}`);
    setDocuments((prev) => prev.filter((d) => d.id !== id));
  }

  function handleUploaded(doc: DocumentItem) {
    setDocuments((prev) => [doc, ...prev]);
  }

  const filtered = documents.filter((d) =>
    d.original_filename.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="h-full overflow-y-auto bg-slate-50 p-8">
      {/* Page Header */}
      <div className="mb-8 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-emerald-700 mb-1">
            <FolderOpen className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-wider">Gestion documentaire</span>
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Bibliothèque de documents</h1>
          <p className="mt-1 text-xs text-slate-500">
            Tous vos compte-rendus, spécifications et guides indexés pour la recherche RAG.
          </p>
        </div>
        <DocumentUploader onUploaded={handleUploaded} />
      </div>

      {/* Search Input */}
      <div className="mb-6 max-w-md">
        <div className="relative">
          <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Rechercher un document par nom..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-xl border border-slate-300 bg-white pl-10 pr-4 py-2 text-xs text-slate-800 placeholder:text-slate-400 outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 transition shadow-sm"
          />
        </div>
      </div>

      {/* Documents List */}
      {loading ? (
        <div className="flex justify-center p-12 text-xs font-semibold text-slate-400">
          Chargement de la bibliothèque...
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
          <FolderOpen className="mx-auto h-10 w-10 text-slate-300 mb-3" />
          <p className="text-sm font-semibold text-slate-700">Aucun document trouvé</p>
          <p className="mt-1 text-xs text-slate-400">
            {search ? "Modifiez votre recherche" : "Importez votre premier document (PDF, DOCX, TXT, MD)"}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((doc) => (
            <DocumentCard key={doc.id} document={doc} onDelete={handleDelete} />
          ))}
        </div>
      )}
    </div>
  );
}