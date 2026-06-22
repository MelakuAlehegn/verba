import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import { chatsQueryKey, messagesQueryKey } from "@/features/chats/hooks";
import { streamMessage } from "@/lib/api/streaming";
import type { Message } from "@/lib/api/types";

function tempMessage(chatId: string, role: "user" | "assistant", content: string): Message {
  return {
    id: `temp-${role}-${crypto.randomUUID()}`,
    chat_id: chatId,
    role,
    content,
    status: role === "assistant" ? "streaming" : "complete",
    model: null,
    token_usage: null,
    created_at: new Date().toISOString(),
    citations: [],
  };
}

/**
 * Drives a chat turn: optimistically shows the user message + a streaming
 * assistant bubble, fills it from the SSE stream, then reconciles with the
 * server (which has persisted the real rows) and clears the optimistic pair.
 */
export function useChatStream(chatId: string) {
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const send = useCallback(
    async (content: string) => {
      const userMessage = tempMessage(chatId, "user", content);
      const assistantMessage = tempMessage(chatId, "assistant", "");
      const assistantId = assistantMessage.id;
      setPending([userMessage, assistantMessage]);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      const patchAssistant = (patch: Partial<Message>) =>
        setPending((prev) =>
          prev.map((message) => (message.id === assistantId ? { ...message, ...patch } : message)),
        );

      try {
        await streamMessage(
          chatId,
          content,
          {
            onDelta: (delta) =>
              setPending((prev) =>
                prev.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: message.content + delta }
                    : message,
                ),
              ),
            onDone: () => patchAssistant({ status: "complete" }),
            onError: () => patchAssistant({ status: "failed" }),
          },
          controller.signal,
        );
        // Server now holds the persisted messages; refetch then drop the optimistic pair.
        await queryClient.invalidateQueries({ queryKey: messagesQueryKey(chatId) });
        await queryClient.invalidateQueries({ queryKey: chatsQueryKey });
        setPending([]);
      } catch {
        patchAssistant({ status: "failed" });
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [chatId, queryClient],
  );

  return { pending, isStreaming, send };
}
