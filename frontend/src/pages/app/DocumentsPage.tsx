import { DocumentCard } from "@/features/documents/components/DocumentCard";
import { UploadDropzone } from "@/features/documents/components/UploadDropzone";
import { useDocuments } from "@/features/documents/hooks";
import { Skeleton } from "@/components/ui/skeleton";

export default function DocumentsPage() {
  const { data: documents, isLoading, isError, refetch } = useDocuments();

  return (
    <div className="mx-auto w-full max-w-4xl px-6 py-8">
      <header className="mb-6">
        <h1 className="text-2xl font-semibold tracking-tight">Documents</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload the files Verba should answer from. Each one is processed, then ready to ask about.
        </p>
      </header>

      <UploadDropzone />

      <section className="mt-8">
        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {Array.from({ length: 4 }).map((_, index) => (
              <Skeleton key={index} className="h-28 rounded-xl" />
            ))}
          </div>
        ) : isError ? (
          <div className="rounded-xl border border-border bg-card p-8 text-center">
            <p className="text-sm text-muted-foreground">Couldn't load your documents.</p>
            <button
              onClick={() => refetch()}
              className="mt-2 text-sm font-medium text-primary hover:underline"
            >
              Try again
            </button>
          </div>
        ) : documents && documents.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2">
            {documents.map((document) => (
              <DocumentCard key={document.id} document={document} />
            ))}
          </div>
        ) : (
          <div className="rounded-xl border border-dashed border-border bg-card/40 p-10 text-center">
            <p className="font-medium">No documents yet</p>
            <p className="mx-auto mt-1 max-w-sm text-sm text-muted-foreground">
              Add your first file above. Once it's ready, head to Ask and start asking questions.
            </p>
          </div>
        )}
      </section>
    </div>
  );
}
