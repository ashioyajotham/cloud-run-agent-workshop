"""Offline scripted SDK rehearsal. Does NOT call Gemini or evaluate intelligence."""
import asyncio
import json
from pathlib import Path
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import PrivateAttr
from workshop.agent import run_agent
from workshop.domain import ProposalSigner, SupportTools


class ScriptedLlm(BaseLlm):
    model: str = "test-scripted"
    _step: int = PrivateAttr(default=0)

    async def generate_content_async(self, llm_request, stream=False):
        calls = [
            ('get_order', {'order_id': 'KE-1042'}),
            ('get_refund_policy', {}),
            ('quote_refund', {'order_id': 'KE-1042', 'reason': 'damaged'}),
            ('propose_refund', {'order_id': 'KE-1042', 'reason': 'damaged'}),
        ]
        if self._step < len(calls):
            name, args = calls[self._step]
            content = types.Content(role='model', parts=[types.Part(function_call=types.FunctionCall(name=name, args=args))])
        else:
            content = types.Content(role='model', parts=[types.Part(text='[Scripted SDK rehearsal] A KES 4500 demo refund is proposed. Please confirm in the app.')])
        self._step += 1
        yield LlmResponse(content=content)


async def main():
    result = await run_agent('KE-1042 arrived damaged.', SupportTools(ProposalSigner('offline-rehearsal-'+'x'*40)), ScriptedLlm())
    result['mode'] = 'offline_scripted_sdk_rehearsal_not_gemini'
    result['proposals'] = [{k:v for k,v in p.items() if k!='token'} for p in result['proposals']]
    Path('artifacts').mkdir(exist_ok=True)
    Path('artifacts/sdk-rehearsal.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__': asyncio.run(main())
