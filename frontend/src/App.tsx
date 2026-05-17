import { Button } from "@/components/ui/button";

export default function App() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold tracking-tight">RAG Chat</h1>
      <p className="text-muted-foreground">
        Upload PDFs, ask questions, get cited answers.
      </p>
      <Button>Get Started</Button>
    </main>
  );
}
