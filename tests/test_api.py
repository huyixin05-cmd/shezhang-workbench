import time
import pytest
from fastapi.testclient import TestClient
from teach_agent.app import create_app

PLAN = dict(title='力与加速度',kind='interactive',grade='高中',objective='观察力与加速度的关系',
    misconception='速度大不等于加速度大',interaction='调整力，比较运动',steps=['观察','改变力','比较'],
    observation='质量相同时力越大加速度越大',check_question='力为零时速度一定为零吗？',assumptions=['忽略摩擦'],components=[])
PAGE = '<!doctype html><html><head><title>力</title></head><body><button id="b">变化</button><output id="o">0</output><script>document.querySelector("#b").onclick=()=>document.querySelector("#o").textContent="1";</script></body></html>'


class Provider:
    async def json(self, messages):
        if 'PLAN_SCHEMA' in messages[0]['content']:
            return dict(PLAN)
        if 'REVIEW_SCHEMA' in messages[0]['content']:
            return dict(passed=True, issues=[])
        return dict(html=PAGE, checks=[dict(action='click',selector='#b',expect_selector='#o',expect_text='1')])


async def checker(path, steps):
    return dict(passed=True, errors=[], steps=len(steps), browser_checked=False)


def wait_job(client, ident):
    for _ in range(200):
        j = client.get('/api/jobs/'+ident).json()
        if j['status'] not in ('queued','running'):
            return j
        time.sleep(.02)
    pytest.fail('job did not finish')


@pytest.fixture
def client(tmp_path):
    app = create_app(tmp_path, model=Provider(), checker=checker)
    with TestClient(app, base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        yield c


def test_authentication_and_cross_origin_rejected(client):
    assert client.get('/api/status',headers={'Authorization':''}).status_code == 401
    assert client.get('/api/status',headers={'Origin':'https://evil.example'}).status_code == 403
    assert client.get('/api/status',headers={'Origin':'null'}).status_code == 403
    assert client.get('/api/status',headers={'Host':'evil.example'}).status_code == 403
    assert client.get('/api/status').status_code == 200


def test_confirmation_then_version_export_and_revision(client):
    result = client.post('/api/projects',json={'request':'让学生看懂力','kind':'interactive'}).json()
    assert wait_job(client,result['job']['id'])['status'] == 'completed'
    pid = result['project']['id']
    p = client.get('/api/projects/'+pid).json()['project']
    assert p['confirmed_revision'] is None
    assert client.post(f'/api/projects/{pid}/confirm',json={'revision':0}).status_code == 409
    job = client.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
    done = wait_job(client,job['id'])
    assert done['status'] == 'completed',done
    vid = done['version_id']
    assert client.get('/api/versions/'+vid+'/download?format=html').status_code == 200
    r = client.post(f'/api/projects/{pid}/revise',json={'version_id':vid,'request':'字大一点'}).json()
    revised = wait_job(client,r['id'])
    assert revised['status'] == 'completed',revised
    assert revised['version_id'] != vid
    assert len(client.get('/api/projects/'+pid).json()['versions']) == 2


def test_plan_edits_invalidate_previous_confirmation(client):
    result = client.post('/api/projects',json={'request':'力','kind':'interactive'}).json()
    wait_job(client,result['job']['id'])
    pid=result['project']['id']
    updated=client.post(f'/api/projects/{pid}/plan',json={'revision':1,'plan':dict(PLAN,title='新的方案')})
    assert updated.status_code==200
    assert client.post(f'/api/projects/{pid}/confirm',json={'revision':1}).status_code==409


def test_config_never_returns_credentials(client):
    r=client.put('/api/settings',json={'base_url':'https://api.example.org/v1','model':'test','api_key':'a-private-key'})
    assert r.status_code==200
    assert 'a-private-key' not in r.text
    assert 'a-private-key' not in client.get('/api/settings').text


def test_no_model_is_an_explicit_error(tmp_path):
    app=create_app(tmp_path,checker=checker)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        r=c.post('/api/projects',json={'request':'力','kind':'interactive'})
        assert r.status_code==400
        assert '模型' in r.json()['detail']


def test_review_issues_cannot_be_marked_as_success(tmp_path):
    class DisagreeingProvider(Provider):
        async def json(self,messages):
            if 'REVIEW_SCHEMA' in messages[0]['content']:
                return {'passed':True,'issues':['合力为零不等于速度为零']}
            return await super().json(messages)
    app=create_app(tmp_path,model=DisagreeingProvider(),checker=checker)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        r=c.post('/api/projects',json={'request':'力'}).json()
        wait_job(c,r['job']['id']);pid=r['project']['id']
        j=c.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
        assert wait_job(c,j['id'])['status']=='failed'
        assert c.get('/api/projects/'+pid).json()['versions']==[]


def test_second_service_cannot_interrupt_live_jobs(tmp_path):
    first=create_app(tmp_path,model=Provider(),checker=checker)
    with TestClient(first,base_url='http://127.0.0.1:8765'):
        second=create_app(tmp_path,model=Provider(),checker=checker)
        with pytest.raises(RuntimeError,match='已在运行'):
            with TestClient(second,base_url='http://127.0.0.1:8766'):
                pass


def test_cancel_in_progress_revision_preserves_existing_version(client):
    import asyncio
    created=client.post('/api/projects',json={'request':'力'}).json()
    wait_job(client,created['job']['id']);pid=created['project']['id']
    j=client.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
    vid=wait_job(client,j['id'])['version_id']
    class Slow:
        async def json(self,messages):
            await asyncio.sleep(60)
    client.app.state.service.model=Slow()
    j=client.post(f'/api/projects/{pid}/revise',json={'version_id':vid,'request':'字大一些'}).json()
    assert client.post('/api/jobs/'+j['id']+'/cancel').status_code==200
    assert wait_job(client,j['id'])['status']=='cancelled'
    assert [v['id'] for v in client.get('/api/projects/'+pid).json()['versions']]==[vid]


def test_scoped_file_access_is_not_a_management_credential(client):
    r=client.post('/api/projects',json={'request':'力'}).json()
    wait_job(client,r['job']['id']);pid=r['project']['id']
    j=client.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
    vid=wait_job(client,j['id'])['version_id']
    access=client.get('/api/versions/'+vid+'/access')
    assert access.status_code==200
    url=access.json()['url']
    response=client.get(url+'?format=html',headers={'Authorization':'','Origin':'null'})
    assert response.status_code==200
    assert response.headers['content-disposition'].startswith('attachment')
    assert client.get('/api/settings',headers={'Authorization':'Bearer '+url.rsplit('/',1)[1]}).status_code==401
    assert client.get('/files/not-a-capability?format=html',headers={'Authorization':''}).status_code==404
