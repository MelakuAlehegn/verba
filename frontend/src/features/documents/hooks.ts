import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Query } from "@tanstack/react-query";
import { deleteDocument, listDocuments, uploadDocument } from "@/lib/api/documents";
import type { Document } from "@/lib/api/types";

export const documentsQueryKey = ["documents"] as const;

// Non-terminal states — while any document is in one, ingestion is still running
// on the worker, so we poll for status changes.
const ACTIVE_STATUSES = new Set([
  "created",
  "uploading",
  "uploaded",
  "queued",
  "processing",
  "deleting",
]);

export function useDocuments() {
  return useQuery({
    queryKey: documentsQueryKey,
    queryFn: listDocuments,
    refetchInterval: (query: Query<Document[]>) => {
      const docs = query.state.data;
      return docs?.some((doc) => ACTIVE_STATUSES.has(doc.status)) ? 2500 : false;
    },
  });
}

export function useUploadDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsQueryKey }),
  });
}

export function useDeleteDocument() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: documentsQueryKey }),
  });
}
