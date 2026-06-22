import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { createChat, deleteChat, listChats, listMessages, renameChat } from "@/lib/api/chats";

export const chatsQueryKey = ["chats"] as const;
export const messagesQueryKey = (chatId: string) => ["chats", chatId, "messages"] as const;

export function useChats() {
  return useQuery({ queryKey: chatsQueryKey, queryFn: listChats });
}

export function useMessages(chatId: string) {
  return useQuery({
    queryKey: messagesQueryKey(chatId),
    queryFn: () => listMessages(chatId),
    enabled: Boolean(chatId),
  });
}

export function useCreateChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (title?: string) => createChat(title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatsQueryKey }),
  });
}

export function useRenameChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, title }: { id: string; title: string }) => renameChat(id, title),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatsQueryKey }),
  });
}

export function useDeleteChat() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => deleteChat(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: chatsQueryKey }),
  });
}
