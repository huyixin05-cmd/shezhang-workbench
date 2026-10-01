"""Native Sol workflow worker. No template routing and no HTTP-provider substitution."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .animation_contract import validate_animation
from .animation_rendering import inspect_source,render_scene
from .animation_workflow import ROOT,owned_file,validate_visual_review
from .animation_workflow import clean_environment
from .process_tree import ProcessTree

VENDOR=ROOT/'vendor/math_to_manim'
sys.path.insert(0,str(VENDOR))
from sol.client import CodexCli
from sol.models import RunRequest,StageRunResult
from sol.staged import StagedPipeline
from sol.validation import validate_run


def write_json(path,value):
    path=Path(path);temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8');temp.replace(path)


def progress(work,message):write_json(work/'progress.json',{'stage':message})


class WorkbenchCli(CodexCli):
    def __init__(self,*args,images=(),**kwargs):
        super().__init__(*args,**kwargs);self.images=images

    def build_command(self,**kwargs):
        # Each role reads durable artifacts. Fresh sessions avoid CLI-version-specific resume flags.
        kwargs['session_id']=None
        command=super().build_command(**kwargs)
        command[-1:-1]=['--skip-git-repo-check']
        for path in self.images:command[-1:-1]=['--image',str(path)]
        return command

    def run(self,prompt,**kwargs):
        guidance='''
Workbench binding rules: approved_plan.json is the teacher-approved lesson and storyboard. Read it before producing artifacts. Preserve its learning goal, shot order, aspect ratio and approximate duration. Do not ask the teacher for intermediate approvals. Implementation refinements are allowed; changing the teaching goal is not.
You may also read runtime.json, video_guard.py, VIDEO_WORKFLOW.md and previous_* files when present. Scene composer must read 03_curriculum.json, 04_math_dossier.json and 05_shot_list.json together. Reuse previous_sol_scene.py for requested local revisions; do not discard unaffected scenes.
All on-screen teaching text must be Chinese. Use meaningful diagrams and motion, not a slideshow of paragraphs. Only use 3D if the topic benefits from it. No obligatory cinematic/white/3D theme.
Use VideoScene, text_label, fit_content and ZH_FONT from video_guard when suitable; use the requested frame dimensions. No external files, online resources, API calls, subprocesses, filesystem access, introspection or dynamic code execution in sol_scene.py. Allowed imports: manim, math, numpy, random, video_guard. Do not create/manipulate config files or renderer options. The wrapper alone renders and reads evidence. If LaTeX is unavailable, do not silently lose mathematical meaning: use readable simple text only when adequate; otherwise report the missing requirement.
In render review, inspect all supplied images. Judge the confirmed lesson, correctness, motion evidence, legibility and framing; do not reject a correct 2D scene for lacking 3D or a white background. Mark defects with frame/timestamp references.
'''
        # Keep native CLI commands/contracts; own its entire descendant lifetime instead
        # of the upstream parent's kill + unbounded reader-thread joins on timeout.
        command=self.build_command(cwd=kwargs['cwd'],schema_path=kwargs['schema_path'],
            output_path=kwargs['output_path'],reasoning_effort=kwargs.get('reasoning_effort'))
        output_path=Path(kwargs['output_path']);output_path.unlink(missing_ok=True)
        trace_path=Path(kwargs['trace_path'])
        with trace_path.open('wb') as trace,trace_path.with_suffix('.stderr.log').open('wb') as errors:
            with ProcessTree(command,stdin=subprocess.PIPE,stdout=trace,stderr=errors,env=clean_environment()) as process:
                try:process.communicate((guidance+'\n'+prompt).encode('utf-8'),timeout=self.timeout)
                except subprocess.TimeoutExpired as error:raise ValueError('动画模型响应超时，调用已停止，日志已保留') from error
                if process.returncode:raise ValueError('动画模型调用失败，请检查 Codex 登录、模型权限和本地日志')
        if not output_path.is_file():raise ValueError('动画模型没有返回阶段结果')
        return kwargs.get('result_model',StageRunResult).model_validate_json(output_path.read_text(encoding='utf-8'))


def check_runtime(config):
    version=subprocess.run([config['manim_python'],'-c','import manim,av;print(manim.__version__)'],
        capture_output=True,text=True,timeout=30)
    if version.returncode:raise ValueError('所选 Python 无法加载 Manim，请选择已有 Manim 环境')
    login=subprocess.run([config['codex'],'login','status'],capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30)
    message=(login.stdout+' '+login.stderr).lower()
    if login.returncode or 'not logged' in message:
        raise ValueError('动画工作流尚未登录 Codex CLI，请先运行 codex login 登录，再重新制作')
    if 'api key' in message and 'chatgpt' not in message:
        raise ValueError('现有 Sol 工作流使用 Codex 的 ChatGPT 登录，请切换到该登录方式')
    return {'manim':version.stdout.strip(),'latex_available':bool(shutil.which('latex')),
            'dvisvgm_available':bool(shutil.which('dvisvgm'))}


def visual_review(work,plan,config,frames,tag):
    work=Path(work);review_path=work/'review.json'
    # Archive the prior verdict so a new model call cannot accidentally reuse it.
    if review_path.exists():shutil.move(str(review_path),str(work/f'review-before-{tag}.json'))
    schema=work/'review-result.schema.json'
    write_json(schema,StageRunResult.model_json_schema())
    evidence=[p.relative_to(work).as_posix() for p in frames]
    prompt='''Inspect the attached rendered frames, their timestamps.json files, sol_scene.py and approved_plan.json.
Check whether the actual images support the approved visual argument and order, formulas are correct, Chinese is readable, labels stay inside the frame, and key steps are not skipped. A movie decoding correctly does not establish teaching correctness.
Write only review.json with {"status":"approved" or "needs_repair","defects":[concrete issues],"observations":[specific observed evidence],"evidence":[all inspected relative image paths]}.
Return the structured stage summary with role="cinematographer", artifacts=["review.json"]. Do not edit the scene.
Required frame evidence: '''+json.dumps(evidence,ensure_ascii=False)
    client=WorkbenchCli(command=config['codex'],model=config['model'],timeout=600,images=frames)
    result=client.run(prompt,cwd=work,schema_path=schema,output_path=work/f'review-{tag}-result.json',
        trace_path=work/f'review-{tag}.jsonl',result_model=StageRunResult)
    if result.status!='completed' or result.role!='cinematographer' or result.artifacts!=['review.json']:
        raise ValueError('画面复核没有完成')
    review=json.loads(owned_file(work,'review.json').read_text(encoding='utf-8'))
    return validate_visual_review(review,work,frames)


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
    protected={name:(work/name).read_bytes() for name in ['approved_plan.json','video_guard.py']}
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
    pipeline=pipeline or StagedPipeline(client=WorkbenchCli(command=config['codex'],model=config['model'],timeout=600))
    prompt='制作 approved_plan.json 中已经确认的教学动画。全部教学决策按该文件执行；中间无需用户确认。'
    if config.get('changes'):prompt+=' 本次修改要求：'+config['changes'][:4000]
    request=RunRequest(prompt=prompt,render=True,quality='m',max_repairs=2)
    write_json(work/'request.json',request.model_dump())
    history=[]
    progress(work,'正在编排动画画面…')
    pipeline.run(work,request)
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
            result=dict(passed=True,workflow='sol',video_path=final.relative_to(work).as_posix(),
                frames=[p.relative_to(work).as_posix() for p in frames],visual_review=review,
                scene_sha256=hashlib.sha256(source.encode()).hexdigest(),video=metadata,repairs=history,
                preview_checked=True,final_checked=True)
            write_json(work/'worker-result.json',result)
            return result
        except (ValueError,subprocess.TimeoutExpired) as error:
            history.append(dict(attempt=attempt,issue=str(error)[:5000]))
            write_json(work/'repairs.json',history)
            if attempt==2:raise ValueError('动画经过两轮修复仍未通过检查：'+str(error)[:1000]) from error
            progress(work,f'正在调整动画（{attempt+1}/2）…')
            pipeline.run(work,request,from_stage='scene-composer',feedback={'scene-composer':str(error)[:5000]})


def main():
    work=Path(sys.argv[1]).resolve()
    config=json.loads(owned_file(work,'worker-input.json').read_text(encoding='utf-8'))
    try:produce(work,config)
    except Exception as error:
        # Raw CLI traces remain local, are never exported, and are not echoed to the UI.
        message=str(error)[:1200] if isinstance(error,ValueError) else f'动画工作流失败（{type(error).__name__}），请检查登录与运行环境；日志已保留'
        write_json(work/'worker-result.json',dict(passed=False,error=message))
        raise


if __name__=='__main__':main()
