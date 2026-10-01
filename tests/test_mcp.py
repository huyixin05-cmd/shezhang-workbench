import os
import sys
import pytest
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


@pytest.mark.asyncio
async def test_official_mcp_stdio_lists_planning_and_confirmation_tools(tmp_path):
    env=dict(os.environ,TEACH_DATA_DIR=str(tmp_path),PYTHONUTF8='1')
    params=StdioServerParameters(command=sys.executable,args=['-m','teach_agent.mcp_server'],env=env)
    async with stdio_client(params) as (read,write):
        async with ClientSession(read,write) as session:
            await session.initialize()
            tools=await session.list_tools()
            names={t.name for t in tools.tools}
            assert {'prepare_lesson','read_lesson','revise_plan','confirm_and_make','job_status','export_lesson'} <= names
            result=await session.call_tool('confirm_and_make',{'project_id':'x','revision':1,'teacher_confirmed':False})
            assert result.is_error
            assert '明确确认' in result.content[0].text
