import { apiClient } from "@/lib/api/client";
import type { Chat, Message } from "@/lib/api/types";

export function listChats(): Promise<Chat[]> {
  return apiClient<Chat[]>("/chats");
}

export function createChat(title?: string): Promise<Chat> {
  return apiClient<Chat>("/chats", { method: "POST", body: title ? { title } : {} });
}

export function renameChat(id: string, title: string): Promise<Chat> {
  return apiClient<Chat>(`/chats/${id}`, { method: "PATCH", body: { title } });
}

export function deleteChat(id: string): Promise<void> {
  return apiClient<void>(`/chats/${id}`, { method: "DELETE" });
}

export function listMessages(chatId: string, limit = 100, offset = 0): Promise<Message[]> {
  return apiClient<Message[]>(`/chats/${chatId}/messages?limit=${limit}&offset=${offset}`);
}
