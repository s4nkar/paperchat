import type { StreamCallbacks, StreamEvent } from "@/types";

export async function streamChat(
  question: string,
  callbacks: StreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  let res: Response;
  try {
    res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
      signal,
    });
  } catch (err) {
    if ((err as Error).name === "AbortError") return;
    callbacks.onError((err as Error).message);
    return;
  }

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)).join(", ")
          : `Chat failed (${res.status})`;
    callbacks.onError(message);
    return;
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;
      try {
        const event = JSON.parse(trimmed) as StreamEvent;
        if (event.type === "sources") callbacks.onSources(event.data);
        else if (event.type === "token") callbacks.onToken(event.data);
        else if (event.type === "done") callbacks.onDone();
        else if (event.type === "error") callbacks.onError(event.data);
      } catch {
        // malformed line — skip
      }
    }
  }
}
