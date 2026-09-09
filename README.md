# GitHub-to-Social AI Agent

An event-driven AI agent that turns meaningful GitHub commits into ready-to-post
LinkedIn and X drafts — so build-in-public updates don't require manually
writing a post every time you ship something.

## The problem

Developers ship real work — features, integrations, bug fixes, performance
wins — but most of it never gets shared publicly. Writing a LinkedIn/X post
after every meaningful commit takes time, and raw commit messages aren't
post-ready on their own.

## How it works


1. **Collect context** — diff, commit message, changed files, README snippet
2. **Pre-filter** — skip obviously trivial changes (lockfiles, typo fixes) before spending any tokens
3. **Classify & score** — LLM judges change type and how post-worthy it is (0–100)
4. **Generate drafts** — separate tone/length for LinkedIn (descriptive) vs. X (concise)
5. **Verify grounding** — a second LLM pass checks the drafts don't claim anything the diff doesn't support
6. **Output** — drafts + decision trail saved for review

## Status

**Phase 1 — AI Agent Core** (local, webhook-free, in progress)

- [x] `models/context.py` — `CommitContext`
- [x] `collectors/git.py` — local git → `CommitContext`
- [x] `guardrails/prefilter.py` — skip trivial commits before any LLM call
- [x] `llm/providers.py` — Groq primary, Gemini fallback
- [ ] `llm/prompts.py`
- [ ] `nodes/classify.py`, `nodes/generate.py`, `nodes/verify.py`
- [ ] `graph.py` — wire everything into a LangGraph `StateGraph`
- [ ] `pipeline.py`, `main.py` — CLI entrypoint
- [ ] Eval set

Later phases (webhook backend, approval dashboard, real publishing, multi-user
SaaS) start only once Phase 1 is proven on real commits.

## Tech stack

| Layer               | Choice                                  |
|----------------------|------------------------------------------|
| Language             | Python 3.12+                             |
| Package manager       | `uv`                                    |
| Orchestration         | LangGraph (`StateGraph`)                |
| Primary LLM           | Groq — `openai/gpt-oss-120b`            |
| Fallback LLM           | Gemini — `gemini-3.6-flash`             |
| Structured outputs     | Pydantic                                |
| Config                 | `pydantic-settings`                     |
| Backend (Phase 2+)      | FastAPI                                 |
| Queue (Phase 2+)         | Redis + `arq`                           |
| Database (Phase 2+)       | MongoDB                                 |
| Frontend (Phase 3+)        | React + Vite                            |



## Setup

**Backend:**
```bash
uv sync
cp .env.example .env
# fill in: GROQ_API_KEY, GITHUB_WEBHOOK_SECRET, GITHUB_TOKEN,
#          LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET, TOKEN_ENCRYPTION_KEY
# optional: GEMINI_API_KEY (enables the fallback path)
```

Run everything (5 processes): MongoDB, Redis, `uv run uvicorn social_agent.api.app:app --reload`,
`uv run arq social_agent.queue.tasks.WorkerSettings`, and the dashboard (below).

**Dashboard:**
```bash
cd dashboard
npm install
cp .env.example .env   # VITE_API_URL=http://localhost:8000
npm run dev
```

**CLI (no webhook, local git only):**
```bash
uv run social-agent /path/to/repo <commit_sha>
```

## Production practices

- **Never crash** — every graph node handles its own failures and routes to an
  error state instead of raising unhandled; every external call has a timeout
- **Retry + fallback** — Groq retried first, Gemini used only if Groq keeps
  failing; LinkedIn publish calls retry on 429/5xx with exponential backoff
- **Token-waste guardrail** — trivial commits filtered out before any LLM
  call; large diffs truncated
- **Prompt-injection guardrail** — commit/diff/README content is treated as
  data, never as instructions, in every prompt
- **Idempotency** — webhook deliveries deduped via Redis; pipeline results
  upserted, not duplicated
- **Encrypted secrets** — LinkedIn tokens encrypted at rest (Fernet), never
  exposed to the frontend
- **Rate limiting** — daily publish quota tracked per connected account,
  enforced before the LinkedIn API is even called
- **Evals** — a hand-built commit set catches regressions when prompts change
  (LangSmith integration planned)

## Workflow

Each remaining feature is tracked as a GitHub issue and built on its own branch:

```bash
git checkout main && git pull
git checkout -b <feature-branch>
# ... work, commit ...
git push -u origin <feature-branch>
# open PR on GitHub, description: "Fixes #N", merge
```
