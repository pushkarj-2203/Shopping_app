# PriceWise — LLM Orchestration Architecture

**Status:** implemented (`backend/app/orchestration/`, `backend/app/worker/`) ·
**Default cost:** $0 (rule-based fallbacks at every step) · **Runtime:** native FastAPI,
optional n8n for autonomous triggers · **Vector memory:** pluggable (in-memory → pgvector).

This document is the design behind the code, with the tradeoffs that drove each
decision. It is deliberately opinionated: it describes *one* coherent production
architecture, not a menu.

---

## 0. Design goals → how they're met (the contract)

| Goal | Mechanism | File |
|------|-----------|------|
| Persistent long-term memory | `memory_records` (fact/episodic/summary) + vector recall | `orchestration/memory.py`, `db/models.py` |
| Resumable after token/context reset | rolling summary + facts persisted on the session; rebuilt via RAG, no transcript replay | `memory.py` (`build_context`, `apply_summary`) |
| Modular agents | 6 single-purpose agents, decoupled, each with a rule-based fallback | `orchestration/agents.py` |
| Scalable orchestration | stateless controller per request; state in Postgres/Redis | `orchestration/orchestrator.py` |
| Cost optimization | provider switch, tiered model routing, response cache, per-user/global budgets | `core/llm.py`, `orchestration/router.py`, `runtime.py` |
| Model routing | task-tier router (cheap/standard/deep) with complexity escalation | `orchestration/router.py` |
| High reliability | retry w/ backoff → fallback to deterministic engine output; never 5xx on LLM failure | `orchestration/runtime.py` |
| Low hallucination | validator agent + hard price/spec guard against "allowed facts"; correction loop | `agents.py` (`ValidatorAgent`), `orchestrator.py` |
| Autonomous workflows | APScheduler worker (price sweeps, memory upkeep); n8n-triggerable | `worker/` |
| RAG / vector memory | pluggable `VectorIndex` (in-mem default, pgvector prod) + local $0 embeddings | `orchestration/vector.py`, `embeddings.py` |
| Async/background tasks | separate worker process; jobs take their own DB session | `worker/scheduler.py` |
| Observability | per-call `LLMCallLog`, request-id tracing, Prometheus, structured logs | `runtime.py`, `core/logging.py` |
| Tool calling / APIs | engine + data-provider are the "tools"; clean seam to add MCP/function tools | `services/`, `orchestrator.py` |

**Central tradeoff:** the deterministic rule-based engine is the *source of truth*;
the LLM is a *presentation and disambiguation layer*. This inverts the usual
"LLM decides, tools assist" pattern. The cost: the LLM can't freely reason its way
to a recommendation. The benefit: hallucination is structurally bounded (the model
may only rephrase facts the engine produced), latency/cost are predictable, and the
product works fully with no model at all. For a consumer-advocacy product where a
wrong "BUY" is a real harm, this is the right inversion.

---

## 1. Architecture diagram

```
                         ┌─────────────────────────────────────────────┐
   Client (web/n8n) ───► │            FastAPI  /api/chat                 │
                         └───────────────────────┬───────────────────────┘
                                                 ▼
                         ┌─────────────────────────────────────────────┐
                         │      Controller / Orchestrator               │
                         │  (orchestrator.py — owns the lifecycle)      │
                         └──┬───────┬─────────┬─────────┬─────────┬──────┘
                            │       │         │         │         │
              ┌─────────────▼─┐ ┌───▼────┐ ┌──▼─────┐ ┌─▼──────┐ ┌▼─────────┐
              │ Engine (truth)│ │Planner │ │Executor│ │Validator│ │Summarizer│
              │ rule-based AI │ │ agent  │ │ agent  │ │ agent   │ │ agent    │
              └───────────────┘ └────────┘ └───┬────┘ └────────┘ └──────────┘
                                                │ (all agents)
                                                ▼
                         ┌─────────────────────────────────────────────┐
                         │  Runtime: route → retry/backoff → fallback   │
                         │           → LLMCallLog (runtime.py)          │
                         └───────────────┬──────────────┬───────────────┘
                                         ▼              ▼
                              Provider adapters    Memory Manager
                              (anthropic/openai/    (4 tiers + RAG +
                               ollama/none)          context stitching)
                                                         │
                         ┌───────────────────────────────▼──────────────┐
                         │  Postgres (sessions, memory_records, logs)   │
                         │  Redis (cache, rate-limit, budget counters)   │
                         │  VectorIndex (in-mem default | pgvector)     │
                         └──────────────────────────────────────────────┘

   Worker process (worker/) ── APScheduler ──► price_alert_sweep, memory_maintenance
                                              (own DB session; n8n can also trigger)
```

---

## 2. Data flow (one chat turn)

1. **Ingress** → `/api/chat` (rate-limited, optional auth) → `Orchestrator.run`.
2. **Truth** → engine parses the query and produces the factual *finding* + the
   `allowed_facts` whitelist (product names, prices, verdicts).
3. **Plan** → `PlannerAgent` sets `complexity` and `needs_clarification` from engine
   confidence; escalates to the DEEP model tier only when genuinely ambiguous.
4. **Stitch context** → `MemoryManager.build_context`: rolling summary + long-term
   facts + top-K RAG over episodic/fact memory + last N verbatim turns, capped at
   `MAX_CONTEXT_TOKENS`.
5. **Execute** → `ExecutorAgent` rewrites the finding warmly (LLM if configured,
   else returns the finding verbatim).
6. **Validate** → `ValidatorAgent` checks the draft against `allowed_facts`
   (hard price-regex guard always; LLM JSON check if available). On failure →
   one correction pass → re-validate → else fall back to the raw finding.
7. **Persist** → record user+assistant turns; `MemoryAgent` extracts durable
   facts/episodes (budget, priorities, avoided brands).
8. **Compress** → if context exceeded the summarize threshold, roll older turns
   into a new rolling summary (persisted → enables resume).
9. **Respond** → reply + `session_id` + `answer_source` + `trace_id` + `validated`.

---

## 3. Component breakdown

- **Controller** (`orchestrator.py`): the only component that knows the full
  sequence; agents stay ignorant of each other. Stateless per request.
- **Agents** (`agents.py`): Planner, Executor, Validator, Memory, Summarizer. Each
  has a deterministic fallback so the pipeline never hard-depends on an LLM.
- **Runtime** (`runtime.py`): the single LLM choke point — routing, retry/backoff,
  fallback, and `LLMCallLog` tracing. Reliability/cost live here, nowhere else.
- **Providers** (`providers.py`): thin vendor adapters (Anthropic/OpenAI/Ollama)
  behind one `complete()`; `ProviderDisabled` drives the $0 path.
- **Router** (`router.py`): maps (agent, complexity) → (model, max_tokens). ~80% of
  spend is decided here before any token is used.
- **Memory** (`memory.py`): session lifecycle, 4-tier writes, context stitching,
  compression. **Vector** (`vector.py`) + **embeddings** (`embeddings.py`) are
  pluggable and default to $0.
- **Worker** (`worker/`): autonomous jobs on a schedule, isolated from request path.

---

## 4. Prompt strategy (layered, versioned)

`prompts.py` assembles four layers in order: **SYSTEM** (immutable identity +
anti-dark-pattern + "never invent facts" guardrails, carries `PROMPT_VERSION`) →
**MEMORY** (rolling summary + known facts + RAG snippets) → **TASK** (per-agent) →
**CORRECTION** (only on retry, citing the prior failure). Self-reflection is a
distinct prompt (`reflection_task`) available for high-stakes turns.

Tradeoff: layered string prompts (not a framework's prompt objects) keep prompts
unit-testable and diffable, at the cost of manual assembly. Versioning the SYSTEM
layer makes eval runs reproducible across prompt changes.

---

## 5. Memory strategy

Four tiers in one table (`memory_records.kind`):

| Tier | Lifetime | Use | Injected as |
|------|----------|-----|-------------|
| working | short, pruned by worker | turn scratch | recent verbatim turns |
| episodic | durable | events/decisions ("rejected iPhone: over budget") | RAG |
| summary | durable | compressed history | session rolling summary |
| fact | long-term | stable preferences (budget, priorities) | always-injected facts |

- **Context stitching:** summary + facts + RAG + last N turns, budget-capped.
- **Compression:** past `SUMMARIZE_THRESHOLD_TOKENS`, older turns roll into a new
  summary (extractive fallback when no LLM) persisted on the session.
- **Resumable sessions:** because summary + facts live in Postgres, a new process
  with only `session_id` rebuilds full context (reload summary + re-run RAG) — no
  transcript replay, so resume cost is O(1) in conversation length.
- **Embeddings:** local feature-hashing embedder ($0, deterministic, real cosine
  similarity); swap to OpenAI via env. **Vector store:** in-memory ranker by default;
  `pgvector` on your existing Supabase Postgres for production (HNSW index, no new
  service) — the recommended path at scale.

---

## 6. API design (contracts)

`POST /api/chat`
```jsonc
// request
{ "query": "good camera phone under 70000", "session_id": "sess_ab12…?" }
// response
{
  "response": "Best match is the OnePlus 12 (…) — verdict BUY …",
  "structured_requirement": { "category": "smartphone", "budget_range": [0, 70000], … },
  "recommended_products": [ { "product": {…}, "match_score": 88, "verdict": "BUY" } ],
  "follow_up_questions": ["What matters more, battery or display?"],
  "session_id": "sess_ab12…",
  "answer_source": "rule_based",   // | anthropic | openai | ollama
  "trace_id": "9f3c…",
  "validated": true
}
```

`POST /api/discover` → `{ "provider": "MockProvider", "results": [ … ] }`
(live data provider; CSE behind a 24h cache).

Internal/worker job contract (callable + n8n-triggerable):
`price_alert_sweep(db, price_lookup) -> { "checked": N, "triggered": M }`.

---

## 7. Failure handling & recovery patterns

- **Provider error** → exponential backoff retries (`LLM_MAX_RETRIES`) → **fallback**
  to deterministic engine text. The endpoint never returns 5xx because a model
  failed. Outcome recorded as `retry|fallback|error` in `LLMCallLog`.
- **Budget breach** (per-user daily / global monthly) → serve rule-based text.
- **Hallucination** → validator → correction pass → raw-finding fallback.
- **Context reset / crash** → resume from persisted summary + facts.
- **Worker job crash** → isolated try/except per job; next interval retries; jobs are
  idempotent (triggered alerts won't re-fire).
- **DB/cache down** → `/ready` reports degraded; cache transparently falls back to
  in-process; rate-limit still functions locally.

---

## 8. Scaling strategy

- API and worker are **separate, stateless** processes — scale independently.
- Set `REDIS_URL` so cache + rate-limit + budget counters are shared across replicas.
- Move catalog from seed loader → Postgres + data provider; switch `VECTOR_BACKEND=pgvector`.
- Heavy/long autonomous flows → externalize to **n8n** calling the worker job
  endpoints; backend stays source of truth.
- Routing keeps cost sublinear to traffic: most turns hit the CHEAP tier; DEEP is
  reserved for ambiguous planning.

---

## 9. Security

- JWT auth (access/refresh) + bcrypt; chat usable anonymously but personalized when
  authed. Memory is partitioned by `user_id`.
- Strict Pydantic validation on every body; CORS locked to configured origins.
- Secrets only via env; non-root Docker images; no marketplace self-scraping (legal).
- Prompt-injection posture: the SYSTEM layer forbids inventing facts, and the
  validator enforces it against an explicit whitelist — model output cannot smuggle
  in prices/products the engine didn't produce.
- PII: long-term `fact` memories are preference-level by design; avoid persisting
  sensitive personal data (the MemoryAgent extracts only budget/priority/brand).

---

## 10. Recommended next steps

1. **Turn on a provider in staging** (`LLM_PROVIDER=anthropic`, Haiku) and watch
   `LLMCallLog` cost/latency before production.
2. **Promote vector memory to pgvector** on Supabase (Alembic adds the `vector`
   column + HNSW index; `PgVectorIndex` already stubs the query).
3. **Add a tool-calling seam**: expose engine ops as typed tools so the executor can
   request a fresh price-check mid-conversation (kept off the hot path today).
4. **Eval harness**: golden-set of queries → assert verdict appropriateness +
   zero unsupported-fact rate (the validator already produces the signal).
5. **n8n autonomous flows**: nightly catalog refresh + price-history ingestion via
   the data provider, writing back to Postgres.
