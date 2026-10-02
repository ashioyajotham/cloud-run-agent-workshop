# From Prompt to Action

**Build and deploy a tool-using support agent on Cloud Run.** A 60-minute workshop for Build with Google AI Kenya, facilitated by Victor Ashioya Jotham.

An agent checks an order, reads a refund policy, calculates eligibility with code, and proposes a demo refund. The browser displays actual tool calls and results. The participant confirms through an application endpoint that the model cannot call.

This is a teaching application. Orders, policy and receipts are fictional. No payments occur, and no persistent refund ledger exists. Each request starts a new agent session; include the full context in each request. A repeated confirmation returns the same deterministic demo receipt while its signed proposal remains valid.

## Start locally

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/getting-started/installation/) and a Gemini API key with access to the configured model.

```bash
uv sync --frozen
cp .env.example .env
# Edit .env: set GEMINI_API_KEY; replace the signing-key placeholder with a random key.
uv run uvicorn workshop.server:app --host 127.0.0.1 --port 8080
```

Open http://localhost:8080. Try: **“My headphones arrived damaged. Order KE-1042. Can you sort this out?”** Inspect the tool results, then press **Confirm demo refund**. Set the confirmation backend to unavailable and request a new proposal to test failure handling.

For the local key path use `GOOGLE_GENAI_USE_VERTEXAI=FALSE`. `GEMINI_API_KEY` is normalized to `GOOGLE_API_KEY` for ADK compatibility; if both exist, `GOOGLE_API_KEY` wins. Do not include `.env` in commits or uploads.

## What you learn

- Model-selected tool execution and the observe/act loop.
- Python function signatures and docstrings as tool interfaces.
- Business rules enforced by deterministic code.
- Human confirmation controlled by the application.
- Deploying your agent runtime as a Cloud Run service.
- Evidence-based failure testing, request limits and honest errors.

## Workshop material

| File | Purpose |
| --- | --- |
| `docs/participant-lab.md` | Guided exercises and checkpoints |
| `docs/facilitator.md` | Minute-by-minute delivery and demo script |
| `docs/cloud-run.md` | Project setup, IAM, deployment and cleanup |
| `docs/compatibility.md` | Verified dependencies, current docs and update procedure |
| `docs/validation.md` | What has been tested and what remains |
| `exercises/add_tool.py` | Participant delivery-status tool exercise |
| `exercises/solution.py` | Reference solution |
| `scripts/live_eval.py` | Six-case real Gemini evaluation |
| `tests/test_workshop.py` | Policy, API and real ADK runner integration tests |

## Deploy

Follow [the Cloud Run guide](docs/cloud-run.md). The normal cloud path uses Vertex AI access through the runtime service account, with no downloaded credential file. Local development can keep using the Gemini Developer API.

```bash
export PROJECT_ID='your-existing-demo-project'
export REGION='europe-west1'
bash scripts/setup_gcp.sh  # facilitator/admin, before the event
bash scripts/deploy.sh
# Stop the local uvicorn server first to free port 8080.
gcloud run services proxy support-agent-workshop --project "$PROJECT_ID" --region "$REGION" --port 8080
```

The service is private. The authenticated proxy lets its browser UI call the API. Participant identities need Cloud Run Invoker on the service. Deployment/build IAM and propagation must be resolved before the workshop.

## Verify

```bash
uv run pytest -q
uv run python -m scripts.live_eval  # real provider requests; requires credentials
```

Offline tests use a scripted model with the actual ADK runner; they verify integration, not Gemini's behavior. Live evaluation writes `artifacts/live-eval.json`; review answer honesty manually as well as structural checks. No live success is claimed until this credentialed evaluation and deployed smoke test pass.

## Runtime choices

Python 3.12; `google-adk==2.10.0`; exact transitive dependencies in `uv.lock` and exported `requirements.txt`; default `GEMINI_MODEL=gemini-3.8-flash`. Documentation checked **2026-10-01**. Model availability and Cloud CLI/IAM remain external dependencies—rehearse before the event. Avoid `pip install -U` on workshop day.

The ADK loop is limited to eight model calls and 55 seconds; the service timeout is 90 seconds. These are practical demo limits, not spending caps. Deployments use up to two service instances, with scale to zero. Billing can also include model calls, builds, artifact storage and secrets.

## Extensions

After the hour: persist tickets and idempotency records in a database, add authenticated customer ownership checks, store sessions outside the process for multi-turn conversations, and add richer evaluation. None are prerequisites for this lab. A production refund system must validate actual delivery evidence and authorization, rather than trusting the user's reported issue.
