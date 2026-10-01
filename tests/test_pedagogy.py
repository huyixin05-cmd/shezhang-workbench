from copy import deepcopy
import json
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError
from teach_agent.app import create_app
from teach_agent.model import Plan, ModelOutputError
from test_api import PLAN, Provider, checker, wait_job

from pedagogy_fixture import DESIGN


def test_design_is_structured_and_old_plans_remain_readable():
    assert Plan.model_validate(PLAN)
    raw=dict(PLAN,learning_design=DESIGN)
    p=Plan.model_validate(raw)
    assert p.learning_design.sequence[0].action
    assert p.steps==['先暴露直觉','对比速度变化']
    bad=deepcopy(raw);bad['learning_design']['sequence'][0]['observation']=' '
    with pytest.raises(ValidationError): Plan.model_validate(bad)


def test_actual_model_inputs_use_selected_sources_and_teaching_review(tmp_path):
    class Recording(Provider):
        def __init__(self): self.calls=[]
        async def json(self,messages):
            self.calls.append(deepcopy(messages))
            if 'PLAN_SCHEMA' in messages[0]['content']:
                return dict(PLAN,learning_design=DESIGN)
            return await super().json(messages)
    model=Recording();app=create_app(tmp_path,model=model,checker=checker)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        result=c.post('/api/projects',json={'request':'讲清楚速度和加速度'}).json()
        assert wait_job(c,result['job']['id'])['status']=='completed'
        assert len(model.calls)==2  # design + separate pedagogy review
        assert 'PLAN_REVIEW_SCHEMA' in model.calls[1][0]['content']
        schema=Plan.model_json_schema()['$defs']['LearningDesign']
        assert 'evidence' not in schema['properties'] and 'basis' not in schema['properties']
        assert all(key in schema['required'] for key in ('request_analysis','difficulty_reason','design_response'))
        j=c.post('/api/projects/'+result['project']['id']+'/confirm',json={'revision':1}).json()
        assert wait_job(c,j['id'])['status']=='completed'
        build=model.calls[2][0]['content']
        assert 'Every step changes visible state.' in build
        assert 'Style Fidelity Contract' in build
        assert 'Tone & rules' in build
        assert 'bank-transactions' not in build and 'love-romance-3d' not in build
        data=json.loads(model.calls[2][1]['content'])
        assert data['plan']['learning_design']['sequence'][0]['action']==DESIGN['sequence'][0]['action']
        assert data['plan']['learning_design']['request_analysis']==DESIGN['request_analysis']
        report=c.get('/api/projects/'+result['project']['id']).json()['versions'][0]['report']
        assert len(report['prompt_sources'])==3


def test_failed_teaching_review_does_not_replace_prior_plan(tmp_path):
    class Failing(Provider):
        def __init__(self): self.reviews=0
        async def json(self,messages):
            if 'PLAN_SCHEMA' in messages[0]['content']:return dict(PLAN,learning_design=DESIGN)
            self.reviews+=1
            return {'passed':False,'issues':['操作顺序不能验证学习目标']}
    app=create_app(tmp_path,model=Failing(),checker=checker)
    store=app.state.service.store
    p=store.create_project('速度与加速度','interactive');store.save_plan(p['id'],PLAN,0)
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        job=c.post('/api/projects/'+p['id']+'/rethink',json={'revision':1,'request':'补齐教学设计'}).json()
        assert wait_job(c,job['id'])['status']=='failed'
        assert store.project(p['id'])['plan_revision']==1
        assert app.state.service.model.reviews==2


def test_malformed_plan_output_is_repaired_but_transport_error_is_not(tmp_path):
    class Broken(Provider):
        def __init__(self,error): self.error=error;self.calls=0
        async def json(self,messages):
            self.calls+=1
            if self.calls==1: raise self.error
            return await super().json(messages)
    for name,error,expected,calls in [('output',ModelOutputError('invalid JSON'),'completed',3),
                                      ('transport',ValueError('无法连接模型服务'),'failed',1)]:
        provider=Broken(error);app=create_app(tmp_path/name,model=provider,checker=checker)
        with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
            r=c.post('/api/projects',json={'request':'解释速度和加速度'}).json()
            assert wait_job(c,r['job']['id'])['status']==expected
            assert provider.calls==calls


def test_selected_prompt_files_match_pinned_source_manifest():
    from teach_agent.prompt_sources import ROOT, prompt_sources, selected_rules
    manifest=json.loads((ROOT/'SOURCES.json').read_text(encoding='utf-8'))
    assert manifest['runtime_sources']==prompt_sources('build')
    assert (ROOT/'LICENSE').is_file()
    selected=selected_rules('build')
    assert 'fonts.googleapis.com' not in selected and 'Accent is brand orange' not in selected
    assert 'Use the spacing scale' in selected
