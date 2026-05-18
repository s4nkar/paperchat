import { useRef } from "react";
import { Upload, Loader2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { uploadPdfs } from "@/lib/api";
import type { DocumentMeta } from "@/types";

export default function PdfUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { mutate, isPending, isError, error, data } = useMutation({
    mutationFn: (files: File[]) => uploadPdfs(files),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;
    mutate(Array.from(files));
  }

  return (
    <div className="space-y-2">
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        multiple
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      <Button
        variant="outline"
        className="w-full gap-2 font-medium"
        disabled={isPending}
        onClick={() => inputRef.current?.click()}
      >
        {isPending ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Uploading…
          </>
        ) : (
          <>
            <Upload className="h-4 w-4" />
            Upload PDFs
          </>
        )}
      </Button>

      {isError && (
        <p className="text-xs text-destructive">
          {(error as Error).message}
        </p>
      )}

      {data?.map((doc: DocumentMeta) => (
        <div key={doc.filename} className="text-xs space-y-0.5">
          <p className="font-medium truncate text-foreground">{doc.filename}</p>
          <p className="text-muted-foreground">
            {doc.pages} {doc.pages === 1 ? "page" : "pages"} · {doc.chunk_count} chunks indexed
          </p>
          {doc.warning && (
            <p className="text-amber-600 dark:text-amber-400">{doc.warning}</p>
          )}
        </div>
      ))}
    </div>
  );
}
