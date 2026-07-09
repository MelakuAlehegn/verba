import { Check, Copy } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";
import { CitationChips } from "@/features/chats/components/CitationChips";
import { Markdown } from "@/features/chats/components/Markdown";
import { cn } from "@/lib/utils";
import type { Message } from "@/lib/api/types";

function CopyButton({ content }: { content: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    toast("Copied to clipboard");
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <button
      type="button"
      onClick={copy}
      className="inline-flex items-center gap-1 text-xs text-muted-foreground transition-colors hover:text-foreground"
    >
      {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isStreaming = message.status === "streaming";
  const isFailed = message.status === "failed";
  const isStopped = message.status === "stopped";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div
        className={cn(
          "max-w-[85%] rounded-xl rounded-bl-md bg-secondary px-4 py-3 text-secondary-foreground",
          isFailed && "bg-destructive/5",
        )}
      >
        {isFailed ? (
          <p className="text-sm text-destructive">
            Something went wrong generating this answer. Try sending again.
          </p>
        ) : message.content ? (
          <>
            <Markdown content={message.content} />
            {isStreaming ? (
              <span className="ml-0.5 inline-block h-4 w-1.5 translate-y-0.5 animate-pulse rounded-sm bg-primary align-middle" />
            ) : (
              <>
                <CitationChips content={message.content} citations={message.citations} />
                <div className="mt-2 flex items-center gap-3">
                  <CopyButton content={message.content} />
                  {isStopped ? (
                    <span className="text-xs text-muted-foreground">Stopped</span>
                  ) : null}
                </div>
              </>
            )}
          </>
        ) : isStreaming ? (
          <span className="inline-flex gap-1 py-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" />
          </span>
        ) : (
          <p className="text-sm text-muted-foreground">Stopped before an answer was generated.</p>
        )}
      </div>
    </div>
  );
}
