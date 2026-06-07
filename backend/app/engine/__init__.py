"""
PriceWise AI Engine — core rule-based intelligence.

This package contains the consumer-first recommendation engine. It is fully
deterministic and rule/statistics-based, requiring **no LLM and no GPU** to run.
An optional LLM layer (see ``app.core.llm``) can be layered on top for the
conversational endpoint, but the engine works at zero marginal cost by default.
"""

from .requirement_engine import (
    RequirementParser,
    QuestionnaireGenerator,
    UserRequirement,
    ShoppingIntent,
    Priority,
)
from .product_matcher import (
    ProductKnowledgeGraph,
    ProductMatcher,
    Product,
    MatchResult,
)
from .price_intelligence import (
    PriceAnalyzer,
    PriceHistory,
    PricePoint,
    DynamicPricingDetector,
)
from .trust_engine import ReviewTrustEngine, Review, ReviewAnalysis
from .verdict_engine import VerdictGenerator, ComparisonSummarizer, Verdict

__all__ = [
    "RequirementParser",
    "QuestionnaireGenerator",
    "UserRequirement",
    "ShoppingIntent",
    "Priority",
    "ProductKnowledgeGraph",
    "ProductMatcher",
    "Product",
    "MatchResult",
    "PriceAnalyzer",
    "PriceHistory",
    "PricePoint",
    "DynamicPricingDetector",
    "ReviewTrustEngine",
    "Review",
    "ReviewAnalysis",
    "VerdictGenerator",
    "ComparisonSummarizer",
    "Verdict",
]
