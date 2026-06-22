import { Markdown } from "@/features/chats/components/Markdown";
import { cn } from "@/lib/utils";
import type { Message } from "@/lib/api/types";

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isStreaming = message.status === "streaming";
  const isFailed = message.status === "failed";

  if (isUser) {
    return (
      <div className="flex justify-end">
        <div className="max-w-[85%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-sm text-primary-foreground">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start">
      <div
        className={cn(
          "max-w-[85%] rounded-2xl rounded-bl-md bg-secondary px-4 py-3 text-secondary-foreground",
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
            ) : null}
          </>
        ) : (
          <span className="inline-flex gap-1 py-1">
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.3s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50 [animation-delay:-0.15s]" />
            <span className="h-2 w-2 animate-bounce rounded-full bg-muted-foreground/50" />
          </span>
        )}
      </div>
    </div>
  );
}
