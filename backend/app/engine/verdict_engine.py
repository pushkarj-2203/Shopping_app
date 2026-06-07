"""
PriceWise AI Engine - Verdict Generator
The core reasoning engine that produces honest buy/wait/don't buy recommendations
"""

import json
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from .requirement_engine import UserRequirement, Priority
from .product_matcher import Product, MatchResult
from .price_intelligence import PriceAnalyzer
from .trust_engine import ReviewTrustEngine

@dataclass
class Verdict:
    """Final AI verdict with full reasoning"""
    verdict: str  # BUY, WAIT, DONT_BUY, COMPARE
    confidence: float  # 0-100
    summary: str  # Natural language summary
    reasoning: List[str]
    risks: List[str]
    alternatives: List[str]
    timing_advice: str
    total_cost_analysis: Dict

class VerdictGenerator:
    """
    The consumer advocate brain.
    Generates honest verdicts that sometimes say "don't buy" or "wait".
    This is the core differentiator from seller-first platforms.
    """

    VERDICT_TEMPLATES = {
        "BUY": [
            "This is an excellent match for your needs. Buy with confidence.",
            "Strong recommendation. Price is fair and features align perfectly.",
            "Best option in your budget. Go for it.",
            "This checks all your boxes. Recommended purchase."
        ],
        "WAIT": [
            "Good match, but waiting for sale could save you {savings}%.",
            "Decent option, but price is likely to drop soon. Consider waiting.",
            "Fair match. Better deals expected in upcoming sales.",
            "Not the best value right now. Wait for price correction."
        ],
        "DONT_BUY": [
            "Does not meet your core requirements. Look for alternatives.",
            "Poor value at current price. Consider other options.",
            "Missing critical features you need. Not recommended.",
            "Better alternatives available at this price point."
        ],
        "COMPARE": [
            "Good match, but compare with {alternatives} before deciding.",
            "Solid option. Worth comparing alternatives in the same range.",
            "Decent fit. Check similar products for better value."
        ]
    }

    def __init__(self, price_analyzer: Optional[PriceAnalyzer] = None,
                 trust_engine: Optional[ReviewTrustEngine] = None):
        self.price_analyzer = price_analyzer or PriceAnalyzer()
        self.trust_engine = trust_engine or ReviewTrustEngine()

    def generate_verdict(self, match_result: MatchResult, requirement: UserRequirement,
                        context: Optional[Dict] = None) -> Verdict:
        """
        Generate comprehensive verdict for a product match.

        Args:
            match_result: Product match result with scores
            requirement: User requirements
            context: Additional context (price history, reviews, etc.)

        Returns:
            Verdict with full reasoning
        """
        product = match_result.product

        # Gather all intelligence
        price_intel = self._get_price_intelligence(product, context)
        trust_intel = self._get_trust_intelligence(product, context)

        # Determine base verdict
        base_verdict = match_result.verdict

        # Override based on price intelligence
        if price_intel.get("is_fake_discount") and base_verdict == "BUY":
            base_verdict = "WAIT"

        if price_intel.get("price_trend") == "falling" and requirement.urgency != "urgent":
            if base_verdict == "BUY":
                base_verdict = "WAIT"

        # Override based on trust issues
        if trust_intel.get("trust_score", 100) < 40:
            if base_verdict == "BUY":
                base_verdict = "COMPARE"

        # Generate confidence
        confidence = self._calculate_confidence(match_result, price_intel, trust_intel)

        # Generate summary
        summary = self._generate_summary(base_verdict, match_result, requirement, price_intel)

        # Generate reasoning
        reasoning = self._generate_reasoning(match_result, price_intel, trust_intel, requirement)

        # Generate risks
        risks = self._generate_risks(match_result, price_intel, trust_intel)

        # Generate alternatives
        alternatives = self._suggest_alternatives(match_result, requirement, context)

        # Timing advice
        timing = self._generate_timing_advice(match_result, price_intel, requirement)

        # Total cost analysis
        cost_analysis = self._analyze_total_cost(product, match_result)

        return Verdict(
            verdict=base_verdict,
            confidence=round(confidence, 1),
            summary=summary,
            reasoning=reasoning,
            risks=risks,
            alternatives=alternatives,
            timing_advice=timing,
            total_cost_analysis=cost_analysis
        )

    def _get_price_intelligence(self, product: Product, context: Optional[Dict]) -> Dict:
        """Get price intelligence for product"""
        if not context or "price_history" not in context:
            return {}

        fake_discount = self.price_analyzer.detect_fake_discount(product.id)
        buy_timing = self.price_analyzer.predict_optimal_buy_time(product.id)

        return {
            "is_fake_discount": fake_discount.get("is_fake", False),
            "true_discount": fake_discount.get("true_discount", 0),
            "price_trend": buy_timing.get("price_trend", "stable"),
            "next_sale": buy_timing.get("next_sale_date"),
            "expected_discount": buy_timing.get("expected_discount", 0)
        }

    def _get_trust_intelligence(self, product: Product, context: Optional[Dict]) -> Dict:
        """Get trust intelligence for product"""
        if not context or "reviews" not in context:
            return {"trust_score": 100}

        analysis = self.trust_engine.analyze(product.id)
        return {
            "trust_score": analysis.overall_trust_score,
            "suspicious_patterns": analysis.suspicious_patterns,
            "verified_ratio": analysis.verified_purchase_ratio
        }

    def _calculate_confidence(self, match_result: MatchResult, price_intel: Dict, 
                             trust_intel: Dict) -> float:
        """Calculate overall confidence in verdict"""
        base = match_result.match_score

        # Adjust for price concerns
        if price_intel.get("is_fake_discount"):
            base -= 15

        # Adjust for trust issues
        trust_score = trust_intel.get("trust_score", 100)
        if trust_score < 50:
            base -= 20

        # Adjust for missing data
        if not price_intel:
            base -= 10
        if not trust_intel:
            base -= 10

        return max(0, min(100, base))

    def _generate_summary(self, verdict: str, match_result: MatchResult, 
                         requirement: UserRequirement, price_intel: Dict) -> str:
        """Generate natural language summary"""
        product = match_result.product

        templates = self.VERDICT_TEMPLATES.get(verdict, self.VERDICT_TEMPLATES["COMPARE"])
        template = random.choice(templates)

        # Fill in template variables
        if "{savings}" in template:
            savings = price_intel.get("expected_discount", 10)
            template = template.replace("{savings}", str(savings))

        if "{alternatives}" in template:
            alts = "similar products"  # Would be populated from knowledge graph
            template = template.replace("{alternatives}", alts)

        # Build rich summary
        parts = [template]

        # Add match context
        parts.append(f" Match score: {match_result.match_score}%")

        # Add priority alignment
        if requirement.priorities:
            priority_names = [p.value for p in requirement.priorities[:2]]
            parts.append(f" Strong in: {', '.join(priority_names)}")

        # Add price context
        if price_intel.get("true_discount", 0) > 15:
            parts.append(f" Genuine discount: {price_intel['true_discount']}% off")
        elif price_intel.get("is_fake_discount"):
            parts.append(" Warning: Discount may be inflated")

        return " | ".join(parts)

    def _generate_reasoning(self, match_result: MatchResult, price_intel: Dict,
                           trust_intel: Dict, requirement: UserRequirement) -> List[str]:
        """Generate detailed reasoning points"""
        reasoning = []

        # Match score reasoning
        breakdown = match_result.match_breakdown
        for component, score in breakdown.items():
            if score >= 80:
                reasoning.append(f"✅ {component.replace('_', ' ').title()}: Excellent ({score}%)")
            elif score >= 60:
                reasoning.append(f"⚠️ {component.replace('_', ' ').title()}: Good ({score}%)")
            else:
                reasoning.append(f"❌ {component.replace('_', ' ').title()}: Weak ({score}%)")

        # Price reasoning
        if price_intel.get("is_fake_discount"):
            reasoning.append("⚠️ Price alert: Listed discount appears inflated")
        if price_intel.get("true_discount", 0) > 20:
            reasoning.append(f"✅ Genuine savings: {price_intel['true_discount']}% below fair price")

        # Trust reasoning
        trust_score = trust_intel.get("trust_score", 100)
        if trust_score < 50:
            reasoning.append(f"⚠️ Review trust: Low ({trust_score}/100) - possible manipulation")
        elif trust_score > 80:
            reasoning.append(f"✅ Review trust: High ({trust_score}/100) - authentic feedback")

        # Urgency reasoning
        if requirement.urgency == "urgent":
            reasoning.append("⏰ Urgency override: Recommendation adjusted for immediate need")
        elif requirement.urgency == "can_wait":
            reasoning.append("💡 Patience advantage: Better deals likely in upcoming sales")

        return reasoning

    def _generate_risks(self, match_result: MatchResult, price_intel: Dict, 
                       trust_intel: Dict) -> List[str]:
        """Generate risk warnings"""
        risks = []

        # Price risks
        if price_intel.get("price_trend") == "rising":
            risks.append("Price may increase soon")
        if match_result.price_fairness == "inflated":
            risks.append("Current price above fair baseline")

        # Product risks
        if match_result.match_score < 70:
            risks.append("Not optimal fit for your requirements")

        # Review risks
        if trust_intel.get("trust_score", 100) < 50:
            risks.append("Review authenticity concerns")
        if trust_intel.get("verified_ratio", 1.0) < 0.3:
            risks.append("Most reviews from unverified purchases")

        # Hidden cost risks
        if match_result.true_cost > match_result.product.price * 1.1:
            risks.append("Hidden costs (warranty, delivery) may add 10%+")

        return risks

    def _suggest_alternatives(self, match_result: MatchResult, requirement: UserRequirement,
                             context: Optional[Dict]) -> List[str]:
        """Suggest alternative products"""
        # In real implementation, query knowledge graph for substitutes
        alternatives = []

        if match_result.match_score < 80:
            alternatives.append("Consider products with higher match scores")

        if match_result.product.price > requirement.budget_max:
            alternatives.append(f"Look for options under ₹{requirement.budget_max}")

        if requirement.priorities:
            priority = requirement.priorities[0].value
            alternatives.append(f"Check other products strong in {priority}")

        return alternatives[:3]

    def _generate_timing_advice(self, match_result: MatchResult, price_intel: Dict,
                               requirement: UserRequirement) -> str:
        """Generate timing advice"""
        if requirement.urgency == "urgent":
            return "Buy now - urgency takes priority over price optimization"

        if price_intel.get("next_sale"):
            days = price_intel.get("days_to_sale", 30)
            if days <= 14:
                return f"Wait {days} days for sale - expect {price_intel.get('expected_discount', 15)}% off"

        if price_intel.get("price_trend") == "falling":
            return "Price is dropping - wait 2-4 weeks for better deal"

        if match_result.price_fairness == "good_deal":
            return "Good time to buy - price is at or near historical low"

        return "No strong timing signal - buy when convenient"

    def _analyze_total_cost(self, product: Product, match_result: MatchResult) -> Dict:
        """Analyze true total cost of ownership"""
        base_price = product.price

        # Common hidden costs
        delivery = 0 if base_price > 500 else 40
        warranty = base_price * 0.05  # Extended warranty push
        case_protector = base_price * 0.03  # Common upsell

        # EMI trap (if applicable)
        emi_cost = 0
        if base_price > 10000:
            # Typical EMI has hidden interest
            emi_cost = base_price * 0.08  # 8% effective interest

        total = base_price + delivery + warranty + case_protector

        return {
            "base_price": base_price,
            "delivery": delivery,
            "warranty_push": round(warranty, 0),
            "accessories": round(case_protector, 0),
            "emi_trap": round(emi_cost, 0),
            "true_total": round(total, 0),
            "hidden_cost_percent": round((total - base_price) / base_price * 100, 1)
        }


class ComparisonSummarizer:
    """
    Generates natural language summaries for product comparisons.
    Perplexity-style synthesis with citations.
    """

    def summarize_comparison(self, match_results: List[MatchResult], 
                            requirement: UserRequirement) -> Dict:
        """
        Generate comparison summary with natural language.

        Returns:
            {
                "summary": str,
                "winner": str,
                "key_differences": List[str],
                "recommendation": str
            }
        """
        if not match_results:
            return {"summary": "No products to compare", "winner": "", "key_differences": []}

        # Sort by match score
        sorted_results = sorted(match_results, key=lambda x: x.match_score, reverse=True)
        winner = sorted_results[0]
        runner_up = sorted_results[1] if len(sorted_results) > 1 else None

        # Generate summary
        parts = []
        parts.append(f"Based on your requirements (priority: {requirement.priorities[0].value if requirement.priorities else 'value'}),")
        parts.append(f"the {winner.product.name} is your best match at ₹{winner.product.price} with a {winner.match_score}% fit score.")

        if winner.verdict == "BUY":
            parts.append("It's a good time to buy as the price is at a historical low.")
        elif winner.verdict == "WAIT":
            parts.append("Consider waiting for upcoming sales for better value.")

        # Key differences
        differences = []
        if runner_up:
            if winner.match_score > runner_up.match_score + 10:
                differences.append(f"{winner.product.name} is significantly better match ({winner.match_score}% vs {runner_up.match_score}%)")

            if winner.product.price < runner_up.product.price:
                differences.append(f"₹{runner_up.product.price - winner.product.price} cheaper than {runner_up.product.name}")

            # Spec differences
            for spec in ["camera_main_mp", "battery_mah", "ram_gb"]:
                w_val = winner.product.specs.get(spec, 0)
                r_val = runner_up.product.specs.get(spec, 0)
                if w_val != r_val:
                    spec_name = spec.replace("_", " ").replace("main", "").replace("mp", "MP").replace("mah", "mAh").replace("gb", "GB")
                    if w_val > r_val:
                        differences.append(f"Better {spec_name}: {w_val} vs {r_val}")
                    else:
                        differences.append(f"Lower {spec_name}: {w_val} vs {r_val}")

        # Recommendation
        recommendation = f"Recommendation: {winner.verdict} - {winner.product.name}"
        if winner.verdict == "WAIT":
            recommendation += " (but wait for better price)"

        return {
            "summary": " ".join(parts),
            "winner": winner.product.name,
            "key_differences": differences[:5],
            "recommendation": recommendation,
            "full_results": [{
                "product": r.product.name,
                "match_score": r.match_score,
                "verdict": r.verdict,
                "price": r.product.price
            } for r in sorted_results[:4]]
        }


# Example usage
if __name__ == "__main__":
    from .product_matcher import Product

    generator = VerdictGenerator()

    # Create sample match result
    product = Product(
        id="s24ultra", name="Samsung S24 Ultra", brand="samsung",
        category="smartphone", price=107999, mrp=134999,
        specs={"camera_main_mp": 200, "battery_mah": 5000, "ram_gb": 12},
        features=["5g", "wireless_charging", "water_resistant"],
        rating=4.5, review_count=1800
    )

    match_result = MatchResult(
        product=product,
        match_score=85.5,
        match_breakdown={"budget": 90, "priority": 95, "must_haves": 80, "brand": 70, "use_case": 85, "reviews": 88},
        verdict="BUY",
        reasoning=["Excellent camera match", "Within budget", "Strong battery"],
        pros=["200MP camera", "5000mAh battery", "S Pen included"],
        cons=["Expensive", "Large size"],
        true_cost=115000,
        price_fairness="good_deal"
    )

    from .requirement_engine import UserRequirement, Priority, ShoppingIntent
    req = UserRequirement(
        category="smartphone",
        budget_max=120000,
        priorities=[Priority.CAMERA, Priority.BATTERY],
        use_cases=["photography"],
        must_haves=["5g"],
        intent=ShoppingIntent.BUY
    )

    verdict = generator.generate_verdict(match_result, req)

    print(f"Verdict: {verdict.verdict} (Confidence: {verdict.confidence}%)")
    print(f"Summary: {verdict.summary}")
    print(f"Reasoning: {verdict.reasoning}")
    print(f"Risks: {verdict.risks}")
    print(f"Timing: {verdict.timing_advice}")
    print(f"Total Cost: {verdict.total_cost_analysis}")
