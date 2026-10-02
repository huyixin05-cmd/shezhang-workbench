import httpx
import pytest
from teach_agent.config import Settings
from teach_agent.model import Model
from teach_agent.model import ModelServiceError


@pytest.mark.asyncio
@pytest.mark.parametrize('payload,expected',[
    ({'choices':[{'finish_reason':'stop','message':{'content':'{"title":"test"}'}}]},None),
    ({'choices':[{'finish_reason':'length','message':{'content':'{"title":'}}]},'截断'),
    ({'choices':[{'message':{'content':'not-json'}}]},'JSON'),
    ({'error':'bad upstream'},'不兼容'),
])
async def test_chat_completions_contract(tmp_path,monkeypatch,payload,expected):
    settings=Settings(tmp_path)
    settings.save(dict(base_url='https://model.invalid/v1',model='test-model',api_key='local-test-key'))
    def handler(request):
        assert str(request.url)=='https://model.invalid/v1/chat/completions'
        assert request.headers['authorization']=='Bearer local-test-key'
        return httpx.Response(200,json=payload)
    real_client=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:real_client(transport=httpx.MockTransport(handler),**kw))
    if expected:
        with pytest.raises(ValueError,match=expected):
            await Model(settings).json([{'role':'user','content':'test'}])
    else:
        assert await Model(settings).json([{'role':'user','content':'test'}])=={'title':'test'}


@pytest.mark.asyncio
@pytest.mark.parametrize('payload',[
    {'choices':[{'finish_reason':'length','message':{'content':'{"status":'}}]},
    {'error':'provider returned incompatible success response'},
])
async def test_protocol_and_output_limit_are_service_errors(tmp_path,monkeypatch,payload):
    settings=Settings(tmp_path);settings.save({'base_url':'https://model.invalid/v1','model':'fixture'})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(lambda _:httpx.Response(200,json=payload)),**kw))
    with pytest.raises(ModelServiceError):await Model(settings).json([{'role':'user','content':'test'}])
