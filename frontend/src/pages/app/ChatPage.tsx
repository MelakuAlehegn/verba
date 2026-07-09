import { RefreshCw } from "lucide-react";
import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ChatComposer } from "@/features/chats/components/ChatComposer";
import { ChatSourcesBar } from "@/features/chats/components/ChatSourcesBar";
import { MessageList } from "@/features/chats/components/MessageList";
import { useMessages } from "@/features/chats/hooks";
import { useChatStream } from "@/features/chats/useChatStream";
import { Button } from "@/components/ui/button";

export default function ChatPage() {
  const { chatId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: serverMessages = [] } = useMessages(chatId);
  const { pending, isStreaming, send, stop, regenerate } = useChatStream(chatId);
  const sentInitial = useRef(false);

  // A chat opened from "new chat" carries the first message in router state.
  useEffect(() => {
    const initial = (location.state as { initialMessage?: string } | null)?.initialMessage;
    if (initial && !sentInitial.current) {
      sentInitial.current = true;
      navigate(location.pathname, { replace: true, state: null });
      void send(initial);
    }
  }, [location, navigate, send]);

  const messages = [...serverMessages, ...pending];
  const last = messages[messages.length - 1];
  // Offer regenerate once a finished answer sits at the end of the thread.
  const canRegenerate =
    !isStreaming && last?.role === "assistant" && messages.some((m) => m.role === "user");

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>
      <div className="border-t border-border/60">
        {canRegenerate ? (
          <div className="mx-auto flex w-full max-w-3xl justify-center px-4 pt-3">
            <Button variant="outline" size="sm" className="gap-2 rounded-full" onClick={regenerate}>
              <RefreshCw className="h-3.5 w-3.5" />
              Regenerate
            </Button>
          </div>
        ) : null}
        <ChatSourcesBar chatId={chatId} />
        <ChatComposer onSend={send} disabled={isStreaming} streaming={isStreaming} onStop={stop} autoFocus />
      </div>
    </div>
  );
}
