import { useState } from "react";
import type { FormEvent } from "react";
import { ApiError, askQuestion } from "../api";
import type { QueryResponse } from "../api";
import { ErrorMessage } from "./ErrorMessage";
import { Spinner } from "./Spinner";

export function QuerySection() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<QueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sourcesExpanded, setSourcesExpanded] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;

    setLoading(true);
    setError(null);
    setSourcesExpanded(false);

    try {
      const response = await askQuestion(question);
      setResult(response);
    } catch (err) {
      setResult(null);
      setError(err instanceof ApiError ? err.message : "Something went wrong unexpectedly.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <form onSubmit={handleSubmit} className="flex flex-wrap items-center gap-3">
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="Ask a question about the loaded document..."
          disabled={loading}
          className="min-w-0 flex-1 rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />
        <button
          type="submit"
          disabled={!question.trim() || loading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Ask
        </button>
        {loading && <Spinner label="Thinking..." />}
      </form>

      {error && <ErrorMessage message={error} />}

      {result && (
        <div className="space-y-4">
          <div className="rounded-lg border border-slate-200 bg-white p-4">
            <p className="text-xs font-medium uppercase tracking-wide text-slate-400">Answer</p>
            <p className="mt-1 text-sm text-slate-800">{result.answer}</p>
          </div>

          {result.sources.length > 0 && (
            <div className="space-y-2">
              <button
                type="button"
                onClick={() => setSourcesExpanded((expanded) => !expanded)}
                className="flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-slate-400 hover:text-slate-600"
              >
                {sourcesExpanded ? "Hide" : "Show"} sources ({result.sources.length})
                <span className="text-[10px]">{sourcesExpanded ? "▲" : "▼"}</span>
              </button>

              {sourcesExpanded &&
                result.sources.map((source, index) => (
                  <div
                    key={index}
                    className="rounded-lg border border-slate-200 bg-white p-3 text-sm"
                  >
                    <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                      <span>{source.document_name}</span>
                      <span>similarity: {source.similarity.toFixed(3)}</span>
                    </div>
                    <p className="text-slate-600">{source.content}</p>
                  </div>
                ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
