import type { DocumentMeta } from "@/types";

export async function uploadPdfs(files: File[]): Promise<DocumentMeta[]> {
  const body = new FormData();
  files.forEach((f) => body.append("files", f));

  const res = await fetch("/api/upload", { method: "POST", body });

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? `Upload failed (${res.status})`);
  }

  return res.json();
}
