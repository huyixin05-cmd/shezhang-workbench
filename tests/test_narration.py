import io
import json
import math
import struct
import wave

import httpx
import pytest


def wav_bytes(seconds=1):
    target = io.BytesIO()
    with wave.open(target, 'wb') as out:
        out.setparams((1, 2, 24000, 0, 'NONE', ''))
        out.writeframes(b''.join(struct.pack('<h', int(2000*math.sin(i*.1))) for i in range(int(seconds*24000))))
    return target.getvalue()


def test_speech_settings_separate_secret(tmp_path):
    from teach_agent.config import Settings
    settings = Settings(tmp_path)
    public = settings.save(dict(speech_enabled=True, speech_base_url='https://speech.invalid/v1',
        speech_model='voice-model', speech_voice='teacher', speech_api_key='speech-secret'))
    assert public['speech_enabled'] and public['has_speech_key']
    assert 'speech-secret' not in json.dumps(public)
    settings.save({'speech_voice':'other', 'speech_api_key':''})
    assert settings.read()['speech_api_key']=='speech-secret'
    settings.save({'clear_speech_key':True})
    assert not settings.public()['has_speech_key']
    with pytest.raises(ValueError): settings.save({'speech_base_url':'http://external.invalid/v1'})


def test_speech_http_and_measured_duration(tmp_path):
    from teach_agent.narration import SpeechService
    seen=[]
    def handler(request):
        seen.append(json.loads(request.content))
        assert request.url.path=='/v1/audio/speech'
        assert request.headers['authorization']=='Bearer speech-key'
        return httpx.Response(200,content=wav_bytes(1.25))
    service=SpeechService(dict(speech_base_url='https://speech.invalid/v1',speech_model='test',
        speech_voice='teacher',speech_api_key='speech-key',speech_instructions=True), transport=httpx.MockTransport(handler))
    path,duration=service.synthesize('质量不变，再看力。','平静地引导观察',tmp_path)
    assert duration==pytest.approx(1.25,abs=.01) and path.is_file()
    assert 'instructions' in seen[0] and 'speed' not in seen[0]
    service.synthesize('质量不变，再看力。','平静地引导观察',tmp_path)
    assert len(seen)==1


def test_speech_rejects_redirect_and_silent_audio(tmp_path):
    from teach_agent.narration import SpeechService
    config=dict(speech_base_url='https://speech.invalid/v1',speech_model='test',speech_voice='teacher')
    for response in [httpx.Response(302,headers={'location':'https://other.invalid'}),httpx.Response(200,content=b'not audio')]:
        service=SpeechService(config,transport=httpx.MockTransport(lambda _:response))
        with pytest.raises(ValueError): service.synthesize('看看这个小车。','',tmp_path)


def test_timeline_honors_question_pause_and_shot_budget():
    from teach_agent.narration import Delivery, build_timeline
    script=Delivery.model_validate({'beats':[
        dict(shot=0,text='你觉得会怎样？',kind='question',focus='小车停住，等待预测',pause_after=.1),
        dict(shot=0,text='观察速度的变化。',kind='reveal',focus='小车加速',pause_after=.3),
        dict(shot=1,text='质量不变，合力变大，加速度变大。',kind='explain',focus='对比箭头',pause_after=.4)]})
    brief={'duration_seconds':12,'shots':[{'seconds':6},{'seconds':6}]}
    timeline=build_timeline(script,[1,1,3],brief)
    assert timeline['cues'][1]['start']>=3.4
    assert timeline['cues'][2]['start']==pytest.approx(6.4)
    with pytest.raises(ValueError,match='讲稿'): build_timeline(script,[4,4,3],brief)


def test_guard_enforces_cue_order_and_no_missing_cues(tmp_path):
    from teach_agent.narration import guard_source
    class Base:
        time=0
        def setup(self):pass
        def add_sound(self,*a,**k):pass
        def wait(self,duration):self.time+=duration
        def tear_down(self):pass
        def add(self,*a):pass
    class Label:
        def to_corner(self,*a,**k):return self
    timeline={'duration':6,'cues':[{'id':1,'start':.4,'end':1.4,'file':'a.wav'}]}
    scope={'VideoScene':Base,'text_label':lambda *a,**k:Label(),'C_MUTED':'gray','DR':0}
    exec(guard_source(timeline),scope)
    scene=scope['NarratedScene']();scene.setup()
    with pytest.raises(ValueError):scene.tear_down()
    scene.cue(1);assert scene.time==pytest.approx(.4)
    scene.finish_lesson();scene.tear_down()
    assert scene.time==6
    with pytest.raises(ValueError):scene.cue(1)


def test_prepare_rewrites_overlong_script_and_keeps_secrets_out(tmp_path,monkeypatch):
    from teach_agent.narration import prepare_narration
    from test_animation_workflow import BRIEF
    config=dict(speech_enabled=True,speech_base_url='https://speech.invalid/v1',speech_model='teacher',
        speech_voice='warm',speech_api_key='secret-never-export')
    calls=[]
    class Model:
        def json(self,messages):
            assert 'secret-never-export' not in json.dumps(messages)
            if 'TEACHER_DELIVERY_REVIEW' in messages[0]['content']:
                return {'approved':True,'defects':[]}
            calls.append(messages)
            return {'beats':[
                dict(shot=0,text='长讲稿' if len(calls)==1 else '先看变化。',kind='explain',focus='对比两个小车',pause_after=.4),
                dict(shot=1,text='再看合力。',kind='explain',focus='显示合力箭头',pause_after=.4)]}
    def synth(self,text,style,folder):
        folder.mkdir(exist_ok=True)
        path=folder/('long.wav' if text=='长讲稿' else 'short.wav')
        path.write_bytes(wav_bytes(1))
        return path,9 if text=='长讲稿' else 3
    monkeypatch.setattr('teach_agent.narration.SpeechService.synthesize',synth)
    (tmp_path/'video_guard.py').write_text('# helper\n')
    timeline=prepare_narration(tmp_path,{'animation':BRIEF},Model(),config,changes='讲解先让学生观察')
    assert len(calls)==2 and '实测需要' in calls[1][1]['content']
    assert all('讲解先让学生观察' in call[1]['content'] for call in calls)
    assert timeline['cues'][1]['start']==pytest.approx(6.4)
    assert 'NarratedScene' in (tmp_path/'video_guard.py').read_text(encoding='utf-8')
    assert not json.loads((tmp_path/'narration-report.json').read_text(encoding='utf-8'))['listening_reviewed']
    for path in tmp_path.glob('*.json'):assert 'secret-never-export' not in path.read_text(encoding='utf-8')


def test_editable_export_contains_portable_audio(tmp_path):
    from teach_agent.artifacts import bundle
    import zipfile
    for name in ['animation/narration-script.json','animation/narration-timeline.json','animation/speech/cue.wav','animation/private-key.json']:
        path=tmp_path/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text('fixture')
    with zipfile.ZipFile(bundle(tmp_path,tmp_path/'lesson.zip',editable=True)) as archive:
        assert 'animation/speech/cue.wav' in archive.namelist()
        assert 'animation/narration-timeline.json' in archive.namelist()
        assert 'animation/private-key.json' not in archive.namelist()


def test_preview_auth_and_real_pause(tmp_path,monkeypatch):
    from fastapi.testclient import TestClient
    from teach_agent.app import create_app
    app=create_app(tmp_path)
    app.state.settings.save(dict(speech_base_url='https://speech.invalid/v1',speech_model='test',speech_voice='teacher'))
    def synth(self,text,style,folder):
        from pathlib import Path
        path=Path(folder)/'clip.wav';path.write_bytes(wav_bytes(1));return path,1
    monkeypatch.setattr('teach_agent.narration.SpeechService.synthesize',synth)
    with TestClient(app,base_url='http://127.0.0.1') as client:
        assert client.post('/api/speech-preview').status_code==401
        response=client.post('/api/speech-preview',headers={'Authorization':'Bearer '+app.state.settings.token})
        assert response.status_code==200
        with wave.open(io.BytesIO(response.content)) as audio:
            assert audio.getnframes()/audio.getframerate()==4
            audio.setpos(24000)
            assert audio.readframes(48000)==b'\0'*96000


def test_contract_tolerance_cannot_overrun_global_duration():
    from copy import deepcopy
    from test_animation_workflow import BRIEF
    from teach_agent.animation_contract import validate_animation
    from teach_agent.narration import Delivery,build_timeline
    brief=deepcopy(BRIEF);brief['shots'][1]['seconds']=7
    brief=validate_animation(brief)
    script=Delivery.model_validate({'beats':[
        dict(shot=i,text='观察速度变化。',kind='explain',focus='小车向前加速',pause_after=.3) for i in range(2)]})
    with pytest.raises(ValueError,match='讲稿'):build_timeline(script,[5,6.2],brief)
    timeline=build_timeline(script,[3,3],brief)
    assert all(c['end']+c['pause_after']<=12 for c in timeline['cues'])
