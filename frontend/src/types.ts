export interface Document {
  id: string;
  filename: string;
  pages: number;
  size: number;
  uploaded_at: string;
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
