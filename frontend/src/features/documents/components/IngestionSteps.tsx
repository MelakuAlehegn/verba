import { AlertCircle, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { DocumentStatus } from "@/lib/api/types";

// The real, backend-driven ingestion lifecycle. "Processing" covers parse →
// chunk → embed, which the worker logs but doesn't persist as separate states.
const STEPS = [
  { label: "Uploaded", hint: "File received" },
  { label: "Queued", hint: "Waiting for the worker" },
  { label: "Processing", hint: "Parsing, chunking & embedding" },
  { label: "Indexed", hint: "Ready to answer questions" },
] as const;

// Map a status to the step in flight. `current === STEPS.length` means every
// step is done (ready); on failure the run stopped at "Processing".
function progressOf(status: DocumentStatus): { current: number; failed: boolean } {
  switch (status) {
    case "created":
    case "uploading":
    case "uploaded":
      return { current: 0, failed: false };
    case "queued":
      return { current: 1, failed: false };
    case "processing":
      return { current: 2, failed: false };
    case "ready":
      return { current: STEPS.length, failed: false };
    case "failed":
      return { current: 2, failed: true };
    default:
      return { current: 0, failed: false };
  }
}

type StepState = "done" | "current" | "pending" | "failed";

export function IngestionSteps({ status }: { status: DocumentStatus }) {
  const { current, failed } = progressOf(status);

  return (
    <ol className="flex flex-col">
      {STEPS.map((step, index) => {
        const isLast = index === STEPS.length - 1;
        const state: StepState =
          failed && index === current
            ? "failed"
            : index < current
              ? "done"
              : index === current
                ? "current"
                : "pending";

        return (
          <li key={step.label} className="flex gap-3">
            {/* Node + connector rail */}
            <div className="flex flex-col items-center">
              <span
                className={cn(
                  "flex h-6 w-6 items-center justify-center rounded-full border transition-colors duration-500",
                  state === "done" && "border-primary bg-primary text-primary-foreground",
                  state === "current" &&
                    "border-primary bg-primary/10 text-primary ring-4 ring-primary/10",
                  state === "failed" &&
                    "border-destructive bg-destructive text-destructive-foreground",
                  state === "pending" && "border-border bg-transparent text-muted-foreground/40",
                )}
              >
                {state === "done" ? (
                  <Check className="h-3.5 w-3.5" />
                ) : state === "failed" ? (
                  <AlertCircle className="h-3.5 w-3.5" />
                ) : state === "current" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <span className="h-1.5 w-1.5 rounded-full bg-current" />
                )}
              </span>
              {!isLast ? (
                <span
                  className={cn(
                    "my-1 w-px flex-1 transition-colors duration-500",
                    index < current ? "bg-primary" : "bg-border",
                  )}
                />
              ) : null}
            </div>

            {/* Label + contextual hint */}
            <div className={cn("min-w-0", isLast ? "pb-0" : "pb-4")}>
              <p
                className={cn(
                  "text-sm leading-6 transition-colors duration-500",
                  state === "done" && "text-foreground",
                  state === "current" && "font-medium text-foreground",
                  state === "failed" && "font-medium text-destructive",
                  state === "pending" && "text-muted-foreground/60",
                )}
              >
                {step.label}
              </p>
              {state === "current" || state === "failed" ? (
                <p
                  className={cn(
                    "text-xs",
                    state === "failed" ? "text-destructive/80" : "text-muted-foreground",
                  )}
                >
                  {step.hint}
                </p>
              ) : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
