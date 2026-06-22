import { apiClient } from "@/lib/api/client";
import type { Document } from "@/lib/api/types";

export function listDocuments(): Promise<Document[]> {
  return apiClient<Document[]>("/documents");
}

export function uploadDocument(file: File): Promise<Document> {
  const form = new FormData();
  form.append("file", file);
  return apiClient<Document>("/documents", { method: "POST", body: form });
}

export function deleteDocument(id: string): Promise<void> {
  return apiClient<void>(`/documents/${id}`, { method: "DELETE" });
}
