"""Engine request/response schemas (parse, match, verdict, compare, chat, alerts)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


# ---- Parse ----
class ParseRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    category: str | None = Field(default=None, max_length=64)


class ParseResponse(BaseModel):
    requirement: dict[str, Any]
    confidence: float
    parsed_intent: str


# ---- Questionnaire ----
class QuestionnaireRequest(BaseModel):
    category: str = Field(min_length=1, max_length=64)
    answered_questions: dict[str, Any] | None = None


class QuestionnaireResponse(BaseModel):
    questions: list[dict[str, Any]]
    follow_up_questions: list[str]
    progress: float


# ---- Match ----
class MatchRequest(BaseModel):
    requirement: dict[str, Any]
    product_ids: list[str] | None = None
    limit: int = Field(default=10, ge=1, le=50)


class MatchResponse(BaseModel):
    results: list[dict[str, Any]]
    total_matches: int
    query_time_ms: float


# ---- Verdict ----
class VerdictRequest(BaseModel):
    match_result: dict[str, Any]
    requirement: dict[str, Any]
    include_price_intel: bool = True
    include_trust_intel: bool = True


class VerdictResponse(BaseModel):
    verdict: str
    confidence: float
    summary: str
    reasoning: list[str]
    risks: list[str]
    alternatives: list[str]
    timing_advice: str
    total_cost_analysis: dict[str, Any]


# ---- Compare ----
class CompareRequest(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=4)
    requirement: dict[str, Any]


class CompareResponse(BaseModel):
    summary: str
    winner: str
    key_differences: list[str]
    recommendation: str
    full_results: list[dict[str, Any]]


# ---- Price / Review ----
class PriceCheckRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    urgency: str = "flexible"


class PriceCheckResponse(BaseModel):
    fake_discount_analysis: dict[str, Any]
    buy_timing_prediction: dict[str, Any]
    price_fairness: str


class ReviewCheckRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)


class ReviewCheckResponse(BaseModel):
    trust_score: float
    authenticity_breakdown: dict[str, Any]
    suspicious_patterns: list[str]
    sentiment_distribution: dict[str, Any]
    key_themes: list[Any]
    verified_purchase_ratio: float


# ---- Discover (live data provider) ----
class DiscoverRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)
    category: str | None = Field(default=None, max_length=64)
    limit: int = Field(default=10, ge=1, le=10)


class DiscoverResponse(BaseModel):
    provider: str
    results: list[dict[str, Any]]


# ---- Chat ----
class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    session_id: str | None = Field(default=None, max_length=64)


class ChatResponse(BaseModel):
    response: str
    structured_requirement: dict[str, Any] | None = None
    recommended_products: list[dict[str, Any]] | None = None
    follow_up_questions: list[str]
    session_id: str
    answer_source: str  # rule_based | anthropic | openai | ollama | cache
    trace_id: str | None = None
    validated: bool = True


# ---- Alerts ----
class AlertCreateRequest(BaseModel):
    product_id: str = Field(min_length=1, max_length=128)
    product_name: str = Field(min_length=1, max_length=255)
    target_price: float = Field(gt=0)


class AlertResponse(BaseModel):
    id: str
    product_id: str
    product_name: str
    target_price: float
    last_seen_price: float | None = None
    is_active: bool
    triggered_at: Any | None = None

    model_config = {"from_attributes": True}
