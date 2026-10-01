"""Manual UI QA only. Fixed responses, never used by the production launcher."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import uvicorn
from teach_agent.app import create_app
from test_api import Provider, PLAN
from pedagogy_fixture import DESIGN


class FixtureProvider(Provider):
    async def json(self,messages):
        if 'PLAN_SCHEMA' in messages[0]['content']:
            return dict(PLAN,learning_design=DESIGN,title='【界面测试·固定响应】力与加速度',components=['phy.apparatus.spring-scale.interactive'])
        if 'REVIEW_SCHEMA' in messages[0]['content']:
            return dict(passed=True,issues=[])
        return dict(html=Path('teach_agent/static/example.html').read_text(encoding='utf-8'),
                    checks=[dict(action='click',selector='#reset',expect_selector='.ss__lcd',expect_text='2.50')])


if __name__=='__main__':
    app=create_app(Path('verification-local/ui-data'),model=FixtureProvider())
    app.state.server_url='http://127.0.0.1:8766'
    uvicorn.run(app,host='127.0.0.1',port=8766,log_level='warning',access_log=False)
