# PriceWise AI Engine v3.0

## Consumer-First AI Shopping Engine

A self-hosted, API-first AI system that understands what users actually need and tells them honestly whether to buy, wait, or skip.

---

## What Makes This Different

| Traditional Shopping AI | PriceWise AI |
|------------------------|--------------|
| Ranks by commission | Ranks by true user value |
| Never says "don't buy" | Honest verdicts: BUY, WAIT, DONT_BUY |
| Hides fake discounts | Exposes inflated MRPs |
| Generic reviews | Trust scoring with fake detection |
| Seller-first | Consumer-first |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI ENGINE (Python/FastAPI)               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          REQUIREMENT UNDERSTANDING LAYER              │   │
│  │  • Natural Language Parser (budget, priority, brands)   │   │
│  │  • Intent Classification (buy vs research vs compare)   │   │
│  │  • Constraint Extraction (must-haves, deal-breakers)  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           PRODUCT KNOWLEDGE GRAPH                     │   │
│  │  • Entity Recognition (brands, models, specs)          │   │
│  │  • Relationship Mapping (successors, substitutes)     │   │
│  │  • Category Ontology (smartphone → camera → sensor)   │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           PRICE INTELLIGENCE LAYER                      │   │
│  │  • Historical Price Tracking (6-12 month patterns)     │   │
│  │  • Fake Discount Detection (MRP inflation analysis)     │   │
│  │  • Sale Prediction (Diwali, Republic Day, Prime Day)  │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           TRUST & REVIEW ENGINE                         │   │
│  │  • Review Authenticity Scoring (verified vs fake)     │   │
│  │  • Sentiment Analysis (pros/cons extraction)          │   │
│  │  • Burst Detection (review bombs, coordinated)        │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           VERDICT GENERATOR                             │   │
│  │  • Match Scoring (0-100% fit to requirements)         │   │
│  │  • Value Assessment (price vs features vs need)         │   │
│  │  • Timing Advice (buy now vs wait vs never)             │   │
│  │  • Alternative Suggestion (better fit, lower price)     │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
   ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
   │  WEB    │         │BROWSER  │         │  API    │
   │  APP    │         │EXTENSION│         │  LAYER  │
   │         │         │         │         │         │
   │ Next.js │         │ Chrome  │         │ REST    │
   │ React   │         │ Firefox │         │ GraphQL │
   │ Mobile  │         │ Edge    │         │ Webhook │
   └─────────┘         └─────────┘         └─────────┘
```

---

## Quick Start

### 1. Clone & Setup

```bash
git clone <repo-url>
cd pricewise-engine
pip install -r requirements.txt
```

### 2. Run API Server

```bash
python -m uvicorn src.api.main:app --reload
```

API docs at: http://localhost:8000/docs

### 3. Docker Deploy

```bash
docker-compose up -d
```

---

## API Endpoints

### Parse Requirements
```bash
POST /api/parse
{
  "query": "I need a phone with great camera under 50000, good battery, not Apple"
}
```

### Generate Questionnaire
```bash
POST /api/questionnaire
{
  "category": "smartphone",
  "answered_questions": {"budget": 50000}
}
```

### Match Products
```bash
POST /api/match
{
  "requirement": {"category": "smartphone", "budget_max": 50000},
  "limit": 5
}
```

### Generate Verdict
```bash
POST /api/verdict
{
  "match_result": {...},
  "requirement": {...}
}
```

### Compare Products
```bash
POST /api/compare
{
  "product_ids": ["p1", "p2", "p3"],
  "requirement": {...}
}
```

### Price Check
```bash
POST /api/price-check
{
  "product_id": "iphone16pro",
  "urgency": "can_wait"
}
```

### Review Check
```bash
POST /api/review-check
{
  "product_id": "s24ultra"
}
```

### Chat (Conversational)
```bash
POST /api/chat
{
  "query": "Should I buy iPhone 16 or wait?",
  "session_id": "abc123"
}
```

---

## Training Pipeline

### Generate Synthetic Data
```bash
python src/training/pipeline.py
```

This creates:
- `training_data/requirement_parsing.jsonl` (1000 examples)
- `training_data/verdict_generation.json` (500 examples)
- `training_data/price_intelligence.json` (300 examples)
- `training_data/review_trust.jsonl` (500 examples)

### Fine-tune Model
```bash
python train_lora.py
```

Uses LoRA (Low-Rank Adaptation) for efficient fine-tuning:
- Base: Llama 3.1 8B
- Training cost: ~$50 on Lambda Labs
- Inference: Runs on CPU

---

## Data Sources (Zero Cost)

| Source | Cost | What It Provides |
|--------|------|------------------|
| Built-in mock data | $0 | Demo/testing |
| Google Custom Search | $0 (100/day) | Product discovery |
| DuckDuckGo | $0 | Fallback search |
| Ollama (local LLM) | $0 | AI inference |
| User community | $0 | Price reports |

---

## Deployment Options

| Platform | Time | Cost |
|----------|------|------|
| Self-hosted (Docker) | 10 min | $0 |
| AWS EC2 (t3.medium) | 15 min | ~$30/mo |
| Railway/Render | 5 min | $0-5/mo |
| Hetzner (CX21) | 10 min | ~$6/mo |

---

## Key Files

| File | Purpose |
|------|---------|
| `src/models/requirement_engine.py` | Parse user intent |
| `src/models/product_matcher.py` | Match products to needs |
| `src/models/price_intelligence.py` | Detect fake discounts |
| `src/models/trust_engine.py` | Review authenticity |
| `src/models/verdict_engine.py` | Generate honest verdicts |
| `src/api/main.py` | FastAPI REST endpoints |
| `src/training/pipeline.py` | Synthetic data + LoRA training |

---

## The Philosophy

> "Most shopping AI asks: 'What do you want to buy?' We ask: 'What do you actually need?' Then we tell you honestly whether you should buy it."

**The engine sometimes says DONT_BUY. That's the feature, not the bug.**

---

## License

MIT License - Commercial use allowed.

## Contributing

This is a consumer advocacy project. All contributions that improve honesty and transparency are welcome.
