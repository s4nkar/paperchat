import type { DocumentInfo, DocumentMeta } from "@/types";

export async function fetchDocuments(): Promise<DocumentInfo[]> {
  const res = await fetch("/api/documents");
  if (!res.ok) throw new Error(`Failed to load documents (${res.status})`);
  return res.json();
}

export async function deleteDocument(filename: string): Promise<void> {
  const res = await fetch(`/api/documents/${encodeURIComponent(filename)}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete document (${res.status})`);
}

export async function uploadPdfs(files: File[]): Promise<DocumentMeta[]> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));

  const res = await fetch("/api/upload", { method: "POST", body });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const detail = err.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
          : `Upload failed (${res.status})`;
    throw new Error(message);
  }

  return res.json();
}
