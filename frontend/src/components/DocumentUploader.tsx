import { useRef, useState } from "react";
import { Upload, Loader2 } from "lucide-react";
import api from "@/hooks/useApi";
import type { DocumentItem } from "@/types";

interface DocumentUploaderProps {
  onUploaded: (doc: DocumentItem) => void;
}

export default function DocumentUploader({ onUploaded }: DocumentUploaderProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await api.post("/documents/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onUploaded(res.data.document as DocumentItem);
    } catch {
      setError("Échec de l'envoi. Vérifiez le format (PDF, DOCX, TXT, MD) et la taille.");
    } finally {
      setUploading(false);
      if (inputRef.current) inputRef.current.value = "";
    }
  }

  return (
    <div className="space-y-1.5">
      <button
        onClick={() => inputRef.current?.click()}
        disabled={uploading}
        className="inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-emerald-700 active:bg-emerald-800 disabled:opacity-50"
      >
        {uploading ? (
          <>
            <Loader2 size={15} className="animate-spin" />
            <span>Envoi en cours...</span>
          </>
        ) : (
          <>
            <Upload size={15} />
            <span>Ajouter un document</span>
          </>
        )}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,.txt,.md"
        onChange={handleFileChange}
        className="hidden"
      />
      {error && <p className="text-xs font-medium text-red-600">{error}</p>}
    </div>
  );
}