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
