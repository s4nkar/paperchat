import { useRef } from "react";
import { Upload, Loader2, CheckCircle2 } from "lucide-react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import { uploadPdfs } from "@/lib/api";

export default function PdfUploader() {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();

  const { mutate, isPending, isError, error, isSuccess, data } = useMutation({
    mutationFn: (files: File[]) => uploadPdfs(files),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  function handleFiles(list: FileList | null) {
    if (!list || list.length === 0) return;
    const fileArray = Array.from(list);
    if (inputRef.current) inputRef.current.value = "";
    mutate(fileArray);
  }

  const warnings = data?.filter((d) => d.warning) ?? [];

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

      {isSuccess && (
        <p className="flex items-center gap-1.5 text-xs text-green-700 dark:text-green-400">
          <CheckCircle2 className="h-3.5 w-3.5 shrink-0" />
          {data.length === 1
            ? `${data[0].filename} indexed`
            : `${data.length} files indexed`}
        </p>
      )}

      {warnings.map((doc) => (
        <p key={doc.filename} className="text-xs text-amber-600 dark:text-amber-400">
          {doc.filename}: {doc.warning}
        </p>
      ))}

      {isError && (
        <p className="text-xs text-destructive">{(error as Error).message}</p>
      )}
    </div>
  );
}
