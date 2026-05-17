import { FlaskConical } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function EvalPanel() {
  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Evaluation
        </p>
      </div>
      <div className="flex-1 flex flex-col items-center justify-center gap-4 p-6 text-center">
        <div className="rounded-full bg-muted p-3">
          <FlaskConical className="h-5 w-5 text-muted-foreground" />
        </div>
        <div className="space-y-1.5">
          <p className="text-sm font-medium">Retrieval Evaluation</p>
          <p className="text-xs text-muted-foreground leading-relaxed">
            Run 5 golden questions against the retrieval pipeline to measure
            Recall@5.
          </p>
        </div>
        <Button variant="outline" size="sm" disabled>
          Run Eval
        </Button>
      </div>
    </div>
  );
}
