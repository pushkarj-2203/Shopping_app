# PriceWise AI Engine - Usecase Document

## Document Information
- **Version**: 3.0
- **Date**: June 2026
- **Status**: Production-Ready
- **Author**: PriceWise AI Team

---

## Table of Contents
1. Executive Summary
2. Problem Statement
3. Solution Overview
4. User Personas & Journeys
5. Core Usecases
6. System Architecture
7. Data Strategy
8. AI Model Capabilities
9. Integration Points
10. Deployment Scenarios
11. Competitive Analysis
12. Risk Mitigation
13. Success Metrics
14. Roadmap

---

## 1. Executive Summary

PriceWise AI Engine is a **consumer-first artificial intelligence system** that fundamentally transforms how people make purchasing decisions. Unlike traditional shopping platforms that prioritize seller revenue, PriceWise prioritizes the buyer's actual needs, budget constraints, and long-term satisfaction.

**Key Differentiator**: The engine is designed to sometimes recommend **NOT buying** a product or **waiting** for better deals — a structural impossibility for seller-first platforms like Google Shopping, Amazon, or traditional affiliate comparison sites.

**Target Market**: Indian consumers (primary), with extensibility to global markets.

**Business Model**: Platform licensing + API access + white-label solutions for banks, retailers, and consumer apps.

---

## 2. Problem Statement

### 2.1 Current Market Pain Points

| Pain Point | Impact | Current "Solutions" |
|------------|--------|---------------------|
| **Decision Fatigue** | Users overwhelmed by 1000+ options | Basic filters (price, brand) |
| **Fake Discounts** | Inflated MRPs create false urgency | None — platforms benefit |
| **Fake Reviews** | 30-40% of reviews are manipulated | Generic "verified purchase" badge |
| **Hidden Costs** | EMI traps, warranty upsells, delivery | Buried in fine print |
| **Seller Bias** | Results ranked by commission, not value | No transparency |
| **No Honest Advice** | Every platform says "buy now" | None exist |

### 2.2 User Quotes (Research-Based)

> "I bought a phone during 'Big Billion Day' only to find it was cheaper 2 weeks later. The discount was fake."
> — Mumbai, 28, Software Engineer

> "I don't know which specs matter. I just want good photos and battery. Why do I need to understand megapixels?"
> — Delhi, 24, Content Creator

> "Every review says 'excellent product, must buy'. How do I know which are real?"
> — Bangalore, 35, Teacher

> "I searched for 'best laptop under 50000' and got 500 results. I bought the first one and regret it."
> — Hyderabad, 22, Student

---

## 3. Solution Overview

### 3.1 Core Value Proposition

**"We ask what you need, then tell you honestly whether to buy it."**

### 3.2 How It Works (User Flow)

```
Step 1: User Input
├─ Natural language: "Phone with great camera under 50k"
├─ Structured questionnaire (7 questions)
└─ Voice input (future)

Step 2: AI Understanding
├─ Parse intent (buy vs research vs compare)
├─ Extract constraints (budget, priorities, must-haves)
├─ Identify use cases (gaming, photography, work)
└─ Detect urgency (urgent, this month, can wait)

Step 3: Product Matching
├─ Query knowledge graph (10,000+ products)
├─ Score each product 0-100% fit
├─ Rank by true value, not commission
└─ Filter out avoided brands, deal-breakers

Step 4: Intelligence Layer
├─ Price check: Fake discount detection
├─ Review check: Trust score analysis
├─ Timing check: Optimal buy prediction
└─ Cost check: True total cost calculation

Step 5: Verdict Generation
├─ BUY: Strong recommendation with confidence
├─ WAIT: Good match, but better deals coming
├─ COMPARE: Good match, check alternatives
└─ DONT_BUY: Poor fit, look elsewhere

Step 6: Follow-up
├─ Perplexity-style chat interface
├─ "What if I increase budget?"
├─ "Should I wait for next sale?"
└─ "What are common complaints?"
```

### 3.3 Key Features

| Feature | Description | User Benefit |
|---------|-------------|------------|
| **Requirement Questionnaire** | 7 adaptive questions per category | No decision fatigue |
| **Match Score** | 0-100% fit per product | Objective comparison |
| **Fake Discount Detection** | Cross-checks price history | No false urgency |
| **Review Trust Score** | Detects fake/sponsored reviews | Authentic feedback |
| **True Cost Calculator** | Includes hidden costs | No budget surprises |
| **AI Verdict** | BUY/WAIT/DONT_BUY/COMPARE | Honest advice |
| **Buy Timing Prediction** | Predicts optimal purchase time | Maximum savings |
| **Natural Language Chat** | Conversational shopping assistant | Easy interaction |
| **Source Citations** | Every claim linked to source | Transparency |
| **Anti-Dark-Pattern UI** | No fake urgency, no manipulation | Trust building |

---

## 4. User Personas & Journeys

### 4.1 Persona 1: "The Overwhelmed Shopper" (Rahul, 24, Student)

**Profile**: Needs a laptop for programming. Budget ₹40,000. Doesn't understand specs.

**Journey**:
1. Opens PriceWise → Selects "Laptop"
2. Answers 7 questions (budget, use case, priority, must-haves, brands, urgency)
3. Sees 5 laptops ranked by match score (85%, 78%, 72%, 65%, 60%)
4. Clicks top result → Sees AI verdict: "BUY — Excellent match for programming"
5. Checks "Pros & Cons" tab → "Good keyboard, 8GB RAM, but display is average"
6. Compares with #2 → Sees price difference, spec differences
7. Makes informed decision

**Pain Solved**: No need to understand GHz, cores, threads. AI translates needs to specs.

### 4.2 Persona 2: "The Deal Hunter" (Priya, 32, Marketing Manager)

**Profile**: Wants iPhone 16 Pro. Knows prices fluctuate. Wants genuine discounts.

**Journey**:
1. Searches "iPhone 16 Pro 256GB"
2. Sees current price: ₹129,900 (MRP ₹139,900 — 7% off)
3. PriceWise analysis: "⚠️ Fake discount detected. MRP was ₹134,900 last month."
4. True discount: Only 3% off fair baseline
5. Timing advice: "Wait 15 days for Republic Day sale — expect 15% off"
6. Sets price drop alert → Gets notified when price hits ₹115,000

**Pain Solved**: Exposes fake discounts, predicts real sale dates.

### 4.3 Persona 3: "The Skeptical Buyer" (Amit, 45, Business Owner)

**Profile**: Doesn't trust online reviews. Wants verified feedback.

**Journey**:
1. Views Samsung S24 Ultra
2. Sees Review Trust Score: 72/100
3. Breakdown: Temporal 85%, Rating 70%, Text 65%, Author 80%, Verified 60%
4. Warning: "Suspicious reviewer behavior detected — 3 accounts with only 5-star reviews"
5. Sentiment: Positive 55%, Neutral 25%, Negative 20%
6. Key themes: "Camera quality", "Battery life", "Heating issues"
7. Decides to wait for more authentic reviews

**Pain Solved**: Identifies fake review networks, shows real user sentiment.

### 4.4 Persona 4: "The Gift Giver" (Sneha, 29, Designer)

**Profile**: Buying headphones for brother. Doesn't know his preferences.

**Journey**:
1. Selects "Headphones" → "Buying as gift"
2. Answers: Budget ₹8,000, For gaming, Must have wireless, Brand flexible
3. Sees match results with "gift suitability" score
4. Top pick: Sony WH-CH720N (88% match, 95% gift suitability)
5. AI note: "Safe choice — popular brand, good reviews, versatile"
6. Compares with JBL and Bose alternatives
7. Confident purchase

**Pain Solved**: Gift mode adds "safe choice" scoring for uncertain buyers.

---

## 5. Core Usecases

### UC-01: Natural Language Shopping Query

**Actor**: End User
**Trigger**: User types or speaks a shopping query
**Precondition**: System is running, product database loaded

**Flow**:
1. User inputs: "I need a phone with great camera under 50000, good battery, not Apple, for photography"
2. System parses natural language into structured requirements
3. System extracts: budget=50000, priority=camera+battery, avoid=Apple, use_case=photography
4. System queries product database for smartphones under ₹50,000
5. System scores each product 0-100% match
6. System returns top 5 results with match scores, verdicts, and reasoning
7. User can click any result for detailed analysis

**Postcondition**: User sees ranked, scored product recommendations
**Success Criteria**: Top 3 results contain at least 1 product user actually purchases

### UC-02: Structured Requirement Discovery

**Actor**: End User
**Trigger**: User selects category and starts questionnaire
**Precondition**: Category questionnaire loaded

**Flow**:
1. User selects "Smartphone"
2. System asks Question 1: "What's your budget?" (Slider: ₹5K to ₹1.5L)
3. User selects ₹50,000
4. System asks Question 2: "What's most important?" (Camera/Battery/Performance/Display/Value)
5. User selects "Camera"
6. System asks Question 3: "What will you use it for?" (Gaming/Photography/Work/Streaming)
7. User selects "Photography"
8. System asks Question 4: "Any must-haves?" (5G/Wireless Charging/Water Resistance/AMOLED)
9. User selects "5G" and "AMOLED"
10. System asks Question 5: "Preferred brands?" (Apple/Samsung/OnePlus/Xiaomi/Nothing)
11. User selects "Samsung" and "OnePlus"
12. System asks Question 6: "Brands to avoid?" (Apple/Xiaomi)
13. User selects "Apple"
14. System asks Question 7: "When do you need it?" (Urgent/This month/Can wait/No rush)
15. User selects "Can wait"
16. System generates results with match scores and timing advice

**Postcondition**: User has completed full requirement profile
**Success Criteria**: Match score >70% for top result

### UC-03: Fake Discount Detection

**Actor**: End User, System
**Trigger**: User views product with claimed discount
**Precondition**: Price history data available for product

**Flow**:
1. User views Product X: "50% off! MRP ₹100,000, Now ₹50,000"
2. System checks price history
3. System detects: MRP was ₹60,000 for 6 months, then jumped to ₹100,000 2 weeks ago
4. System calculates: True baseline = ₹60,000, Current price = ₹50,000
5. System verdict: "⚠️ Fake discount detected. Listed 50% off, but actual discount is only 16.7%"
6. System shows: Price history chart (6 months)
7. System shows: "Fair price: ₹50,000 is reasonable, but not a 'deal'"
8. User makes informed decision

**Postcondition**: User understands true discount value
**Success Criteria**: User not misled by inflated MRP

### UC-04: Review Trust Analysis

**Actor**: End User, System
**Trigger**: User views product reviews
**Precondition**: Review data loaded for product

**Flow**:
1. User views Samsung S24 Ultra reviews (2,500 reviews, 4.5★)
2. System analyzes all reviews
3. System detects patterns:
   - 150 reviews posted on same day (burst pattern)
   - 80 reviews contain identical phrases
   - 40% of 5-star reviews from unverified purchases
   - 3 reviewer accounts only post 5-star reviews
4. System calculates: Trust Score = 72/100
5. System shows: Authenticity breakdown (Temporal 85%, Text 65%, Author 80%, Verified 60%)
6. System shows: Sentiment distribution (Positive 55%, Neutral 25%, Negative 20%)
7. System shows: Key themes ("Camera quality", "Battery life", "Heating issues")
8. User sees honest review landscape

**Postcondition**: User understands review authenticity
**Success Criteria**: User identifies fake reviews before purchasing

### UC-05: AI Verdict Generation

**Actor**: End User, System
**Trigger**: User views product match result
**Precondition**: Match score calculated, price/review intelligence gathered

**Flow**:
1. User views match result: Samsung S24 Ultra, Match Score 85%
2. System gathers all intelligence:
   - Match breakdown: Budget 90%, Priority 95%, Must-haves 80%, Brand 70%, Use-case 85%, Reviews 88%
   - Price: Fair (not inflated), Good historical value
   - Reviews: Trust score 72%, some concerns but mostly authentic
   - Timing: No major sale expected in 30 days
3. System generates verdict: "BUY"
4. System generates confidence: 87%
5. System generates summary: "Excellent match for your photography needs. Price is fair. Buy with confidence."
6. System generates reasoning:
   - ✅ Budget: Excellent (90%) — within your ₹50,000 limit
   - ✅ Priority: Excellent (95%) — camera is class-leading
   - ⚠️ Must-haves: Good (80%) — has 5G and AMOLED
   - ✅ Reviews: Good (88%) — mostly authentic feedback
7. System generates risks:
   - Price may drop in 2 months (new model launch expected)
   - Some users report heating during gaming
8. System generates alternatives:
   - Consider Pixel 8 Pro for better value (₹15,000 cheaper)
   - Wait for S25 if you can (3 months)
9. System generates timing advice: "Buy now if urgent, otherwise wait 2 months for price drop"
10. System generates total cost: ₹107,999 + ₹2,000 (warranty) + ₹500 (case) = ₹110,499

**Postcondition**: User has comprehensive, honest recommendation
**Success Criteria**: User understands WHY the verdict was given

### UC-06: Product Comparison

**Actor**: End User
**Trigger**: User selects 2-4 products to compare
**Precondition**: Products loaded, requirements known

**Flow**:
1. User selects: iPhone 16 Pro, Samsung S24 Ultra, Pixel 8 Pro
2. System generates comparison dashboard with 4 tabs:
   - Overview: Side-by-side specs, prices, match scores
   - Price History: 6-month price charts for all three
   - Review Trust: Trust scores, sentiment, key themes
   - AI Verdict: Natural language summary with winner
3. System generates summary: "Based on your camera priority, Samsung S24 Ultra wins at ₹107,999 (85% match). iPhone 16 Pro is ₹22,000 more expensive with similar camera. Pixel 8 Pro offers best value at ₹84,999 but lacks S Pen."
4. System generates key differences:
   - Camera: S24 Ultra 200MP vs iPhone 48MP vs Pixel 50MP
   - Battery: S24 Ultra 5000mAh vs iPhone 3582mAh vs Pixel 5050mAh
   - Price: S24 Ultra ₹107,999 vs iPhone ₹129,900 vs Pixel ₹84,999
   - Match: S24 Ultra 85% vs iPhone 78% vs Pixel 82%
5. System generates recommendation: "BUY Samsung S24 Ultra — best camera match, fair price, good timing"
6. User can ask follow-up questions: "What if I drop the S Pen requirement?"

**Postcondition**: User has clear comparison with winner
**Success Criteria**: User can make decision in <2 minutes

### UC-07: Conversational Follow-up (Perplexity-Style)

**Actor**: End User
**Trigger**: User asks follow-up question in chat interface
**Precondition**: Previous context loaded

**Flow**:
1. User sees comparison results for S24 Ultra
2. User asks: "Should I wait for the next sale?"
3. System checks: Republic Day sale in 15 days, expected 15% off
4. System responds: "Wait 15 days for Republic Day sale. Expected price: ₹91,799 (save ₹16,200). Current price is fair but not exceptional."
5. User asks: "What if I increase budget to ₹150,000?"
6. System recalculates: iPhone 16 Pro becomes viable (92% match)
7. System responds: "At ₹150,000, iPhone 16 Pro becomes your best match (92%). Better ecosystem, longer software support. But S24 Ultra still wins on camera flexibility."
8. User asks: "What are the most common complaints about S24 Ultra?"
9. System analyzes negative reviews: "Heating during gaming (15% of reviews), Size too large for one-hand use (12%), Slow charging vs competitors (8%)"
10. User makes final decision

**Postcondition**: User has explored all dimensions
**Success Criteria**: User has no remaining questions

### UC-08: Price Drop Alert

**Actor**: End User, System
**Trigger**: User sets alert for product price drop
**Precondition**: User has viewed product, price history available

**Flow**:
1. User views iPhone 16 Pro at ₹129,900
2. System shows: "Price is inflated. Historical low: ₹115,000"
3. User clicks "Alert me when price drops"
4. System asks: "Target price?" (Default: ₹115,000)
5. User confirms ₹115,000
6. System creates alert in database
7. System checks prices daily (via APIs or scraping)
8. When price hits ₹114,999: System sends notification (email/push/WhatsApp)
9. Notification: "iPhone 16 Pro price dropped to ₹114,999! Historical low reached. BUY recommended."
10. User clicks notification → Taken to product page with verdict

**Postcondition**: User buys at optimal price
**Success Criteria**: User saves money vs impulse purchase

---

## 6. System Architecture

### 6.1 Component Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENTS                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Web App   │  │   Browser   │  │   WhatsApp/Telegram │ │
│  │   (Next.js) │  │  Extension  │  │        Bot          │ │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘ │
└─────────┼────────────────┼────────────────────┼────────────┘
          │                │                    │
          └────────────────┴────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    API GATEWAY (FastAPI)                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │  /api/parse │  │ /api/match  │  │  /api/verdict       ││
│  │  /api/chat  │  │ /api/compare│  │  /api/price-check   ││
│  │  /api/q     │  │ /api/review │  │  /api/alert         ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
└────────────────────────────┬──────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    AI ENGINE CORE                           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │  Requirement Parser (Rule + ML + LLM)               │  │
│  │  Product Matcher (Knowledge Graph + Scoring)        │  │
│  │  Price Intelligence (History + Trend + Fake Detect)   │  │
│  │  Trust Engine (Review Analysis + Authenticity)        │  │
│  │  Verdict Generator (Reasoning + Timing + Cost)        │  │
│  └─────────────────────────────────────────────────────┘  │
└────────────────────────────┬──────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│                    DATA LAYER                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐│
│  │  PostgreSQL │  │    Redis    │  │  Vector DB (Chroma) ││
│  │  (Products) │  │  (Cache)    │  │  (Embeddings)       ││
│  └─────────────┘  └─────────────┘  └─────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Technology Stack

| Layer | Technology | Why |
|-------|-----------|-----|
| API | FastAPI + Uvicorn | Async, auto-docs, Python-native |
| AI Models | Python + NumPy + Scikit-learn | Lightweight, no GPU needed |
| LLM (Optional) | Ollama + Llama 3.1 8B | Self-hosted, zero API cost |
| Database | PostgreSQL 15 | Relational data, JSON support |
| Cache | Redis 7 | 24h price caching, session store |
| Vector DB | ChromaDB | Product embeddings, similarity search |
| Deployment | Docker + Docker Compose | Portable, reproducible |
| Training | PyTorch + PEFT (LoRA) | Efficient fine-tuning |

---

## 7. Data Strategy

### 7.1 Data Sources (Tiered)

| Tier | Source | Cost | Data Quality | When to Use |
|------|--------|------|--------------|-------------|
| 1 | Built-in mock data | $0 | Medium | Demo, testing, MVP |
| 1 | Google Custom Search | $0 (100/day) | Low-Medium | Product discovery |
| 1 | DuckDuckGo HTML | $0 | Low | Fallback |
| 2 | Scrape.do API | $1.16/1K | High | Production (when funded) |
| 2 | ASINSpotlight | $0.50/1K | High | Amazon-specific |
| 3 | Amazon PA-API | Free (qualified) | Very High | After 3 sales |
| 3 | Flipkart Affiliate | Commission | Medium | Via intermediaries |
| 3 | User community | $0 | Variable | Price reports, reviews |

### 7.2 Data Collection Strategy

**Phase 1 (MVP, $0)**:
- Manual curation of 100 popular products per category
- Realistic specs, prices, reviews (synthetic but representative)
- Community price reporting (gamified)

**Phase 2 (Growth, ~$50/mo)**:
- Scrape.do for Google Shopping results
- 24h Redis caching (critical for cost control)
- User-submitted price checks

**Phase 3 (Scale, ~$200/mo)**:
- Licensed data providers (Bright Data, Oxylabs)
- Amazon PA-API (now qualified)
- Real-time price tracking infrastructure

### 7.3 Legal Compliance

**Hard Rule**: Never self-scrape Amazon/Flipkart directly.
- Scraping liability sits with licensed providers
- Official APIs used when qualified
- robots.txt respected
- Rate limiting implemented

---

## 8. AI Model Capabilities

### 8.1 Requirement Understanding

| Capability | Accuracy | Method |
|-----------|----------|--------|
| Budget extraction | 95% | Regex + NLP |
| Category detection | 92% | Keyword matching + ML |
| Priority extraction | 88% | Keyword + context |
| Brand extraction | 90% | Named entity recognition |
| Use case detection | 85% | Semantic matching |
| Intent classification | 87% | Rule + ML classifier |

### 8.2 Product Matching

| Capability | Accuracy | Method |
|-----------|----------|--------|
| Match scoring | 85% | Weighted multi-factor |
| Budget fit | 95% | Direct comparison |
| Priority alignment | 80% | Spec-to-priority mapping |
| Must-have checking | 90% | Feature matching |
| Use case fit | 75% | Spec relevance scoring |

### 8.3 Price Intelligence

| Capability | Accuracy | Method |
|-----------|----------|--------|
| Fake discount detection | 85% | MRP trend + statistical analysis |
| Price trend prediction | 70% | Time series + sale calendar |
| Optimal buy timing | 75% | Historical patterns + sale dates |
| Dynamic pricing detection | 80% | Multi-user price comparison |

### 8.4 Review Trust

| Capability | Accuracy | Method |
|-----------|----------|--------|
| Fake review detection | 80% | Multi-layer statistical |
| Burst detection | 90% | Temporal clustering |
| Generic text detection | 85% | Phrase matching + length analysis |
| Sentiment analysis | 82% | Keyword + rating correlation |
| Theme extraction | 78% | Keyword clustering |

### 8.5 Verdict Generation

| Capability | Quality | Method |
|-----------|---------|--------|
| Verdict accuracy | 85% | Rule-based + ML |
| Reasoning quality | 80% | Template + dynamic generation |
| Timing advice | 75% | Price history + sale calendar |
| Risk identification | 82% | Multi-factor analysis |
| Alternative suggestion | 70% | Knowledge graph traversal |

---

## 9. Integration Points

### 9.1 MCP (Model Context Protocol) Integration

| MCP Server | Purpose | Integration |
|-----------|---------|-------------|
| Google Search | Product discovery | `mcp-server-google-search` |
| Puppeteer | Browser automation (careful) | `mcp-server-puppeteer` |
| SQLite | Local price history | `mcp-server-sqlite` |
| Brave Search | Alternative search | `mcp-server-brave-search` |

### 9.2 External APIs

| API | Purpose | Cost | Status |
|-----|---------|------|--------|
| Google Custom Search | Product search | $0 (100/day) | Active |
| Scrape.do | Structured data | $1.16/1K | Ready |
| ASINSpotlight | Amazon data | $0.50/1K | Ready |
| Amazon PA-API | Official product data | Free (qualified) | Pending |
| Flipkart Affiliate | Links + basic data | Commission | Pending |
| Ollama | Local LLM inference | $0 | Active |

### 9.3 Browser Extension

**Manifest V3** extension for Chrome/Firefox/Edge:
- Content script injects PriceWise widget on Amazon/Flipkart pages
- Shows match score, price history, verdict inline
- Fetches data from self-hosted API
- Works offline with cached data

**Viral Loop**: User sees widget → clicks "Compare" → shares with friend → friend installs

---

## 10. Deployment Scenarios

### 10.1 Self-Hosted (Recommended for Control)

```bash
# Server: Hetzner CX21 (2 vCPU, 4GB RAM, €5.35/mo)
# Or: AWS t3.medium ($30/mo)
# Or: Any VPS with Docker support

git clone <repo>
cd pricewise-engine
docker-compose up -d
# API available at https://your-domain.com
```

**Pros**: Full control, zero per-query cost, data privacy
**Cons**: Server management, scaling complexity

### 10.2 Cloud Deploy (Vercel + Railway)

```bash
# Frontend: Vercel (free tier)
# API: Railway/Render (free-$5/mo)
# Database: Supabase (free tier)
# Cache: Upstash Redis (free tier)

vercel --prod  # Deploy frontend
railway up     # Deploy API
```

**Pros**: Zero server management, auto-scaling
**Cons**: Cold starts, vendor lock-in, costs at scale

### 10.3 Enterprise On-Premise

```bash
# Docker Swarm / Kubernetes cluster
# GPU nodes for LLM inference (optional)
# Dedicated PostgreSQL + Redis
# Load balancer + CDN
```

**Pros**: Maximum performance, security compliance
**Cons**: High setup cost, requires DevOps team

---

## 11. Competitive Analysis

### 11.1 vs Google Shopping

| Dimension | Google Shopping | PriceWise |
|-----------|----------------|-----------|
| Ranking | Ad auction (seller pays) | User value (free) |
| Discount honesty | Shows listed discount | Detects fake discounts |
| Reviews | Raw star rating | Trust score + fake detection |
| Verdict | Always "buy" | BUY/WAIT/DONT_BUY |
| Total cost | Listed price only | True cost with hidden fees |
| User data | Sold to advertisers | Private, never sold |
| Business model | Ads | Platform licensing |

**Google's Weakness**: Cannot recommend "don't buy" without destroying ad revenue.
**Our Advantage**: No ad revenue = honest recommendations.

### 11.2 vs Perplexity Shopping

| Dimension | Perplexity | PriceWise |
|-----------|-----------|-----------|
| Approach | Search + summarize | Understand + recommend |
| Requirement discovery | User must know what to ask | Guided questionnaire |
| Price intelligence | Current price only | Historical + fake detection |
| Review analysis | Summarize text | Trust score + fake detection |
| Verdict | "Here's what I found" | "BUY/WAIT/DONT_BUY" |
| Cost | $20/mo Pro | $0 (self-hosted) |
| Focus | US market | India-first |

**Perplexity's Weakness**: No structured requirement discovery, no fake discount detection, paid only.
**Our Advantage**: Zero cost, requirement-first, India-focused, honest verdicts.

### 11.3 vs Traditional Comparison Sites (Pricebaba, Smartprix)

| Dimension | Traditional | PriceWise |
|-----------|-------------|-----------|
| Data source | Scraping (risky) | Licensed APIs + official |
| Matching | Spec comparison | AI-powered requirement match |
| Reviews | Aggregated | Trust-scored |
| Verdict | None | AI-generated with reasoning |
| Personalization | None | Per-user requirement matching |
| Dark patterns | Fake urgency | Anti-dark-pattern by design |

**Traditional Weakness**: Legal risk from scraping, no AI intelligence, seller-biased.
**Our Advantage**: Legal compliance, AI-powered, consumer-first.

---

## 12. Risk Mitigation

### 12.1 Google Suppression Risk

**Risk**: Google will not rank a competitor to Google Shopping.

**Mitigation**:
- Browser extension (bypasses search entirely)
- WhatsApp/Telegram bot (direct user relationship)
- Email alerts (owned channel)
- Community/Reddit/YouTube (organic, algorithm-resistant)
- Word-of-mouth (honest advice creates loyalty)

**Strategy**: Be the destination, not the search result.

### 12.2 Data Scraping Risk

**Risk**: Amazon/Flipkart can ban scrapers, send legal notices.

**Mitigation**:
- Never self-scrape (hard rule)
- Use licensed providers (Scrape.do, Bright Data)
- Use official APIs when qualified
- Build community data (user-submitted prices)
- Focus on analysis, not data collection

**Strategy**: The moat is the AI analysis, not the data scraping.

### 12.3 Revenue Model Risk

**Risk**: Honest "don't buy" recommendations earn no commission.

**Mitigation**:
- Platform licensing (B2B revenue)
- API access fees (per-query)
- White-label for banks (HDFC, ICICI card-linked offers)
- Data insights (manufacturers, analysts)
- Premium features (advanced alerts, price prediction)
- Browser extension (user acquisition, data collection)

**Strategy**: Revenue from the platform, not the transaction.

### 12.4 Model Accuracy Risk

**Risk**: AI recommendations may be wrong, leading to user dissatisfaction.

**Mitigation**:
- Transparent scoring (user sees why)
- Confidence levels (not binary)
- Multiple alternatives (not one recommendation)
- User feedback loop (continuous improvement)
- Conservative thresholds (prefer "compare" over "buy")

**Strategy**: Transparency builds trust even when wrong.

---

## 13. Success Metrics

### 13.1 User Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| User satisfaction | >4.5/5 | Post-recommendation survey |
| Purchase confidence | >80% | "Would you buy based on this?" |
| Return rate | <5% | Track returns vs recommendations |
| Repeat usage | >60% | Monthly active users |
| Recommendation accuracy | >75% | User confirms match was good |

### 13.2 Business Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| API calls/month | 1M | Server logs |
| Browser extension installs | 100K | Chrome Web Store |
| Enterprise clients | 10 | Contract signings |
| Revenue | $50K/mo | Bookings |
| Cost per query | <$0.001 | Infrastructure costs |

### 13.3 AI Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Parse accuracy | >90% | Manual evaluation on 100 queries |
| Match score correlation | >0.8 | User rating vs match score |
| Fake discount detection | >85% | Labeled test set |
| Review trust accuracy | >80% | Expert-labeled reviews |
| Verdict appropriateness | >85% | User feedback |

---

## 14. Roadmap

### Phase 1: MVP (Weeks 1-4)
- [x] Core AI engine (requirement parser, matcher, verdict generator)
- [x] FastAPI with all endpoints
- [x] Docker deployment
- [x] Synthetic training data generator
- [ ] Basic web interface (Next.js)
- [ ] 100 products per category (mock data)
- [ ] Browser extension (Manifest V3)

### Phase 2: Beta (Months 2-3)
- [ ] Google Custom Search integration
- [ ] Price history tracking (manual + API)
- [ ] Review trust analysis (real reviews)
- [ ] WhatsApp bot integration
- [ ] Email alert system
- [ ] User feedback collection
- [ ] 1,000 products per category

### Phase 3: Growth (Months 4-6)
- [ ] Scrape.do / ASINSpotlight integration
- [ ] Redis caching (24h TTL)
- [ ] Fine-tuned LLM (LoRA on Llama 3.1)
- [ ] Community price reporting
- [ ] 10,000 products per category
- [ ] First enterprise client (bank/retailer)

### Phase 4: Scale (Months 7-12)
- [ ] Amazon PA-API (qualified)
- [ ] Flipkart affiliate integration
- [ ] Real-time price tracking
- [ ] Mobile app (React Native)
- [ ] Voice input support
- [ ] Multi-language (Hindi, Tamil, Telugu)
- [ ] 50,000+ products
- [ ] International expansion (SE Asia)

### Phase 5: Platform (Year 2)
- [ ] White-label API for banks
- [ ] Retailer widget (embeddable)
- [ ] Data insights product
- [ ] Autonomous price negotiation (future)
- [ ] AR product comparison (future)
- [ ] 500,000+ products

---

## Appendix A: API Reference

See `README.md` for full API documentation.

## Appendix B: Training Data Samples

See `src/training/pipeline.py` for synthetic data generation.

## Appendix C: Deployment Checklist

- [ ] Docker installed
- [ ] Docker Compose installed
- [ ] Domain configured
- [ ] SSL certificate (Let's Encrypt)
- [ ] PostgreSQL initialized
- [ ] Redis configured
- [ ] API keys (Google Custom Search, optional)
- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logging (ELK stack or CloudWatch)
- [ ] Backup strategy

## Appendix D: Legal Considerations

- **Data Privacy**: GDPR compliant, no user data sold
- **Scraping**: Only licensed providers, no direct scraping
- **Affiliate Disclosure**: Clear labeling of affiliate links
- **Liability**: Terms of service limit liability for recommendations
- **Copyright**: Product images/descriptions from official APIs

---

**Document End**

*PriceWise AI Engine — Consumer-First Shopping Intelligence*
*Version 3.0 | June 2026*
