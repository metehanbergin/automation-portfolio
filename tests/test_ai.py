import json
import httpx
import pytest
from app.ai import draft


def test_disabled_by_default(monkeypatch):
    monkeypatch.delenv('PORTFOLIO_LLM_ENABLED',raising=False)
    with pytest.raises(RuntimeError):draft('qualification','Please clean tomorrow')


@pytest.mark.parametrize('task,output',[
 ('qualification',dict(service='Deep clean',urgency='urgent',summary='Cleaning request',evidence='tomorrow')),
 ('knowledge',dict(question='Where can I store bags?',answer='In the lobby cupboard.',private_data_detected=False,needs_policy_review=False)),
 ('extraction',dict(customer='C101',invoice='INV-1001',amount='1250',currency='USD',reference='BANK-1',missing_fields=[]))])
def test_adapter_contract(monkeypatch,task,output):
    monkeypatch.setenv('PORTFOLIO_LLM_ENABLED','1');monkeypatch.setenv('PORTFOLIO_LLM_BASE_URL','https://model.example.test/v1');monkeypatch.setenv('PORTFOLIO_LLM_MODEL','contract-test')
    def handle(request):
        assert str(request.url)=='https://model.example.test/v1/chat/completions'
        body=json.loads(request.content);assert body['response_format']['type']=='json_object'
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(output)}}]})
    with httpx.Client(transport=httpx.MockTransport(handle)) as client:
        assert draft(task,'Please clean tomorrow',client)==output


def test_model_failure_is_not_empty_success(monkeypatch):
    monkeypatch.setenv('PORTFOLIO_LLM_ENABLED','1');monkeypatch.setenv('PORTFOLIO_LLM_BASE_URL','https://model.example.test/v1');monkeypatch.setenv('PORTFOLIO_LLM_MODEL','test')
    with httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(503))) as client:
        with pytest.raises(httpx.HTTPStatusError):draft('qualification','hello',client)
