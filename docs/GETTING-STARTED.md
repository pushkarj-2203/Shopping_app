# Getting Started — Run & Test PriceWise in VS Code + GitHub

This guide gets you from "I have the folder" to "I can see it working and push to GitHub",
even if you're not a developer. Two ways to run it — pick **A (Docker, easiest)** or
**B (VS Code, best for testing/debugging)**.

---

## 0. Install the tools (one time)

- **VS Code**: https://code.visualstudio.com/
- **Git**: https://git-scm.com/downloads
- **Python 3.12**: https://www.python.org/downloads/ (tick "Add Python to PATH" on Windows)
- **Node.js 20+**: https://nodejs.org/
- *(Option A only)* **Docker Desktop**: https://www.docker.com/products/docker-desktop/

Open the project: VS Code → **File → Open Folder…** → select the `Shopping_app` folder.
When VS Code asks *"Install recommended extensions?"* → click **Install** (this adds Python,
Tailwind, Docker, and the REST Client used below).

---

## Option A — Run everything with Docker (one command)

In VS Code: **Terminal → New Terminal**, then:

```bash
docker compose up --build
```

Wait until logs settle, then open:
- Web app → http://localhost:3000
- API docs (Swagger) → http://localhost:8000/docs
- Health → http://localhost:8000/health

Stop with `Ctrl+C`. That's it.

---

## Option B — Run in VS Code (for testing & debugging)

### B1. Backend (API)
1. **Terminal → Run Task… → "Backend: setup (venv + deps)"** — creates `backend/.venv`
   and installs dependencies. Run once.
2. Copy env file: in `backend/`, copy `.env.example` to `.env` (defaults work as-is; it uses
   SQLite + in-memory cache, no external services, $0).
3. Press **F5** → choose **"Backend: FastAPI (uvicorn)"**. The API starts at
   http://localhost:8000 — open **/docs** to try endpoints in the browser.
   - VS Code may prompt to select a Python interpreter → pick `backend/.venv`.

### B2. Frontend (web app)
1. **Run Task… → "Frontend: install"** (once).
2. **Run Task… → "Frontend: dev"** → open http://localhost:3000.
   (Make sure the backend from B1 is running so the UI has data.)

> Tip: **Run → "Full stack (API + Web)"** (compound debug config) starts both together.

---

## How to confirm it's actually working

**1. Swagger UI (no setup):** open http://localhost:8000/docs, expand `POST /api/match`,
click **Try it out**, send the default body — you should get ranked products with verdicts.

**2. One-click API tests:** open `backend/requests.http`. With the REST Client extension
installed, a **"Send Request"** link appears above each request. Click them top to bottom:
- `health` → `{ "status": "ok" }`
- `parse` → extracts budget 50000, avoids "apple"
- `price-check` (iphone16pro) → flags the inflated MRP
- `chat` → returns a verdict + `session_id`; the next block **resumes** that session
- `register` → then `me` and `alerts` reuse the captured token automatically

**3. Automated tests:** **Run Task… → "Backend: run tests"** (or **F5 → "Backend: Pytest (all)"**).
You should see **31 passing**. This is the fastest "is everything wired correctly?" check.

**4. The web flow:** at http://localhost:3000 pick a category → answer the questions →
see ranked results with BUY/WAIT/DON'T BUY badges, and chat in the side panel.

---

## Push to GitHub

> If a `.git` folder already exists in the project and Git acts strangely, delete it
> first (it may be a stray from setup). In the project folder run **`rmdir /s /q .git`**
> (Windows CMD) or delete the `.git` folder in File Explorer (enable "show hidden items"),
> then continue below.

### Step 1 — initialize the repo (once)
In VS Code: **Terminal → New Terminal**, in the project root:
```bash
git init
git add -A
git commit -m "Initial commit: PriceWise AI (backend, frontend, orchestration, worker)"
```
(The `.gitignore` already excludes `.env`, `node_modules`, `.venv`, and databases, so no
secrets or junk get committed.)

### Step 2 — put it on GitHub

**Easiest — GitHub CLI**
1. Install GitHub CLI: https://cli.github.com/ → then `gh auth login` (once).
2. ```bash
   gh repo create pricewise-ai --private --source=. --remote=origin --push
   ```
   Done — your code is on GitHub and CI runs automatically.

**Manual (no CLI)**
1. Create an empty repo at https://github.com/new (don't add a README/.gitignore).
2. ```bash
   git remote add origin https://github.com/<you>/<repo>.git
   git branch -M main
   git push -u origin main
   ```

> Tip: after Step 1 you can also do everything visually from the VS Code **Source Control**
> panel and the **"Publish to GitHub"** button — no commands needed.

### What runs on GitHub
`.github/workflows/ci.yml` runs on every push/PR: backend tests, frontend type-check +
build, and Docker image builds. Green check = it works. See the **Actions** tab on GitHub.

### Day-to-day Git in VS Code
Use the **Source Control** panel (left sidebar): stage changes (+), type a message,
click **✓ Commit**, then **Sync/Push**. No commands needed.

---

## Troubleshooting

- **"python not found"** → reinstall Python with "Add to PATH", reopen VS Code.
- **Frontend shows no data** → the backend (B1) must be running on port 8000.
- **Port already in use** → change `--port 8000` (backend) or run `npm run dev -- -p 3001`.
- **Tests can't find `app`** → run them via the VS Code task (it sets the working dir to `backend/`).
