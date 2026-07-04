import { useEffect, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { ChatComposer } from "@/features/chats/components/ChatComposer";
import { ChatSourcesBar } from "@/features/chats/components/ChatSourcesBar";
import { MessageList } from "@/features/chats/components/MessageList";
import { useMessages } from "@/features/chats/hooks";
import { useChatStream } from "@/features/chats/useChatStream";

export default function ChatPage() {
  const { chatId = "" } = useParams();
  const location = useLocation();
  const navigate = useNavigate();
  const { data: serverMessages = [] } = useMessages(chatId);
  const { pending, isStreaming, send } = useChatStream(chatId);
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

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex-1 overflow-y-auto">
        <MessageList messages={messages} />
      </div>
      <div className="border-t border-border/60">
        <ChatSourcesBar chatId={chatId} />
        <ChatComposer onSend={send} disabled={isStreaming} autoFocus />
      </div>
    </div>
  );
}
