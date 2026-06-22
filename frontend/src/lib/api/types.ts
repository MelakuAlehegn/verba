export interface User {
  id: string;
  email: string;
  name: string | null;
  avatar_url: string | null;
  onboarded_at: string | null;
  last_login_at: string | null;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  name?: string | null;
}

export type DocumentStatus =
  | "created"
  | "uploading"
  | "uploaded"
  | "queued"
  | "processing"
  | "ready"
  | "failed"
  | "deleting"
  | "deleted";

export interface Document {
  id: string;
  filename: string;
  mime_type: string;
  size_bytes: number;
  status: DocumentStatus;
  chunk_count: number;
  error_code: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface Chat {
  id: string;
  title: string;
  provider: string;
  pinned_at: string | null;
  archived_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface Citation {
  document_id: string | null;
  chunk_id: string | null;
  rank: number;
  score: number | null;
  quote_preview: string | null;
}

export type MessageRole = "user" | "assistant" | "system";
export type MessageStatus = "pending" | "streaming" | "complete" | "failed";

export interface Message {
  id: string;
  chat_id: string;
  role: MessageRole;
  content: string;
  status: MessageStatus;
  model: string | null;
  token_usage: Record<string, unknown> | null;
  created_at: string;
  citations: Citation[];
}
