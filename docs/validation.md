# Validation record

Build date: 2026-10-01. Python 3.12.14, ADK 2.10.0, dependencies installed from the checked-in lock.

## Completed

- 15 automated Python tests: eligibility, token integrity/expiry, policy enforcement, no model-accessible confirmation tool, failure blocking, real ADK tool schema and runner execution, API input validation, confirmation retry semantics, error sanitization, eight-call limit, timeout mapping and request isolation.
- Offline SDK rehearsal: four actual tool calls and four actual tool responses executed through ADK with a scripted model, followed by a scripted final answer. This is not a Gemini evaluation.
- Node JavaScript syntax check and a minimal DOM behavior check: rendering trace/proposal, confirmation failure, recovery, and cleanup after a failed request.
- Python compilation and Bash syntax checks for both deployment scripts.
- Uvicorn imported the application, completed startup and listened on port 8080. API routes were tested through FastAPI's test client.
- Frozen requirements export matches the lock; no `.env`, credential files or virtual environment are included in the distribution.

Two upstream warnings occur in the Python tests: Starlette's current `httpx` test-client compatibility deprecation, and ADK's experimental JSON-schema function declaration warning. Tests pass with these visible warnings; neither is suppressed.

## Still requires credentialed rehearsal

- Real Gemini access and answer quality on the six live-evaluation cases. No Gemini key was available here.
- Cloud Run container build, deployment, IAM, Secret Manager, runtime inference and authenticated browser invocation. Google Cloud CLI and cloud credentials were unavailable here.
- Visual browser layout on a laptop/mobile viewport and live browser interaction. Chromium download returned truncated archives in this environment; DOM checks cover behavior but not rendering.

These boundaries matter: passing a scripted SDK test proves the selected API integration works locally. It does not prove a live model chooses the right tools, the cloud identity has access, or a deployed service works.

## Rehearsal gate

Before presenting: `uv run pytest -q`, `uv run python -m scripts.live_eval`, deploy in the intended project, open via the authenticated proxy, and complete the main demo and both backend failure cases. Manually inspect answer honesty and tool-use order in addition to automated evaluation results.
