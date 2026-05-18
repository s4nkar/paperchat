import type { ChatMessage } from "@/types";
import SourceCard from "@/components/SourceCard";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({ message }: Props) {
  const isUser = message.role === "user";

  return (
    <div className={`flex flex-col gap-2 ${isUser ? "items-end" : "items-start"}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
          isUser
            ? "bg-accent text-accent-foreground rounded-br-sm"
            : "bg-card border border-border text-foreground rounded-bl-sm"
        }`}
      >
        {message.content}
      </div>

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
