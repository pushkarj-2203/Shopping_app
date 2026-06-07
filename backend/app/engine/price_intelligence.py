"""
PriceWise AI Engine - Price Intelligence Layer
Detects fake discounts, analyzes price history, predicts optimal buy timing
"""

import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict
import statistics

@dataclass
class PricePoint:
    """Single price observation"""
    price: float
    mrp: float
    date: datetime
    source: str
    discount_label: str = ""  # "50% off", "Diwali Sale", etc.

@dataclass
class PriceHistory:
    """Complete price history for a product"""
    product_id: str
    price_points: List[PricePoint]

    @property
    def min_price(self) -> float:
        return min(p.price for p in self.price_points) if self.price_points else 0

    @property
    def max_price(self) -> float:
        return max(p.price for p in self.price_points) if self.price_points else 0

    @property
    def avg_price(self) -> float:
        return statistics.mean(p.price for p in self.price_points) if self.price_points else 0

    @property
    def current_price(self) -> float:
        return self.price_points[-1].price if self.price_points else 0

    @property
    def current_mrp(self) -> float:
        return self.price_points[-1].mrp if self.price_points else 0

class PriceAnalyzer:
    """
    Analyzes price patterns to detect manipulation and predict trends.
    """

    # Sale calendar for India
    SALE_CALENDAR = {
        "republic_day": {"month": 1, "day": 26, "window": 7},
        "holi": {"month": 3, "day": 10, "window": 5, "variable": True},
        "prime_day": {"month": 7, "day": 15, "window": 3, "variable": True},
        "independence_day": {"month": 8, "day": 15, "window": 7},
        "diwali": {"month": 11, "day": 12, "window": 14, "variable": True},
        "black_friday": {"month": 11, "day": 29, "window": 5},
        "christmas": {"month": 12, "day": 25, "window": 7},
        "new_year": {"month": 1, "day": 1, "window": 5},
        "end_of_season": {"month": 6, "day": 30, "window": 10},
    }

    def __init__(self):
        self.price_histories: Dict[str, PriceHistory] = {}
        self.mrp_inflation_patterns = defaultdict(list)

    def add_price_history(self, history: PriceHistory):
        """Add price history for a product"""
        self.price_histories[history.product_id] = history

    def detect_fake_discount(self, product_id: str) -> Dict:
        """
        Detect if current discount is genuine or manipulated.

        Returns:
            {
                "is_fake": bool,
                "confidence": float,
                "reasoning": List[str],
                "true_discount": float,  # Actual discount from fair baseline
                "inflated_mrp": float,   # How much MRP was inflated
                "recommendation": str
            }
        """
        if product_id not in self.price_histories:
            return {"is_fake": False, "confidence": 0, "reasoning": ["No price history available"]}

        history = self.price_histories[product_id]
        current = history.price_points[-1]

        reasoning = []
        is_fake = False
        confidence = 0.0
        inflated_mrp = 0.0

        # Pattern 1: MRP suddenly increased before sale
        mrp_trend = self._analyze_mrp_trend(history)
        if mrp_trend["inflated_before_sale"]:
            is_fake = True
            confidence += 0.4
            inflated_mrp = mrp_trend["inflation_amount"]
            reasoning.append(f"MRP inflated by ₹{inflated_mrp} before sale period")

        # Pattern 2: Discount percentage higher than historical average
        avg_discount = self._calculate_avg_discount(history)
        current_discount = (1 - current.price / current.mrp) * 100 if current.mrp > 0 else 0

        if current_discount > avg_discount * 1.5 + 10:
            is_fake = True
            confidence += 0.3
            reasoning.append(f"Discount ({current_discount:.0f}%) is unusually high vs historical average ({avg_discount:.0f}%)")

        # Pattern 3: Price never actually sold at MRP
        if self._check_never_sold_at_mrp(history):
            is_fake = True
            confidence += 0.2
            reasoning.append("Product has never been sold at listed MRP price")

        # Pattern 4: Compare to similar products
        similar_discount = self._get_similar_products_discount(product_id)
        if similar_discount and current_discount > similar_discount * 1.8:
            is_fake = True
            confidence += 0.1
            reasoning.append("Discount much higher than similar products in category")

        # Calculate true discount from fair baseline
        fair_baseline = self._calculate_fair_baseline(history)
        true_discount = (1 - current.price / fair_baseline) * 100 if fair_baseline > 0 else 0

        recommendation = "good_deal" if true_discount > 20 else "fair" if true_discount > 10 else "inflated"
        if is_fake and confidence > 0.5:
            recommendation = "fake_discount"

        return {
            "is_fake": is_fake,
            "confidence": min(confidence, 1.0),
            "reasoning": reasoning,
            "true_discount": round(true_discount, 1),
            "inflated_mrp": round(inflated_mrp, 0),
            "recommendation": recommendation,
            "fair_baseline": round(fair_baseline, 0)
        }

    def predict_optimal_buy_time(self, product_id: str, urgency: str = "flexible") -> Dict:
        """
        Predict best time to buy based on price patterns and sale calendar.

        Returns:
            {
                "buy_now": bool,
                "confidence": float,
                "next_sale_date": str,
                "expected_discount": float,
                "price_trend": str,  # rising, falling, stable
                "recommendation": str
            }
        """
        if product_id not in self.price_histories:
            return {
                "buy_now": True,
                "confidence": 0.3,
                "reasoning": ["No price history - cannot predict trends"]
            }

        history = self.price_histories[product_id]
        current_price = history.current_price

        # Analyze price trend
        trend = self._analyze_price_trend(history)

        # Find upcoming sales
        upcoming_sales = self._get_upcoming_sales()

        # Check if current price is near historical minimum
        near_min = current_price <= history.min_price * 1.05

        recommendation = {
            "buy_now": False,
            "confidence": 0.0,
            "next_sale_date": None,
            "expected_discount": 0.0,
            "price_trend": trend["direction"],
            "days_to_sale": None,
            "reasoning": []
        }

        if near_min:
            recommendation["buy_now"] = True
            recommendation["confidence"] = 0.9
            recommendation["reasoning"].append("Current price is near historical minimum")

        if trend["direction"] == "falling":
            recommendation["reasoning"].append("Price is on downward trend")
            if not near_min:
                recommendation["reasoning"].append("May drop further - consider waiting")

        if upcoming_sales:
            next_sale = upcoming_sales[0]
            days_to_sale = (next_sale["date"] - datetime.now()).days
            recommendation["next_sale_date"] = next_sale["date"].strftime("%Y-%m-%d")
            recommendation["expected_discount"] = next_sale["expected_discount"]
            recommendation["days_to_sale"] = days_to_sale

            if days_to_sale <= 14 and urgency != "urgent":
                recommendation["buy_now"] = False
                recommendation["confidence"] = 0.7
                recommendation["reasoning"].append(f"{next_sale['name']} sale in {days_to_sale} days - expect {next_sale['expected_discount']}% off")
            elif days_to_sale <= 30 and urgency == "can_wait":
                recommendation["reasoning"].append(f"Wait for {next_sale['name']} sale for better deals")

        # Urgency override
        if urgency == "urgent":
            recommendation["buy_now"] = True
            recommendation["reasoning"].append("Urgent need - buy now regardless of price")

        return recommendation

    def _analyze_mrp_trend(self, history: PriceHistory) -> Dict:
        """Analyze if MRP was inflated before sale"""
        if len(history.price_points) < 3:
            return {"inflated_before_sale": False}

        # Check for MRP spike followed by discount
        mrps = [p.mrp for p in history.price_points]
        prices = [p.price for p in history.price_points]

        # Find MRP increases
        for i in range(1, len(mrps)):
            if mrps[i] > mrps[i-1] * 1.2:  # 20% increase
                # Check if price stayed same or dropped
                if prices[i] <= prices[i-1]:
                    return {
                        "inflated_before_sale": True,
                        "inflation_amount": mrps[i] - mrps[i-1],
                        "inflation_date": history.price_points[i].date
                    }

        return {"inflated_before_sale": False}

    def _calculate_avg_discount(self, history: PriceHistory) -> float:
        """Calculate average historical discount percentage"""
        discounts = []
        for p in history.price_points:
            if p.mrp > 0:
                discounts.append((1 - p.price / p.mrp) * 100)
        return statistics.mean(discounts) if discounts else 0

    def _check_never_sold_at_mrp(self, history: PriceHistory) -> bool:
        """Check if product was ever sold at listed MRP"""
        for p in history.price_points:
            if p.price >= p.mrp * 0.99:  # Within 1% of MRP
                return False
        return len(history.price_points) > 5  # Only flag if we have enough data

    def _get_similar_products_discount(self, product_id: str) -> Optional[float]:
        """Get average discount for similar products"""
        # In real implementation, query knowledge graph for similar products
        return 15.0  # Default 15%

    def _calculate_fair_baseline(self, history: PriceHistory) -> float:
        """Calculate fair baseline price (not inflated MRP)"""
        # Use 75th percentile of actual selling prices
        prices = sorted([p.price for p in history.price_points])
        if len(prices) >= 4:
            idx = int(len(prices) * 0.75)
            return prices[idx]
        return statistics.median(prices) if prices else 0

    def _analyze_price_trend(self, history: PriceHistory) -> Dict:
        """Analyze price trend direction"""
        if len(history.price_points) < 3:
            return {"direction": "stable", "slope": 0}

        # Simple linear regression on last 6 months
        recent = [p for p in history.price_points 
                  if p.date > datetime.now() - timedelta(days=180)]

        if len(recent) < 3:
            recent = history.price_points[-6:]  # Last 6 points

        prices = [p.price for p in recent]
        x = np.arange(len(prices))

        if len(prices) < 2:
            return {"direction": "stable", "slope": 0}

        slope = np.polyfit(x, prices, 1)[0]

        if slope < -50:  # Dropping fast
            return {"direction": "falling", "slope": slope}
        elif slope > 50:  # Rising fast
            return {"direction": "rising", "slope": slope}
        else:
            return {"direction": "stable", "slope": slope}

    def _get_upcoming_sales(self) -> List[Dict]:
        """Get upcoming sale events with expected discounts"""
        now = datetime.now()
        sales = []

        for name, config in self.SALE_CALENDAR.items():
            sale_date = datetime(now.year, config["month"], config["day"])
            if sale_date < now:
                sale_date = datetime(now.year + 1, config["month"], config["day"])

            days_until = (sale_date - now).days
            if days_until <= 90:  # Only show next 90 days
                sales.append({
                    "name": name.replace("_", " ").title(),
                    "date": sale_date,
                    "days_until": days_until,
                    "expected_discount": self._estimate_sale_discount(name)
                })

        sales.sort(key=lambda x: x["days_until"])
        return sales

    def _estimate_sale_discount(self, sale_name: str) -> float:
        """Estimate typical discount for a sale event"""
        discounts = {
            "republic_day": 15,
            "holi": 10,
            "prime_day": 25,
            "independence_day": 20,
            "diwali": 30,
            "black_friday": 25,
            "christmas": 15,
            "new_year": 10,
            "end_of_season": 20
        }
        return discounts.get(sale_name, 15)


class DynamicPricingDetector:
    """
    Detects personalized/dynamic pricing patterns.
    Some e-commerce sites show different prices to different users.
    """

    def __init__(self):
        self.price_observations = defaultdict(list)

    def add_observation(self, product_id: str, price: float, user_fingerprint: str, 
                       timestamp: datetime, location: str = ""):
        """Add price observation from different users"""
        self.price_observations[product_id].append({
            "price": price,
            "user": user_fingerprint,
            "time": timestamp,
            "location": location
        })

    def detect_personalized_pricing(self, product_id: str) -> Dict:
        """Detect if product has personalized pricing"""
        observations = self.price_observations.get(product_id, [])
        if len(observations) < 5:
            return {"detected": False, "confidence": 0}

        prices = [o["price"] for o in observations]
        unique_prices = set(prices)

        # If many different prices for same product at same time
        time_groups = defaultdict(list)
        for obs in observations:
            hour_key = obs["time"].strftime("%Y-%m-%d-%H")
            time_groups[hour_key].append(obs["price"])

        suspicious = 0
        for hour, prices in time_groups.items():
            if len(set(prices)) > 1:
                price_range = max(prices) - min(prices)
                avg_price = statistics.mean(prices)
                if price_range / avg_price > 0.05:  # >5% variation
                    suspicious += 1

        total_hours = len(time_groups)
        if total_hours > 0 and suspicious / total_hours > 0.3:
            return {
                "detected": True,
                "confidence": suspicious / total_hours,
                "price_range": (min(prices), max(prices)),
                "variation_percent": round((max(prices) - min(prices)) / statistics.mean(prices) * 100, 1)
            }

        return {"detected": False, "confidence": 0}


# Example usage
if __name__ == "__main__":
    analyzer = PriceAnalyzer()

    # Create sample price history
    history = PriceHistory(
        product_id="iphone16pro",
        price_points=[
            PricePoint(price=134900, mrp=134900, date=datetime(2025, 9, 1), source="apple"),
            PricePoint(price=134900, mrp=134900, date=datetime(2025, 10, 1), source="amazon"),
            PricePoint(price=129900, mrp=134900, date=datetime(2025, 11, 1), source="amazon", discount_label="Diwali Sale"),
            PricePoint(price=127900, mrp=134900, date=datetime(2025, 12, 1), source="flipkart"),
            PricePoint(price=129900, mrp=139900, date=datetime(2026, 1, 15), source="amazon"),  # MRP inflated!
            PricePoint(price=124900, mrp=139900, date=datetime(2026, 1, 26), source="amazon", discount_label="Republic Day Sale"),
        ]
    )

    analyzer.add_price_history(history)

    # Detect fake discount
    result = analyzer.detect_fake_discount("iphone16pro")
    print(f"Fake discount detection: {json.dumps(result, indent=2)}")

    # Predict buy timing
    prediction = analyzer.predict_optimal_buy_time("iphone16pro", urgency="can_wait")
    print(f"\nBuy timing prediction: {json.dumps(prediction, indent=2, default=str)}")
