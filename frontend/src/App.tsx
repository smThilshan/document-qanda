import { useCallback, useEffect, useState } from "react";
import { ApiError, getDocuments } from "./api";
import type { DocumentSummary } from "./api";
import { DocumentStatus } from "./components/DocumentStatus";
import { QuerySection } from "./components/QuerySection";
import { UploadSection } from "./components/UploadSection";

function App() {
  const [currentDocument, setCurrentDocument] = useState<DocumentSummary | null>(null);
  const [documentLoading, setDocumentLoading] = useState(true);
  const [documentError, setDocumentError] = useState<string | null>(null);

  const refreshDocuments = useCallback(async () => {
    setDocumentLoading(true);
    setDocumentError(null);
    try {
      const response = await getDocuments();
      setCurrentDocument(response.documents[0] ?? null);
    } catch (err) {
      setDocumentError(err instanceof ApiError ? err.message : "Could not load document status.");
    } finally {
      setDocumentLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshDocuments();
  }, [refreshDocuments]);

  return (
    <div className="min-h-screen bg-slate-50 py-10">
      <div className="mx-auto max-w-2xl space-y-6 px-4">
        <header>
          <h1 className="text-2xl font-semibold text-slate-900">Document Q&amp;A</h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload a PDF and ask questions grounded in its content.
          </p>
        </header>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Document</h2>
          <div className="mb-4">
            <DocumentStatus
              document={currentDocument}
              loading={documentLoading}
              error={documentError}
            />
          </div>
          <UploadSection currentDocument={currentDocument} onUploadSuccess={refreshDocuments} />
        </section>

        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-3 text-sm font-semibold text-slate-900">Ask a question</h2>
          <QuerySection />
        </section>
      </div>
    </div>
  );
}

export default App;
