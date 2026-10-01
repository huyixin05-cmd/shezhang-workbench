import httpx
import pytest
from teach_agent.config import Settings
from teach_agent.model import Model


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
