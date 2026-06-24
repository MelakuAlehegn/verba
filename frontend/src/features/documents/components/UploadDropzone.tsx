import { Loader2, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";
import { useUploadDocument } from "@/features/documents/hooks";
import { cn } from "@/lib/utils";

// Mirror the backend's allowlist + size cap so we reject early with a clear message.
const ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md", ".docx"];
const MAX_BYTES = 25 * 1024 * 1024;

function validate(file: File): string | null {
  const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
  if (!ALLOWED_EXTENSIONS.includes(ext)) {
    return `${file.name}: unsupported type. Use PDF, TXT, MD, or DOCX.`;
  }
  if (file.size > MAX_BYTES) {
    return `${file.name}: too large (max 25 MB).`;
  }
  return null;
}

export function UploadDropzone() {
  const upload = useUploadDocument();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);

  const handleFiles = (files: FileList | null) => {
    if (!files?.length) return;
    for (const file of Array.from(files)) {
      const error = validate(file);
      if (error) {
        toast.error(error);
        continue;
      }
      upload.mutate(file, {
        onSuccess: (doc) => toast(`Uploaded “${doc.filename}” — processing now.`),
        onError: () => toast.error(`Couldn't upload “${file.name}”. Try again.`),
      });
    }
  };

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => inputRef.current?.click()}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          inputRef.current?.click();
        }
      }}
      onDragOver={(event) => {
        event.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={(event) => {
        event.preventDefault();
        setIsDragging(false);
        handleFiles(event.dataTransfer.files);
      }}
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-border bg-card/50 px-6 py-10 text-center transition-colors",
        "hover:border-primary/50 hover:bg-secondary/40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        isDragging && "border-primary bg-secondary/60",
      )}
    >
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-secondary text-primary">
        {upload.isPending ? (
          <Loader2 className="h-5 w-5 animate-spin" />
        ) : (
          <UploadCloud className="h-5 w-5" />
        )}
      </span>
      <div>
        <p className="font-medium">
          {upload.isPending ? "Uploading…" : "Drop files here, or click to browse"}
        </p>
        <p className="mt-1 text-sm text-muted-foreground">PDF, TXT, MD, or DOCX · up to 25 MB</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={ALLOWED_EXTENSIONS.join(",")}
        className="hidden"
        onChange={(event) => {
          handleFiles(event.target.files);
          event.target.value = "";
        }}
      />
    </div>
  );
}
