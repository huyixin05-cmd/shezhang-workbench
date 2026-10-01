from pathlib import Path
import pytest
from teach_agent.materials import Materials
from teach_agent.artifacts import assemble_page
from teach_agent.checking import check_page


@pytest.mark.asyncio
async def test_instrument_reading_changes_with_lesson_reset(tmp_path):
    source = Path('teach_agent/static/example.html').read_text(encoding='utf-8')
    page = assemble_page(Materials().expand(source, ['phy.apparatus.spring-scale.interactive']))
    path = tmp_path / 'index.html'
    path.write_text(page, encoding='utf-8')
    report = await check_page(path, [
        dict(action='click', selector='#reset', expect_selector='.ss__lcd', expect_text='2.50'),
        dict(action='click', selector='#reveal', expect_selector='#answer', expect_text='匀速直线运动'),
    ])
    assert report['passed'], report['errors']
