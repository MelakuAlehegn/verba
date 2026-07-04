import { Check, FileText, Loader2, Plus } from "lucide-react";
import { useState } from "react";
import { UploadDropzone } from "@/features/documents/components/UploadDropzone";
import { useDocuments } from "@/features/documents/hooks";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const IN_PROGRESS = ["created", "uploading", "uploaded", "queued", "processing"];

interface SourcePickerProps {
  selected: string[];
  onChange: (ids: string[]) => void;
}

/** Pick which documents a chat draws on. Ready docs are selectable; docs still
 *  ingesting show a spinner (not yet answerable); "Upload" adds more inline. */
export function SourcePicker({ selected, onChange }: SourcePickerProps) {
  const { data: documents = [], isLoading } = useDocuments();
  const [showUpload, setShowUpload] = useState(false);

  const toggle = (id: string) => {
    onChange(selected.includes(id) ? selected.filter((x) => x !== id) : [...selected, id]);
  };

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading your documents…</p>;
  }

  if (documents.length === 0) {
    return (
      <div className="space-y-3">
        <p className="text-sm text-muted-foreground">Upload a document to ask about.</p>
        <UploadDropzone />
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {documents.map((doc) => {
          const isReady = doc.status === "ready";
          const isSelected = selected.includes(doc.id);
          const inProgress = IN_PROGRESS.includes(doc.status);
          return (
            <button
              key={doc.id}
              type="button"
              disabled={!isReady}
              onClick={() => toggle(doc.id)}
              title={isReady ? doc.filename : `${doc.filename} — ${doc.status}`}
              className={cn(
                "inline-flex max-w-[220px] items-center gap-1.5 rounded-full border px-3 py-1.5 text-sm transition-colors",
                isSelected
                  ? "border-primary bg-primary text-primary-foreground"
                  : isReady
                    ? "border-border bg-card hover:bg-secondary"
                    : "cursor-not-allowed border-border bg-muted/40 text-muted-foreground",
              )}
            >
              {isSelected ? (
                <Check className="h-3.5 w-3.5 shrink-0" />
              ) : inProgress ? (
                <Loader2 className="h-3.5 w-3.5 shrink-0 animate-spin" />
              ) : (
                <FileText className="h-3.5 w-3.5 shrink-0" />
              )}
              <span className="truncate">{doc.filename}</span>
            </button>
          );
        })}
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="gap-1.5 rounded-full"
          onClick={() => setShowUpload((value) => !value)}
        >
          <Plus className="h-3.5 w-3.5" /> Upload
        </Button>
      </div>
      {showUpload ? <UploadDropzone /> : null}
    </div>
  );
}
