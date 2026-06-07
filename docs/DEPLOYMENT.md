# Deployment Guide

PriceWise is a two-service app: a **FastAPI backend** (the AI engine + API) and a
**Next.js frontend**. It is designed to run at **zero marginal cost** by default
(rule-based engine, SQLite, in-process cache, no LLM), and to scale up by flipping
environment variables — no code changes required.

---

## 0. Configuration model

Everything is environment-driven. Copy the example files and edit:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

The single most important production setting:

```bash
# Generate a strong secret — the app refuses to be secure without it
openssl rand -hex 32   # paste into SECRET_KEY
```

Cost controls (see backend/.env.example) keep AI spend bounded:
`LLM_PROVIDER=none` (default, $0), per-user daily call cap, global monthly token
budget, and 24h response caching. The system always *fails open* to the
rule-based answer, so the bill can never run away.

---

## 1. Local — Docker Compose (recommended)

Brings up Postgres, Redis, backend, and frontend together:

```bash
export SECRET_KEY=$(openssl rand -hex 32)
docker compose up --build
```

- Frontend: http://localhost:3000
- API + Swagger docs: http://localhost:8000/docs
- Health/readiness: http://localhost:8000/health, /ready
- Metrics (Prometheus): http://localhost:8000/metrics

## 2. Local — without Docker

```bash
# Backend (uses SQLite + in-process cache by default)
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## 3. Vercel (frontend) + Railway (backend) — cheapest hosted path

### Backend on Railway / Render
1. New project → Deploy from repo → root `backend/`.
2. Add a **PostgreSQL** plugin and a **Redis** plugin; Railway injects their URLs.
3. Set service variables:
   ```
   ENVIRONMENT=production
   DEBUG=false
   LOG_JSON=true
   SECRET_KEY=<openssl rand -hex 32>
   DATABASE_URL=postgresql+asyncpg://<from Railway>   # ensure +asyncpg
   REDIS_URL=<from Railway>
   CORS_ORIGINS=https://<your-vercel-domain>
   LLM_PROVIDER=none
   ```
4. Start command (Railway auto-detects, or set explicitly):
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

> Note: managed Postgres usually gives a `postgresql://` URL. Change the scheme to
> `postgresql+asyncpg://` so the async driver is used.

### Frontend on Vercel
1. Import the repo, set **Root Directory** = `frontend`.
2. Environment variable: `NEXT_PUBLIC_API_URL=https://<your-railway-backend>`.
3. Deploy. Vercel auto-detects Next.js (build `next build`).

---

## 4. Single VPS (Hetzner / EC2) with Docker Compose

```bash
ssh user@server
git clone <repo> && cd pricewise
export SECRET_KEY=$(openssl rand -hex 32)
docker compose up -d --build
# Put Caddy or Nginx in front for TLS (Let's Encrypt). Example with Caddy:
#   yourdomain.com { reverse_proxy localhost:3000 }
#   api.yourdomain.com { reverse_proxy localhost:8000 }
```

A 2 vCPU / 4 GB box (≈ €5/mo) comfortably runs the whole stack.

---

## 5. Database migrations (Alembic — already configured)

For development the app auto-creates tables on startup (`init_db`). For production,
use the bundled Alembic setup — it reads `DATABASE_URL` automatically (translating
the async driver to its sync equivalent) and an initial migration is already committed:

```bash
cd backend
alembic upgrade head                      # apply all migrations
# after changing models:
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

The background worker and API both expect the schema to exist; run `alembic upgrade head`
as a release step (or one-off task) before rolling new app versions.

---

## 6. Observability

- **Logs**: structured JSON when `LOG_JSON=true`; every line carries a `request_id`.
  Ship stdout to CloudWatch / Loki / Datadog.
- **Metrics**: `/metrics` exposes Prometheus metrics (request rate, latency,
  status codes). Scrape it and chart in Grafana.
- **Health**: `/health` (liveness) and `/ready` (DB + cache + catalog) for load
  balancer and Kubernetes probes.

---

## 7. Scaling checklist

- Set `REDIS_URL` so rate-limit counters and caches are shared across instances.
- Run multiple backend workers/replicas behind a load balancer (it's stateless).
- Move the product catalog from the seed loader to Postgres + the data provider.
- Turn on an LLM provider only after validating cost caps in staging.
