import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { BrandOrb } from "@/features/chats/components/BrandOrb";
import { ChatComposer } from "@/features/chats/components/ChatComposer";
import { SourcePicker } from "@/features/chats/components/SourcePicker";
import { useCreateChat } from "@/features/chats/hooks";
import { setChatSources } from "@/lib/api/chats";
import { LANDING_INTENT_KEY } from "@/pages/landing/LandingPage";

const EXAMPLES = [
  "Summarize these documents",
  "What are the key points?",
  "List any action items",
  "What does it say about pricing?",
];

export default function AppIndexPage() {
  const navigate = useNavigate();
  const createChat = useCreateChat();
  const [selected, setSelected] = useState<string[]>([]);
  const [starting, setStarting] = useState(false);

  // A question typed on the landing page is handed off here, prefilled so the
  // user can review and send (read once, then cleared).
  const [intent] = useState(() => {
    const stored = sessionStorage.getItem(LANDING_INTENT_KEY);
    if (stored) sessionStorage.removeItem(LANDING_INTENT_KEY);
    return stored ?? "";
  });

  const canStart = selected.length > 0 && !starting;

  const startChat = async (content: string) => {
    if (selected.length === 0) {
      toast.error("Pick at least one source for this chat.");
      return;
    }
    const title = content.length > 48 ? `${content.slice(0, 48)}…` : content;
    setStarting(true);
    try {
      const chat = await createChat.mutateAsync(title);
      await setChatSources(chat.id, selected);
      navigate(`/app/chats/${chat.id}`, { state: { initialMessage: content } });
    } catch {
      toast.error("Couldn't start a new chat. Try again.");
      setStarting(false);
    }
  };

  return (
    <div className="flex flex-1 flex-col items-center justify-center">
      <div className="w-full max-w-2xl px-4 text-center">
        <div className="mb-8 flex justify-center">
          <BrandOrb />
        </div>
        <h1 className="text-balance text-3xl font-semibold tracking-tight sm:text-4xl">
          Ask anything about your documents.
        </h1>
        <p className="mx-auto mt-3 max-w-md text-balance text-muted-foreground">
          Verba answers from the sources you pick and shows the passages it used.
        </p>

        {/* Source gate — a chat must be grounded in at least one document. */}
        <div className="mt-6 rounded-xl border border-border bg-card/50 p-4 text-left">
          <p className="mb-3 text-sm font-medium">Sources for this chat</p>
          <SourcePicker selected={selected} onChange={setSelected} />
          {selected.length === 0 ? (
            <p className="mt-3 text-xs text-muted-foreground">
              Select at least one document to start asking.
            </p>
          ) : null}
        </div>

        {selected.length > 0 ? (
          <div className="mt-6 flex flex-wrap justify-center gap-2">
            {EXAMPLES.map((example) => (
              <Button
                key={example}
                variant="outline"
                size="sm"
                className="rounded-full"
                disabled={!canStart}
                onClick={() => startChat(example)}
              >
                {example}
              </Button>
            ))}
          </div>
        ) : null}
      </div>

      <div className="mt-6 w-full">
        <ChatComposer
          onSend={startChat}
          disabled={!canStart}
          autoFocus
          initialValue={intent}
          placeholder={
            selected.length === 0
              ? "Select a source above to start…"
              : "Ask anything about your sources…"
          }
        />
      </div>
    </div>
  );
}
