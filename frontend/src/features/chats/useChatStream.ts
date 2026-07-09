import { useQueryClient } from "@tanstack/react-query";
import { useCallback, useRef, useState } from "react";
import { chatsQueryKey, messagesQueryKey } from "@/features/chats/hooks";
import { type StreamCallbacks, streamMessage, streamRegenerate } from "@/lib/api/streaming";
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
 * Drives a chat turn: optimistically shows a streaming assistant bubble, fills
 * it from the SSE stream, then reconciles with the server (which persists the
 * real rows) and clears the optimistic pair. Supports stop (abort) and
 * regenerate (re-answer the last question).
 */
export function useChatStream(chatId: string) {
  const queryClient = useQueryClient();
  const [pending, setPending] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const abortRef = useRef<AbortController | null>(null);

  const refetch = useCallback(async () => {
    await queryClient.invalidateQueries({ queryKey: messagesQueryKey(chatId) });
    await queryClient.invalidateQueries({ queryKey: chatsQueryKey });
  }, [chatId, queryClient]);

  // Shared driver: seed optimistic bubbles, stream into the assistant one, then
  // reconcile. Stopping (abort) still reconciles — the server persisted the
  // partial answer as 'stopped'.
  const drive = useCallback(
    async (
      seed: Message[],
      assistantId: string,
      call: (callbacks: StreamCallbacks, signal: AbortSignal) => Promise<void>,
    ) => {
      setPending(seed);
      setIsStreaming(true);
      const controller = new AbortController();
      abortRef.current = controller;

      const patch = (patch: Partial<Message>) =>
        setPending((prev) =>
          prev.map((message) => (message.id === assistantId ? { ...message, ...patch } : message)),
        );

      try {
        await call(
          {
            onDelta: (delta) =>
              setPending((prev) =>
                prev.map((message) =>
                  message.id === assistantId
                    ? { ...message, content: message.content + delta }
                    : message,
                ),
              ),
            onDone: () => patch({ status: "complete" }),
            onError: () => patch({ status: "failed" }),
          },
          controller.signal,
        );
        await refetch();
        setPending([]);
      } catch {
        if (controller.signal.aborted) {
          // Stopped by the user: the server saved the partial answer.
          await refetch();
          setPending([]);
        } else {
          patch({ status: "failed" });
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [refetch],
  );

  const send = useCallback(
    async (content: string) => {
      const user = tempMessage(chatId, "user", content);
      const assistant = tempMessage(chatId, "assistant", "");
      await drive([user, assistant], assistant.id, (callbacks, signal) =>
        streamMessage(chatId, content, callbacks, signal),
      );
    },
    [chatId, drive],
  );

  const regenerate = useCallback(async () => {
    // Optimistically hide the previous answer so it isn't shown alongside the
    // new streaming one; the refetch reconciles with the server afterwards.
    const key = messagesQueryKey(chatId);
    const current = queryClient.getQueryData<Message[]>(key) ?? [];
    const lastAssistant = [...current].reverse().find((message) => message.role === "assistant");
    if (lastAssistant) {
      queryClient.setQueryData<Message[]>(
        key,
        current.filter((message) => message.id !== lastAssistant.id),
      );
    }
    const assistant = tempMessage(chatId, "assistant", "");
    await drive([assistant], assistant.id, (callbacks, signal) =>
      streamRegenerate(chatId, callbacks, signal),
    );
  }, [chatId, drive, queryClient]);

  const stop = useCallback(() => abortRef.current?.abort(), []);

  return { pending, isStreaming, send, stop, regenerate };
}
