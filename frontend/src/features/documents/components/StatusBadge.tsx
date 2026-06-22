import { AlertCircle, CheckCircle2, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DocumentStatus } from "@/lib/api/types";

type Tone = "ready" | "failed" | "progress";

const STATUS_META: Record<DocumentStatus, { label: string; tone: Tone }> = {
  created: { label: "Pending", tone: "progress" },
  uploading: { label: "Uploading", tone: "progress" },
  uploaded: { label: "Pending", tone: "progress" },
  queued: { label: "Queued", tone: "progress" },
  processing: { label: "Processing", tone: "progress" },
  ready: { label: "Ready", tone: "ready" },
  failed: { label: "Failed", tone: "failed" },
  deleting: { label: "Deleting", tone: "progress" },
  deleted: { label: "Deleted", tone: "progress" },
};

const TONE_CLASSES: Record<Tone, string> = {
  ready: "bg-primary/10 text-primary",
  failed: "bg-destructive/10 text-destructive",
  progress: "bg-muted text-muted-foreground",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  const { label, tone } = STATUS_META[status];
  const Icon = tone === "ready" ? CheckCircle2 : tone === "failed" ? AlertCircle : Loader2;

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium",
        TONE_CLASSES[tone],
      )}
    >
      <Icon className={cn("h-3.5 w-3.5", tone === "progress" && "animate-spin")} />
      {label}
    </span>
  );
}
