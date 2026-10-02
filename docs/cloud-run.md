# Cloud Run deployment

Checked against official Google documentation on 2026-10-01. No deployment has been executed from this build environment. Rehearse these commands in the intended account/project.

## Facilitator setup

Use an existing billing-enabled demo project and a current Google Cloud CLI. Sign in with `gcloud auth login`; validate the selected account with `gcloud auth list`. Every script passes the project explicitly.

```bash
export PROJECT_ID='your-demo-project'
export REGION='europe-west1'
bash scripts/setup_gcp.sh
```

The setup script enables Cloud Run, Cloud Build, Artifact Registry, Vertex AI and Secret Manager APIs; creates a dedicated runtime identity; grants it model access; grants the default Compute Engine build identity `roles/run.builder`; and creates version 1 of a random signing-key secret. An administrator must have permission for these changes. If your organization uses a custom build identity, grant `roles/run.builder` to that identity and adjust the deployment flags to match the official source deployment guidance.

Participant/deployer identities need:

| Scope | Role |
| --- | --- |
| Project | `roles/run.sourceDeveloper` |
| Project | `roles/serviceusage.serviceUsageConsumer` |
| Runtime service account | `roles/iam.serviceAccountUser` |
| Deployed service | `roles/run.invoker` for proxy/browser access |
| Project | `roles/logging.viewer` to inspect logs |

The setup script intentionally does not grant participants project-wide Owner or Editor. Have an administrator grant the listed roles before the session. Creating/managing service IAM may require separate administrator assistance; the source developer role alone may not suffice.

The runtime identity needs `roles/aiplatform.user` on the project and `roles/secretmanager.secretAccessor` on the signing-key secret. It does not need Cloud Run deployment roles. Allow IAM propagation before rehearsal.

## Build and deploy

```bash
bash scripts/deploy.sh
```

`gcloud run deploy --source .` uses the checked-in Dockerfile. Cloud Build builds the container and Artifact Registry stores it. Python dependencies come from the frozen export. The Dockerfile runs a non-root user and listens on Cloud Run's `PORT`.

Cloud Run service region defaults to `europe-west1`; model location is `global`, matching current Gemini 3.8 Flash documentation. Set `GEMINI_MODEL` before deployment to override the model ID; verify the replacement's availability and rerun live evaluation. These are distinct locations, not a data-residency guarantee.

The cloud path uses `GOOGLE_GENAI_USE_VERTEXAI=TRUE`, project ID and service identity. Never set `GOOGLE_APPLICATION_CREDENTIALS` in Cloud Run or upload a service-account key. The signing key is mounted as a secret environment variable pinned to version 1. If version 1 is disabled or removed, deployment will fail; rotate deliberately and update the flag. Changing the signing key invalidates outstanding proposals.

## Invoke privately

Stop your local uvicorn process, then:

```bash
gcloud run services proxy support-agent-workshop \
  --project "$PROJECT_ID" --region "$REGION" --port 8080
```

Open http://localhost:8080. The proxy uses your active CLI identity, which needs Cloud Run Invoker. Keep the private-service setting for the lab. Public QR-code access would require a separate access and abuse-control design.

## Smoke test

1. Visit `/healthz` through the proxy.
2. Send KE-1042 damaged and inspect the actual tool trace.
3. Confirm the signed proposal; verify a demo receipt with `money_moved: false`.
4. Test KE-1043, unknown ID, both backend failures, and the policy override.
5. Inspect Cloud Run logs and the deployed revision. The app logs failure types without prompts or tokens. The browser trace is not a distributed tracing implementation.

Useful inspection commands:

```bash
gcloud run services describe support-agent-workshop --project "$PROJECT_ID" --region "$REGION"
gcloud run services logs read support-agent-workshop --project "$PROJECT_ID" --region "$REGION" --limit 30
```

## Common failures

| Symptom | Next check |
| --- | --- |
| Build permission denied | Actual build service account and `roles/run.builder`; deployer source roles |
| Signing secret access denied | Runtime identity's secret accessor role and enabled version 1 |
| Startup failure | Secret exists; signing key is at least 32 characters; container can import installed packages |
| Browser gets 403 | Private service requires authenticated proxy and Invoker permission |
| Agent returns 502 | Model ID, model access, Vertex API, runtime role, quota and error type in logs |
| Local Developer API fails | Key, enabled API access, model access; Vertex flag must be FALSE |
| Cloud build still pending | Use previously deployed demo; inspect build logs after the lab |

## Cleanup

Delete only the workshop service after use:

```bash
gcloud run services delete support-agent-workshop --project "$PROJECT_ID" --region "$REGION"
```

Review and remove workshop-only artifacts, secrets and IAM bindings afterward if no longer needed. Do not delete shared artifact repositories or projects. Builds, artifacts, secrets and model calls can incur charges even when the service scales to zero. Max instances and call limits are not budget caps.

## Official references

- [Deploy from source](https://docs.cloud.google.com/run/docs/deploying-source-code)
- [Configure secrets](https://docs.cloud.google.com/run/docs/configuring/services/secrets)
- [Authenticate developers and proxy private services](https://docs.cloud.google.com/run/docs/authenticating/developers)
- [ADK on Cloud Run](https://docs.cloud.google.com/run/docs/ai/build-and-deploy-ai-agents/deploy-adk-agent)
- [Gemini 3.8 Flash model and locations](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/3-8-flash)
