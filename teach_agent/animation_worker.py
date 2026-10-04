"""Program-owned model API, Manim rendering and visual-review worker."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .animation_contract import validate_animation
from .animation_rendering import inspect_source,render_scene
from .animation_workflow import ROOT,owned_file,validate_visual_review
from .animation_pipeline import AnimationPipeline,APIModel,review_frames,write_json
from .animation_validation import validate_run
from .model import ModelServiceError


def progress(work,message):write_json(work/'progress.json',{'stage':message})


def check_runtime(config):
    version=subprocess.run([config['manim_python'],'-c','import manim,av;print(manim.__version__)'],
        capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    if version.returncode:raise ValueError('所选 Python 无法加载 Manim，请选择已有 Manim 环境')
    return {'manim':version.stdout.strip(),'latex_available':bool(shutil.which('latex')),
            'dvisvgm_available':bool(shutil.which('dvisvgm'))}


visual_review=review_frames


def produce(work,config,*,pipeline=None,renderer=render_scene,reviewer=visual_review,preflight=check_runtime):
    work=Path(work).resolve()
    plan=json.loads(owned_file(work,'approved_plan.json').read_text(encoding='utf-8'))
    brief=validate_animation(plan.get('animation'),allow_legacy=False)
    runtime=preflight(config);write_json(work/'runtime.json',runtime)
    for name in ['video_guard.py','VIDEO_WORKFLOW.md']:
        shutil.copyfile(ROOT/'vendor/video_toolkit'/name,work/name)
    if brief['aspect_ratio']=='9:16':
        with (work/'video_guard.py').open('a',encoding='utf-8') as f:
            f.write('\nSAFE_X = 2.1\nSAFE_Y = 3.82\nCONTENT_MAX_W = 4.0\nCONTENT_MAX_H = 5.45\n')
    protected={name:(work/name).read_bytes() for name in ['approved_plan.json']}
    def unchanged_inputs():
        if any(owned_file(work,name).read_bytes()!=value for name,value in protected.items()):
            raise ValueError('工作流修改了已确认方案或运行辅助文件，已停止制作')
    def checked_review(frames,tag,source):
        before={p:p.read_bytes() for p in frames}
        result=reviewer(work,plan,config,frames,tag)
        unchanged_inputs()
        if owned_file(work,'sol_scene.py').read_text(encoding='utf-8')!=source or any(p.read_bytes()!=value for p,value in before.items()):
            raise ValueError('复核期间场景或检查画面被修改，需要重新渲染')
        return validate_visual_review(result,work,frames)
    pipeline=pipeline or AnimationPipeline(APIModel(config))
    request={'changes':config.get('changes')}
    write_json(work/'request.json',request)
    history=[]
    progress(work,'正在编排动画画面…')
    pipeline.run(work,request)
    unchanged_inputs()
    protected['video_guard.py']=(work/'video_guard.py').read_bytes()
    if config.get('speech_enabled'):
        for path in [work/'narration-timeline.json',*list((work/'speech').glob('*.wav'))]:
            protected[path.relative_to(work).as_posix()]=path.read_bytes()
    for attempt in range(3):
        unchanged_inputs()
        try:
            source=owned_file(work,'sol_scene.py').read_text(encoding='utf-8');inspect_source(source)
            failures,scene_name,_=validate_run(work,require_video=False)
            if failures or not scene_name:raise ValueError('场景检查失败：'+'；'.join(failures))
            text_check=subprocess.run([sys.executable,str(ROOT/'vendor/video_toolkit/check_text.py'),str(work/'sol_scene.py')],
                capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=20)
            if text_check.returncode:raise ValueError('文字预检失败：'+text_check.stdout[-2000:])
            progress(work,'正在生成动画预览…')
            preview,preview_frames,_=renderer(work,config['manim_python'],scene_name,'l',brief,attempt)
            progress(work,'正在检查动画画面…')
            checked_review(preview_frames,f'preview-{attempt}',source)
            progress(work,'正在输出清晰版本…')
            final,frames,metadata=renderer(work,config['manim_python'],scene_name,'m',brief,attempt)
            progress(work,'正在检查最终画面…')
            review=checked_review(frames,f'final-{attempt}',source)
            result=dict(passed=True,workflow='manim',video_path=final.relative_to(work).as_posix(),
                frames=[p.relative_to(work).as_posix() for p in frames],visual_review=review,
                scene_sha256=hashlib.sha256(source.encode()).hexdigest(),video=metadata,repairs=history,
                preview_checked=True,final_checked=True)
            write_json(work/'worker-result.json',result)
            return result
        except ModelServiceError:
            raise
        except (ValueError,subprocess.TimeoutExpired) as error:
            history.append(dict(attempt=attempt,issue=str(error)[:5000]))
            write_json(work/'repairs.json',history)
            if attempt==2:raise ValueError('动画经过两轮修复仍未通过检查：'+str(error)[:1000]) from error
            progress(work,f'正在调整动画（{attempt+1}/2）…')
            pipeline.run(work,request,from_stage='scene-composer',feedback={'scene-composer':str(error)[:5000]})


def main():
    work=Path(sys.argv[1]).resolve()
    config=json.loads(sys.stdin.buffer.read(32769).decode('utf-8'))
    try:produce(work,config)
    except Exception as error:
        # Provider credentials are never written to the run directory or traceback.
        message=str(error)[:1200] if isinstance(error,ValueError) else f'动画工作流失败（{type(error).__name__}），请检查模型设置与运行环境；日志已保留'
        for key in ('api_key','speech_api_key'):
            if config.get(key):message=message.replace(config[key],'[已隐藏]')
        write_json(work/'worker-result.json',dict(passed=False,error=message))
        sys.exit(1)


if __name__=='__main__':main()
