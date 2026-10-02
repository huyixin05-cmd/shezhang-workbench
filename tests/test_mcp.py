import os
import sys
import json
import asyncio
from pathlib import Path
import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_official_mcp_stdio_lists_planning_and_confirmation_tools(tmp_path):
    env=dict(os.environ,TEACH_DATA_DIR=str(tmp_path),PYTHONUTF8='1')
    params=StdioServerParameters(command=sys.executable,args=['-m','teach_agent.mcp_server'],env=env)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            names={t.name for t in tools.tools}
            assert {'prepare_lesson','read_lesson','revise_plan','confirm_and_make','job_status','export_lesson'} <= names
            result=await session.call_tool('confirm_and_make',{'project_id':'x','revision':1,'teacher_confirmed':False})
            assert result.is_error
            assert '明确确认' in result.content[0].text


def payload(result):
    assert not result.is_error, result.content
    return json.loads(result.content[0].text)


@pytest.mark.asyncio
async def test_stdio_cold_start_without_browser_and_shutdown(tmp_path):
    import httpx
    from teach_agent.config import Settings
    # Recover from a stale service address without asking the teacher to start a web page.
    (tmp_path/'server.json').write_text('{"url":"http://127.0.0.1:1"}')
    params=StdioServerParameters(command=sys.executable,args=['-m','teach_agent.mcp_server'],
        env=dict(os.environ,TEACH_DATA_DIR=str(tmp_path),PYTHONUTF8='1'))
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            status=payload(await session.call_tool('environment_status',{}))
            assert status['standalone_export'] is True
            url=json.loads((tmp_path/'server.json').read_text())['url']
            assert url != 'http://127.0.0.1:1'
            assert Settings(tmp_path).token not in json.dumps(status)
    async with httpx.AsyncClient(trust_env=False,timeout=2) as client:
        with pytest.raises(httpx.HTTPError):
            await client.get(url+'/api/status')


@pytest.mark.asyncio
async def test_conversation_prepare_confirm_revise_export_and_reuse(tmp_path):
    from teach_agent.local_runtime import LocalRuntime
    from teach_agent.app import create_app
    from test_api import Provider, checker
    # Real HTTP backend + real stdio MCP; deterministic model/checker isolate orchestration.
    runtime=LocalRuntime(tmp_path,app_factory=lambda root:create_app(root,model=Provider(),checker=checker))
    try:
        url=await runtime.address()
        params=StdioServerParameters(command=sys.executable,args=['-m','teach_agent.mcp_server'],
            env=dict(os.environ,TEACH_DATA_DIR=str(tmp_path),PYTHONUTF8='1'))
        async with stdio_client(params) as (read,write):
            async with ClientSession(read,write) as session:
                await session.initialize()
                async def call(name,**args):
                    return payload(await session.call_tool(name,args))
                initial=await call('prepare_lesson',requirement='让学生看懂力和加速度')
                pid=initial['project']['id']
                ready=await call('wait_for_lesson',job_id=initial['job']['id'])
                assert ready['next_action']=='await_teacher_confirmation'
                assert ready['plan_summary']['difficulty']
                assert ready['plan_summary']['sequence']
                assert not (await call('read_lesson',project_id=pid))['versions']
                changed=await call('revise_plan',project_id=pid,revision=1,changes='先比较再讲解')
                ready=await call('wait_for_lesson',job_id=changed['id'])
                assert ready['plan_summary']['revision']==2
                stale=await session.call_tool('confirm_and_make',dict(project_id=pid,revision=1,teacher_confirmed=True))
                assert stale.is_error
                job=await call('confirm_and_make',project_id=pid,revision=2,teacher_confirmed=True)
                done=await call('wait_for_lesson',job_id=job['id'])
                assert done['next_action']=='export_lesson'
                exported=await call('export_lesson',version_id=done['job']['version_id'])
                assert exported['format']=='html'
                assert '<html' in Path(exported['path']).read_text(encoding='utf-8')
                revision=await call('revise_lesson',project_id=pid,version_id=done['job']['version_id'],changes='字大一点')
                revised=await call('wait_for_lesson',job_id=revision['id'])
                assert revised['job']['status']=='completed'
                assert len((await call('read_lesson',project_id=pid))['versions'])==2
        # Disconnecting the MCP client must not stop a separately owned backend.
        assert await runtime.address()==url
        import httpx
        async with httpx.AsyncClient(trust_env=False) as client:
            assert (await client.get(url+'/api/status',headers={'Authorization':'Bearer '+runtime.settings.token})).status_code==200
    finally:
        await runtime.close()


@pytest.mark.asyncio
async def test_simultaneous_clients_share_one_backend(tmp_path):
    from teach_agent.local_runtime import LocalRuntime
    first,second=LocalRuntime(tmp_path),LocalRuntime(tmp_path)
    try:
        urls=await asyncio.gather(first.address(),second.address())
        assert urls[0]==urls[1]
        owner=first if first.task else second
        guest=second if first.task else first
        await guest.close()
        assert owner.task and not owner.task.done()
    finally:
        await first.close()
        await second.close()


@pytest.mark.asyncio
@pytest.mark.parametrize('kind,expected,suffix',[('animation','video','.mp4'),('combined','zip','.zip')])
async def test_export_chooses_portable_format(tmp_path,monkeypatch,kind,expected,suffix):
    import teach_agent.mcp_server as mcp
    async def request(method,path,body=None,raw=False):
        if raw:
            assert path.endswith('format='+expected)
            return b'portable-content'
        return {'kind':kind}
    monkeypatch.setattr(mcp,'request',request)
    monkeypatch.setattr(mcp,'default_data',lambda:tmp_path)
    result=await mcp.export_lesson('a'*32)
    assert result['format']==expected
    assert Path(result['path']).suffix==suffix
    assert Path(result['path']).read_bytes()==b'portable-content'
