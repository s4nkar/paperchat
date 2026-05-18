import ReactMarkdown from "react-markdown";
import { AlertCircle } from "lucide-react";
import type { ChatMessage } from "@/types";
import SourceCard from "@/components/SourceCard";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      {message.error ? (
        <div className="flex items-start gap-2 max-w-[80%] rounded-2xl rounded-bl-sm px-4 py-2.5 bg-destructive/10 border border-destructive/30 text-destructive text-sm">
          <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
          <span>{message.error}</span>
        </div>
      ) : (
        <div
          className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-accent text-accent-foreground rounded-br-sm"
              : "bg-card border border-border text-foreground rounded-bl-sm"
          }`}
        >
          {isUser ? (
            message.content
          ) : (
            <ReactMarkdown
              components={{
                p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
                ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                code: ({ children }) => (
                  <code className="bg-muted px-1 py-0.5 rounded text-xs font-mono">{children}</code>
                ),
                strong: ({ children }) => <strong className="font-semibold">{children}</strong>,
              }}
            >
              {message.content}
            </ReactMarkdown>
          )}
        </div>
      )}

      {!isUser && message.tokens !== undefined && (
        <p className="text-[10px] text-muted-foreground px-1">
          {message.cached
            ? "cached · 0 tokens"
            : `${message.tokens} tokens total`}
        </p>
      )}

      {!isUser && message.sources && message.sources.length > 0 && (
        <div className="w-full max-w-[80%] space-y-1.5">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground px-1">
            Sources
          </p>
          {message.sources.map((chunk, i) => (
            <SourceCard key={i} chunk={chunk} index={i + 1} />
          ))}
        </div>
      )}
    </div>
  );
}
