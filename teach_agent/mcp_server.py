"""Official MCP stdio adapter sharing the browser service's data and approvals."""
import json
from pathlib import Path
from typing import Literal
from uuid import uuid4
from urllib.parse import urlsplit
import httpx
from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from .__main__ import default_data
from .config import Settings

server=MCPServer('Teach Agent',instructions='先准备教学方案并完整展示给老师，等待老师明确确认当前方案，再调用 confirm_and_make。不能替老师确认。生成较慢时用 job_status 查询。')


async def request(method,path,body=None,raw=False):
    settings=Settings(default_data())
    server_file=settings.root/'server.json'
    if not server_file.is_file():
        raise ToolError('请先启动 Teach Agent 本地工作台，并与 MCP 使用同一数据目录')
    url=json.loads(server_file.read_text(encoding='utf-8'))['url']
    parsed=urlsplit(url)
    if parsed.scheme!='http' or parsed.hostname not in ('127.0.0.1','localhost','::1') or parsed.username or parsed.password:
        raise ToolError('本机服务地址无效')
    async with httpx.AsyncClient(timeout=30,trust_env=False) as client:
        try:
            response=await client.request(method,url+path,json=body,headers={'Authorization':'Bearer '+settings.token})
        except httpx.HTTPError as error:
            raise ToolError('本机工作台未运行或连接失败，请先启动') from error
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
    return await request('GET','/api/projects/'+ident(project_id))


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
async def cancel_job(job_id: str) -> dict:
    """Cancel a task when the teacher asks; previous versions are preserved."""
    return await request('POST','/api/jobs/'+ident(job_id)+'/cancel',{})


@server.tool()
async def export_lesson(version_id: str, format: Literal['html','video','zip','project']='html') -> dict:
    """Save portable content into the local exports directory and return its actual path."""
    raw=await request('GET','/api/versions/'+ident(version_id)+'/download?format='+format,raw=True)
    root=default_data()/'exports'
    root.mkdir(parents=True,exist_ok=True)
    suffix={'html':'.html','video':'.mp4','zip':'.zip','project':'.zip'}[format]
    path=root/(version_id+'-'+uuid4().hex[:8]+suffix)
    path.write_bytes(raw)
    return {'path':str(path),'bytes':len(raw),'format':format}


@server.tool()
def workbench_address() -> dict:
    """Get the local workbench address; open using the launcher if a new browser needs authentication."""
    file=default_data()/'server.json'
    if not file.is_file():
        raise ToolError('请先启动本地工作台')
    return {'url':json.loads(file.read_text(encoding='utf-8'))['url'],'note':'新浏览器请通过启动器打开，以完成本机身份验证。'}


if __name__=='__main__':
    server.run(transport='stdio')
