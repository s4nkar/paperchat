export interface DocumentMeta {
  filename: string;
  size: number;
  pages: number;
  chunk_count: number;
  warning: string | null;
}

export interface DocumentInfo {
  filename: string;
  page_count: number;
  chunk_count: number;
}

export interface Chunk {
  id: string;
  text: string;
  filename: string;
  page: number;
  section: string;
  score: number;
}

export interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: Chunk[];
}

export type StreamEvent =
  | { type: "sources"; data: Chunk[] }
  | { type: "token"; data: string }
  | { type: "done" }
  | { type: "error"; data: string };
