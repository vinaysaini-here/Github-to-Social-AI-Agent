# GitHub-to-Social AI Agent

An event-driven AI agent that watches GitHub pushes, decides which ones are worth
sharing, generates LinkedIn and X drafts grounded in the actual code change,
and publishes human-approved drafts to LinkedIn, so build-in-public updates
don't need a manual write-up after every meaningful commit.

## How it works

```
GitHub push
   │  webhook (HMAC-verified, deduplicated)
   ▼
FastAPI ──► Redis queue (arq) ──► Worker
                                    │
        Pre-filter (no LLM) ► Classify & score ► Post-worthy?
                                    │ yes
                    Generate drafts (LinkedIn + X) ► Verify grounding
                                    │ (regenerate on failure, capped)
                                    ▼
                               MongoDB
                                    │
                    Approval dashboard (React) ► Approve
                                    │
        Quota check ► Safety check ► Publish to LinkedIn ► Audit log
```

1. **Webhook intake**: signature verified, duplicate deliveries dropped via Redis, the whole push (not just the last commit) is diffed using GitHub's compare API.
2. **Pre-filter**: lockfile-only and trivial typo-style changes are skipped before any LLM call.
3. **Classify & score**: the LLM labels the change type and scores post-worthiness (0-100) with a reason. The threshold can be overridden per repository.
4. **Generate**: separate drafts for LinkedIn (descriptive) and X (concise).
5. **Verify**: a second LLM pass checks every claim against the diff. Failures trigger a regeneration with feedback, capped at 3 retries.
6. **Approve**: nothing is published until a human approves it in the dashboard (edit by regenerating with a note, reject, attach media).
7. **Publish**: approved drafts pass a quota check and an LLM safety check before going to LinkedIn. Every step is written to an audit log.

## Status

| Area | State |
|---|---|
| AI pipeline (classify, generate, verify, fallback, evals) | Done |
| Webhook intake, queue, MongoDB storage | Done |
| Approval dashboard (list, approve, reject, regenerate, media upload) | Done |
| LinkedIn OAuth + publishing (retry, quota, safety check) | Done |
| GitHub OAuth (user identity + token) | Done |
| Per-repo config (enabled, threshold, tone, hashtags) | Done |
| Audit log + analytics summary | Done |
| LangSmith tracing | Done |
| X (Twitter) publishing | Not started |
| AI-generated images | Deferred (Gemini image models have no free tier) |

## Tech stack

| Layer | Choice |
|---|---|
| Backend | Python 3.12+, FastAPI |
| Orchestration | LangGraph (`StateGraph`) |
| LLMs | Groq `openai/gpt-oss-120b` (primary), Gemini `gemini-3.6-flash` (fallback) |
| Structured outputs / config | Pydantic, `pydantic-settings` |
| Queue | Redis + `arq` |
| Database | MongoDB (`motor`) |
| HTTP / retry | `httpx`, `tenacity` |
| Secrets | `cryptography` (Fernet) for tokens at rest |
| Observability | LangSmith |
| Frontend | React + Vite + TypeScript + Tailwind CSS v4 + axios |
| Package managers | `uv` (backend), `npm` (dashboard) |

## Project structure

```
src/social_agent/
├── config.py                  # typed settings, lazy get_settings()
├── observability.py           # LangSmith tracing bootstrap
├── models/                    # context, classification, worthiness, content,
│                              # verification, safety, repo_config
├── collectors/git.py          # local git -> CommitContext (CLI path)
├── guardrails/                # prefilter, safety, media_validation
├── llm/                       # providers (Groq + Gemini fallback), prompts
├── nodes/                     # classify, generate, verify
├── webhook/                   # security (HMAC), parser, idempotency
├── api/                       # app, routes (webhook), drafts, linkedin_auth,
│                              # github_auth, repo_config, analytics
├── queue/tasks.py             # arq worker job
├── db/                        # client, repository
├── social/                    # linkedin publisher, rate_limit
├── security/token_encryption.py
├── media/storage.py
├── graph.py                   # LangGraph wiring
├── pipeline.py                # run_pipeline / run_pipeline_from_context
└── main.py                    # CLI

evals/                         # dataset + runner (8 cases)
dashboard/                     # React approval inbox
scripts/                       # local helpers (simulate a signed webhook, inspect MongoDB)
```

## Setup

**Prerequisites:** Python 3.12+, `uv`, Docker. Node.js is optional (see dashboard).

```bash
uv sync
cp .env.example .env
```

Environment variables:

| Variable | Required | Purpose |
|---|---|---|
| `GROQ_API_KEY` | yes | Primary LLM |
| `GEMINI_API_KEY` | no | Enables the fallback LLM |
| `GITHUB_WEBHOOK_SECRET` | yes | Verifies webhook signatures |
| `GITHUB_TOKEN` | yes | Fetches diffs/README from the GitHub API |
| `GITHUB_OAUTH_CLIENT_ID` / `GITHUB_OAUTH_CLIENT_SECRET` | yes | GitHub OAuth app |
| `LINKEDIN_CLIENT_ID` / `LINKEDIN_CLIENT_SECRET` | yes | LinkedIn app (Share on LinkedIn + Sign In with OpenID Connect) |
| `TOKEN_ENCRYPTION_KEY` | yes | Fernet key for tokens at rest |
| `LANGSMITH_API_KEY`, `LANGSMITH_TRACING`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` | no | Tracing |
| `LINKEDIN_API_VERSION` | no | `YYYYMM`, see Known limitations |

Generate an encryption key:

```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Run

Five processes:

```bash
docker run -p 27017:27017 mongo                                   # 1. MongoDB
docker run -p 6379:6379 redis                                     # 2. Redis
uv run uvicorn social_agent.api.app:app --reload                  # 3. API
uv run arq social_agent.queue.tasks.WorkerSettings                # 4. Worker
cd dashboard && npm install && npm run dev                        # 5. Dashboard
```

No Node installed? Run the dashboard in Docker instead (from the repo root, PowerShell):

```powershell
docker run --rm -it -p 5173:5173 -v "${PWD}\dashboard:/app" -v social-dashboard-node-modules:/app/node_modules -w /app node:22-slim sh -c "npm install && npm run dev -- --host 0.0.0.0"
```

The dashboard needs `dashboard/.env` with `VITE_API_URL=http://localhost:8000`.
API docs: `http://localhost:8000/docs`, dashboard: `http://localhost:5173`.

Connect accounts once (tokens are stored encrypted):
`http://localhost:8000/auth/linkedin/login` and `http://localhost:8000/auth/github/login`.
Each returns an `authorization_url` to open in the browser.

**CLI (no webhook, local git only):**

```bash
uv run social-agent /path/to/repo <commit_sha>
```

**Evals:**

```bash
uv run python -m evals.run_evals
```

**Real GitHub webhooks** need a publicly reachable URL (a tunnel such as ngrok) pointed
at `/webhook/github`, with the same secret as `GITHUB_WEBHOOK_SECRET`.

## API overview

| Method | Path | Purpose |
|---|---|---|
| POST | `/webhook/github` | Push intake |
| GET | `/drafts` | List drafts (`?status=`) |
| GET | `/drafts/{repo}/{sha}` | One draft |
| POST | `/drafts/{repo}/{sha}/approve` / `reject` | Review actions |
| POST | `/drafts/{repo}/{sha}/regenerate` | New draft, optional note |
| POST | `/drafts/{repo}/{sha}/media` | Attach image/video |
| POST | `/drafts/{repo}/{sha}/publish` | Publish an approved draft to LinkedIn |
| GET | `/auth/linkedin/login`, `/auth/github/login` | Start OAuth |
| GET/PUT | `/repos/{owner}/{repo}/config` | Per-repo settings |
| GET | `/analytics/summary`, `/analytics/audit-log` | Metrics and event history |

Publish checks run cheapest-first: approved? account connected? daily quota? content safety? then the LinkedIn call.
Audit events: `approved`, `rejected`, `regenerated`, `published`, `publish_failed`,
`publish_blocked_quota`, `publish_blocked_safety`.

## Production practices

- **Never crash:** every graph node catches its own failures and routes to an error state; every external call has a timeout.
- **Retry and fallback:** Groq is retried, then Gemini takes over; LinkedIn calls retry 429/5xx with exponential backoff.
- **Token-waste guardrails:** trivial commits skip the LLM entirely; large diffs are truncated before prompting.
- **Prompt-injection guardrail:** commit, diff and README text is delimited and treated as data in every prompt.
- **Human in the loop:** nothing is published without explicit approval.
- **Idempotency:** webhook deliveries are deduplicated (Redis `SET NX`); results are upserted by repo and commit.
- **Secrets:** tokens are encrypted at rest and never sent to the frontend; `SecretStr` keeps keys out of logs.
- **Rate limiting:** a per-account daily publish quota is enforced before the LinkedIn API is called.
- **Auditability:** append-only audit log, and the audit write can never break the action being logged.
- **Evals and tracing:** an 8-case eval set guards prompt changes; LangSmith traces every run.

## Known limitations

- **No authentication on the API or dashboard.** Anyone who can reach the server can approve and publish. Fine for local use, must be fixed before any deployment.
- **Single LinkedIn account:** publishing uses whichever LinkedIn token is stored.
- **GitHub OAuth is not yet fully multi-tenant:** it stores a user's identity and token, but the webhook pipeline still reads repos with the global `GITHUB_TOKEN`.
- **The dashboard has no Publish button yet;** publishing is done through the API.
- **`LINKEDIN_API_VERSION` needs maintenance:** LinkedIn retires versions about a year after release. A `426 NONEXISTENT_VERSION` error means it is time to bump it.
- **Diffs are truncated** (default 4000 characters) before they reach the LLM.

## Possible next steps

- API authentication and per-user token association
- Publish button and "published" state in the dashboard
- X (Twitter) publishing
- Auto-publish mode above a confidence threshold
- Scheduled publishing, weekly summaries from multiple commits
- AI-generated images, once a paid Gemini image tier is available

## Development workflow

Every feature was tracked as a GitHub issue and built on its own branch:

```bash
git checkout main && git pull
git checkout -b <feature-branch>
# work, commit
git push -u origin <feature-branch>
# open a PR with "Fixes #N" and merge
```
