# PriceWise AI — Consumer-First Shopping Intelligence

> *"We ask what you need, then tell you honestly whether to buy it."*

PriceWise is a production-ready AI application that helps people make purchasing
decisions in their own interest. Unlike seller-first platforms, it can recommend
**WAIT** or **DON'T BUY** — that's the feature, not a bug.

It pairs a deterministic, **zero-cost rule-based AI engine** (requirement parsing,
product matching, fake-discount detection, review-trust scoring, honest verdicts)
with a production web stack: auth, database, caching, rate limiting, structured
logging, metrics, and strict AI cost controls.

---

## Architecture

```
frontend/  Next.js 14 (App Router, TypeScript, Tailwind)
   │  REST over HTTPS (JWT bearer)
   ▼
backend/   FastAPI (async)
   ├─ app/api/routes   auth · engine · chat · alerts · health
   ├─ app/core         config · security(JWT) · logging · cache · rate_limit · llm
   ├─ app/db           async SQLAlchemy models + session
   ├─ app/services     engine singleton + seed catalog · pluggable data provider
   └─ app/engine       the rule-based AI engine (no LLM / no GPU required)
   │
   ├─ PostgreSQL   (users, alerts, usage logs, chat history)
   └─ Redis        (cache, rate-limit counters, AI budget counters)
```

The engine works **fully offline at $0**. An optional LLM layer (Anthropic Claude
or self-hosted Ollama) can polish chat replies — gated by caching, per-user caps,
and a global token budget, and it always falls back to the rule-based answer.

---

## Tech stack & why

| Layer | Choice | Why |
|-------|--------|-----|
| Frontend | Next.js 14 + TS + Tailwind | SSR, file routing, type safety, fast UI |
| Backend | FastAPI (async) | Async I/O, auto OpenAPI docs, Pydantic validation |
| AI engine | Pure Python (rule/statistics) | Deterministic, explainable, **zero per-query cost** |
| Optional LLM | Claude Haiku / Ollama | Cheap or self-hosted; off by default |
| DB | PostgreSQL (SQLite in dev) | Relational + JSON; SQLite means zero-setup dev |
| Cache | Redis (in-proc fallback) | 24h price/review cache + shared rate limits |
| Auth | JWT (access+refresh), bcrypt | Stateless, scalable, standard |
| Deploy | Docker / Compose, Vercel, Railway | Portable; cheapest hosted path documented |

---

## Quick start

```bash
# Everything (Postgres + Redis + API + web) in one command
export SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build
# Web → http://localhost:3000   API docs → http://localhost:8000/docs
```

Without Docker:

```bash
cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

Full instructions: [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

---

## API surface (prefix `/api`)

| Endpoint | Purpose |
|----------|---------|
| `POST /parse` | Natural language → structured requirement (UC-01) |
| `POST /questionnaire` | Adaptive 7-question discovery (UC-02) |
| `POST /match` | Score & rank products by true fit |
| `POST /verdict` | Honest BUY/WAIT/DONT_BUY/COMPARE with reasoning (UC-05) |
| `POST /compare` | Side-by-side comparison + winner (UC-06) |
| `POST /price-check` | Fake-discount detection + buy-timing (UC-03) |
| `POST /review-check` | Review trust score + fake detection (UC-04) |
| `POST /discover` | Live product discovery via data provider (mock/Google CSE) |
| `POST /chat` | Conversational assistant (UC-07) |
| `POST/GET/DELETE /alerts` | Price-drop alerts, auth required (UC-08) |
| `POST /auth/register·login·refresh`, `GET /auth/me` | Authentication |
| `GET /health`, `/ready`, `/metrics` | Ops |

Interactive docs are auto-generated at `/docs`.

---

## LLM orchestration & autonomous jobs

The `/api/chat` endpoint runs a **multi-agent orchestration layer** (planner ·
executor · validator · memory · summarizer · controller) with persistent +
resumable memory, RAG over a pluggable vector store, tiered model routing, and
retry→fallback. It runs at **$0 by default** (rule-based fallbacks) and upgrades in
quality when you set `LLM_PROVIDER`. Full design: [docs/LLM-ORCHESTRATION.md](docs/LLM-ORCHESTRATION.md).

A separate **background worker** (`backend/app/worker/`, an APScheduler process and
a `worker` compose service) runs autonomous jobs: the UC-08 price-drop sweep and
memory maintenance. Database schema is managed by **Alembic** (`backend/alembic/`,
`alembic upgrade head`).

## Security & production hardening

- JWT auth with separate access/refresh tokens; bcrypt password hashing.
- Pydantic validation on every request body (lengths, types, ranges, email).
- Per-route rate limiting (auth, chat, default) keyed by user/IP, Redis-backed.
- AI cost control: provider switch, response caching, per-user daily cap, global
  monthly token budget — fails open to rule-based output.
- Structured JSON logging with per-request IDs; Prometheus metrics; health probes.
- CORS locked to configured origins; secrets never committed; non-root Docker images.
- No self-scraping of marketplaces — only official/licensed data providers (legal).

---

## Tests & CI

```bash
cd backend && pytest          # 24 tests: engine + full API (auth, alerts, chat…)
cd frontend && npm run typecheck && npm run build
```

GitHub Actions (`.github/workflows/ci.yml`) runs backend tests, frontend
type-check + build, and Docker image builds on every push/PR.

---

## Repository layout

```
backend/    FastAPI app, engine, tests, Dockerfile, requirements.txt, .env.example
frontend/   Next.js app, components, lib, Dockerfile, .env.example
docs/        DEPLOYMENT.md, original engine docs, usecase document
docker-compose.yml   full local stack
.github/workflows/ci.yml   CI/CD pipeline
```

## License

MIT — commercial use allowed. A consumer-advocacy project: contributions that
improve honesty and transparency are welcome.
