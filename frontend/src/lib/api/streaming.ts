import { env } from "@/config/env";
import type { Citation } from "@/lib/api/types";

export interface StreamDonePayload {
  chat_id: string;
  message_id: string;
  citations: Citation[];
}

export interface StreamCallbacks {
  onDelta: (text: string) => void;
  onDone: (payload: StreamDonePayload) => void;
  onError: (error: Error) => void;
}

function handleFrame(frame: string, callbacks: StreamCallbacks) {
  // A frame is an optional `event:` line plus a `data:` line (SSE).
  let event: string | null = null;
  const dataLines: string[] = [];
  for (const line of frame.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (dataLines.length === 0) return;

  const data = JSON.parse(dataLines.join("\n"));
  if (event === "done") callbacks.onDone(data as StreamDonePayload);
  else if (event === "error") callbacks.onError(new Error(data.message ?? "Generation failed"));
  else if (typeof data.delta === "string") callbacks.onDelta(data.delta);
}

async function readSse(response: Response, callbacks: StreamCallbacks): Promise<void> {
  if (!response.ok || !response.body) {
    callbacks.onError(new Error(`Stream failed (${response.status})`));
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const frames = buffer.split("\n\n");
    buffer = frames.pop() ?? ""; // keep the trailing partial frame
    for (const frame of frames) {
      if (frame.trim()) handleFrame(frame, callbacks);
    }
  }
  if (buffer.trim()) handleFrame(buffer, callbacks);
}

/**
 * Stream an assistant reply over SSE. The endpoint is a POST returning
 * text/event-stream, so we read the body with a ReadableStream reader rather
 * than EventSource (which only supports GET). Abort the `signal` to stop.
 */
export async function streamMessage(
  chatId: string,
  content: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${env.apiUrl}/chats/${chatId}/messages/stream`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
    signal,
  });
  await readSse(response, callbacks);
}

/** Re-answer the chat's last question: the server drops the old answer and
 *  streams a fresh one. No body — the question is taken from history. */
export async function streamRegenerate(
  chatId: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch(`${env.apiUrl}/chats/${chatId}/messages/regenerate`, {
    method: "POST",
    credentials: "include",
    signal,
  });
  await readSse(response, callbacks);
}
