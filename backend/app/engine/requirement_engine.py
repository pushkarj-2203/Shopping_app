"""
PriceWise AI Engine - Requirement Understanding Layer
Parses natural language / structured input into structured shopping intent
"""

import re
import json
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import numpy as np
# transformers imported lazily inside __init__ when use_llm=True (keeps base install light)

class ShoppingIntent(Enum):
    BUY = "buy"
    RESEARCH = "research"
    COMPARE = "compare"
    PRICE_CHECK = "price_check"
    GIFT = "gift"

class Priority(Enum):
    CAMERA = "camera"
    BATTERY = "battery"
    PERFORMANCE = "performance"
    DISPLAY = "display"
    VALUE = "value"
    BUILD_QUALITY = "build_quality"
    SOFTWARE = "software"
    BRAND = "brand"

@dataclass
class UserRequirement:
    """Structured representation of user shopping intent"""
    category: str
    budget_min: float = 0
    budget_max: float = float('inf')
    currency: str = "INR"
    priorities: List[Priority] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    must_haves: List[str] = field(default_factory=list)
    deal_breakers: List[str] = field(default_factory=list)
    preferred_brands: List[str] = field(default_factory=list)
    avoided_brands: List[str] = field(default_factory=list)
    urgency: str = "flexible"  # urgent, this_month, can_wait, no_rush
    intent: ShoppingIntent = ShoppingIntent.BUY
    natural_language_query: str = ""
    confidence_score: float = 0.0

    def to_dict(self) -> Dict:
        return {
            "category": self.category,
            "budget_range": [self.budget_min, self.budget_max],
            "currency": self.currency,
            "priorities": [p.value for p in self.priorities],
            "use_cases": self.use_cases,
            "must_haves": self.must_haves,
            "deal_breakers": self.deal_breakers,
            "preferred_brands": self.preferred_brands,
            "avoided_brands": self.avoided_brands,
            "urgency": self.urgency,
            "intent": self.intent.value,
            "confidence_score": self.confidence_score
        }

class RequirementParser:
    """
    Advanced requirement parser using hybrid approach:
    1. Rule-based extraction for structured data (budget, brands)
    2. ML-based classification for intent and priorities
    3. LLM-based extraction for complex natural language
    """

    # Budget extraction patterns
    BUDGET_PATTERNS = [
        r'(?:under|below|less than|max|maximum|upto|up to)\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:k|thousand)?',
        r'(?:budget|price|cost)\s*(?:of|is)?\s*(?:Rs\.?|₹|INR)?\s*([\d,]+(?:\.\d+)?)\s*(?:k|thousand)?',
        r'(?:Rs\.?|₹|INR)\s*([\d,]+(?:\.\d+)?)\s*(?:k|thousand)?\s*(?:budget|range)?',
        r'([\d,]+(?:\.\d+)?)\s*(?:k|thousand)\s*(?:budget|range|max)?',
    ]

    # Category keywords
    CATEGORIES = {
        "smartphone": ["phone", "mobile", "smartphone", "cell", "handset", "android", "iphone"],
        "laptop": ["laptop", "notebook", "macbook", "ultrabook", "chromebook"],
        "headphones": ["headphones", "earphones", "earbuds", "tws", "airpods", "headset"],
        "tablet": ["tablet", "ipad", "tab", "slate"],
        "smartwatch": ["watch", "smartwatch", "fitness band", "wearable"],
        "camera": ["camera", "dslr", "mirrorless", "gopro", "action camera"],
        "tv": ["tv", "television", "smart tv", "oled", "qled", "4k tv"],
        "refrigerator": ["fridge", "refrigerator", "freezer"],
        "washing_machine": ["washing machine", "washer", "dryer"],
        "ac": ["ac", "air conditioner", "cooler", "split ac"]
    }

    # Priority keywords
    PRIORITY_KEYWORDS = {
        Priority.CAMERA: ["camera", "photo", "photography", "selfie", "video", "zoom", "megapixel", "mp", "lens"],
        Priority.BATTERY: ["battery", "charge", "charging", "backup", "power", "mah", "endurance", "lasts"],
        Priority.PERFORMANCE: ["performance", "speed", "fast", "gaming", "processor", "chip", "ram", "smooth"],
        Priority.DISPLAY: ["display", "screen", "resolution", "amoled", "oled", "refresh", "hz", "bright"],
        Priority.VALUE: ["value", "worth", "deal", "bang", "budget", "affordable", "cheap", "best value"],
        Priority.BUILD_QUALITY: ["build", "quality", "premium", "durable", "strong", "metal", "glass"],
        Priority.SOFTWARE: ["software", "ui", "os", "android", "ios", "updates", "clean", "bloatware"],
        Priority.BRAND: ["brand", "apple", "samsung", "oneplus", "reliable", "trust", "service"]
    }

    # Must-have features
    MUST_HAVE_FEATURES = {
        "5g": ["5g", "5g support", "fifth generation"],
        "wireless_charging": ["wireless charging", "wireless charge", "qi charging"],
        "water_resistant": ["water resistant", "waterproof", "ip68", "ip67", "splash proof"],
        "amoled": ["amoled", "oled", "super amoled"],
        "fast_charging": ["fast charging", "quick charge", "dash charge", "warp charge", "65w", "120w"],
        "headphone_jack": ["headphone jack", "3.5mm", "audio jack"],
        "expandable_storage": ["sd card", "expandable", "micro sd", "memory card"],
        "dual_sim": ["dual sim", "esim", "dual standby"],
        "nfc": ["nfc", "contactless", "google pay", "tap to pay"],
        "stylus": ["stylus", "s pen", "pen support"]
    }

    def __init__(self, use_llm: bool = False, model_path: Optional[str] = None):
        self.use_llm = use_llm
        self.model_path = model_path

        # Initialize lightweight ML models (can run on CPU)
        if use_llm and model_path:
            from transformers import pipeline  # lazy import: heavy dependency
            self.intent_classifier = pipeline(
                "text-classification",
                model=model_path,
                device=-1  # CPU
            )
        else:
            self.intent_classifier = None

    def parse(self, query: str, category: Optional[str] = None) -> UserRequirement:
        """
        Main parsing method. Handles both natural language and structured input.

        Args:
            query: Natural language query or structured JSON string
            category: Optional category hint

        Returns:
            UserRequirement object with structured intent
        """
        # Try JSON parsing first
        try:
            data = json.loads(query)
            return self._parse_structured(data)
        except (json.JSONDecodeError, TypeError):
            pass

        # Natural language parsing
        return self._parse_natural_language(query, category)

    def _parse_structured(self, data: Dict) -> UserRequirement:
        """Parse structured JSON input"""
        req = UserRequirement(
            category=data.get("category", "unknown"),
            budget_min=data.get("budget_min", 0),
            budget_max=data.get("budget_max", float('inf')),
            currency=data.get("currency", "INR"),
            priorities=[Priority(p) for p in data.get("priorities", [])],
            use_cases=data.get("use_cases", []),
            must_haves=data.get("must_haves", []),
            deal_breakers=data.get("deal_breakers", []),
            preferred_brands=data.get("preferred_brands", []),
            avoided_brands=data.get("avoided_brands", []),
            urgency=data.get("urgency", "flexible"),
            intent=ShoppingIntent(data.get("intent", "buy")),
            confidence_score=1.0
        )
        return req

    def _parse_natural_language(self, query: str, category_hint: Optional[str] = None) -> UserRequirement:
        """Parse natural language query using hybrid rule + ML approach"""
        query_lower = query.lower()

        # Extract category
        category = category_hint or self._extract_category(query_lower)

        # Extract budget
        budget_min, budget_max = self._extract_budget(query_lower)

        # Extract priorities
        priorities = self._extract_priorities(query_lower)

        # Extract use cases
        use_cases = self._extract_use_cases(query_lower)

        # Extract must-haves and deal-breakers
        must_haves, deal_breakers = self._extract_features(query_lower)

        # Extract brands
        preferred_brands, avoided_brands = self._extract_brands(query_lower)

        # Extract urgency
        urgency = self._extract_urgency(query_lower)

        # Determine intent
        intent = self._classify_intent(query_lower)

        # Calculate confidence based on extraction completeness
        confidence = self._calculate_confidence(
            category, budget_max, priorities, use_cases, must_haves
        )

        req = UserRequirement(
            category=category,
            budget_min=budget_min,
            budget_max=budget_max,
            priorities=priorities,
            use_cases=use_cases,
            must_haves=must_haves,
            deal_breakers=deal_breakers,
            preferred_brands=preferred_brands,
            avoided_brands=avoided_brands,
            urgency=urgency,
            intent=intent,
            natural_language_query=query,
            confidence_score=confidence
        )

        return req

    def _extract_category(self, query: str) -> str:
        """Extract product category from query"""
        scores = {}
        for cat, keywords in self.CATEGORIES.items():
            score = sum(1 for kw in keywords if kw in query)
            if score > 0:
                scores[cat] = score

        return max(scores, key=scores.get) if scores else "unknown"

    def _extract_budget(self, query: str) -> Tuple[float, float]:
        """Extract budget range from query"""
        budget_min = 0
        budget_max = float('inf')

        for pattern in self.BUDGET_PATTERNS:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                amount_str = match[0] if isinstance(match, tuple) else match
                amount_str = amount_str.replace(',', '')

                try:
                    amount = float(amount_str)
                    # Handle 'k' suffix
                    if 'k' in query[query.find(amount_str):query.find(amount_str)+len(amount_str)+2]:
                        amount *= 1000

                    # Determine if this is min or max
                    if any(word in query[max(0, query.find(amount_str)-20):query.find(amount_str)] 
                           for word in ['under', 'below', 'less', 'max', 'maximum', 'upto']):
                        budget_max = amount
                    else:
                        budget_max = amount

                except ValueError:
                    continue

        return budget_min, budget_max

    def _extract_priorities(self, query: str) -> List[Priority]:
        """Extract user priorities from query"""
        priorities = []
        for priority, keywords in self.PRIORITY_KEYWORDS.items():
            score = sum(2 if kw in query else 0 for kw in keywords)
            if score > 0:
                priorities.append((priority, score))

        # Sort by score and return top 3
        priorities.sort(key=lambda x: x[1], reverse=True)
        return [p[0] for p in priorities[:3]]

    def _extract_use_cases(self, query: str) -> List[str]:
        """Extract use cases from query"""
        use_cases = []
        use_case_keywords = {
            "gaming": ["game", "gaming", "pubg", "cod", "fortnite", "gamer"],
            "photography": ["photo", "camera", "photography", "vlog", "content creation"],
            "work": ["work", "office", "productivity", "business", "professional", "programming", "coding", "developer", "development", "engineering"],
            "streaming": ["stream", "netflix", "youtube", "watch", "media"],
            "social_media": ["social", "instagram", "tiktok", "reels", "stories"],
            "travel": ["travel", "trip", "vacation", "outdoor", "adventure"],
            "student": ["student", "study", "college", "university", "education"],
            "elderly": ["parent", "elderly", "simple", "easy to use", "senior"]
        }

        for use_case, keywords in use_case_keywords.items():
            if any(kw in query for kw in keywords):
                use_cases.append(use_case)

        return use_cases

    def _extract_features(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract must-have features and deal-breakers"""
        must_haves = []
        deal_breakers = []

        for feature, keywords in self.MUST_HAVE_FEATURES.items():
            for kw in keywords:
                if kw in query:
                    # Check if negated
                    context = query[max(0, query.find(kw)-30):query.find(kw)+len(kw)+10]
                    if any(neg in context for neg in ['no ', 'not ', 'without ', "don't want", 'avoid']):
                        deal_breakers.append(feature)
                    else:
                        must_haves.append(feature)
                    break

        return must_haves, deal_breakers

    def _extract_brands(self, query: str) -> Tuple[List[str], List[str]]:
        """Extract preferred and avoided brands"""
        brands = ["apple", "samsung", "oneplus", "xiaomi", "redmi", "realme", "oppo", 
                  "vivo", "nothing", "google", "motorola", "nokia", "asus", "lenovo",
                  "hp", "dell", "acer", "msi", "sony", "bose", "jbl", "sennheiser"]

        preferred = []
        avoided = []

        for brand in brands:
            if brand in query:
                context = query[max(0, query.find(brand)-40):query.find(brand)+len(brand)+20]
                if any(neg in context for neg in ['not ', 'no ', 'avoid', "don't like", 'hate', 'excluding']):
                    avoided.append(brand)
                elif any(pos in context for pos in ['prefer', 'like', 'want', 'love', 'only']):
                    preferred.append(brand)
                else:
                    preferred.append(brand)

        return preferred, avoided

    def _extract_urgency(self, query: str) -> str:
        """Extract urgency level"""
        urgent_keywords = ['urgent', 'immediately', 'today', 'asap', 'right now', 'emergency']
        this_month_keywords = ['this month', 'soon', 'next week', 'upcoming', 'diwali', 'sale']
        can_wait_keywords = ['can wait', 'not urgent', 'whenever', 'eventually']

        if any(kw in query for kw in urgent_keywords):
            return "urgent"
        elif any(kw in query for kw in this_month_keywords):
            return "this_month"
        elif any(kw in query for kw in can_wait_keywords):
            return "can_wait"
        return "flexible"

    def _classify_intent(self, query: str) -> ShoppingIntent:
        """Classify shopping intent"""
        if any(kw in query for kw in ['compare', 'vs', 'versus', 'difference', 'better']):
            return ShoppingIntent.COMPARE
        elif any(kw in query for kw in ['price', 'cost', 'how much', 'cheapest', 'deal']):
            return ShoppingIntent.PRICE_CHECK
        elif any(kw in query for kw in ['gift', 'present', 'buy for', 'surprise']):
            return ShoppingIntent.GIFT
        elif any(kw in query for kw in ['research', 'learn', 'info', 'specs', 'review']):
            return ShoppingIntent.RESEARCH
        return ShoppingIntent.BUY

    def _calculate_confidence(self, category: str, budget: float, priorities: List, 
                             use_cases: List, must_haves: List) -> float:
        """Calculate confidence score based on extraction completeness"""
        score = 0.0
        if category != "unknown": score += 0.30
        if budget != float('inf'): score += 0.25
        if priorities: score += 0.20
        if use_cases: score += 0.15
        if must_haves: score += 0.10
        return min(round(score, 2), 1.0)


class QuestionnaireGenerator:
    """
    Generates dynamic questionnaires based on category and partial requirements.
    Adapts questions based on previous answers to narrow down user needs.
    """

    BASE_QUESTIONS = {
        "smartphone": [
            {"id": "budget", "type": "range", "min": 5000, "max": 150000, "step": 1000,
             "question": "What's your budget?", "unit": "₹"},
            {"id": "priority", "type": "single_choice",
             "options": ["Camera", "Battery", "Performance", "Display", "Value for Money"],
             "question": "What's most important to you?"},
            {"id": "use_case", "type": "multi_choice",
             "options": ["Gaming", "Photography", "Work/Office", "Social Media", "Streaming", "Travel"],
             "question": "What will you use it for?"},
            {"id": "must_haves", "type": "multi_choice",
             "options": ["5G", "Wireless Charging", "Water Resistance", "AMOLED Display", 
                        "Fast Charging", "Headphone Jack", "Expandable Storage"],
             "question": "Any must-have features?"},
            {"id": "brands", "type": "multi_choice",
             "options": ["Apple", "Samsung", "OnePlus", "Xiaomi", "Nothing", "Google", "Realme"],
             "question": "Preferred brands?"},
            {"id": "avoid_brands", "type": "multi_choice",
             "options": ["Apple", "Samsung", "OnePlus", "Xiaomi", "Nothing", "Google", "Realme"],
             "question": "Brands to avoid?"},
            {"id": "urgency", "type": "single_choice",
             "options": ["Urgent (this week)", "This month", "Can wait for sale", "No rush"],
             "question": "When do you need it?"}
        ],
        "laptop": [
            {"id": "budget", "type": "range", "min": 20000, "max": 200000, "step": 5000,
             "question": "What's your budget?", "unit": "₹"},
            {"id": "priority", "type": "single_choice",
             "options": ["Performance", "Portability", "Display", "Battery", "Value"],
             "question": "What's most important?"},
            {"id": "use_case", "type": "multi_choice",
             "options": ["Programming", "Design/Video Editing", "Gaming", "Office Work", "Student", "Content Creation"],
             "question": "Primary use case?"},
            {"id": "must_haves", "type": "multi_choice",
             "options": ["Touchscreen", "Backlit Keyboard", "Fingerprint Reader", "Thunderbolt", 
                        "Dedicated GPU", "OLED Display", "Lightweight (<1.5kg)"],
             "question": "Must-have features?"},
            {"id": "brands", "type": "multi_choice",
             "options": ["Apple", "Dell", "HP", "Lenovo", "Asus", "Acer", "MSI"],
             "question": "Preferred brands?"}
        ]
    }

    def generate(self, category: str, answered_questions: Dict = None) -> List[Dict]:
        """Generate questionnaire, optionally skipping answered questions"""
        answered_questions = answered_questions or {}
        questions = self.BASE_QUESTIONS.get(category, self.BASE_QUESTIONS["smartphone"])

        # Filter out already answered questions
        remaining = [q for q in questions if q["id"] not in answered_questions]

        # Adaptive: at premium budgets, replace the generic must-haves question
        # with a premium-features question (more relevant for high-end buyers).
        if answered_questions.get("budget", 0) > 80000:
            remaining = [q for q in remaining if q["id"] != "must_haves"]
            remaining.append({
                "id": "premium_features",
                "type": "multi_choice",
                "options": ["Flagship processor", "Pro camera system", "Premium build", "Latest tech"],
                "question": "Which premium features matter?"
            })

        # Adaptive: if gaming selected, add gaming-specific questions
        if "gaming" in str(answered_questions.get("use_case", "")).lower():
            remaining.append({
                "id": "gaming_priority",
                "type": "single_choice",
                "options": ["High FPS", "Ray Tracing", "Battery while gaming", "Thermal management"],
                "question": "Gaming priority?"
            })

        return remaining

    def generate_follow_up(self, requirement: UserRequirement, products_seen: int) -> List[str]:
        """Generate Perplexity-style follow-up questions based on current state"""
        follow_ups = []

        if products_seen > 0:
            follow_ups.extend([
                "Should I wait for the next sale?",
                "What if I increase my budget slightly?",
                "What if I drop some requirements?",
                "How does this compare to last year's model?",
                "What are the most common complaints?",
                "Is there a better alternative?",
                "Will the price drop soon?"
            ])

        if requirement.urgency == "can_wait":
            follow_ups.append("When is the best time to buy?")

        if requirement.budget_max < 50000:
            follow_ups.append("What features will I miss at this budget?")

        return follow_ups[:5]  # Return top 5


# Example usage and testing
if __name__ == "__main__":
    parser = RequirementParser()

    # Test natural language parsing
    test_queries = [
        "I need a phone with great camera under 50000, good battery, not Apple, for photography",
        "Best laptop for programming under 80000, prefer lightweight, avoid HP",
        '{"category": "smartphone", "budget_max": 60000, "priorities": ["camera"], "use_cases": ["photography"]}'
    ]

    for query in test_queries:
        req = parser.parse(query)
        print(f"\nQuery: {query[:50]}...")
        print(f"Parsed: {json.dumps(req.to_dict(), indent=2)}")
