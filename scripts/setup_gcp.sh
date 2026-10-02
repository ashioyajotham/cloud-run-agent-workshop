#!/usr/bin/env bash
# Facilitator/admin only; run before the workshop in an isolated demo project.
set -euo pipefail
: "${PROJECT_ID:?Set PROJECT_ID to an existing billing-enabled demo project}"
command -v gcloud >/dev/null || { echo 'Install the Google Cloud CLI first.' >&2; exit 1; }
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com aiplatform.googleapis.com secretmanager.googleapis.com --project "$PROJECT_ID"
PROJECT_NUMBER="$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')"
RUNTIME_SA="support-agent-runtime@${PROJECT_ID}.iam.gserviceaccount.com"
if ! gcloud iam service-accounts describe "$RUNTIME_SA" --project "$PROJECT_ID" >/dev/null 2>&1; then
  gcloud iam service-accounts create support-agent-runtime --project "$PROJECT_ID" --display-name='Workshop agent runtime'
fi
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:$RUNTIME_SA" --role=roles/aiplatform.user --condition=None
gcloud projects add-iam-policy-binding "$PROJECT_ID" --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" --role=roles/run.builder --condition=None
if ! gcloud secrets describe workshop-proposal-key --project "$PROJECT_ID" >/dev/null 2>&1; then
  umask 077
  secret_file="$(mktemp)"
  trap 'rm -f "$secret_file"' EXIT
  python3 -c 'import secrets; print(secrets.token_hex(32), end="")' > "$secret_file"
  gcloud secrets create workshop-proposal-key --project "$PROJECT_ID" --replication-policy=automatic --data-file="$secret_file"
fi
gcloud secrets add-iam-policy-binding workshop-proposal-key --project "$PROJECT_ID" --member="serviceAccount:$RUNTIME_SA" --role=roles/secretmanager.secretAccessor --condition=None
echo 'Setup complete. Grant participant deployer roles as documented in docs/cloud-run.md; allow IAM propagation before rehearsal.'
