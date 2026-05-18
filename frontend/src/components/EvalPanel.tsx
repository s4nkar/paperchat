import { FlaskConical, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { useQuery } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";

interface QuestionResult {
  id: string;
  question: string;
  expected_answer: string;
  recall: boolean;
  reciprocal_rank: number;
  precision: number;
}

interface EvalResult {
  recall_at_k: number;
  mrr: number;
  precision_at_k: number;
  retrieval_k: number;
  rerank_k: number;
  results: QuestionResult[];
}

async function fetchEval(): Promise<EvalResult> {
  const res = await fetch("/api/eval");
  if (!res.ok) throw new Error(`Eval failed (${res.status})`);
  return res.json();
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col items-center gap-0.5">
      <span className="text-lg font-semibold">{(value * 100).toFixed(0)}%</span>
      <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
    </div>
  );
}

export default function EvalPanel() {
  const { data, isFetching, error, refetch } = useQuery<EvalResult>({
    queryKey: ["eval"],
    queryFn: fetchEval,
    enabled: false,
    retry: false,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="p-4 border-b border-border">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Evaluation
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!data && !isFetching && !error && (
          <div className="flex flex-col items-center justify-center h-full gap-4 text-center">
            <div className="rounded-full bg-muted p-3">
              <FlaskConical className="h-5 w-5 text-muted-foreground" />
            </div>
            <div className="space-y-1.5">
              <p className="text-sm font-medium">Retrieval Evaluation</p>
              <p className="text-xs text-muted-foreground leading-relaxed max-w-[180px]">
                Run 5 golden questions against the pipeline to measure retrieval quality.
              </p>
            </div>
          </div>
        )}

        {error && (
          <p className="text-xs text-destructive text-center pt-8">
            {(error as Error).message}
          </p>
        )}

        {data && (
          <div className="space-y-4">
            <div className="flex justify-around rounded-xl border border-border bg-card p-4">
              <Metric label={`Recall@${data.retrieval_k}`} value={data.recall_at_k} />
              <Metric label={`MRR@${data.rerank_k}`} value={data.mrr} />
              <Metric label={`Prec@${data.rerank_k}`} value={data.precision_at_k} />
            </div>

            <div className="space-y-2">
              {data.results.map((r) => (
                <div
                  key={r.id}
                  className="rounded-lg border border-border bg-card p-3 space-y-1.5"
                >
                  <div className="flex items-start gap-2">
                    {r.recall ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500 shrink-0 mt-0.5" />
                    ) : (
                      <XCircle className="h-4 w-4 text-destructive shrink-0 mt-0.5" />
                    )}
                    <p className="text-xs leading-relaxed">{r.question}</p>
                  </div>
                  {r.expected_answer && (
                    <p className="pl-6 text-[11px] text-muted-foreground leading-relaxed">
                      {r.expected_answer}
                    </p>
                  )}
                  <div className="flex gap-3 pl-6 text-[10px] text-muted-foreground">
                    <span>Rank {r.reciprocal_rank > 0 ? Math.round(1 / r.reciprocal_rank) : "—"}</span>
                    <span>Prec {(r.precision * 100).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="p-4 border-t border-border">
        <Button
          variant="outline"
          size="sm"
          className="w-full"
          disabled={isFetching}
          onClick={() => refetch()}
        >
          {isFetching ? (
            <>
              <Loader2 className="h-3.5 w-3.5 mr-2 animate-spin" />
              Running…
            </>
          ) : (
            <>
              <FlaskConical className="h-3.5 w-3.5 mr-2" />
              Run Eval
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
