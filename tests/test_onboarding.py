import json
from teach_agent.config import Settings


def test_workbuddy_config_is_portable_setup_without_credentials(tmp_path):
    from teach_agent.onboarding import write_mcp_config
    root=tmp_path/'中文 空格'
    settings=Settings(root/'.data')
    settings.save({'base_url':'https://example.org/v1','model':'test','api_key':'private-secret'})
    output=write_mcp_config(root,settings.root)
    data=json.loads(output.read_text(encoding='utf-8'))['mcpServers']['teach-agent']
    assert data['args']==['-m','teach_agent.mcp_server']
    assert data['env']['PYTHONPATH']==str(root.resolve())
    assert data['env']['TEACH_DATA_DIR']==str(settings.root.resolve())
    assert 'private-secret' not in output.read_text(encoding='utf-8')
    assert settings.token not in output.read_text(encoding='utf-8')


def test_concurrent_initialization_publishes_complete_token(tmp_path,monkeypatch):
    import os
    from pathlib import Path
    original=os.link
    contenders=[]
    racing=False
    def publish(source,destination):
        nonlocal racing
        assert len(Path(source).read_text())>=40
        if not racing:
            racing=True
            contenders.append(Settings(tmp_path))
        return original(source,destination)
    monkeypatch.setattr(os,'link',publish)
    settings=Settings(tmp_path)
    assert len(contenders)==1
    assert settings.token==contenders[0].token
    assert len(settings.token)>=40
    assert sorted(p.name for p in tmp_path.iterdir())==['session-token']
