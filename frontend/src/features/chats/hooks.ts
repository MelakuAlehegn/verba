import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createChat,
  deleteChat,
  listChatSources,
  listChats,
  listMessages,
  renameChat,
  setChatSources,
} from "@/lib/api/chats";

export const chatsQueryKey = ["chats"] as const;
export const messagesQueryKey = (chatId: string) => ["chats", chatId, "messages"] as const;
export const chatSourcesQueryKey = (chatId: string) => ["chats", chatId, "sources"] as const;

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

export function useChatSources(chatId: string) {
  return useQuery({
    queryKey: chatSourcesQueryKey(chatId),
    queryFn: () => listChatSources(chatId),
    enabled: Boolean(chatId),
  });
}

export function useSetChatSources(chatId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (documentIds: string[]) => setChatSources(chatId, documentIds),
    onSuccess: (sources) => {
      queryClient.setQueryData(chatSourcesQueryKey(chatId), sources);
    },
  });
}
