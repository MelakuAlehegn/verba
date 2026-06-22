import { FileText, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { StatusBadge } from "@/features/documents/components/StatusBadge";
import { useDeleteDocument } from "@/features/documents/hooks";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import type { Document } from "@/lib/api/types";

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  const units = ["KB", "MB", "GB"];
  let value = bytes / 1024;
  let unit = 0;
  while (value >= 1024 && unit < units.length - 1) {
    value /= 1024;
    unit += 1;
  }
  return `${value.toFixed(value >= 10 || unit === 0 ? 0 : 1)} ${units[unit]}`;
}

export function DocumentCard({ document }: { document: Document }) {
  const remove = useDeleteDocument();

  const meta =
    document.status === "ready"
      ? `${formatBytes(document.size_bytes)} · ${document.chunk_count} chunks`
      : formatBytes(document.size_bytes);

  const handleDelete = () => {
    remove.mutate(document.id, {
      onSuccess: () => toast(`Removed “${document.filename}”.`),
      onError: () => toast.error("Couldn't remove that document. Try again."),
    });
  };

  return (
    <div className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 shadow-sm transition-shadow hover:shadow-md">
      <div className="flex items-start gap-3">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-secondary text-primary">
          <FileText className="h-5 w-5" />
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-medium" title={document.filename}>
            {document.filename}
          </p>
          <p className="mt-0.5 text-xs text-muted-foreground">{meta}</p>
        </div>

        <AlertDialog>
          <AlertDialogTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
              aria-label={`Delete ${document.filename}`}
              disabled={remove.isPending}
            >
              {remove.isPending ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </Button>
          </AlertDialogTrigger>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Delete this document?</AlertDialogTitle>
              <AlertDialogDescription>
                “{document.filename}” and everything Verba indexed from it will be removed.
                Answers that cited it will keep their saved excerpts.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>Cancel</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDelete}
                className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
              >
                Delete
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>

      <div className="flex items-center justify-between">
        <StatusBadge status={document.status} />
      </div>

      {document.status === "failed" && document.error_message ? (
        <p className="rounded-lg bg-destructive/5 px-3 py-2 text-xs text-destructive">
          {document.error_message}
        </p>
      ) : null}
    </div>
  );
}
