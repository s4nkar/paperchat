import { useEffect, useRef, useState } from "react";
import { Send, Loader2, MessageSquareText } from "lucide-react";
import { Button } from "@/components/ui/button";
import MessageBubble from "@/components/MessageBubble";
import { streamChat } from "@/lib/stream";
import type { ChatMessage, Chunk } from "@/types";

export default function ChatWindow() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isPending, setIsPending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isPending]);

  // Cancel any in-flight stream on unmount
  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const question = input.trim();
    if (!question || isPending) return;

    // Cancel previous stream if still running
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setInput("");
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question },
      { role: "assistant", content: "", sources: [] },
    ]);
    setIsPending(true);

    let sources: Chunk[] = [];

    await streamChat(
      question,
      {
        onSources: (s) => {
          sources = s;
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === "assistant") next[next.length - 1] = { ...last, sources };
            return next;
          });
        },
        onToken: (token) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === "assistant")
              next[next.length - 1] = { ...last, content: last.content + token };
            return next;
          });
        },
        onDone: () => setIsPending(false),
        onError: (message) => {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (last?.role === "assistant")
              next[next.length - 1] = { ...last, content: "", error: message };
            return next;
          });
          setIsPending(false);
        },
      },
      controller.signal,
    );

    setIsPending(false);
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="rounded-full bg-muted p-4">
              <MessageSquareText className="h-6 w-6 text-muted-foreground" />
            </div>
            <div className="space-y-1.5">
              <p className="font-display text-2xl font-semibold tracking-tight">
                Ask anything.
              </p>
              <p className="text-sm text-muted-foreground max-w-xs leading-relaxed">
                Upload a PDF from the sidebar, then ask questions about its contents.
              </p>
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <MessageBubble key={i} message={msg} />
        ))}

        {isPending && messages[messages.length - 1]?.content === "" && !messages[messages.length - 1]?.error && (
          <div className="flex items-start">
            <div className="bg-card border border-border rounded-2xl rounded-bl-sm px-4 py-2.5">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>

      <form onSubmit={handleSubmit} className="border-t border-border p-4 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask a question about your documents…"
          disabled={isPending}
          className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50"
        />
        <Button type="submit" size="icon" disabled={isPending || !input.trim()}>
          <Send className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}
