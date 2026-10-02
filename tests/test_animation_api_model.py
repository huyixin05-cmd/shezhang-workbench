import base64
import json
import sys
from pathlib import Path
import httpx
import pytest
from test_animation_workflow import BRIEF, SCENE


def test_animation_uses_shared_model_without_cli(monkeypatch):
    from teach_agent.animation_workflow import workflow_configuration
    monkeypatch.setattr('shutil.which',lambda _: None)
    result=workflow_configuration({'manim_python':sys.executable,'base_url':'https://model.invalid/v1',
        'model':'teacher-model','api_key':'private-test-key','animation_model':'obsolete-cli-model'})
    assert result['model']=='teacher-model'
    assert result['base_url']=='https://model.invalid/v1'
    assert 'codex' not in result


def test_runtime_only_checks_manim(monkeypatch):
    from types import SimpleNamespace
    from teach_agent.animation_worker import check_runtime
    calls=[]
    def run(command,**kwargs):
        calls.append(command)
        assert command[0]==sys.executable and command[1]=='-c'
        return SimpleNamespace(returncode=0,stdout='0.20.1',stderr='')
    monkeypatch.setattr('teach_agent.animation_worker.subprocess.run',run)
    assert check_runtime({'manim_python':sys.executable})['manim']=='0.20.1'
    assert len(calls)==1


def test_program_writes_scene_and_repairs_through_model_api(tmp_path):
    from teach_agent.animation_pipeline import AnimationPipeline
    calls=[]
    class Model:
        def json(self,messages):
            calls.append(messages)
            if 'ANIMATION_DOSSIER' in messages[0]['content']:
                return {'relations':['v 与 Δv 是不同量'],'assumptions':['理想直线运动'],'pitfalls':['不要比较末速度大小']}
            return {'scene_spec':{'summary':'小车对比'},'code':SCENE}
    (tmp_path/'approved_plan.json').write_text(json.dumps({'title':'小车对比','animation':BRIEF}))
    (tmp_path/'video_guard.py').write_text('# fixed helper')
    (tmp_path/'VIDEO_WORKFLOW.md').write_text('检查可读性',encoding='utf-8')
    (tmp_path/'runtime.json').write_text('{}')
    (tmp_path/'previous_sol_scene.py').write_text('# previous scene')
    pipeline=AnimationPipeline(Model())
    pipeline.run(tmp_path,{'changes':'第二段放慢'})
    assert (tmp_path/'sol_scene.py').read_text()==SCENE
    assert len(calls)==2
    assert 'previous scene' in calls[-1][1]['content']
    assert '第二段放慢' in calls[-1][1]['content']
    pipeline.run(tmp_path,{'changes':'第二段放慢'},from_stage='scene-composer',feedback={'scene-composer':'文字重叠'})
    assert len(calls)==3 and '文字重叠' in calls[-1][1]['content']
    assert json.loads((tmp_path/'05_shot_list.json').read_text(encoding='utf-8'))['shots']==BRIEF['shots']


def test_review_sends_real_images_to_configured_api(tmp_path,monkeypatch):
    from teach_agent.animation_worker import visual_review
    frame=tmp_path/'frame.png';frame.write_bytes(b'\x89PNG\r\n\x1a\nfixture')
    (tmp_path/'sol_scene.py').write_text(SCENE)
    config={'base_url':'https://model.invalid/v1','model':'vision-model','api_key':'secret-test-key'}
    def handler(request):
        payload=json.loads(request.content)
        assert payload['model']=='vision-model'
        assert request.headers['authorization']=='Bearer secret-test-key'
        content=payload['messages'][-1]['content']
        pictures=[item['image_url']['url'] for item in content if item['type']=='image_url']
        assert base64.b64decode(pictures[0].split(',')[1])==frame.read_bytes()
        review=dict(status='approved',defects=[],observations=['画面有两个小车'],evidence=['frame.png'])
        return httpx.Response(200,json={'choices':[{'message':{'content':json.dumps(review)}}]})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    assert visual_review(tmp_path,{'animation':BRIEF},config,[frame],'preview-0')['status']=='approved'
    assert not any('secret-test-key' in p.read_text(errors='ignore') for p in tmp_path.rglob('*') if p.is_file())


def test_malformed_scene_cannot_write_arbitrary_model_paths(tmp_path):
    from teach_agent.animation_pipeline import AnimationPipeline
    class BadModel:
        def json(self,messages):return {'scene_spec':{},'code':'','path':'../escape.py'}
    for name,value in [('approved_plan.json',{'animation':BRIEF}),('04_math_dossier.json',{'relations':['x']})]:
        (tmp_path/name).write_text(json.dumps(value))
    (tmp_path/'video_guard.py').write_text('# helper');(tmp_path/'VIDEO_WORKFLOW.md').write_text('guide')
    (tmp_path/'runtime.json').write_text('{}')
    with pytest.raises(ValueError):AnimationPipeline(BadModel()).run(tmp_path,{},from_stage='scene-composer')
    assert not (tmp_path/'sol_scene.py').exists()


def test_image_rejection_is_explicit_not_a_text_only_fallback(tmp_path,monkeypatch):
    from teach_agent.animation_worker import visual_review
    from teach_agent.model import ModelServiceError
    frame=tmp_path/'frame.png';frame.write_bytes(b'frame')
    (tmp_path/'sol_scene.py').write_text(SCENE)
    calls=[]
    def handler(request):
        calls.append(json.loads(request.content))
        return httpx.Response(400,json={'error':'image not supported'})
    original=httpx.AsyncClient
    monkeypatch.setattr(httpx,'AsyncClient',lambda **kw:original(transport=httpx.MockTransport(handler),**kw))
    with pytest.raises(ModelServiceError,match='图片输入'):
        visual_review(tmp_path,{'animation':BRIEF},{'base_url':'https://model.invalid/v1','model':'text-only'},[frame],'preview')
    assert len(calls)==1
    assert not (tmp_path/'review.json').exists()


def test_animation_runtime_does_not_import_cli_modules():
    import subprocess
    result=subprocess.run([sys.executable,'-c',
        'import sys; import teach_agent.animation_worker; assert "sol.client" not in sys.modules; assert "sol.staged" not in sys.modules'],
        capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_old_animation_plans_remain_readable():
    from teach_agent.animation_contract import validate_animation
    assert validate_animation(dict(BRIEF,workflow='sol'))['shots']==BRIEF['shots']


def test_api_settings_hide_and_remove_obsolete_cli_configuration(tmp_path):
    from teach_agent.config import Settings
    settings=Settings(tmp_path)
    settings.path.write_text(json.dumps({'animation_codex':'old.exe','animation_model':'old-model'}))
    assert 'animation_codex' not in settings.public() and 'animation_model' not in settings.public()
    settings.save({'base_url':'https://model.invalid/v1','model':'one-model'})
    assert 'animation_codex' not in settings.read()
