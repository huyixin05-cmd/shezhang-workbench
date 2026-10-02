from copy import deepcopy
import json
from pathlib import Path
import pytest
from pydantic import ValidationError

BRIEF = dict(workflow='manim',duration_seconds=12,aspect_ratio='16:9',shots=[
    dict(title='比较运动',visual='并排的匀速与加速小车',motion='小车向右运动并显示等时间位置',explanation='比较相同时间内的位移变化',seconds=6),
    dict(title='解释差别',visual='对应的位置与速度读数',motion='逐步出现速度增量与结论',explanation='速度与速度变化是不同的量',seconds=6)])


def test_general_storyboard_and_duration_validation():
    from teach_agent.animation_contract import AnimationBrief
    assert AnimationBrief.model_validate(BRIEF).shots[0].title=='比较运动'
    bad=deepcopy(BRIEF);bad['duration_seconds']=80
    with pytest.raises(ValidationError): AnimationBrief.model_validate(bad)


def test_review_requires_inspected_frames_and_no_defects(tmp_path):
    from teach_agent.animation_workflow import validate_visual_review
    frame=tmp_path/'review_frames/f1.png';frame.parent.mkdir();frame.write_bytes(b'frame')
    review=dict(status='approved',defects=[],observations=['文字完整'],evidence=['review_frames/f1.png'])
    assert validate_visual_review(review,tmp_path,[frame])
    for changes in [dict(defects=['公式被截断']),dict(evidence=[]),dict(evidence=['../outside.png'])]:
        with pytest.raises(ValueError):validate_visual_review(dict(review,**changes),tmp_path,[frame])


def test_result_paths_cannot_escape_owned_folder(tmp_path):
    from teach_agent.animation_workflow import owned_file
    outside=tmp_path/'outside.mp4';outside.write_bytes(b'x');root=tmp_path/'run';root.mkdir()
    with pytest.raises(ValueError):owned_file(root,'../outside.mp4')
    with pytest.raises(ValueError):owned_file(root,str(outside.resolve()))


def test_missing_workflow_runtime_is_clear():
    from teach_agent.animation_workflow import workflow_configuration
    with pytest.raises(ValueError,match='Manim'):workflow_configuration({'manim_python':'Z:/no-such-python.exe'})


def test_animation_project_export_includes_editable_sources_not_traces(tmp_path):
    from teach_agent.artifacts import bundle
    import zipfile
    for name in ['plan.json','source.json','animation/sol_scene.py','animation/05_shot_list.json',
                 'animation/review.json','animation/validation.json','animation/review_frames/f1.png','animation/stages/01-intent.jsonl']:
        p=tmp_path/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('test')
    with zipfile.ZipFile(bundle(tmp_path,tmp_path/'out.zip',editable=True)) as z:
        assert 'animation/sol_scene.py' in z.namelist()
        assert 'animation/05_shot_list.json' in z.namelist()
        assert 'animation/validation.json' in z.namelist()
        assert 'animation/review_frames/f1.png' in z.namelist()
        assert 'animation/stages/01-intent.jsonl' not in z.namelist()


SCENE = '''from manim import *
from video_guard import VideoScene, ZH_FONT
class LessonScene(VideoScene):
    def construct(self):
        self.add(Circle())
        self.wait(12)
'''


class FixedPipeline:
    def __init__(self): self.calls=[]
    def run(self,work,request,**kwargs):
        from teach_agent.animation_validation import ARTIFACT_NAMES
        self.calls.append(kwargs)
        for name in ARTIFACT_NAMES:
            (work/name).write_text(SCENE if name.endswith('.py') else '{"fixture":true}',encoding='utf-8')


def worker_fixture(tmp_path,monkeypatch):
    import teach_agent.animation_worker as worker
    (tmp_path/'approved_plan.json').write_text(json.dumps({'animation':BRIEF}),encoding='utf-8')
    pipeline=FixedPipeline();renders=[]
    def render(work,python,scene,quality,brief,attempt):
        renders.append((quality,attempt))
        video=work/f'{quality}-{attempt}.mp4';video.write_bytes(b'x'*2048)
        frame=work/f'{quality}-{attempt}.png';frame.write_bytes(b'frame')
        return video,[frame],{'duration':12,'width':854,'height':480}
    def review(work,plan,config,frames,tag):
        return dict(status='approved',defects=[],observations=['小车与读数可见'],evidence=[p.name for p in frames])
    return worker,pipeline,renders,render,review


def test_worker_repairs_failed_preview_and_checks_new_final(tmp_path,monkeypatch):
    worker,pipeline,renders,render,review=worker_fixture(tmp_path,monkeypatch)
    def reject_first(work,plan,config,frames,tag):
        if tag=='preview-0':raise ValueError('读数超出画面')
        return review(work,plan,config,frames,tag)
    result=worker.produce(tmp_path,{'manim_python':'fixture'},pipeline=pipeline,renderer=render,
        reviewer=reject_first,preflight=lambda _: {})
    assert result['passed'] and result['video_path']=='m-1.mp4'
    assert renders==[('l',0),('l',1),('m',1)]
    assert pipeline.calls[1]['from_stage']=='scene-composer'
    assert '读数超出画面' in pipeline.calls[1]['feedback']['scene-composer']


def test_review_cannot_modify_scene_after_render(tmp_path,monkeypatch):
    worker,pipeline,renders,render,review=worker_fixture(tmp_path,monkeypatch)
    def mutating_review(work,plan,config,frames,tag):
        (work/'sol_scene.py').write_text(SCENE+'\n# changed after render',encoding='utf-8')
        return review(work,plan,config,frames,tag)
    with pytest.raises(ValueError,match='复核期间'):
        worker.produce(tmp_path,{'manim_python':'fixture'},pipeline=pipeline,renderer=render,
            reviewer=mutating_review,preflight=lambda _: {})
    assert not (tmp_path/'worker-result.json').exists()


def test_review_service_failure_does_not_regenerate_scene(tmp_path,monkeypatch):
    from teach_agent.model import ModelServiceError
    worker,pipeline,renders,render,review=worker_fixture(tmp_path,monkeypatch)
    def unavailable(*args):raise ModelServiceError('模型输出被截断')
    with pytest.raises(ModelServiceError):
        worker.produce(tmp_path,{'manim_python':'fixture'},pipeline=pipeline,renderer=render,
            reviewer=unavailable,preflight=lambda _: {})
    assert len(pipeline.calls)==1
    assert renders==[('l',0)]


def test_missing_shared_model_is_clear():
    import sys
    from teach_agent.animation_workflow import workflow_configuration
    with pytest.raises(ValueError,match='模型地址'):
        workflow_configuration({'manim_python':sys.executable})


def test_animation_api_confirmation_and_revision(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from teach_agent.app import create_app
    from test_api import PLAN,Provider,wait_job
    from pedagogy_fixture import DESIGN
    class AnimationProvider(Provider):
        async def json(self,messages):
            if 'PLAN_SCHEMA' in messages[0]['content']:
                return dict(PLAN,title='速度与速度变化',kind='animation',animation=BRIEF,learning_design=DESIGN)
            return await super().json(messages)
    calls=[]
    async def produce(plan,folder,config,progress,previous=None,changes=None):
        calls.append((previous,changes));(folder/'index.html').write_text('<html>fixture</html>')
        return {'animation':BRIEF},{'passed':True,'workflow':'sol'}
    monkeypatch.setattr('teach_agent.animation_workflow.run_animation_workflow',produce)
    monkeypatch.setattr('teach_agent.animation_workflow.workflow_configuration',lambda _: {})
    app=create_app(tmp_path,model=AnimationProvider())
    with TestClient(app,base_url='http://127.0.0.1:8765',headers={'Authorization':'Bearer '+app.state.settings.token}) as c:
        result=c.post('/api/projects',json={'request':'解释速度与速度变化','kind':'animation'}).json()
        assert wait_job(c,result['job']['id'])['status']=='completed'
        assert calls==[]
        pid=result['project']['id']
        job=c.post(f'/api/projects/{pid}/confirm',json={'revision':1}).json()
        done=wait_job(c,job['id']);assert done['status']=='completed',done
        job=c.post(f'/api/projects/{pid}/revise',json={'version_id':done['version_id'],'request':'第二段慢一点'}).json()
        revised=wait_job(c,job['id']);assert revised['status']=='completed',revised
        assert len(c.get('/api/projects/'+pid).json()['versions'])==2
        assert calls[1][0].is_dir() and calls[1][1]=='第二段慢一点'


@pytest.mark.parametrize('parent_exits',[False,True])
def test_process_tree_closes_descendants_even_after_parent_exit(parent_exits):
    import subprocess,sys,time
    from teach_agent.process_tree import ProcessTree
    child='import time;print("ready",flush=True);time.sleep(60)'
    parent='import subprocess,sys,time;subprocess.Popen([sys.executable,"-c",'+repr(child)+']);'+('' if parent_exits else 'time.sleep(60)')
    started=time.monotonic()
    with ProcessTree([sys.executable,'-c',parent],stdout=subprocess.PIPE) as process:
        assert process.stdout.readline().strip()==b'ready'
        if parent_exits: process.wait(timeout=5)
    assert process.stdout.read()==b''
    assert time.monotonic()-started<5


@pytest.mark.parametrize('source',[
    'reader = open\nreader("outside")',
    'from numpy.ctypeslib import load_library',
    'from manim import os as helper',
    'from manim import config\nconfig.media_dir = "outside"',
    'from manim import config\nconfig["media_dir"] = "outside"',
    'from manim import config\nconfig.update({"media_dir":"outside"})',
])
def test_scene_rejects_simple_alias_and_config_bypasses(source):
    from teach_agent.animation_rendering import inspect_source
    with pytest.raises(ValueError):inspect_source(source)
