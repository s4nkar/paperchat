import { FileText } from "lucide-react";
import type { Chunk } from "@/types";

interface Props {
  chunk: Chunk;
  index: number;
}

export default function SourceCard({ chunk, index }: Props) {
  return (
    <div className="rounded-md border border-border bg-background px-3 py-2 space-y-1">
      <div className="flex items-center gap-1.5">
        <FileText className="h-3 w-3 shrink-0 text-muted-foreground" />
        <span className="text-[10px] font-semibold text-accent">
          [{index}]
        </span>
        <span className="text-[10px] text-muted-foreground truncate flex-1" title={chunk.filename}>
          {chunk.filename.replace(/\.pdf$/i, "")} · p.{chunk.page}
        </span>
        <span className="text-[10px] text-muted-foreground shrink-0">
          {Math.round(chunk.score * 100)}%
        </span>
      </div>
      <p className="text-xs text-foreground/70 line-clamp-2 leading-relaxed">
        {chunk.text}
      </p>
    </div>
  );
}
