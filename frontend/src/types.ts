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
  error?: string;
  tokens?: number;
  cached?: boolean;
}

export type StreamEvent =
  | { type: "sources"; data: Chunk[] }
  | { type: "token"; data: string }
  | { type: "usage"; data: { tokens: number; cached: boolean } }
  | { type: "done" }
  | { type: "error"; data: string };

export interface StreamCallbacks {
  onSources: (sources: Chunk[]) => void;
  onToken: (token: string) => void;
  onUsage: (tokens: number, cached: boolean) => void;
  onDone: () => void;
  onError: (message: string) => void;
}
