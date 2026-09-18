/**
 * Thin wrapper around the backend API. Every type here mirrors a Pydantic
 * model in backend/app/schemas.py exactly — if the backend response shape
 * ever changes, these types should change with it, so a mismatch shows up
 * as a TypeScript error here rather than a silent runtime bug in a
 * component reading a field that no longer exists.
 */

// VITE_API_URL is read from a .env file (see .env.example) or, in
// deployment, from the environment variable set in Vercel's dashboard —
// so pointing this at a deployed backend is a config change, not a code
// change. The fallback keeps `npm run dev` working out of the box even
// if no .env file has been created yet.
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface SourceChunk {
  document_name: string;
  content: string;
  similarity: number;
}

export interface QueryResponse {
  question: string;
  answer: string;
  sources: SourceChunk[];
}

export interface UploadResponse {
  filename: string;
  total_chunks: number;
  chunks_stored: number;
  first_chunk_sample: string;
}

export interface DocumentSummary {
  document_name: string;
  chunk_count: number;
}

export interface DocumentsResponse {
  documents: DocumentSummary[];
}

export class ApiError extends Error {}

/**
 * FastAPI returns errors in two different shapes depending on where the
 * rejection happened: a hand-raised HTTPException gives `{"detail": "a
 * string"}`, while a Pydantic validation failure (e.g. an empty question)
 * gives `{"detail": [{"msg": "...", ...}, ...]}` — an array of error
 * objects, not a string. This normalizes both into one readable message
 * so the UI never has to know which case it's looking at.
 */
function extractErrorMessage(body: unknown): string | null {
  if (typeof body !== "object" || body === null || !("detail" in body)) {
    return null;
  }
  const detail = (body as { detail: unknown }).detail;

  if (typeof detail === "string") {
    return detail;
  }
  if (Array.isArray(detail)) {
    return detail
      .map((item) => (typeof item?.msg === "string" ? item.msg : JSON.stringify(item)))
      .join(" ");
  }
  return null;
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, options);
  } catch {
    // fetch() itself throws on network failure (server down, wrong port,
    // CORS block) — this is distinct from the server responding with an
    // error status, and deserves its own message since "the server said
    // X" isn't true here; the server was never reached at all.
    throw new ApiError("Could not reach the server. Is the backend running on port 8000?");
  }

  let body: unknown = null;
  try {
    body = await response.json();
  } catch {
    // No JSON body (rare) — fall through and use a generic message below.
  }

  if (!response.ok) {
    throw new ApiError(extractErrorMessage(body) ?? `Request failed with status ${response.status}.`);
  }

  return body as T;
}

export function getDocuments(): Promise<DocumentsResponse> {
  return request<DocumentsResponse>("/documents");
}

export function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  return request<UploadResponse>("/upload", { method: "POST", body: formData });
}

export function askQuestion(question: string): Promise<QueryResponse> {
  return request<QueryResponse>("/query", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });
}
