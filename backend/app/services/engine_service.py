"""
EngineService — a process-wide singleton that owns the rule-based engine
instances and the product knowledge graph, and seeds a realistic demo catalog
so every endpoint returns meaningful data out of the box.

In production the seed catalog is replaced/augmented by the data provider
(``app.services.data_provider``) and a persistent product store. The engine
objects themselves are stateless w.r.t. requests, so a single shared instance
is safe under async concurrency.
"""

from __future__ import annotations

from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.engine import (
    ComparisonSummarizer,
    PriceAnalyzer,
    PriceHistory,
    PricePoint,
    Product,
    ProductKnowledgeGraph,
    ProductMatcher,
    QuestionnaireGenerator,
    RequirementParser,
    Review,
    ReviewTrustEngine,
    VerdictGenerator,
)

logger = get_logger(__name__)


class EngineService:
    def __init__(self) -> None:
        self.parser = RequirementParser(use_llm=False)  # rule-based: zero cost
        self.questionnaire = QuestionnaireGenerator()
        self.kg = ProductKnowledgeGraph()
        self.matcher = ProductMatcher(self.kg)
        self.price_analyzer = PriceAnalyzer()
        self.trust_engine = ReviewTrustEngine()
        self.verdict_generator = VerdictGenerator(self.price_analyzer, self.trust_engine)
        self.comparator = ComparisonSummarizer()
        self.products: dict[str, Product] = {}

    # ---------- catalog management ----------
    def add_product(self, product: Product) -> None:
        self.products[product.id] = product
        self.kg.add_product(product)

    def products_in_category(self, category: str) -> list[Product]:
        return [p for p in self.products.values() if p.category == category]

    def seed_demo_catalog(self) -> None:
        if self.products:
            return
        for p in _SEED_PRODUCTS:
            self.add_product(p)
        for pid, points in _seed_price_histories().items():
            self.price_analyzer.add_price_history(PriceHistory(product_id=pid, price_points=points))
        for pid, reviews in _seed_reviews().items():
            self.trust_engine.add_reviews(pid, reviews)
        logger.info("Seeded demo catalog: %d products", len(self.products))


_engine: EngineService | None = None


def get_engine() -> EngineService:
    global _engine
    if _engine is None:
        _engine = EngineService()
        _engine.seed_demo_catalog()
    return _engine


# ======================= seed data =======================
_SEED_PRODUCTS: list[Product] = [
    Product(
        id="s24ultra", name="Samsung Galaxy S24 Ultra", brand="Samsung", category="smartphone",
        price=107999, mrp=129999,
        specs={"camera_mp": 200, "battery_mah": 5000, "ram_gb": 12, "display": "amoled",
               "refresh_hz": 120, "processor_score": 95},
        features=["5g", "amoled", "wireless_charging", "water_resistant", "stylus", "fast_charging"],
        rating=4.5, review_count=2500,
    ),
    Product(
        id="pixel8pro", name="Google Pixel 8 Pro", brand="Google", category="smartphone",
        price=84999, mrp=106999,
        specs={"camera_mp": 50, "battery_mah": 5050, "ram_gb": 12, "display": "amoled",
               "refresh_hz": 120, "processor_score": 88},
        features=["5g", "amoled", "wireless_charging", "water_resistant", "fast_charging"],
        rating=4.4, review_count=1400,
    ),
    Product(
        id="oneplus12", name="OnePlus 12", brand="OnePlus", category="smartphone",
        price=64999, mrp=69999,
        specs={"camera_mp": 50, "battery_mah": 5400, "ram_gb": 16, "display": "amoled",
               "refresh_hz": 120, "processor_score": 92},
        features=["5g", "amoled", "wireless_charging", "fast_charging"],
        rating=4.3, review_count=980,
    ),
    Product(
        id="nothing2a", name="Nothing Phone (2a)", brand="Nothing", category="smartphone",
        price=27999, mrp=29999,
        specs={"camera_mp": 50, "battery_mah": 5000, "ram_gb": 8, "display": "amoled",
               "refresh_hz": 120, "processor_score": 78},
        features=["5g", "amoled", "fast_charging"],
        rating=4.2, review_count=640,
    ),
    Product(
        id="iphone16pro", name="Apple iPhone 16 Pro", brand="Apple", category="smartphone",
        price=129900, mrp=139900,
        specs={"camera_mp": 48, "battery_mah": 3582, "ram_gb": 8, "display": "amoled",
               "refresh_hz": 120, "processor_score": 98},
        features=["5g", "amoled", "wireless_charging", "water_resistant"],
        rating=4.6, review_count=3100,
    ),
    Product(
        id="sonywhch720n", name="Sony WH-CH720N", brand="Sony", category="headphones",
        price=7990, mrp=9990,
        specs={"battery_mah": 0, "battery_hours": 35, "anc": True, "wireless": True},
        features=["wireless", "anc", "fast_charging"],
        rating=4.4, review_count=1200,
    ),
]


def _seed_price_histories() -> dict[str, list[PricePoint]]:
    today = datetime.now()
    out: dict[str, list[PricePoint]] = {}
    # s24ultra: genuinely fair price, modest fluctuation
    out["s24ultra"] = [
        PricePoint(price=109999 - (i % 3) * 1000, mrp=129999, date=today - timedelta(days=30 * i),
                   source="seed", discount_label="") for i in range(6, 0, -1)
    ] + [PricePoint(price=107999, mrp=129999, date=today, source="seed")]
    # iphone16pro: inflated MRP / fake discount pattern
    out["iphone16pro"] = [
        PricePoint(price=124900, mrp=129900, date=today - timedelta(days=120), source="seed"),
        PricePoint(price=119900, mrp=129900, date=today - timedelta(days=90), source="seed"),
        PricePoint(price=115000, mrp=129900, date=today - timedelta(days=60), source="seed"),
        PricePoint(price=129900, mrp=139900, date=today - timedelta(days=14), source="seed",
                   discount_label="7% off"),
        PricePoint(price=129900, mrp=139900, date=today, source="seed", discount_label="7% off"),
    ]
    out["oneplus12"] = [
        PricePoint(price=66999 - (i % 2) * 1000, mrp=69999, date=today - timedelta(days=30 * i), source="seed")
        for i in range(6, 0, -1)
    ] + [PricePoint(price=64999, mrp=69999, date=today, source="seed")]
    return out


def _seed_reviews() -> dict[str, list[Review]]:
    today = datetime.now()
    out: dict[str, list[Review]] = {}
    # s24ultra: mixed authentic reviews + a burst of suspicious ones
    s24 = []
    for i in range(40):
        s24.append(Review(
            id=f"s24-{i}", product_id="s24ultra", rating=5 if i % 3 else 4,
            title="Great phone", text=("Camera quality is excellent and battery life is solid. "
                                       "Display is gorgeous though it heats up during gaming." if i % 2 else
                                       "Love the cameras, zoom is amazing. Some heating issues noted."),
            author=f"user{i}", date=today - timedelta(days=i * 2),
            verified_purchase=bool(i % 2), helpful_count=i % 7))
    # suspicious burst: identical text, same day, unverified
    for i in range(15):
        s24.append(Review(
            id=f"s24-burst-{i}", product_id="s24ultra", rating=5,
            title="Best in class", text="must buy excellent product best in class amazing",
            author=f"botacct{i % 3}", date=today - timedelta(days=1),
            verified_purchase=False, helpful_count=0))
    out["s24ultra"] = s24
    return out
