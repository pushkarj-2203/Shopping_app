"""
PriceWise AI Engine - Product Knowledge Graph & Matcher
Builds and queries product knowledge for intelligent matching
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field
from collections import defaultdict
import networkx as nx

@dataclass
class Product:
    """Structured product representation"""
    id: str
    name: str
    brand: str
    category: str
    price: float
    currency: str = "INR"
    mrp: float = 0.0
    specs: Dict = field(default_factory=dict)
    features: List[str] = field(default_factory=list)
    rating: float = 0.0
    review_count: int = 0
    sources: List[Dict] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    availability: str = "in_stock"

    # Derived fields
    price_per_spec_score: float = 0.0
    value_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "brand": self.brand,
            "category": self.category,
            "price": self.price,
            "mrp": self.mrp,
            "discount_percent": round((1 - self.price/self.mrp)*100, 1) if self.mrp > 0 else 0,
            "specs": self.specs,
            "features": self.features,
            "rating": self.rating,
            "review_count": self.review_count,
            "sources": self.sources,
            "availability": self.availability
        }

@dataclass
class MatchResult:
    """Result of matching a product to user requirements"""
    product: Product
    match_score: float  # 0-100
    match_breakdown: Dict[str, float]  # Component scores
    verdict: str  # BUY, WAIT, DONT_BUY, COMPARE
    reasoning: List[str]
    pros: List[str]
    cons: List[str]
    true_cost: float  # Price + hidden costs
    price_fairness: str  # fair, inflated, good_deal, wait_for_sale

class ProductKnowledgeGraph:
    """
    Knowledge graph for product relationships, substitutes, and category ontology.
    Enables intelligent product discovery beyond simple keyword matching.
    """

    def __init__(self):
        self.graph = nx.DiGraph()
        self.products: Dict[str, Product] = {}
        self.category_ontology = self._build_category_ontology()
        self.brand_hierarchy = self._build_brand_hierarchy()

    def _build_category_ontology(self) -> Dict:
        """Build hierarchical category structure"""
        return {
            "smartphone": {
                "parent": "electronics",
                "attributes": ["camera", "battery", "processor", "display", "ram", "storage"],
                "subcategories": ["flagship", "mid_range", "budget", "gaming_phone"],
                "price_tiers": {"budget": (5000, 20000), "mid": (20000, 50000), 
                               "premium": (50000, 100000), "flagship": (100000, float('inf'))}
            },
            "laptop": {
                "parent": "electronics",
                "attributes": ["processor", "ram", "storage", "display", "gpu", "battery", "weight"],
                "subcategories": ["ultrabook", "gaming", "workstation", "budget", "2in1"],
                "price_tiers": {"budget": (20000, 40000), "mid": (40000, 80000),
                               "premium": (80000, 150000), "flagship": (150000, float('inf'))}
            },
            "headphones": {
                "parent": "audio",
                "attributes": ["driver_size", "battery", "connectivity", "anc", "codec_support"],
                "subcategories": ["tws", "over_ear", "on_ear", "gaming", "audiophile"],
                "price_tiers": {"budget": (1000, 5000), "mid": (5000, 15000),
                               "premium": (15000, 40000), "flagship": (40000, float('inf'))}
            }
        }

    def _build_brand_hierarchy(self) -> Dict:
        """Build brand positioning map"""
        return {
            "smartphone": {
                "premium": ["apple", "samsung"],
                "flagship_killer": ["oneplus", "nothing", "google"],
                "value": ["xiaomi", "realme", "poco", "iqoo"],
                "budget": ["redmi", "motorola", "nokia"]
            },
            "laptop": {
                "premium": ["apple", "dell", "hp"],
                "performance": ["asus", "msi", "lenovo"],
                "value": ["acer", "hp", "lenovo"]
            }
        }

    def add_product(self, product: Product):
        """Add product to graph with relationships"""
        self.products[product.id] = product
        self.graph.add_node(product.id, **product.to_dict())

        # Add category relationship
        self.graph.add_edge(product.id, f"cat:{product.category}", type="belongs_to")

        # Add brand relationship
        self.graph.add_edge(product.id, f"brand:{product.brand}", type="made_by")

        # Add price tier relationship
        tiers = self.category_ontology.get(product.category, {}).get("price_tiers", {})
        for tier, (min_p, max_p) in tiers.items():
            if min_p <= product.price < max_p:
                self.graph.add_edge(product.id, f"tier:{tier}", type="priced_at")
                break

    def find_substitutes(self, product_id: str, max_price_diff: float = 0.2) -> List[Product]:
        """Find substitute products within price range"""
        if product_id not in self.products:
            return []

        product = self.products[product_id]
        substitutes = []

        for pid, other in self.products.items():
            if pid == product_id:
                continue
            if other.category != product.category:
                continue

            price_diff = abs(other.price - product.price) / product.price
            if price_diff <= max_price_diff:
                # Calculate spec similarity
                spec_sim = self._spec_similarity(product, other)
                if spec_sim > 0.6:
                    substitutes.append((other, spec_sim))

        substitutes.sort(key=lambda x: x[1], reverse=True)
        return [s[0] for s in substitutes[:10]]

    def find_upgrades(self, product_id: str, budget_increase: float = 0.3) -> List[Product]:
        """Find upgrade options within budget increase"""
        if product_id not in self.products:
            return []

        product = self.products[product_id]
        max_budget = product.price * (1 + budget_increase)

        upgrades = []
        for pid, other in self.products.items():
            if pid == product_id or other.category != product.category:
                continue
            if product.price < other.price <= max_budget:
                spec_improvement = self._spec_improvement_score(product, other)
                if spec_improvement > 0.3:
                    upgrades.append((other, spec_improvement))

        upgrades.sort(key=lambda x: x[1], reverse=True)
        return [u[0] for u in upgrades[:10]]

    def _spec_similarity(self, p1: Product, p2: Product) -> float:
        """Calculate specification similarity between two products"""
        if not p1.specs or not p2.specs:
            # No spec data to differentiate; same-category items are treated as
            # reasonable substitutes by default.
            return 0.7

        common_keys = set(p1.specs.keys()) & set(p2.specs.keys())
        if not common_keys:
            return 0.0

        similarities = []
        for key in common_keys:
            v1 = p1.specs[key]
            v2 = p2.specs[key]

            # Numeric comparison
            if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                max_val = max(abs(v1), abs(v2), 1)
                sim = 1 - abs(v1 - v2) / max_val
                similarities.append(max(0, sim))
            # String comparison
            elif isinstance(v1, str) and isinstance(v2, str):
                similarities.append(1.0 if v1.lower() == v2.lower() else 0.0)

        return np.mean(similarities) if similarities else 0.0

    def _spec_improvement_score(self, base: Product, upgrade: Product) -> float:
        """Calculate how much upgrade improves over base"""
        if not base.specs or not upgrade.specs:
            return 0.0

        improvements = []
        for key in base.specs:
            if key in upgrade.specs:
                v1 = base.specs[key]
                v2 = upgrade.specs[key]

                if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
                    if v2 > v1:
                        improvements.append((v2 - v1) / max(v1, 1))

        return np.mean(improvements) if improvements else 0.0

    def get_category_insights(self, category: str) -> Dict:
        """Get market insights for a category"""
        cat_products = [p for p in self.products.values() if p.category == category]
        if not cat_products:
            return {}

        prices = [p.price for p in cat_products]
        ratings = [p.rating for p in cat_products if p.rating > 0]

        return {
            "total_products": len(cat_products),
            "price_range": (min(prices), max(prices)),
            "avg_price": np.mean(prices),
            "median_price": np.median(prices),
            "avg_rating": np.mean(ratings) if ratings else 0,
            "top_brands": self._get_top_brands(cat_products),
            "price_tier_distribution": self._get_price_distribution(cat_products, category)
        }

    def _get_top_brands(self, products: List[Product]) -> List[Tuple[str, int]]:
        """Get top brands by product count"""
        brand_counts = defaultdict(int)
        for p in products:
            brand_counts[p.brand] += 1
        return sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    def _get_price_distribution(self, products: List[Product], category: str) -> Dict:
        """Get price tier distribution"""
        tiers = self.category_ontology.get(category, {}).get("price_tiers", {})
        distribution = {tier: 0 for tier in tiers}

        for p in products:
            for tier, (min_p, max_p) in tiers.items():
                if min_p <= p.price < max_p:
                    distribution[tier] += 1
                    break

        return distribution


class ProductMatcher:
    """
    Core matching engine: scores products against user requirements.
    Produces 0-100% match score with detailed breakdown.
    """

    def __init__(self, knowledge_graph: ProductKnowledgeGraph):
        self.kg = knowledge_graph

        # Weight configuration (can be tuned per category)
        self.weights = {
            "budget": 0.25,
            "priority": 0.25,
            "must_haves": 0.20,
            "brand": 0.10,
            "use_case": 0.10,
            "reviews": 0.10
        }

    def match(self, requirement, products: List[Product]) -> List[MatchResult]:
        """
        Match products to requirements and return ranked results.

        Args:
            requirement: UserRequirement object
            products: List of Product objects to score

        Returns:
            List of MatchResult sorted by match_score descending
        """
        results = []

        for product in products:
            # Skip avoided brands
            if product.brand.lower() in [b.lower() for b in requirement.avoided_brands]:
                continue

            # Hard budget filter: don't recommend products far over budget
            # (consumer-first). Allow a 20% overage band for borderline picks.
            if requirement.budget_max != float('inf') and product.price > requirement.budget_max * 1.2:
                continue

            # Calculate component scores
            budget_score = self._score_budget(product, requirement)
            priority_score = self._score_priorities(product, requirement)
            must_have_score = self._score_must_haves(product, requirement)
            brand_score = self._score_brand(product, requirement)
            use_case_score = self._score_use_cases(product, requirement)
            review_score = self._score_reviews(product)

            # Calculate weighted match score
            match_score = (
                budget_score * self.weights["budget"] +
                priority_score * self.weights["priority"] +
                must_have_score * self.weights["must_haves"] +
                brand_score * self.weights["brand"] +
                use_case_score * self.weights["use_case"] +
                review_score * self.weights["reviews"]
            ) * 100

            # Generate verdict
            verdict, reasoning = self._generate_verdict(
                match_score, budget_score, priority_score, 
                must_have_score, product, requirement
            )

            # Generate pros/cons
            pros, cons = self._generate_pros_cons(product, requirement, match_score)

            # Calculate true cost
            true_cost = self._calculate_true_cost(product)

            # Price fairness
            price_fairness = self._assess_price_fairness(product)

            result = MatchResult(
                product=product,
                match_score=round(match_score, 1),
                match_breakdown={
                    "budget": round(budget_score * 100, 1),
                    "priority": round(priority_score * 100, 1),
                    "must_haves": round(must_have_score * 100, 1),
                    "brand": round(brand_score * 100, 1),
                    "use_case": round(use_case_score * 100, 1),
                    "reviews": round(review_score * 100, 1)
                },
                verdict=verdict,
                reasoning=reasoning,
                pros=pros,
                cons=cons,
                true_cost=true_cost,
                price_fairness=price_fairness
            )

            results.append(result)

        # Sort by match score descending
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results

    def _score_budget(self, product: Product, req) -> float:
        """Score how well product fits budget (0-1)"""
        if req.budget_max == float('inf'):
            return 1.0

        if product.price > req.budget_max:
            # Penalty for over budget, but not disqualifying
            overage = (product.price - req.budget_max) / req.budget_max
            return max(0, 1 - overage * 2)

        # Reward for being within budget
        utilization = product.price / req.budget_max
        # Sweet spot: 80-100% of budget
        if 0.8 <= utilization <= 1.0:
            return 1.0
        elif utilization < 0.5:
            return 0.7  # Too cheap might mean missing features
        else:
            return 0.9

    def _score_priorities(self, product: Product, req) -> float:
        """Score how well product matches user priorities"""
        if not req.priorities:
            return 0.5

        scores = []
        for priority in req.priorities:
            score = self._priority_match(product, priority)
            scores.append(score)

        # Weight first priority more
        weights = [0.5, 0.3, 0.2] + [0.0] * max(0, len(scores) - 3)
        weighted = sum(s * w for s, w in zip(scores, weights[:len(scores)]))
        return weighted

    def _priority_match(self, product: Product, priority) -> float:
        """Match specific priority to product specs"""
        from .requirement_engine import Priority

        specs = product.specs

        if priority == Priority.CAMERA:
            # Check camera specs
            mp = specs.get("camera_main_mp", 0)
            if mp >= 108: return 1.0
            elif mp >= 64: return 0.8
            elif mp >= 48: return 0.6
            elif mp >= 12: return 0.4
            return 0.2

        elif priority == Priority.BATTERY:
            mah = specs.get("battery_mah", 0)
            if mah >= 6000: return 1.0
            elif mah >= 5000: return 0.8
            elif mah >= 4000: return 0.6
            return 0.3

        elif priority == Priority.PERFORMANCE:
            # Check processor tier
            processor = specs.get("processor", "").lower()
            if any(flagship in processor for flagship in ["snapdragon 8", "a17", "a18", "dimensity 9000"]):
                return 1.0
            elif any(mid in processor for mid in ["snapdragon 7", "a16", "dimensity 8000"]):
                return 0.7
            return 0.4

        elif priority == Priority.DISPLAY:
            refresh = specs.get("refresh_rate", 0)
            if refresh >= 144: return 1.0
            elif refresh >= 120: return 0.8
            elif refresh >= 90: return 0.6
            return 0.4

        elif priority == Priority.VALUE:
            # Value is calculated as specs per rupee
            return product.value_score if product.value_score > 0 else 0.5

        return 0.5

    def _score_must_haves(self, product: Product, req) -> float:
        """Score must-have features (binary match)"""
        if not req.must_haves:
            return 1.0

        matches = 0
        for feature in req.must_haves:
            if feature.lower() in [f.lower() for f in product.features]:
                matches += 1
            elif feature.lower() in str(product.specs).lower():
                matches += 1

        return matches / len(req.must_haves) if req.must_haves else 1.0

    def _score_brand(self, product: Product, req) -> float:
        """Score brand preference"""
        if not req.preferred_brands and not req.avoided_brands:
            return 0.5

        if product.brand.lower() in [b.lower() for b in req.preferred_brands]:
            return 1.0

        if product.brand.lower() in [b.lower() for b in req.avoided_brands]:
            return 0.0

        return 0.5

    def _score_use_cases(self, product: Product, req) -> float:
        """Score use case fit"""
        if not req.use_cases:
            return 0.5

        use_case_specs = {
            "gaming": ["gaming", "gpu", "refresh_rate", "thermal"],
            "photography": ["camera", "mp", "zoom", "sensor"],
            "work": ["keyboard", "battery", "display", "port"],
            "streaming": ["display", "speaker", "battery", "hdr"],
            "social_media": ["camera", "front_camera", "battery"],
            "travel": ["battery", "durability", "water_resistant", "gps"]
        }

        scores = []
        for use_case in req.use_cases:
            relevant_specs = use_case_specs.get(use_case, [])
            matches = sum(1 for spec in relevant_specs if spec in str(product.specs).lower())
            scores.append(matches / len(relevant_specs) if relevant_specs else 0.5)

        return np.mean(scores) if scores else 0.5

    def _score_reviews(self, product: Product) -> float:
        """Score based on review quality"""
        if product.rating == 0 or product.review_count < 10:
            return 0.5

        # Rating score (0-5 scale to 0-1)
        rating_score = product.rating / 5.0

        # Review count confidence (more reviews = more reliable)
        count_score = min(product.review_count / 1000, 1.0)

        return rating_score * 0.7 + count_score * 0.3

    def _generate_verdict(self, match_score, budget_score, priority_score, 
                         must_have_score, product, req) -> Tuple[str, List[str]]:
        """Generate BUY/WAIT/DONT_BUY/COMPARE verdict"""
        reasoning = []

        if match_score >= 85 and budget_score >= 0.8:
            verdict = "BUY"
            reasoning.append(f"Excellent match ({match_score}%) within budget")
            if product.rating >= 4.5:
                reasoning.append("Highly rated by users")

        elif match_score >= 70:
            verdict = "COMPARE"
            reasoning.append(f"Good match ({match_score}%), but compare alternatives")
            if budget_score < 0.8:
                reasoning.append("Slightly over budget - check if worth it")

        elif match_score >= 50:
            verdict = "WAIT"
            reasoning.append(f"Moderate match ({match_score}%). Consider waiting for sale or better options")
            if must_have_score < 0.5:
                reasoning.append("Missing some must-have features")

        else:
            verdict = "DONT_BUY"
            reasoning.append(f"Poor match ({match_score}%). Not recommended for your needs")
            if budget_score < 0.5:
                reasoning.append("Significantly over budget")

        # Urgency override
        if req.urgency == "urgent" and match_score >= 60:
            verdict = "BUY"
            reasoning.append("Urgent need - this is the best available option")

        return verdict, reasoning

    def _generate_pros_cons(self, product: Product, req, match_score) -> Tuple[List[str], List[str]]:
        """Generate AI pros and cons from specs"""
        pros = []
        cons = []

        specs = product.specs

        # Auto-generate pros from strong specs
        if specs.get("battery_mah", 0) >= 5000:
            pros.append("Excellent battery life")
        if specs.get("camera_main_mp", 0) >= 64:
            pros.append("Great camera system")
        if specs.get("ram_gb", 0) >= 8:
            pros.append("Smooth multitasking")
        if specs.get("refresh_rate", 0) >= 120:
            pros.append("Smooth display")
        if product.rating >= 4.5:
            pros.append(f"Highly rated ({product.rating}/5)")
        if product.price < product.mrp * 0.8:
            pros.append(f"Good discount ({round((1-product.price/product.mrp)*100)}% off)")

        # Auto-generate cons from weak specs or mismatches
        if specs.get("battery_mah", 0) < 4000:
            cons.append("Battery may be insufficient for heavy use")
        if specs.get("storage_gb", 0) < 128:
            cons.append("Limited storage")
        if product.rating < 4.0 and product.review_count > 50:
            cons.append("Mixed user reviews")
        if product.price > req.budget_max:
            cons.append(f"Over budget by ₹{product.price - req.budget_max}")

        # Add match-specific cons
        if match_score < 70:
            cons.append("Not the best fit for your specific requirements")

        return pros[:5], cons[:3]

    def _calculate_true_cost(self, product: Product) -> float:
        """Calculate true total cost including hidden fees"""
        base = product.price

        # Delivery estimate
        delivery = 0 if product.price > 500 else 40

        # Warranty/extended (optional, but commonly pushed)
        warranty_push = base * 0.05  # ~5% for extended warranty

        # EMI processing (if applicable)
        emi_fee = 0  # Usually hidden in interest

        return base + delivery + warranty_push

    def _assess_price_fairness(self, product: Product) -> str:
        """Assess if current price is fair"""
        if not product.mrp or product.mrp == 0:
            return "unknown"

        discount = (1 - product.price / product.mrp) * 100

        if discount >= 30:
            return "good_deal"
        elif discount >= 15:
            return "fair"
        elif discount > 0:
            return "inflated"
        else:
            return "wait_for_sale"


# Example usage
if __name__ == "__main__":
    # Build knowledge graph
    kg = ProductKnowledgeGraph()

    # Add sample products
    products = [
        Product(id="p1", name="iPhone 16 Pro", brand="apple", category="smartphone",
                price=129900, mrp=134900, specs={"camera_main_mp": 48, "battery_mah": 3582, "ram_gb": 8},
                features=["5g", "wireless_charging", "water_resistant"], rating=4.6, review_count=2500),
        Product(id="p2", name="Samsung S24 Ultra", brand="samsung", category="smartphone",
                price=107999, mrp=134999, specs={"camera_main_mp": 200, "battery_mah": 5000, "ram_gb": 12},
                features=["5g", "wireless_charging", "water_resistant", "s_pen"], rating=4.5, review_count=1800),
        Product(id="p3", name="Pixel 8 Pro", brand="google", category="smartphone",
                price=84999, mrp=99999, specs={"camera_main_mp": 50, "battery_mah": 5050, "ram_gb": 12},
                features=["5g", "wireless_charging", "water_resistant"], rating=4.4, review_count=900),
    ]

    for p in products:
        kg.add_product(p)

    print(f"Knowledge graph built with {len(kg.products)} products")
    print(f"Category insights: {kg.get_category_insights('smartphone')}")
