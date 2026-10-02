import hashlib
import logging
import os
import secrets
from pathlib import Path
from typing import Literal
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from workshop.agent import run_agent
from workshop.domain import ProposalSigner, SupportTools

load_dotenv()
if os.getenv("GEMINI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
    os.environ["GOOGLE_API_KEY"] = os.environ["GEMINI_API_KEY"]
log = logging.getLogger("uvicorn.error")
app = FastAPI(title="From Prompt to Action", version="0.1.0")
key = os.getenv("PROPOSAL_SIGNING_KEY")
if not key:
    if os.getenv("K_SERVICE"):
        raise RuntimeError("Set PROPOSAL_SIGNING_KEY through Secret Manager on Cloud Run")
    key = secrets.token_hex(32)
signer = ProposalSigner(key)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    scenario: Literal["normal", "lookup_failure"] = "normal"


class Confirmation(BaseModel):
    token: str = Field(min_length=1, max_length=2000)
    confirmed: Literal[True]
    scenario: Literal["normal", "commit_failure"] = "normal"


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent.parent / "static" / "index.html")


@app.get("/healthz")
def health():
    return {"status": "ok", "demo_only": True}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    tools = SupportTools(signer, request.scenario)
    try:
        return await run_agent(request.message, tools, model)
    except TimeoutError:
        raise HTTPException(504, "Agent timed out. No demo refund was executed.") from None
    except Exception as exc:
        # Never return SDK errors or credentials to clients, or log prompts/tokens.
        log.warning("agent_failure type=%s", type(exc).__name__)
        raise HTTPException(502, "Agent unavailable. Check model access, configuration and server logs.") from None


@app.post("/api/confirm")
def confirm(request: Confirmation):
    try:
        proposal = signer.verify(request.token)
    except ValueError:
        raise HTTPException(400, "Invalid or expired proposal. Request a new quote.") from None
    if request.scenario == "commit_failure":
        raise HTTPException(503, "Demo refund backend unavailable. No receipt was created.")
    # A deterministic, repeatable receipt; NO database write or money movement.
    receipt_id = "DEMO-" + hashlib.sha256(request.token.encode()).hexdigest()[:12].upper()
    return {"status": "demo_confirmed", "receipt_id": receipt_id, "order_id": proposal["order_id"],
            "amount_kes": proposal["amount_kes"], "currency": "KES", "money_moved": False}
