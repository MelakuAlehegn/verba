import { useParams } from "react-router-dom";

export default function ChatPage() {
  const { chatId } = useParams<{ chatId: string }>();

  return (
    <div className="text-muted-foreground">
      Chat workspace for <code className="text-foreground">{chatId}</code> ships in F5.
    </div>
  );
}
