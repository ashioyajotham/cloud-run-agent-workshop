# Compatibility and update policy

Documentation and installed package APIs checked on **2026-10-01**. The repository freezes its environment; it does not assume Google's rolling docs always match a previously installed SDK.

| Component | Selected version/interface | Evidence |
| --- | --- | --- |
| Python | 3.12, tested with 3.12.14 | Local interpreter; Docker major/minor matches |
| Google ADK | 2.10.0 | Installed release; real Runner/tool execution tests |
| Google Gen AI | 2.26.0 | Installed transitive dependency, locked |
| FastAPI | 0.141.1 | Installed, API tests |
| Uvicorn | 0.54.0 | Installed, server startup smoke test |
| Gemini default | `gemini-3.8-flash` | Official stable model listing and Cloud model page |
| Model endpoint | `global` for cloud path | Official model page lists supported location |
| Deployment | `gcloud run deploy --source .` | Official source deployment guide; Dockerfile selected when present |
| Agent execution | `Agent`, `Runner.run_async`, `InMemorySessionService`, `RunConfig(max_llm_calls=8)` | Imported and executed with installed ADK |

The official Cloud documentation lists Gemini 2.5 Flash retirement on October 20, 2026. Developer API availability follows separate policies and may differ. This project defaults to a currently documented stable model instead of copying an old quickstart's model ID.

## Recheck before the event

1. Read the official model page and confirm access with the intended key/cloud project. Run the six-case live evaluation. Documentation does not prove your account has access.
2. Inspect the ADK release notes only if an upgrade is needed. Keep 2.10.0 for the event unless a tested fix requires changing it.
3. Confirm your Cloud SDK supports the script flags: `gcloud run deploy --help`, `gcloud run services proxy --help`, and `gcloud run services logs read --help`.
4. Run the full deployment rehearsal with the exact identity, project, region and network intended for the session.
5. Record the deployed revision, CLI version and live-eval artifact in your own rehearsal notes.

## Deliberate upgrades

```bash
# Replace X.Y.Z with the chosen actual release. Do not use this during the session.
uv add 'google-adk==X.Y.Z'
uv lock
uv sync --frozen
uv run pytest -q
uv run python -m scripts.live_eval
uv export --frozen --no-dev --no-emit-project --no-hashes \
  --format requirements-txt --output-file requirements.txt
```

Review diffs to `pyproject.toml`, `uv.lock` and `requirements.txt`, then redeploy and smoke-test. The Docker base uses `python:3.12-slim`; OS patches can change on a rebuild. This freezes Python dependencies, not a byte-identical image. Pin a verified image digest if exact image reproduction becomes necessary.

## Sources consulted

- [ADK 2.10.0 release](https://pypi.org/project/google-adk/2.10.0/)
- [ADK runtime configuration](https://adk.dev/runtime/runconfig/)
- [ADK event loop](https://github.com/google/adk-docs/blob/main/docs/runtime/event-loop.md)
- [Cloud Run source deployment and IAM](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Cloud Run secret configuration](https://docs.cloud.google.com/run/docs/configuring/services/secrets)
- [Cloud Run private browser access](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [Gemini model listing](https://ai.google.dev/gemini-api/docs/models)
- [Gemini 3.8 Flash Cloud model](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash)
- [Gemini 2.5 Flash Cloud retirement notice](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/2-5-flash)

Some Google Cloud model pages now redirect to Gemini Enterprise Agent Platform URLs. Existing environment variable names and API setup follow the ADK/Cloud Run deployment guide; the package tests validate import compatibility. Live authentication and inference still require rehearsal.
