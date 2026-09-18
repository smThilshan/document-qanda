import type { DocumentSummary } from "../api";
import { ErrorMessage } from "./ErrorMessage";
import { Spinner } from "./Spinner";

interface DocumentStatusProps {
  document: DocumentSummary | null;
  loading: boolean;
  error: string | null;
}

export function DocumentStatus({ document, loading, error }: DocumentStatusProps) {
  if (loading) {
    return <Spinner label="Checking loaded document..." />;
  }

  if (error) {
    return <ErrorMessage message={error} />;
  }

  if (!document) {
    return (
      <p className="text-sm text-slate-500">
        No document loaded yet — upload a PDF below to get started.
      </p>
    );
  }

  return (
    <p className="text-sm text-slate-700">
      <span className="font-medium text-slate-900">Currently loaded:</span>{" "}
      {document.document_name}{" "}
      <span className="text-slate-500">({document.chunk_count} chunks)</span>
    </p>
  );
}
