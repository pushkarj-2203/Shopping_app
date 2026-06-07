"""Core engine endpoints — the consumer-first recommendation API."""

from __future__ import annotations

import json
from time import perf_counter

from fastapi import APIRouter, Depends, HTTPException

from app.engine import MatchResult, Product
from app.schemas.engine import (
    CompareRequest,
    CompareResponse,
    MatchRequest,
    MatchResponse,
    ParseRequest,
    ParseResponse,
    PriceCheckRequest,
    PriceCheckResponse,
    QuestionnaireRequest,
    QuestionnaireResponse,
    ReviewCheckRequest,
    ReviewCheckResponse,
    VerdictRequest,
    VerdictResponse,
)
from app.services.engine_service import EngineService, get_engine
from app.services.data_provider import get_data_provider
from app.schemas.engine import DiscoverRequest, DiscoverResponse

router = APIRouter(tags=["engine"])


def _product_from_dict(d: dict) -> Product:
    return Product(
        id=d.get("id", ""), name=d.get("name", ""), brand=d.get("brand", ""),
        category=d.get("category", ""), price=d.get("price", 0), mrp=d.get("mrp", 0),
        specs=d.get("specs", {}), features=d.get("features", []),
        rating=d.get("rating", 0), review_count=d.get("review_count", 0),
    )


@router.post("/parse", response_model=ParseResponse)
async def parse_requirement(body: ParseRequest, engine: EngineService = Depends(get_engine)):
    req = engine.parser.parse(body.query, body.category)
    return ParseResponse(
        requirement=req.to_dict(),
        confidence=req.confidence_score,
        parsed_intent=req.intent.value,
    )


@router.post("/questionnaire", response_model=QuestionnaireResponse)
async def get_questionnaire(body: QuestionnaireRequest, engine: EngineService = Depends(get_engine)):
    answered = body.answered_questions or {}
    questions = engine.questionnaire.generate(body.category, answered)
    total = len(engine.questionnaire.BASE_QUESTIONS.get(body.category, []))
    progress = round(len(answered) / total, 2) if total else 0.0
    # Build a partial requirement to derive contextual follow-ups.
    from app.engine import UserRequirement

    partial = UserRequirement(
        category=body.category,
        budget_max=answered.get("budget", 0) or float("inf"),
        use_cases=answered.get("use_case", []) if isinstance(answered.get("use_case"), list) else [],
        urgency=answered.get("urgency", "flexible"),
    )
    follow_ups = engine.questionnaire.generate_follow_up(partial, len(answered))
    return QuestionnaireResponse(questions=questions, follow_up_questions=follow_ups, progress=progress)


@router.post("/match", response_model=MatchResponse)
async def match_products(body: MatchRequest, engine: EngineService = Depends(get_engine)):
    start = perf_counter()
    req = engine.parser.parse(json.dumps(body.requirement))
    if body.product_ids:
        products = [engine.products[p] for p in body.product_ids if p in engine.products]
    else:
        products = engine.products_in_category(req.category)
    if not products:
        raise HTTPException(404, f"No products found for category '{req.category}'")
    results = engine.matcher.match(req, products)[: body.limit]
    elapsed = (perf_counter() - start) * 1000
    return MatchResponse(
        results=[_serialize_match(r) for r in results],
        total_matches=len(results),
        query_time_ms=round(elapsed, 2),
    )


@router.post("/verdict", response_model=VerdictResponse)
async def generate_verdict(body: VerdictRequest, engine: EngineService = Depends(get_engine)):
    pd = body.match_result.get("product", {})
    mr = MatchResult(
        product=_product_from_dict(pd),
        match_score=body.match_result.get("match_score", 0),
        match_breakdown=body.match_result.get("match_breakdown", {}),
        verdict=body.match_result.get("verdict", "COMPARE"),
        reasoning=body.match_result.get("reasoning", []),
        pros=body.match_result.get("pros", []),
        cons=body.match_result.get("cons", []),
        true_cost=body.match_result.get("true_cost", 0),
        price_fairness=body.match_result.get("price_fairness", "unknown"),
    )
    req = engine.parser.parse(json.dumps(body.requirement))
    v = engine.verdict_generator.generate_verdict(mr, req)
    return VerdictResponse(
        verdict=v.verdict, confidence=v.confidence, summary=v.summary,
        reasoning=v.reasoning, risks=v.risks, alternatives=v.alternatives,
        timing_advice=v.timing_advice, total_cost_analysis=v.total_cost_analysis,
    )


@router.post("/compare", response_model=CompareResponse)
async def compare_products(body: CompareRequest, engine: EngineService = Depends(get_engine)):
    products = [engine.products[p] for p in body.product_ids if p in engine.products]
    if len(products) < 2:
        raise HTTPException(400, "Need at least 2 valid product_ids to compare")
    req = engine.parser.parse(json.dumps(body.requirement))
    results = engine.matcher.match(req, products)
    summary = engine.comparator.summarize_comparison(results, req)
    return CompareResponse(
        summary=summary["summary"], winner=summary["winner"],
        key_differences=summary["key_differences"], recommendation=summary["recommendation"],
        full_results=summary["full_results"],
    )


@router.post("/price-check", response_model=PriceCheckResponse)
async def check_price(body: PriceCheckRequest, engine: EngineService = Depends(get_engine)):
    fake = engine.price_analyzer.detect_fake_discount(body.product_id)
    timing = engine.price_analyzer.predict_optimal_buy_time(body.product_id, body.urgency)
    fairness = "unknown"
    product = engine.products.get(body.product_id)
    if product and product.mrp > 0:
        discount = (1 - product.price / product.mrp) * 100
        fairness = "good_deal" if discount >= 30 else "fair" if discount >= 15 else "inflated"
    return PriceCheckResponse(
        fake_discount_analysis=fake, buy_timing_prediction=timing, price_fairness=fairness
    )


@router.post("/review-check", response_model=ReviewCheckResponse)
async def check_reviews(body: ReviewCheckRequest, engine: EngineService = Depends(get_engine)):
    a = engine.trust_engine.analyze(body.product_id)
    return ReviewCheckResponse(
        trust_score=a.overall_trust_score,
        authenticity_breakdown=a.authenticity_breakdown,
        suspicious_patterns=a.suspicious_patterns,
        sentiment_distribution=a.sentiment_distribution,
        key_themes=a.key_themes,
        verified_purchase_ratio=a.verified_purchase_ratio,
    )


@router.post("/discover", response_model=DiscoverResponse)
async def discover(body: DiscoverRequest):
    """
    Live product discovery via the configured data provider.

    DATA_PROVIDER=mock (default) searches the seeded catalog; DATA_PROVIDER=google_cse
    queries Google Custom Search (free tier) with 24h caching to respect quota and keep
    cost at zero. Results are normalized to dicts; structured price/spec ingestion is a
    downstream step (kept out of the request path so discovery stays fast and cheap).
    """
    provider = get_data_provider()
    results = await provider.search(body.query, body.category, body.limit)
    return DiscoverResponse(provider=type(provider).__name__, results=results)


def _serialize_match(r: MatchResult) -> dict:
    return {
        "product": r.product.to_dict(),
        "match_score": r.match_score,
        "match_breakdown": r.match_breakdown,
        "verdict": r.verdict,
        "reasoning": r.reasoning,
        "pros": r.pros,
        "cons": r.cons,
        "true_cost": r.true_cost,
        "price_fairness": r.price_fairness,
    }
