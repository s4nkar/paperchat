import type { Chunk } from "../types";

interface Props {
  chunk: Chunk;
}

export default function SourceCard({ chunk }: Props) {
  return <div>{chunk.filename} — p.{chunk.page}</div>;
}
