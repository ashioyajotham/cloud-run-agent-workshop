# Facilitator guide — Victor Ashioya Jotham

Session: **From Prompt to Action: Build and Deploy an AI Agent on Cloud Run**. Planned duration: 60 minutes, based on the supplied 10:15–11:15 Kai slot. Confirm the final organizer schedule and whether the Agent Studio listing can be replaced by this code-first lab.

## Before the room

Ask organizers for participant skill level, laptop expectations, project/credits arrangement, network quality and model access. Use an isolated demo project. Resolve setup and IAM at least one day beforehand; give IAM propagation time. Install frozen dependencies, run the real model evaluation and deploy once. Prepare a second working service as backup if useful. Do not upgrade the SDK or change model on the morning of the event.

Keep the repo available ahead of time. Participants edit the delivery-status tool and agent instruction; the facilitator teaches deployment and confirmation through the existing implementation. This scope avoids spending the hour typing boilerplate.

## Run of show

| Minutes | Activity | Teaching cue |
| --- | --- | --- |
| 0–5 | Demo KE-1042; pause before confirmation | “It proposed a refund. What evidence tells us anything actually happened?” |
| 5–15 | Trace and inspect Python tools | Goal, model decision, tool execution, observation, next decision |
| 15–25 | Participants add delivery-status tool | Types and docstrings are an interface, not decoration |
| 25–30 | Inspect the confirmation endpoint | Model instructions guide; code enforces |
| 30–42 | Deploy and open through authenticated proxy | Cloud Run hosts the runtime; Gemini supplies inference |
| 42–53 | Break the backend and challenge policy | A fluent answer is not evidence of a successful action |
| 53–60 | Discuss extensions and questions | Session storage, customer auth, real idempotency, evaluation |

## Opening script

“Today we’ll give a model tools, deploy the application, and see what happens when things go wrong. In our shop, it can inspect an order, check a policy and propose a refund. We’ll watch the actual tool calls. Then we’ll decide which actions the model should never be able to authorize by itself.”

Spend at most five minutes on definitions. An LLM answering a prompt is not enough for this lab's agent pattern: the model must choose tools and react to their results. Fixed workflows and agents can coexist; deterministic refund policy stays outside the model.

## Main demo

1. Run KE-1042 damaged; inspect order, policy, quote and proposal.
2. Point to the signed proposal coming from the server, rather than parsing model prose.
3. Confirm; explain that this only creates a repeatable demo receipt, with no ledger or money movement.
4. Run KE-1043 damaged; inspect why code refuses the proposal.
5. Toggle order backend unavailable; run KE-1042 again. Ask the room to identify any invented claim.
6. Restore order backend. Make a new proposal; toggle confirmation backend unavailable; confirm and show failure.

## Recovery plan

If a participant cannot deploy, continue locally and pair them with a participant who can. If a build takes longer than eight minutes, show the previously deployed revision and inspect the pending build afterward. If live model access fails, use the offline SDK rehearsal trace via `uv run python -m scripts.rehearse_sdk`; explicitly call it a scripted integration rehearsal, not a Gemini result. Use it to teach tool execution while troubleshooting access.

## Answers to expect

- **Why Cloud Run?** Request-driven container hosting with autoscaling; the framework and model are separate choices.
- **Why no multi-agent system?** One agent and four tools solve this bounded task. Delegation would add coordination without a clear payoff here.
- **Is this production-ready?** No. It deliberately omits persistent tickets, real refunds and customer ownership checks. The application confirmation gate and deterministic policy are useful building blocks.
- **Why no multi-turn chat?** Fresh sessions keep this lab independent of container-local session state. Multi-turn production work needs an external session store.
- **Does eight calls cap spending?** No. It bounds one run, not the number of requests or total tokens.
- **Does the trace show reasoning?** It shows observable calls/results, not private model thought.
