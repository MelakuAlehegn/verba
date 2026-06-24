import { FileText } from "lucide-react";
import { useState } from "react";
import { useDocuments } from "@/features/documents/hooks";
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import type { Citation } from "@/lib/api/types";

export function CitationChips({
  content,
  citations,
}: {
  content: string;
  citations: Citation[];
}) {
  const { data: documents } = useDocuments();
  const [open, setOpen] = useState(false);

  // Show only the sources the answer actually referenced (e.g. "[Source 2]"),
  // not every chunk that was retrieved as context.
  const citedRanks = new Set(
    [...content.matchAll(/source\s+(\d+)/gi)].map((match) => Number(match[1])),
  );
  const cited = citations.filter((citation) => citedRanks.has(citation.rank));

  if (cited.length === 0) return null;

  const filenameFor = (documentId: string | null) =>
    (documentId && documents?.find((doc) => doc.id === documentId)?.filename) || "Source unavailable";

  return (
    <>
      <div className="mt-3 flex flex-wrap items-center gap-1.5 border-t border-border/60 pt-2">
        <span className="text-xs text-muted-foreground">Sources</span>
        {cited.map((citation) => (
          <button
            key={citation.rank}
            type="button"
            onClick={() => setOpen(true)}
            className="rounded-md bg-background px-1.5 py-0.5 text-xs font-medium text-primary ring-1 ring-border transition-colors hover:bg-secondary"
            title={filenameFor(citation.document_id)}
          >
            {citation.rank}
          </button>
        ))}
      </div>

      <Sheet open={open} onOpenChange={setOpen}>
        <SheetContent className="w-full overflow-y-auto sm:max-w-md">
          <SheetHeader>
            <SheetTitle>Sources</SheetTitle>
            <SheetDescription>The passages this answer drew from.</SheetDescription>
          </SheetHeader>
          <div className="mt-6 space-y-5">
            {cited.map((citation) => (
              <div key={citation.rank} className="rounded-lg border border-border bg-card p-4">
                <div className="flex items-center gap-2 text-sm font-medium">
                  <span className="flex h-5 w-5 items-center justify-center rounded bg-secondary text-xs text-primary">
                    {citation.rank}
                  </span>
                  <FileText className="h-4 w-4 text-muted-foreground" />
                  <span className="truncate">{filenameFor(citation.document_id)}</span>
                </div>
                <p className="mt-2 border-l-2 border-border pl-3 text-sm text-muted-foreground">
                  {citation.quote_preview ?? "No preview available."}
                </p>
              </div>
            ))}
          </div>
        </SheetContent>
      </Sheet>
    </>
  );
}
