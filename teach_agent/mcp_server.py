"""Conversation-first MCP entry; the browser is an optional view of the same data."""
import asyncio
from contextlib import asynccontextmanager
from typing import Literal
from uuid import uuid4
import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from .__main__ import default_data
from .local_runtime import LocalRuntime

runtime = None


@asynccontextmanager
async def lifespan(server):
    global runtime
    runtime = LocalRuntime(default_data())
    try:
        yield {}
    finally:
        await runtime.close()
        runtime = None


server=MCPServer('舍长工作台',lifespan=lifespan,instructions='你是老师的教学制作助手。全程在当前对话完成，不要求先启动网页。先用 environment_status 检查制作模型；未配置时提示运行 setup-workbuddy.cmd 本机向导，不要让老师在聊天中粘贴密钥，也不要声称自动使用宿主模型额度。根据老师的一句话调用 prepare_lesson，自动完成需求分析、难点判断、教学顺序设计和复核，中途不要逐步要求确认。用 wait_for_lesson 等待任务，仍在制作时简短报告真实阶段后继续等待，不要紧密轮询。完成后展示 plan_summary 的简明完整方案（目标、难点、做法、演示顺序和暂定条件），动画需展示分镜，仅在开始制作前等待老师一次明确确认当前方案，再调用 confirm_and_make。详细字段只在老师需要时展示。老师要修改方案时用 revise_plan 自动重做，展示修改后的完整方案。不能替老师确认，不能把首次需求或沉默当作确认。制作完成调用 export_lesson，给老师可点击的本地文件绝对路径，并告知可以继续修改。局部修改用 revise_lesson，保留旧版本；教学目标变化时先改方案。只有老师想看网页工作台时才调用 open_workbench。失败应报告真实原因，不能用示例冒充成品。')


async def request(method,path,body=None,raw=False):
    if runtime is None:
        raise ToolError('请重新连接舍长工作台 MCP 服务')
    try:
        url=await runtime.address()
    except RuntimeError as error:
        raise ToolError(str(error)) from error
    async with httpx.AsyncClient(timeout=30,trust_env=False) as client:
        try:
            response=await client.request(method,url+path,json=body,headers={'Authorization':'Bearer '+runtime.settings.token})
        except httpx.HTTPError as error:
            raise ToolError('本地制作服务连接中断，请重新连接；已有作品已保留。') from error
    if response.status_code!=200:
        raise ToolError(str(response.json().get('detail','本机服务请求失败')))
    return response.content if raw else response.json()


def ident(value):
    if len(value)!=32 or any(c not in '0123456789abcdef' for c in value):
        raise ToolError('无效的作品或任务编号')
    return value


@server.tool()
async def environment_status() -> dict:
    """Read model readiness and current supported capabilities without credentials."""
    return await request('GET','/api/status')


@server.tool()
async def list_lessons() -> list[dict]:
    """List locally saved teaching projects."""
    return await request('GET','/api/projects')


@server.tool()
async def prepare_lesson(requirement: str, kind: Literal['auto','interactive','animation']='auto') -> dict:
    """Prepare a proposed plan, without producing content. Show it to the teacher when ready."""
    return await request('POST','/api/projects',{'request':requirement,'kind':kind})


@server.tool()
async def read_lesson(project_id: str) -> dict:
    """Read current plan revision, jobs and produced versions."""
    result=await request('GET','/api/projects/'+ident(project_id))
    result['plan_summary']=summarize_plan(result['project'])
    return result


def summarize_plan(project):
    plan=project.get('plan')
    if not plan:
        return None
    design=plan.get('learning_design') or {}
    return dict(project_id=project['id'],revision=project['plan_revision'],title=plan['title'],
        kind=plan['kind'],grade=plan.get('grade'),objective=plan['objective'],
        difficulty=design.get('student_problem',plan.get('misconception')),
        reason=design.get('difficulty_reason'),approach=design.get('design_response',plan.get('interaction')),
        sequence=design.get('sequence',plan.get('steps')),assumptions=plan.get('assumptions',[]),
        animation=plan.get('animation'))


@server.tool()
async def revise_plan(project_id: str, revision: int, changes: str) -> dict:
    """Revise the proposed plan. Show the new plan and get confirmation before production."""
    return await request('POST','/api/projects/'+ident(project_id)+'/rethink',{'revision':revision,'request':changes})


@server.tool()
async def confirm_and_make(project_id: str, revision: int, teacher_confirmed: bool) -> dict:
    """Only call after the teacher explicitly approves the displayed current plan revision. Never infer approval from silence or the initial request."""
    if teacher_confirmed is not True:
        raise ToolError('必须先获得老师对当前教学方案的明确确认')
    return await request('POST','/api/projects/'+ident(project_id)+'/confirm',{'revision':revision})


@server.tool()
async def revise_lesson(project_id: str, version_id: str, changes: str) -> dict:
    """Apply teacher-requested local edits. For changed teaching goals, revise the plan first."""
    return await request('POST','/api/projects/'+ident(project_id)+'/revise',{'version_id':ident(version_id),'request':changes})


@server.tool()
async def job_status(job_id: str) -> dict:
    """Read progress, real failure details and output version ID."""
    return await request('GET','/api/jobs/'+ident(job_id))


@server.tool()
async def wait_for_lesson(job_id: str, wait_seconds: int=20) -> dict:
    """Wait up to 25 seconds, then return real progress, a teacher-facing plan, or the version to export. Repeat while running; never approve a plan automatically."""
    if not 0<=wait_seconds<=25:
        raise ToolError('每次等待需在 0 到 25 秒之间')
    deadline=asyncio.get_running_loop().time()+wait_seconds
    while True:
        job=await job_status(job_id)
        if job['status'] not in ('queued','running') or asyncio.get_running_loop().time()>=deadline:
            break
        await asyncio.sleep(min(.5,max(0,deadline-asyncio.get_running_loop().time())))
    result={'job':job}
    if job['status']=='completed' and job['kind']=='plan':
        lesson=await read_lesson(job['project_id'])
        result.update(plan_summary=lesson['plan_summary'],next_action='await_teacher_confirmation')
    elif job['status']=='completed':
        result.update(next_action='export_lesson')
    elif job['status'] in ('queued','running'):
        result.update(next_action='wait_for_lesson')
    else:
        result.update(next_action='report_problem')
    return result


@server.tool()
async def cancel_job(job_id: str) -> dict:
    """Cancel a task when the teacher asks; previous versions are preserved."""
    return await request('POST','/api/jobs/'+ident(job_id)+'/cancel',{})


@server.tool()
async def export_lesson(version_id: str, format: Literal['auto','html','video','zip','project']='auto') -> dict:
    """Save portable content into the local exports directory and return its actual path."""
    if format=='auto':
        version=await request('GET','/api/versions/'+ident(version_id))
        format={'interactive':'html','animation':'video'}.get(version['kind'],'zip')
    raw=await request('GET','/api/versions/'+ident(version_id)+'/download?format='+format,raw=True)
    root=default_data()/'exports'
    root.mkdir(parents=True,exist_ok=True)
    suffix={'html':'.html','video':'.mp4','zip':'.zip','project':'.zip'}[format]
    path=root/(version_id+'-'+uuid4().hex[:8]+suffix)
    path.write_bytes(raw)
    return {'path':str(path),'bytes':len(raw),'format':format}


@server.tool()
async def workbench_address() -> dict:
    """Optional browser address. For an authenticated browser view use open_workbench, only at the teacher's request."""
    await environment_status()
    return {'url':await runtime.address(),'note':'对话制作无需打开网页；想看网页时可调用 open_workbench。'}


@server.tool()
async def open_workbench() -> dict:
    """Open the optional authenticated workbench ONLY when the teacher asks to view it. Never return the private token to the chat."""
    import webbrowser
    await environment_status()
    url=await runtime.address()
    opened=await asyncio.to_thread(webbrowser.open,url+'/#'+runtime.settings.token)
    return {'opened':opened,'url':url,'note':'网页与当前对话共用作品库。'}


def main():
    server.run(transport='stdio')


if __name__=='__main__':
    main()
