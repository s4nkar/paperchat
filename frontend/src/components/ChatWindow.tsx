import { MessageSquareText } from "lucide-react";

export default function ChatWindow() {
  return (
    <div className="flex-1 flex flex-col items-center justify-center gap-4 p-8 text-center">
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
  );
}
