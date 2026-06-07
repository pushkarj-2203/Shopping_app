// Shared API types mirroring the backend Pydantic schemas.

export type Verdict = "BUY" | "WAIT" | "DONT_BUY" | "COMPARE";

export interface Product {
  id: string;
  name: string;
  brand: string;
  category: string;
  price: number;
  mrp: number;
  specs: Record<string, unknown>;
  features: string[];
  rating: number;
  review_count: number;
}

export interface MatchResult {
  product: Product;
  match_score: number;
  match_breakdown: Record<string, number>;
  verdict: Verdict;
  reasoning: string[];
  pros: string[];
  cons: string[];
  true_cost: number;
  price_fairness: string;
}

export interface MatchResponse {
  results: MatchResult[];
  total_matches: number;
  query_time_ms: number;
}

export interface Question {
  id: string;
  type: "single_choice" | "multi_choice" | "slider";
  question: string;
  options?: string[];
  min?: number;
  max?: number;
}

export interface QuestionnaireResponse {
  questions: Question[];
  follow_up_questions: string[];
  progress: number;
}

export interface ParsedRequirement {
  category: string;
  budget_range: [number, number];
  priorities: string[];
  use_cases: string[];
  must_haves: string[];
  avoided_brands: string[];
  preferred_brands: string[];
  urgency: string;
  intent: string;
  confidence_score: number;
}

export interface ChatResponse {
  response: string;
  structured_requirement: ParsedRequirement | null;
  recommended_products: { product: Product; match_score: number; verdict: Verdict }[] | null;
  follow_up_questions: string[];
  session_id: string;
  answer_source: "rule_based" | "llm" | "cache";
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface PriceAlert {
  id: string;
  product_id: string;
  product_name: string;
  target_price: number;
  last_seen_price: number | null;
  is_active: boolean;
  triggered_at: string | null;
}
