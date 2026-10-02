#!/usr/bin/env bash
# Invoke from the repository root. Does not create a project or enable billing.
set -euo pipefail
: "${PROJECT_ID:?Set PROJECT_ID to an existing billing-enabled workshop project}"
REGION="${REGION:-europe-west1}"
SERVICE="${SERVICE:-support-agent-workshop}"
RUNTIME_SA="support-agent-runtime@${PROJECT_ID}.iam.gserviceaccount.com"
command -v gcloud >/dev/null || { echo 'Install the Google Cloud CLI first.' >&2; exit 1; }
# Keep the endpoint private. Use gcloud run services proxy for the browser UI.
gcloud run deploy "$SERVICE" \
  --project "$PROJECT_ID" --region "$REGION" --source . \
  --service-account "$RUNTIME_SA" --no-allow-unauthenticated \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=global,GEMINI_MODEL=${GEMINI_MODEL:-gemini-3.8-flash}" \
  --set-secrets "PROPOSAL_SIGNING_KEY=workshop-proposal-key:1" \
  --memory 512Mi --cpu 1 --concurrency 8 --min-instances 0 --max-instances 2 --timeout 90
