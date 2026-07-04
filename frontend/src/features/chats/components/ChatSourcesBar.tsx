import { FileText, Library, Pencil, X } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { SourcePicker } from "@/features/chats/components/SourcePicker";
import { useChatSources, useSetChatSources } from "@/features/chats/hooks";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

/** Shows the documents a chat is scoped to, with a popover to change them.
 *  No sources attached → the chat searches all documents (legacy chats). */
export function ChatSourcesBar({ chatId }: { chatId: string }) {
  const { data: sources = [] } = useChatSources(chatId);
  const save = useSetChatSources(chatId);
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string[]>([]);

  // Seed the picker with the current scope whenever the popover opens.
  useEffect(() => {
    if (open) setDraft(sources.map((doc) => doc.id));
  }, [open, sources]);

  const commit = () => {
    save.mutate(draft, {
      onSuccess: () => {
        setOpen(false);
        toast("Sources updated.");
      },
      onError: () => toast.error("Couldn't update sources. Try again."),
    });
  };

  const removeSource = (id: string) => {
    save.mutate(
      sources.filter((doc) => doc.id !== id).map((doc) => doc.id),
      { onError: () => toast.error("Couldn't remove that source. Try again.") },
    );
  };

  return (
    <div className="mx-auto flex w-full max-w-3xl items-center gap-2 px-4 py-2">
      <span className="flex shrink-0 items-center gap-1.5 text-xs text-muted-foreground">
        <Library className="h-3.5 w-3.5" />
        Sources
      </span>

      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
        {sources.length === 0 ? (
          <span className="text-xs text-muted-foreground">All documents</span>
        ) : (
          sources.map((doc) => (
            <span
              key={doc.id}
              title={doc.filename}
              className="inline-flex max-w-[180px] items-center gap-1 rounded-full bg-secondary py-1 pl-2.5 pr-1 text-xs text-secondary-foreground"
            >
              <FileText className="h-3 w-3 shrink-0" />
              <span className="truncate">{doc.filename}</span>
              <button
                type="button"
                onClick={() => removeSource(doc.id)}
                disabled={save.isPending}
                aria-label={`Remove ${doc.filename} from this chat`}
                className="ml-0.5 shrink-0 rounded-full p-0.5 text-secondary-foreground/60 transition-colors hover:bg-background/60 hover:text-foreground disabled:opacity-50"
              >
                <X className="h-3 w-3" />
              </button>
            </span>
          ))
        )}
      </div>

      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button variant="ghost" size="sm" className="h-7 shrink-0 gap-1.5 text-xs">
            <Pencil className="h-3.5 w-3.5" /> Edit
          </Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-96">
          <p className="mb-3 text-sm font-medium">Sources for this chat</p>
          <SourcePicker selected={draft} onChange={setDraft} />
          <div className="mt-4 flex justify-end gap-2">
            <Button variant="ghost" size="sm" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button size="sm" onClick={commit} disabled={save.isPending}>
              Save
            </Button>
          </div>
        </PopoverContent>
      </Popover>
    </div>
  );
}
