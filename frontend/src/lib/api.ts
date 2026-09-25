const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      ...(init?.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail ?? detail;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export type User = { id: string; email: string; created_at: string };

export type Document = {
  id: string;
  filename: string;
  document_type: string;
  status: "processing" | "ready" | "failed";
  error: string | null;
  page_count: number;
  size_bytes: number;
  warnings: string[];
  created_at: string;
};

export type Citation = { document_id: string; page: number; clause: string | null; quoted_text: string };

export type AskResponse = {
  conversation_id: string;
  message_id: string;
  answer: string;
  confidence: "document_supported" | "general_information" | "insufficient_evidence" | "professional_review_recommended";
  citations: Citation[];
  disclaimer: string;
};

export type SummaryResponse = {
  document_id: string;
  document_type: string;
  summary: string;
  parties: string[];
  dates: string[];
  obligations: string[];
  disclaimer: string;
};

export type RiskFinding = {
  category: string;
  page: number;
  clause: string | null;
  section: string | null;
  snippet: string;
  needs_attention: boolean;
};

export type RiskScanResponse = {
  document_id: string;
  findings: RiskFinding[];
  categories_found: string[];
  review_note: string;
  disclaimer: string;
};

export type ChecklistResponse = {
  document_id: string;
  your_situation: { category: string; page: number; clause: string | null; needs_attention: boolean }[];
  next_steps: string[];
  questions_for_a_lawyer: string[];
  disclaimer: string;
};

export type CompareRow = {
  category: string;
  a: { value: string; page: number | null; clause: string | null };
  b: { value: string; page: number | null; clause: string | null };
  differs: boolean;
};

export type CompareResponse = {
  document_a: { id: string; filename: string };
  document_b: { id: string; filename: string };
  rows: CompareRow[];
  note: string;
  disclaimer: string;
};

export const api = {
  signup: (email: string, password: string) =>
    request<User>("/api/auth/signup", { method: "POST", body: JSON.stringify({ email, password }) }),
  login: (email: string, password: string) =>
    request<User>("/api/auth/login", { method: "POST", body: JSON.stringify({ email, password }) }),
  logout: () => request<void>("/api/auth/logout", { method: "POST" }),
  me: () => request<User>("/api/auth/me"),

  listDocuments: () => request<Document[]>("/api/documents"),
  getDocument: (id: string) => request<Document>(`/api/documents/${id}`),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return request<Document>("/api/documents", { method: "POST", body: form });
  },
  deleteDocument: (id: string) => request<void>(`/api/documents/${id}`, { method: "DELETE" }),

  getSummary: (id: string) => request<SummaryResponse>(`/api/documents/${id}/summary`),
  getRisks: (id: string) => request<RiskScanResponse>(`/api/documents/${id}/risks`),
  getChecklist: (id: string) => request<ChecklistResponse>(`/api/documents/${id}/checklist`),
  getPage: (id: string, page: number) =>
    request<{ document_id: string; page: number; page_count: number; text: string }>(
      `/api/documents/${id}/pages/${page}`
    ),
  ask: (id: string, question: string, conversationId?: string) =>
    request<AskResponse>(`/api/documents/${id}/ask`, {
      method: "POST",
      body: JSON.stringify({ question, conversation_id: conversationId }),
    }),
  compare: (documentIdA: string, documentIdB: string) =>
    request<CompareResponse>("/api/compare", {
      method: "POST",
      body: JSON.stringify({ document_id_a: documentIdA, document_id_b: documentIdB }),
    }),
};
