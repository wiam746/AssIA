import { useEffect, useState, useRef } from "react";
import api from "@/hooks/useApi";
import type { DocumentItem } from "@/types";
import { FileText, Upload, Loader2, Link as LinkIcon, Check } from "lucide-react";

interface DocumentSelectorProps {
  selectedDocumentId?: string;
  onSelectDocument: (docId: string | undefined) => void;
}

export default function DocumentSelector({ selectedDocumentId, onSelectDocument }: DocumentSelectorProps) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [loadingDocs, setLoadingDocs] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetchDocuments();
  }, []);

  async function fetchDocuments() {
    setLoadingDocs(true);
    try {
      const res = await api.get<DocumentItem[]>("/documents");
      setDocuments(res.data || []);
    } catch {
      // Quiet fallback
    } finally {
      setLoadingDocs(false);
    }
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
      const newDoc = res.data.document as DocumentItem;
      setDocuments((prev) => [newDoc, ...prev]);
      onSelectDocument(newDoc.id);
    } catch {
      setUploadError("Échec de l'envoi du fichier.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  }

  const selectedDoc = documents.find((d) => d.id === selectedDocumentId);

  return (
    <div className="space-y-2">
      <label className="block text-xs font-medium text-slate-700 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <FileText size={14} className="text-emerald-600" />
          <span>Document associé (Bibliothèque)</span>
        </span>
        {selectedDocumentId && (
          <button
            type="button"
            onClick={() => onSelectDocument(undefined)}
            className="text-[11px] font-semibold text-red-500 hover:underline"
          >
            Dissocier
          </button>
        )}
      </label>

      {/* Select Existing Document */}
      <div className="flex gap-2">
        <select
          value={selectedDocumentId || ""}
          onChange={(e) => onSelectDocument(e.target.value || undefined)}
          disabled={loadingDocs}
          className="flex-1 rounded-lg border border-slate-300 bg-slate-50/50 px-3 py-2 text-xs text-slate-900 focus:bg-white focus:border-emerald-500 focus:ring-2 focus:ring-emerald-500/20 outline-none transition disabled:opacity-50"
        >
          <option value="">-- Choisir un document dans la bibliothèque --</option>
          {documents.map((doc) => (
            <option key={doc.id} value={doc.id}>
              📄 {doc.original_filename} ({doc.status === "indexed" ? "Indexé" : "En cours"})
            </option>
          ))}
        </select>

        {/* Upload New Document directly */}
        <button
          type="button"
          onClick={() => fileInputRef.current?.click()}
          disabled={uploading}
          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50 active:bg-slate-100 disabled:opacity-50 shrink-0"
        >
          {uploading ? (
            <Loader2 size={14} className="animate-spin text-emerald-600" />
          ) : (
            <Upload size={14} className="text-emerald-600" />
          )}
          <span>{uploading ? "Import..." : "Uploader"}</span>
        </button>

        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.txt,.md"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>

      {uploadError && <p className="text-[11px] font-medium text-red-600">{uploadError}</p>}

      {/* Preview Selected Doc */}
      {selectedDoc && (
        <div className="flex items-center gap-2 rounded-lg bg-emerald-50 border border-emerald-200 p-2 text-xs text-emerald-900">
          <LinkIcon size={14} className="text-emerald-600 shrink-0" />
          <span className="truncate font-medium flex-1">{selectedDoc.original_filename}</span>
          <span className="inline-flex items-center gap-1 rounded bg-emerald-200/60 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-800">
            <Check size={10} /> Associé
          </span>
        </div>
      )}
    </div>
  );
}
