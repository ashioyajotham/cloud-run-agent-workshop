"""Deterministic demo policy and signed proposals; no payment integration."""
import base64
import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field

ORDERS = {
    "KE-1042": {"item": "Headphones", "amount_kes": 4500, "days_since_delivery": 3, "status": "delivered"},
    "KE-1043": {"item": "Keyboard", "amount_kes": 6200, "days_since_delivery": 45, "status": "delivered"},
    "KE-1044": {"item": "USB hub", "amount_kes": 1800, "days_since_delivery": 0, "status": "in_transit"},
    "KE-1045": {"item": "Laptop stand", "amount_kes": 3200, "days_since_delivery": 7, "status": "delivered"},
}
POLICY = {"version": "demo-v1", "window_days": 14, "eligible_reasons": ["damaged", "wrong_item"], "currency": "KES"}
STORE_CREDITS = {
    "KE-1042": {"balance_kes": 0, "currency": "KES"},
    "KE-1043": {"balance_kes": 500, "currency": "KES"},
    "KE-1044": {"balance_kes": 0, "currency": "KES"},
    "KE-1045": {"balance_kes": 1500, "currency": "KES"},
}


def eligibility(order_id: str, reason: str) -> dict:
    order = ORDERS.get(order_id)
    if order is None:
        return {"status": "not_found", "eligible": False}
    if order["status"] != "delivered":
        return {"status": "not_delivered", "eligible": False}
    if order["days_since_delivery"] > POLICY["window_days"]:
        return {"status": "outside_window", "eligible": False}
    if reason not in POLICY["eligible_reasons"]:
        return {"status": "unsupported_reason", "eligible": False}
    return {"status": "eligible", "eligible": True, "amount_kes": order["amount_kes"], "currency": "KES"}


class ProposalSigner:
    def __init__(self, key: str):
        if len(key) < 32:
            raise ValueError("PROPOSAL_SIGNING_KEY must contain at least 32 characters")
        self.key = key.encode()

    def sign(self, proposal: dict, now: int | None = None) -> str:
        payload = {**proposal, "expires_at": (int(time.time()) if now is None else now) + 900}
        raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        encoded = base64.urlsafe_b64encode(raw).decode().rstrip("=")
        signature = hmac.new(self.key, encoded.encode(), hashlib.sha256).hexdigest()
        return encoded + "." + signature

    def verify(self, token: str, now: int | None = None) -> dict:
        try:
            encoded, signature = token.split(".")
            expected = hmac.new(self.key, encoded.encode(), hashlib.sha256).hexdigest()
            if not hmac.compare_digest(signature, expected):
                raise ValueError("invalid signature")
            payload = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
            if payload["expires_at"] <= (int(time.time()) if now is None else now):
                raise ValueError("expired proposal")
            quote = eligibility(payload["order_id"], payload["reason"])
            if not quote["eligible"] or payload["amount_kes"] != quote["amount_kes"]:
                raise ValueError("proposal does not match policy")
            if payload["policy_version"] != POLICY["version"]:
                raise ValueError("policy changed")
            return payload
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("invalid proposal") from exc


@dataclass
class SupportTools:
    signer: ProposalSigner
    scenario: str = "normal"
    proposals: list[dict] = field(default_factory=list)

    def get_order(self, order_id: str) -> dict:
        """Look up a demo order by exact ID, for example KE-1042."""
        if self.scenario == "lookup_failure":
            return {"status": "unavailable", "retryable": False, "message": "Order backend is unavailable. Escalate; do not guess."}
        order = ORDERS.get(order_id)
        return {"status": "found", "order_id": order_id, **order} if order else {"status": "not_found"}

    def get_refund_policy(self) -> dict:
        """Read the demo refund policy before quoting a refund."""
        return dict(POLICY)

    def quote_refund(self, order_id: str, reason: str) -> dict:
        """Check eligibility deterministically. Reasons: damaged or wrong_item."""
        if self.scenario == "lookup_failure":
            return {"status": "unavailable", "eligible": False}
        return eligibility(order_id, reason)

    def propose_refund(self, order_id: str, reason: str) -> dict:
        """Create a demo proposal for human confirmation. Never executes a refund."""
        if self.scenario == "lookup_failure":
            return {"status": "unavailable"}
        quote = eligibility(order_id, reason)
        if not quote["eligible"]:
            return quote
        proposal = {"order_id": order_id, "reason": reason, "amount_kes": quote["amount_kes"], "currency": "KES", "policy_version": POLICY["version"]}
        signed = {**proposal, "token": self.signer.sign(proposal)}
        # Keep the token out of model context; the app exposes a trusted confirmation button.
        if not any(p["order_id"] == order_id for p in self.proposals):
            self.proposals.append(signed)
        return {"status": "awaiting_confirmation", **proposal}

    def get_store_credit(self, order_id: str) -> dict:
        """Check the store credit balance associated with a demo order.

        Use this when a customer asks about existing credit, or before proposing
        a cash refund to see if partial store credit applies. Returns the balance
        in KES; a zero balance means no credit is available.
        """
        if self.scenario == "lookup_failure":
            return {"status": "unavailable", "retryable": False, "message": "Credit backend is unavailable. Escalate; do not guess."}
        credit = STORE_CREDITS.get(order_id)
        if credit is None:
            return {"status": "not_found", "balance_kes": 0, "currency": "KES"}
        return {"status": "found", "order_id": order_id, **credit}
