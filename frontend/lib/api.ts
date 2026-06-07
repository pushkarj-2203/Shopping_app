// Typed API client for the PriceWise backend.
// Handles auth token storage (in-memory + localStorage) and JSON error surfacing.

import type {
  ChatResponse,
  MatchResponse,
  ParsedRequirement,
  PriceAlert,
  QuestionnaireResponse,
  TokenResponse,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const TOKEN_KEY = "pricewise_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}
export function setToken(token: string | null) {
  if (typeof window === "undefined") return;
  if (token) window.localStorage.setItem(TOKEN_KEY, token);
  else window.localStorage.removeItem(TOKEN_KEY);
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string> | undefined),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* non-JSON error */
    }
    throw new ApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // ---- engine ----
  parse: (query: string, category?: string) =>
    request<{ requirement: ParsedRequirement; confidence: number; parsed_intent: string }>(
      "/api/parse",
      { method: "POST", body: JSON.stringify({ query, category }) },
    ),

  questionnaire: (category: string, answered: Record<string, unknown> = {}) =>
    request<QuestionnaireResponse>("/api/questionnaire", {
      method: "POST",
      body: JSON.stringify({ category, answered_questions: answered }),
    }),

  match: (requirement: Record<string, unknown>, limit = 10) =>
    request<MatchResponse>("/api/match", {
      method: "POST",
      body: JSON.stringify({ requirement, limit }),
    }),

  priceCheck: (productId: string, urgency = "flexible") =>
    request<Record<string, unknown>>("/api/price-check", {
      method: "POST",
      body: JSON.stringify({ product_id: productId, urgency }),
    }),

  reviewCheck: (productId: string) =>
    request<Record<string, unknown>>("/api/review-check", {
      method: "POST",
      body: JSON.stringify({ product_id: productId }),
    }),

  chat: (query: string, sessionId?: string) =>
    request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ query, session_id: sessionId }),
    }),

  // ---- auth ----
  register: (email: string, password: string, fullName?: string) =>
    request<TokenResponse>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    }),

  login: (email: string, password: string) =>
    request<TokenResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    }),

  me: () => request<{ id: string; email: string; full_name: string | null }>("/api/auth/me"),

  // ---- alerts ----
  listAlerts: () => request<PriceAlert[]>("/api/alerts"),
  createAlert: (productId: string, productName: string, targetPrice: number) =>
    request<PriceAlert>("/api/alerts", {
      method: "POST",
      body: JSON.stringify({
        product_id: productId,
        product_name: productName,
        target_price: targetPrice,
      }),
    }),
  deleteAlert: (id: string) => request<void>(`/api/alerts/${id}`, { method: "DELETE" }),
};
