import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from workshop.domain import ProposalSigner, SupportTools, eligibility
from workshop.agent import build_agent, run_agent
from workshop import server

KEY = 'test-key-' + 'a' * 40


from scripts.rehearse_sdk import ScriptedLlm


@pytest.mark.parametrize('order,reason,status', [
    ('KE-1042','damaged','eligible'), ('KE-1042','wrong_item','eligible'),
    ('KE-1043','damaged','outside_window'), ('KE-1044','damaged','not_delivered'),
    ('KE-9999','damaged','not_found'), ('KE-1042','change_of_mind','unsupported_reason'),
])
def test_policy(order, reason, status):
    assert eligibility(order, reason)['status'] == status


def test_approval_token_integrity_and_expiry():
    signer = ProposalSigner(KEY)
    tools = SupportTools(signer)
    tools.propose_refund('KE-1042', 'damaged')
    payload = signer.verify(tools.proposals[0]['token'])
    assert payload['amount_kes'] == 4500
    token = signer.sign({k:v for k,v in payload.items() if k != 'expires_at'}, now=100)
    with pytest.raises(ValueError): signer.verify(token, now=1000)
    with pytest.raises(ValueError): signer.verify('x' + token, now=101)
    tampered = signer.sign({**payload, 'amount_kes': 1}, now=100)
    with pytest.raises(ValueError): signer.verify(tampered, now=101)


def test_model_tools_cannot_bypass_policy_or_execute():
    tools = SupportTools(ProposalSigner(KEY))
    assert not tools.propose_refund('KE-1043','damaged')['eligible']
    assert not tools.proposals
    agent = build_agent(tools, ScriptedLlm())
    assert all('confirm' not in tool.__name__ for tool in agent.tools)


def test_backend_failure_blocks_all_proposals():
    tools = SupportTools(ProposalSigner(KEY), 'lookup_failure')
    assert tools.get_order('KE-1042')['status'] == 'unavailable'
    assert not tools.quote_refund('KE-1042','damaged')['eligible']
    assert tools.propose_refund('KE-1042','damaged')['status'] == 'unavailable'
    assert tools.proposals == []


def test_real_adk_runner_and_tool_schema():
    tools = SupportTools(ProposalSigner(KEY))
    result = asyncio.run(run_agent('Order KE-1042 arrived damaged.', tools, ScriptedLlm()))
    assert [s['name'] for s in result['trace'] if s['type']=='tool_call'] == [
        'get_order','get_refund_policy','quote_refund','propose_refund']
    assert len([s for s in result['trace'] if s['type']=='tool_result']) == 4
    assert result['proposals'][0]['amount_kes'] == 4500
    assert 'token' not in json.dumps(result['trace'])
    assert 'confirm' in result['answer']


def test_confirmation_and_failure_are_application_enforced():
    client = TestClient(server.app)
    tools = SupportTools(server.signer)
    tools.propose_refund('KE-1042','damaged')
    token = tools.proposals[0]['token']
    assert client.post('/api/confirm',json={'token':token,'confirmed':False}).status_code == 422
    assert client.post('/api/confirm',json={'token':'bad','confirmed':True}).status_code == 400
    body = {'token':token,'confirmed':True}
    first = client.post('/api/confirm',json=body).json()
    second = client.post('/api/confirm',json=body).json()
    assert first == second
    assert first['money_moved'] is False
    failure = client.post('/api/confirm',json={**body,'scenario':'commit_failure'})
    assert failure.status_code == 503
    assert 'receipt_id' not in failure.json()


def test_api_validation_and_model_failure(monkeypatch):
    client = TestClient(server.app)
    assert client.get('/healthz').json()['status']=='ok'
    assert client.get('/').status_code==200
    assert client.post('/api/chat',json={'message':''}).status_code==422
    assert client.post('/api/chat',json={'message':'x'*2001}).status_code==422
    async def fail(*args): raise RuntimeError('sensitive provider error')
    monkeypatch.setattr(server, 'run_agent', fail)
    response = client.post('/api/chat',json={'message':'hello'})
    assert response.status_code==502
    assert 'sensitive' not in response.text


def test_api_with_scripted_sdk(monkeypatch):
    real_run = server.run_agent
    async def scripted(message, tools, model):
        return await real_run(message, tools, ScriptedLlm())
    monkeypatch.setattr(server,'run_agent',scripted)
    result = TestClient(server.app).post('/api/chat',json={'message':'KE-1042 damaged'}).json()
    assert len(result['trace'])==8
    assert result['proposals'][0]['order_id']=='KE-1042'


def test_run_call_budget():
    from pydantic import PrivateAttr
    class LoopLlm(BaseLlm):
        model: str = 'test-loop'
        _calls: int = PrivateAttr(default=0)
        async def generate_content_async(self, llm_request, stream=False):
            self._calls += 1
            yield LlmResponse(content=types.Content(role='model',parts=[types.Part(
                function_call=types.FunctionCall(name='get_refund_policy',args={}))]))
    tools=SupportTools(ProposalSigner(KEY))
    model=LoopLlm()
    with pytest.raises(RuntimeError, match='call budget'):
        asyncio.run(run_agent('loop',tools,model))
    assert model._calls == 8
    assert not tools.proposals


def test_api_timeout_and_request_isolation(monkeypatch):
    client=TestClient(server.app)
    async def timeout(*args): raise TimeoutError()
    monkeypatch.setattr(server,'run_agent',timeout)
    assert client.post('/api/chat',json={'message':'hello'}).status_code==504
    one=SupportTools(ProposalSigner(KEY))
    two=SupportTools(ProposalSigner(KEY))
    one.propose_refund('KE-1042','damaged')
    assert not two.proposals
