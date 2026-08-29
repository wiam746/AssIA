export interface User {
  id: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  created_at: string;
}

export interface Conversation {
  id: string;
  title: string;
  projet_id?: string;
  created_at: string;
  updated_at: string;
  messages: Message[];
}

export interface ChatResponse {
  conversation_id: string;
  message: Message;
  sources: string[];
}

export interface DocumentItem {
  id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  content_type?: string;
  status: "pending" | "processing" | "indexed" | "error";
  error_message?: string;
  created_at: string;
  indexed_at?: string;
}

export interface Reunion {
  id: string;
  title: string;
  meeting_date?: string;
  participants?: string;
  objet?: string;
  summary?: string;
  decisions?: string;
  actions?: string;
  prochaine_reunion?: string;
  status: "brouillon" | "valide";
  document_id?: string;
  document?: DocumentItem;
  created_at: string;
}

export interface Incident {
  id: string;
  title: string;
  description: string;
  severity: "mineur" | "majeur" | "critique";
  status: "ouvert" | "en_cours" | "resolu" | "ferme";
  analysis?: string;
  resolution?: string;
  document_id?: string;
  document?: DocumentItem;
  created_at: string;
  resolved_at?: string;
}

export interface Projet {
  id: string;
  name: string;
  description?: string;
  status: "actif" | "en_pause" | "termine" | "archive";
  document_id?: string;
  document?: DocumentItem;
  created_at: string;
  updated_at: string;
}