"""
Tests for Requirement Understanding Engine
"""

import pytest
from app.engine.requirement_engine import RequirementParser, UserRequirement, Priority, ShoppingIntent

class TestRequirementParser:

    def setup_method(self):
        self.parser = RequirementParser()

    def test_parse_simple_budget_query(self):
        query = "I need a phone under 30000"
        result = self.parser.parse(query)

        assert result.category == "smartphone"
        assert result.budget_max == 30000
        assert result.confidence_score > 0.5

    def test_parse_detailed_query(self):
        query = "I want a phone with great camera and battery for photography under 50000, not Apple"
        result = self.parser.parse(query)

        assert result.category == "smartphone"
        assert result.budget_max == 50000
        assert Priority.CAMERA in result.priorities
        assert Priority.BATTERY in result.priorities
        assert "photography" in result.use_cases
        assert "apple" in [b.lower() for b in result.avoided_brands]

    def test_parse_structured_json(self):
        query = '{"category": "laptop", "budget_max": 80000, "priorities": ["performance"]}'
        result = self.parser.parse(query)

        assert result.category == "laptop"
        assert result.budget_max == 80000
        assert result.confidence_score == 1.0

    def test_parse_laptop_query(self):
        query = "Best laptop for programming under 60000, prefer lightweight"
        result = self.parser.parse(query)

        assert result.category == "laptop"
        assert result.budget_max == 60000
        assert "work" in result.use_cases

    def test_parse_gaming_query(self):
        query = "Phone for gaming under 40000, good performance, fast charging"
        result = self.parser.parse(query)

        assert "gaming" in result.use_cases
        assert Priority.PERFORMANCE in result.priorities
        assert "fast_charging" in result.must_haves

    def test_parse_urgency(self):
        query = "Need phone urgently under 25000"
        result = self.parser.parse(query)

        assert result.urgency == "urgent"

    def test_parse_brand_preference(self):
        query = "Samsung phone under 50000, avoid Xiaomi"
        result = self.parser.parse(query)

        assert "samsung" in [b.lower() for b in result.preferred_brands]
        assert "xiaomi" in [b.lower() for b in result.avoided_brands]


class TestQuestionnaireGenerator:

    def setup_method(self):
        from app.engine.requirement_engine import QuestionnaireGenerator
        self.gen = QuestionnaireGenerator()

    def test_generate_smartphone_questionnaire(self):
        questions = self.gen.generate("smartphone")

        assert len(questions) > 0
        assert any(q["id"] == "budget" for q in questions)
        assert any(q["id"] == "priority" for q in questions)

    def test_adaptive_questionnaire(self):
        answered = {"budget": 100000}
        questions = self.gen.generate("smartphone", answered)

        # Should have fewer questions
        assert len(questions) < len(self.gen.BASE_QUESTIONS["smartphone"])

    def test_premium_questions_for_high_budget(self):
        answered = {"budget": 100000}
        questions = self.gen.generate("smartphone", answered)

        # Should include premium questions
        assert any(q["id"] == "premium_features" for q in questions)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
