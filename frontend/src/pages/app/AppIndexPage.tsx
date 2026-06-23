import { FileText } from "lucide-react";
import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ChatComposer } from "@/features/chats/components/ChatComposer";
import { useCreateChat } from "@/features/chats/hooks";
import { useDocuments } from "@/features/documents/hooks";
import { LANDING_INTENT_KEY } from "@/pages/landing/LandingPage";

const EXAMPLES = [
  "Summarize my documents",
  "What are the key points?",
  "List any action items",
  "What does it say about pricing?",
];

export default function AppIndexPage() {
  const navigate = useNavigate();
  const createChat = useCreateChat();
  const { data: documents } = useDocuments();
  const hasReadyDocs = (documents ?? []).some((doc) => doc.status === "ready");

  // A question typed on the landing page is handed off here, prefilled so the
  // user can review and send (read once, then cleared).
  const [intent] = useState(() => {
    const stored = sessionStorage.getItem(LANDING_INTENT_KEY);
    if (stored) sessionStorage.removeItem(LANDING_INTENT_KEY);
    return stored ?? "";
  });

  const startChat = async (content: string) => {
    const title = content.length > 48 ? `${content.slice(0, 48)}…` : content;
    try {
      const chat = await createChat.mutateAsync(title);
      navigate(`/app/chats/${chat.id}`, { state: { initialMessage: content } });
    } catch {
      toast.error("Couldn't start a new chat. Try again.");
    }
  };

  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      <div className="w-full max-w-2xl px-4 text-center">
        <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          Ask anything about your documents.
        </h1>
        <p className="mx-auto mt-3 max-w-md text-balance text-muted-foreground">
          Verba answers from your own files and shows the passages it used.
        </p>

        {hasReadyDocs ? (
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {EXAMPLES.map((example) => (
              <Button
                key={example}
                variant="outline"
                size="sm"
                className="rounded-full"
                disabled={createChat.isPending}
                onClick={() => startChat(example)}
              >
                {example}
              </Button>
            ))}
          </div>
        ) : (
          <div className="mt-6 inline-flex items-center gap-2 rounded-full bg-secondary px-4 py-2 text-sm text-muted-foreground">
            <FileText className="h-4 w-4" />
            <span>
              Add a document first —{" "}
              <Link to="/app/documents" className="font-medium text-primary hover:underline">
                go to Documents
              </Link>
            </span>
          </div>
        )}
      </div>

      <div className="mt-6 w-full">
        <ChatComposer
          onSend={startChat}
          disabled={createChat.isPending}
          autoFocus
          initialValue={intent}
        />
      </div>
    </div>
  );
}
