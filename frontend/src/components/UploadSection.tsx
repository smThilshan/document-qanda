import { useState } from "react";
import type { ChangeEvent } from "react";
import { ApiError, uploadDocument } from "../api";
import type { DocumentSummary } from "../api";
import { ErrorMessage } from "./ErrorMessage";
import { Spinner } from "./Spinner";

interface UploadSectionProps {
  currentDocument: DocumentSummary | null;
  onUploadSuccess: () => void;
}

export function UploadSection({ currentDocument, onUploadSuccess }: UploadSectionProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setSelectedFile(event.target.files?.[0] ?? null);
    setError(null);
  }

  async function handleUpload() {
    if (!selectedFile) return;

    // The backend only ever stores one document at a time — uploading a
    // new file deletes the previous document's chunks entirely. This is
    // the second half of making that unmissable (the persistent note
    // below the button is the first half): a deliberate, explicit
    // confirmation step right before the destructive action happens.
    if (currentDocument) {
      const confirmed = window.confirm(
        `This will replace "${currentDocument.document_name}" and permanently delete its stored data. Continue?`,
      );
      if (!confirmed) return;
    }

    setUploading(true);
    setError(null);

    try {
      await uploadDocument(selectedFile);
      setSelectedFile(null);
      onUploadSuccess();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed unexpectedly.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <input
          type="file"
          accept="application/pdf"
          onChange={handleFileChange}
          disabled={uploading}
          className="block text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-slate-100 file:px-3 file:py-2 file:text-sm file:font-medium file:text-slate-700 hover:file:bg-slate-200"
        />
        <button
          type="button"
          onClick={handleUpload}
          disabled={!selectedFile || uploading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:cursor-not-allowed disabled:bg-slate-300"
        >
          Upload
        </button>
        {uploading && <Spinner label="Uploading and processing..." />}
      </div>

      <p className="text-xs text-slate-500">
        Uploading a new file will replace the currently loaded document — only one document is
        stored at a time.
      </p>

      {error && <ErrorMessage message={error} />}
    </div>
  );
}
