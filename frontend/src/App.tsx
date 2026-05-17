import { useState } from "react";
import { PanelLeftOpen, PanelLeftClose, FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";
import PdfUploader from "@/components/PdfUploader";
import DocumentList from "@/components/DocumentList";
import ChatWindow from "@/components/ChatWindow";
import EvalPanel from "@/components/EvalPanel";

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [evalOpen, setEvalOpen] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-background overflow-hidden">
      <header className="h-13 flex items-center justify-between px-4 border-b border-border shrink-0 bg-card/60 backdrop-blur-sm">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            className="md:hidden h-8 w-8"
            onClick={() => setSidebarOpen((o) => !o)}
          >
            {sidebarOpen ? (
              <PanelLeftClose className="h-4 w-4" />
            ) : (
              <PanelLeftOpen className="h-4 w-4" />
            )}
          </Button>
          <span className="font-display text-xl font-semibold tracking-tight text-foreground">
            paper<span className="text-accent">chat</span>
          </span>
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => setEvalOpen((o) => !o)}
          title="Toggle evaluation panel"
        >
          <FlaskConical className="h-4 w-4" />
        </Button>
      </header>

      <div className="flex-1 flex overflow-hidden relative">
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-foreground/20 z-10 md:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={[
            "w-72 border-r border-border flex flex-col shrink-0 bg-card",
            "fixed md:relative inset-y-0 left-0 z-20 md:z-auto",
            "transition-transform duration-200 ease-in-out",
            sidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0",
          ].join(" ")}
        >
          <div className="p-4 border-b border-border">
            <PdfUploader />
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            <DocumentList />
          </div>
        </aside>

        <main className="flex-1 flex flex-col overflow-hidden min-w-0">
          <ChatWindow />
        </main>

        {evalOpen && (
          <aside className="w-80 border-l border-border flex flex-col shrink-0 bg-card animate-fade-in">
            <EvalPanel />
          </aside>
        )}
      </div>
    </div>
  );
}
