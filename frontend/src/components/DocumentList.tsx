import { Trash2, FileText } from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchDocuments, deleteDocument } from "@/lib/api";
import type { DocumentInfo } from "@/types";

export default function DocumentList() {
  const queryClient = useQueryClient();

  const { data: docs = [], isLoading } = useQuery<DocumentInfo[]>({
    queryKey: ["documents"],
    queryFn: fetchDocuments,
  });

  const { mutate: remove } = useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  return (
    <div className="space-y-2">
      <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        Documents
      </p>

      {isLoading && (
        <p className="text-xs text-muted-foreground">Loading…</p>
      )}

      {!isLoading && docs.length === 0 && (
        <p className="text-xs text-muted-foreground">No documents yet.</p>
      )}

      {docs.map((doc, i) => (
        <div
          key={doc.filename}
          className="group flex items-start gap-2.5 rounded-lg border border-border bg-card px-3 py-2.5 hover:bg-muted/40 transition-colors"
        >
          <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-accent/10 text-accent">
            <FileText className="h-3.5 w-3.5" />
          </div>

          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-semibold text-muted-foreground mb-0.5">
              PDF {i + 1}
            </p>
            <p className="text-xs font-medium text-foreground truncate leading-tight" title={doc.filename}>
              {doc.filename.replace(/\.pdf$/i, "")}
            </p>
            <p className="text-[10px] text-muted-foreground mt-0.5">
              {doc.page_count} {doc.page_count === 1 ? "page" : "pages"} · {doc.chunk_count} chunks
            </p>
          </div>

          <button
            onClick={() => remove(doc.filename)}
            className="shrink-0 mt-0.5 opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-destructive transition-opacity"
            title="Remove"
          >
            <Trash2 className="h-3.5 w-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
