"""
Tests for Product Matcher
"""

import pytest
from app.engine.product_matcher import Product, ProductMatcher, ProductKnowledgeGraph, MatchResult
from app.engine.requirement_engine import UserRequirement, Priority, ShoppingIntent

class TestProductMatcher:

    def setup_method(self):
        self.kg = ProductKnowledgeGraph()
        self.matcher = ProductMatcher(self.kg)

        # Add test products
        self.products = [
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

        for p in self.products:
            self.kg.add_product(p)

    def test_match_camera_priority(self):
        req = UserRequirement(
            category="smartphone",
            budget_max=120000,
            priorities=[Priority.CAMERA],
            use_cases=["photography"]
        )

        results = self.matcher.match(req, self.products)

        assert len(results) > 0
        # Samsung should win on camera (200MP)
        assert results[0].product.id == "p2"
        assert results[0].match_score > 70

    def test_match_budget_constraint(self):
        req = UserRequirement(
            category="smartphone",
            budget_max=90000,
            priorities=[Priority.CAMERA]
        )

        results = self.matcher.match(req, self.products)

        # iPhone should be filtered out (over budget)
        assert all(r.product.price <= 90000 * 1.2 for r in results)  # Allow slight overage

    def test_match_avoid_brand(self):
        req = UserRequirement(
            category="smartphone",
            budget_max=150000,
            avoided_brands=["apple"]
        )

        results = self.matcher.match(req, self.products)

        # iPhone should not appear
        assert all(r.product.brand != "apple" for r in results)

    def test_match_must_haves(self):
        req = UserRequirement(
            category="smartphone",
            budget_max=150000,
            must_haves=["5g", "water_resistant"]
        )

        results = self.matcher.match(req, self.products)

        # All should have must-haves
        for r in results:
            assert "5g" in [f.lower() for f in r.product.features]

    def test_verdict_generation(self):
        req = UserRequirement(
            category="smartphone",
            budget_max=120000,
            priorities=[Priority.CAMERA],
            urgency="urgent"
        )

        results = self.matcher.match(req, self.products)

        # Urgent should override to BUY if match > 60
        if results:
            assert results[0].verdict in ["BUY", "COMPARE"]


class TestProductKnowledgeGraph:

    def setup_method(self):
        self.kg = ProductKnowledgeGraph()

        self.products = [
            Product(id="p1", name="Phone A", brand="brand1", category="smartphone", price=30000),
            Product(id="p2", name="Phone B", brand="brand1", category="smartphone", price=35000),
            Product(id="p3", name="Laptop A", brand="brand2", category="laptop", price=50000),
        ]

        for p in self.products:
            self.kg.add_product(p)

    def test_find_substitutes(self):
        substitutes = self.kg.find_substitutes("p1", max_price_diff=0.3)

        # Should find p2 as substitute (same category, similar price)
        assert any(s.id == "p2" for s in substitutes)

    def test_category_insights(self):
        insights = self.kg.get_category_insights("smartphone")

        assert insights["total_products"] == 2
        assert insights["price_range"] == (30000, 35000)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
