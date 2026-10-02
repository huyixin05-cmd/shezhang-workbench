import asyncio
import json
import pytest
from fastapi.testclient import TestClient
from teach_agent.app import create_app
from test_api import Provider, checker, wait_job


def serve_host(client,job_id):
    for _ in range(100):
        job=client.get('/api/jobs/'+job_id).json()
        if job['status'] not in ('queued','running'):
            return job
        pending=client.get('/api/host-requests/'+job_id).json()
        if pending:
            result=asyncio.run(Provider().json(pending['messages']))
            response=client.post('/api/host-requests/'+job_id+'/'+pending['id'],json={'result':result})
            assert response.status_code==200,response.text
        else:
            import time
            time.sleep(.02)
    pytest.fail('host job did not finish')


def test_host_mode_needs_no_api_and_preserves_confirmation_and_revision(tmp_path):
    app=create_app(tmp_path,checker=checker)
    with TestClient(app,base_url='http://127.0.0.1',headers={'Authorization':'Bearer '+app.state.settings.token}) as client:
        assert not client.get('/api/status').json()['model']['configured']
        created=client.post('/api/projects',json={'request':'解释力和加速度','generation_mode':'host'}).json()
        assert 'job' in created,created
        pid=created['project']['id']
        assert serve_host(client,created['job']['id'])['status']=='completed'
        assert client.get('/api/projects/'+pid).json()['versions']==[]
        assert client.post('/api/projects/'+pid+'/confirm',json={'revision':0}).status_code==409
        job=client.post('/api/projects/'+pid+'/confirm',json={'revision':1}).json()
        done=serve_host(client,job['id'])
        assert done['status']=='completed',done
        assert client.get('/api/versions/'+done['version_id']+'/download').status_code==200
        edit=client.post('/api/projects/'+pid+'/revise',json={'version_id':done['version_id'],'request':'字大一点'}).json()
        assert serve_host(client,edit['id'])['status']=='completed'
        assert len(client.get('/api/projects/'+pid).json()['versions'])==2
        # The independent web/API path still requires its own configured model.
        assert client.post('/api/projects',json={'request':'另一份课件'}).status_code==400


def test_waiting_host_does_not_block_web_and_web_can_continue_host_project(tmp_path):
    app=create_app(tmp_path,model=Provider(),checker=checker)
    with TestClient(app,base_url='http://127.0.0.1',headers={'Authorization':'Bearer '+app.state.settings.token}) as client:
        host=client.post('/api/projects',json={'request':'对话方案','generation_mode':'host'}).json()
        web=client.post('/api/projects',json={'request':'网页方案'}).json()
        assert wait_job(client,web['job']['id'])['status']=='completed'
        assert client.get('/api/jobs/'+host['job']['id']).json()['status']=='running'
        assert serve_host(client,host['job']['id'])['status']=='completed'
        pid=host['project']['id']
        made=client.post('/api/projects/'+pid+'/confirm',json={'revision':1,'generation_mode':'api'}).json()
        done=wait_job(client,made['id'])
        assert done['status']=='completed',done
        assert done['input']['generation_mode']=='api'
        assert client.get('/api/host-requests/'+made['id']).json() is None


@pytest.mark.asyncio
async def test_host_requests_are_job_bound_single_use_and_cancelled():
    from teach_agent.host_model import HostBroker
    broker=HostBroker(timeout=.1)
    task=asyncio.create_task(broker.ask('job-one',[{'role':'user','content':'test'}]))
    await asyncio.sleep(0)
    pending=broker.pending('job-one')
    with pytest.raises(ValueError):broker.submit('job-two',pending['id'],{})
    broker.submit('job-one',pending['id'],{'ok':True})
    with pytest.raises(ValueError):broker.submit('job-one',pending['id'],{})
    assert await task=={'ok':True}
    assert broker.pending('job-one') is None
    task=asyncio.create_task(broker.ask('job-two',[]))
    await asyncio.sleep(0)
    pending=broker.pending('job-two')
    task.cancel()
    await asyncio.gather(task,return_exceptions=True)
    with pytest.raises(ValueError):broker.submit('job-two',pending['id'],{})
    with pytest.raises(ValueError,match='等待'):
        await broker.ask('job-three',[])


@pytest.mark.asyncio
async def test_animation_worker_bridge_and_mcp_real_image_blocks(tmp_path,monkeypatch):
    import base64
    import httpx
    from teach_agent.local_runtime import LocalRuntime
    from teach_agent.model import Model
    import teach_agent.mcp_server as mcp
    from test_api import PLAN
    from test_animation_workflow import BRIEF
    app=create_app(tmp_path,checker=checker)
    runtime=LocalRuntime(tmp_path,app_factory=lambda root:app)
    monkeypatch.setattr(mcp,'runtime',runtime)
    task=None
    try:
        url=await runtime.address()
        store=app.state.service.store
        p=store.create_project('动画','animation','host')
        store.save_plan(p['id'],dict(PLAN,kind='animation',animation=BRIEF),0)
        store.confirm(p['id'],1)
        job=store.new_job(p['id'],'build',{'revision':1})
        store.update_job(job['id'],status='running')
        config=app.state.service.model_configuration(p,job['id'])
        assert config['base_url'].startswith(url)
        assert not runtime.settings.public()['configured']
        png=base64.b64encode(b'\x89PNG\r\n\x1a\nfixture').decode()
        messages=[{'role':'system','content':'ANIMATION_VISUAL_REVIEW'},
            {'role':'user','content':[{'type':'text','text':'检查画面：frame.png'},
             {'type':'image_url','image_url':{'url':'data:image/png;base64,'+png}}]}]
        class Config:
            def read(self):return config
        task=asyncio.create_task(Model(Config()).json(messages))
        for _ in range(100):
            pending=app.state.service.host.pending(job['id'])
            if pending:break
            await asyncio.sleep(.02)
        assert pending
        blocks=await mcp.get_generation_step(job['id'])
        images=[b for b in blocks.content if b.type=='image']
        assert len(images)==1 and images[0].data==png
        assert config['api_key'] not in blocks.model_dump_json()
        verdict={'status':'needs_repair','defects':['测试缺陷'],'observations':['实际看图'],'evidence':['frame.png']}
        await mcp.submit_generation_step(job['id'],pending['id'],result=verdict)
        assert await task==verdict
        task=asyncio.create_task(Model(Config()).json(messages))
        for _ in range(100):
            pending=app.state.service.host.pending(job['id'])
            if pending:break
            await asyncio.sleep(.02)
        await mcp.submit_generation_step(job['id'],pending['id'],error='当前模型无法查看图片')
        with pytest.raises(ValueError,match='当前模型无法查看图片'):
            await task
        async with httpx.AsyncClient(trust_env=False) as client:
            response=await client.post(config['base_url']+'/chat/completions',json={'messages':messages})
            assert response.status_code==401
        store.update_job(job['id'],status='cancelled')
        async with httpx.AsyncClient(trust_env=False) as client:
            response=await client.post(config['base_url']+'/chat/completions',json={'messages':messages},
                headers={'Authorization':'Bearer '+config['api_key']})
            assert response.status_code==400
    finally:
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task,return_exceptions=True)
        await runtime.close()
