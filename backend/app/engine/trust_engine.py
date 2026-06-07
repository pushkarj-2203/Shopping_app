"""
PriceWise AI Engine - Trust & Review Engine
Detects fake reviews, sponsored content, and review manipulation
"""

import re
import json
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime

@dataclass
class Review:
    """Individual product review"""
    id: str
    product_id: str
    rating: int  # 1-5
    title: str
    text: str
    author: str
    date: datetime
    verified_purchase: bool = False
    helpful_count: int = 0
    total_helpful_votes: int = 0
    images: List[str] = field(default_factory=list)

    @property
    def length(self) -> int:
        return len(self.text)

    @property
    def has_images(self) -> bool:
        return len(self.images) > 0

@dataclass
class ReviewAnalysis:
    """Analysis result for a product's reviews"""
    product_id: str
    overall_trust_score: float  # 0-100
    authenticity_breakdown: Dict[str, float]
    sentiment_distribution: Dict[str, float]
    suspicious_patterns: List[str]
    key_themes: List[Tuple[str, float]]
    verified_purchase_ratio: float
    review_velocity: float  # Reviews per day
    rating_distribution: Dict[int, int]

class ReviewTrustEngine:
    """
    Multi-layer review analysis system:
    1. Statistical anomaly detection
    2. Text pattern analysis (generic vs. specific)
    3. Temporal pattern detection (review bombs)
    4. Author behavior analysis
    5. Cross-platform verification
    """

    # Generic review phrases (indicators of fake/paid reviews)
    GENERIC_PHRASES = [
        "good product", "nice product", "great product", "awesome product",
        "value for money", "worth buying", "go for it", "highly recommended",
        "must buy", "dont think twice", "just buy it", "best in class",
        "fully satisfied", "totally worth it", "amazing quality",
        "excellent product", "loved it", "superb", "fantastic"
    ]

    # Suspicious patterns
    SUSPICIOUS_PATTERNS = {
        "burst_reviews": "Many reviews in short time period",
        "all_five_star": "Unusually high percentage of 5-star reviews",
        "generic_text": "High proportion of generic review text",
        "no_verified": "Low verified purchase ratio",
        "duplicate_text": "Identical or near-identical reviews",
        "extreme_polarization": "Only 1-star and 5-star reviews",
        "early_positive": "All early reviews are positive",
        "helpful_manipulation": "Suspicious helpful vote patterns",
        "brand_defense": "Reviews that only defend against negative reviews",
        "keyword_stuffing": "Unnatural repetition of product keywords"
    }

    def __init__(self):
        self.reviews_db = defaultdict(list)
        self.author_history = defaultdict(list)
        self.product_stats = {}

    def add_reviews(self, product_id: str, reviews: List[Review]):
        """Add reviews for analysis"""
        self.reviews_db[product_id].extend(reviews)

        # Update author history
        for review in reviews:
            self.author_history[review.author].append(review)

    def analyze(self, product_id: str) -> ReviewAnalysis:
        """
        Comprehensive review analysis for a product.

        Returns:
            ReviewAnalysis with trust scores and suspicious patterns
        """
        reviews = self.reviews_db.get(product_id, [])
        if not reviews:
            return ReviewAnalysis(
                product_id=product_id,
                overall_trust_score=50.0,
                authenticity_breakdown={},
                sentiment_distribution={},
                suspicious_patterns=["No reviews available"],
                key_themes=[],
                verified_purchase_ratio=0.0,
                review_velocity=0.0,
                rating_distribution={}
            )

        # Run all detection modules
        patterns = []

        # 1. Temporal analysis
        temporal = self._analyze_temporal_patterns(reviews)
        if temporal["suspicious"]:
            patterns.append(temporal["pattern"])

        # 2. Rating distribution analysis
        rating_dist = self._analyze_rating_distribution(reviews)
        if rating_dist["suspicious"]:
            patterns.append(rating_dist["pattern"])

        # 3. Text authenticity analysis
        text_auth = self._analyze_text_authenticity(reviews)

        # 4. Author behavior analysis
        author = self._analyze_author_behavior(reviews)
        if author["suspicious"]:
            patterns.append(author["pattern"])

        # 5. Verified purchase ratio
        verified_ratio = self._calculate_verified_ratio(reviews)

        # Calculate overall trust score
        trust_score = self._calculate_trust_score(
            temporal, rating_dist, text_auth, author, verified_ratio
        )

        # Sentiment analysis
        sentiment = self._analyze_sentiment(reviews)

        # Extract key themes
        themes = self._extract_themes(reviews)

        # Review velocity
        velocity = self._calculate_review_velocity(reviews)

        return ReviewAnalysis(
            product_id=product_id,
            overall_trust_score=round(trust_score, 1),
            authenticity_breakdown={
                "temporal": round(temporal["score"] * 100, 1),
                "rating_distribution": round(rating_dist["score"] * 100, 1),
                "text_authenticity": round(text_auth["score"] * 100, 1),
                "author_behavior": round(author["score"] * 100, 1),
                "verified_purchase": round(verified_ratio * 100, 1)
            },
            sentiment_distribution=sentiment,
            suspicious_patterns=patterns,
            key_themes=themes,
            verified_purchase_ratio=round(verified_ratio, 2),
            review_velocity=round(velocity, 2),
            rating_distribution=self._get_rating_counts(reviews)
        )

    def _analyze_temporal_patterns(self, reviews: List[Review]) -> Dict:
        """Detect review bombs and burst patterns"""
        if len(reviews) < 10:
            return {"suspicious": False, "score": 0.5, "pattern": ""}

        # Group by date
        date_groups = defaultdict(list)
        for r in reviews:
            date_key = r.date.strftime("%Y-%m-%d")
            date_groups[date_key].append(r)

        # Check for bursts (>10 reviews in single day)
        max_day_reviews = max(len(group) for group in date_groups.values())
        total_days = len(date_groups)
        avg_per_day = len(reviews) / max(total_days, 1)

        suspicious = False
        if max_day_reviews > avg_per_day * 5 and max_day_reviews >= 10:
            suspicious = True

        # Check for review bombs (many negative reviews in short period)
        negative_bursts = 0
        for date, group in date_groups.items():
            negative = sum(1 for r in group if r.rating <= 2)
            if negative >= 5 and len(group) >= 5:
                negative_bursts += 1

        if negative_bursts >= 2:
            suspicious = True

        score = 1.0 - (max_day_reviews / len(reviews)) if len(reviews) > 0 else 0.5
        score = max(0, min(1, score))

        return {
            "suspicious": suspicious,
            "score": score,
            "pattern": "Burst review pattern detected" if suspicious else "",
            "max_day_reviews": max_day_reviews,
            "avg_per_day": avg_per_day
        }

    def _analyze_rating_distribution(self, reviews: List[Review]) -> Dict:
        """Analyze if rating distribution is natural"""
        if len(reviews) < 20:
            return {"suspicious": False, "score": 0.5, "pattern": ""}

        ratings = [r.rating for r in reviews]
        counts = Counter(ratings)

        total = len(reviews)
        five_star_pct = counts.get(5, 0) / total
        one_star_pct = counts.get(1, 0) / total

        # Natural distribution: usually bell curve or J-curve
        # Suspicious: >80% 5-star or extreme polarization
        suspicious = False
        pattern = ""

        if five_star_pct > 0.85:
            suspicious = True
            pattern = "Unusually high 5-star percentage"
        elif five_star_pct > 0.7 and one_star_pct > 0.2:
            suspicious = True
            pattern = "Extreme polarization (only 1-star and 5-star)"

        # Calculate naturalness score
        # Ideal: some distribution across all ratings
        expected = total / 5  # Uniform distribution baseline
        chi_square = sum((counts.get(i, 0) - expected) ** 2 / expected for i in range(1, 6))

        # Lower chi-square = more uniform = more suspicious
        score = min(1.0, chi_square / 50)  # Normalize

        return {
            "suspicious": suspicious,
            "score": score,
            "pattern": pattern,
            "five_star_pct": round(five_star_pct, 2),
            "one_star_pct": round(one_star_pct, 2)
        }

    def _analyze_text_authenticity(self, reviews: List[Review]) -> Dict:
        """Analyze review text for authenticity"""
        if not reviews:
            return {"suspicious": False, "score": 0.5, "pattern": ""}

        generic_count = 0
        specific_count = 0
        duplicate_groups = defaultdict(list)

        for review in reviews:
            text_lower = review.text.lower()

            # Check for generic phrases
            is_generic = any(phrase in text_lower for phrase in self.GENERIC_PHRASES)
            if is_generic:
                generic_count += 1

            # Check for specific details (model numbers, specific features)
            has_specific = bool(re.search(r'\d+\s*(mp|gb|mah|hz|inch|mm|w)', text_lower))
            has_experience = any(word in text_lower for word in ['after', 'month', 'week', 'day', 'using', 'experience'])

            if has_specific or has_experience:
                specific_count += 1

            # Check for duplicates
            text_hash = hash(text_lower[:100])  # First 100 chars
            duplicate_groups[text_hash].append(review)

        # Calculate scores
        total = len(reviews)
        generic_ratio = generic_count / total if total > 0 else 0
        specific_ratio = specific_count / total if total > 0 else 0

        # Check duplicates
        duplicates = sum(1 for group in duplicate_groups.values() if len(group) > 1)

        suspicious = False
        pattern = ""

        if generic_ratio > 0.6:
            suspicious = True
            pattern = "High proportion of generic reviews"
        elif duplicates >= 3:
            suspicious = True
            pattern = "Duplicate or near-duplicate reviews detected"

        # Score: higher specific ratio = more authentic
        score = specific_ratio + (1 - generic_ratio) * 0.5
        score = max(0, min(1, score))

        return {
            "suspicious": suspicious,
            "score": score,
            "pattern": pattern,
            "generic_ratio": round(generic_ratio, 2),
            "specific_ratio": round(specific_ratio, 2),
            "duplicates": duplicates
        }

    def _analyze_author_behavior(self, reviews: List[Review]) -> Dict:
        """Analyze reviewer behavior patterns"""
        if not reviews:
            return {"suspicious": False, "score": 0.5, "pattern": ""}

        suspicious_authors = 0

        for author, author_reviews in self.author_history.items():
            if len(author_reviews) < 3:
                continue

            # Check if author only reviews one brand
            brands = set(r.product_id.split("_")[0] if "_" in r.product_id else r.product_id 
                        for r in author_reviews)
            if len(brands) == 1 and len(author_reviews) > 5:
                suspicious_authors += 1

            # Check if all reviews are same rating
            ratings = [r.rating for r in author_reviews]
            if len(set(ratings)) == 1 and len(ratings) > 5:
                suspicious_authors += 1

            # Check review frequency (more than 1 per day)
            dates = [r.date for r in author_reviews]
            if len(dates) > 2:
                date_range = (max(dates) - min(dates)).days
                if date_range > 0 and len(dates) / date_range > 1:
                    suspicious_authors += 1

        total_authors = len(set(r.author for r in reviews))
        suspicious_ratio = suspicious_authors / max(total_authors, 1)

        suspicious = suspicious_ratio > 0.2

        return {
            "suspicious": suspicious,
            "score": 1 - suspicious_ratio,
            "pattern": "Suspicious reviewer behavior detected" if suspicious else "",
            "suspicious_authors": suspicious_authors
        }

    def _calculate_verified_ratio(self, reviews: List[Review]) -> float:
        """Calculate verified purchase ratio"""
        if not reviews:
            return 0.0
        verified = sum(1 for r in reviews if r.verified_purchase)
        return verified / len(reviews)

    def _calculate_trust_score(self, temporal, rating_dist, text_auth, author, verified_ratio) -> float:
        """Calculate overall trust score from components"""
        weights = {
            "temporal": 0.15,
            "rating": 0.20,
            "text": 0.25,
            "author": 0.20,
            "verified": 0.20
        }

        score = (
            temporal["score"] * weights["temporal"] +
            rating_dist["score"] * weights["rating"] +
            text_auth["score"] * weights["text"] +
            author["score"] * weights["author"] +
            verified_ratio * weights["verified"]
        )

        return score * 100

    def _analyze_sentiment(self, reviews: List[Review]) -> Dict[str, float]:
        """Simple sentiment analysis based on ratings and keywords"""
        if not reviews:
            return {"positive": 0, "neutral": 0, "negative": 0}

        positive_words = ['good', 'great', 'excellent', 'amazing', 'love', 'perfect', 'best', 'awesome']
        negative_words = ['bad', 'worst', 'terrible', 'hate', 'poor', 'disappointing', 'waste', 'broken']

        positive = 0
        negative = 0
        neutral = 0

        for review in reviews:
            text = review.text.lower()
            pos_count = sum(1 for w in positive_words if w in text)
            neg_count = sum(1 for w in negative_words if w in text)

            if review.rating >= 4 or pos_count > neg_count:
                positive += 1
            elif review.rating <= 2 or neg_count > pos_count:
                negative += 1
            else:
                neutral += 1

        total = len(reviews)
        return {
            "positive": round(positive / total * 100, 1),
            "neutral": round(neutral / total * 100, 1),
            "negative": round(negative / total * 100, 1)
        }

    def _extract_themes(self, reviews: List[Review]) -> List[Tuple[str, float]]:
        """Extract key themes from reviews"""
        if not reviews:
            return []

        # Simple keyword extraction
        theme_keywords = {
            "camera": ["camera", "photo", "picture", "zoom", "selfie", "video"],
            "battery": ["battery", "charge", "charging", "backup", "lasts"],
            "performance": ["performance", "speed", "fast", "slow", "lag", "smooth"],
            "display": ["display", "screen", "resolution", "bright", "colors"],
            "build": ["build", "quality", "premium", "plastic", "durable", "fragile"],
            "heating": ["heat", "heating", "warm", "temperature", "thermal"],
            "software": ["software", "ui", "bug", "update", "android", "ios"]
        }

        theme_scores = {}
        for theme, keywords in theme_keywords.items():
            mentions = 0
            for review in reviews:
                text = review.text.lower()
                if any(kw in text for kw in keywords):
                    mentions += 1

            if mentions > 0:
                theme_scores[theme] = mentions / len(reviews)

        # Sort by frequency
        sorted_themes = sorted(theme_scores.items(), key=lambda x: x[1], reverse=True)
        return [(t, round(s * 100, 1)) for t, s in sorted_themes[:5]]

    def _calculate_review_velocity(self, reviews: List[Review]) -> float:
        """Calculate reviews per day"""
        if len(reviews) < 2:
            return 0.0

        dates = sorted([r.date for r in reviews])
        days = (dates[-1] - dates[0]).days

        if days == 0:
            return len(reviews)

        return len(reviews) / days

    def _get_rating_counts(self, reviews: List[Review]) -> Dict[int, int]:
        """Get distribution of ratings"""
        counts = Counter(r.rating for r in reviews)
        return {i: counts.get(i, 0) for i in range(1, 6)}


# Example usage
if __name__ == "__main__":
    engine = ReviewTrustEngine()

    # Add sample reviews
    reviews = [
        Review("r1", "p1", 5, "Great phone", "Excellent camera, battery lasts all day. Using for 3 months.", 
               "user1", datetime(2026, 1, 1), verified_purchase=True),
        Review("r2", "p1", 5, "Good product", "Value for money. Must buy.", 
               "user2", datetime(2026, 1, 1), verified_purchase=False),
        Review("r3", "p1", 5, "Awesome", "Great product. Highly recommended.", 
               "user3", datetime(2026, 1, 1), verified_purchase=False),
        Review("r4", "p1", 5, "Nice", "Good product. Worth buying.", 
               "user4", datetime(2026, 1, 1), verified_purchase=False),
        Review("r5", "p1", 5, "Best", "Excellent product. Go for it.", 
               "user5", datetime(2026, 1, 1), verified_purchase=False),
        Review("r6", "p1", 4, "Good", "Camera is decent, battery could be better. Overall satisfied.", 
               "user6", datetime(2026, 1, 5), verified_purchase=True),
    ]

    engine.add_reviews("p1", reviews)
    analysis = engine.analyze("p1")

    print(f"Review Trust Analysis:")
    print(f"Trust Score: {analysis.overall_trust_score}/100")
    print(f"Suspicious Patterns: {analysis.suspicious_patterns}")
    print(f"Verified Purchase Ratio: {analysis.verified_purchase_ratio}")
    print(f"Sentiment: {analysis.sentiment_distribution}")
    print(f"Key Themes: {analysis.key_themes}")
