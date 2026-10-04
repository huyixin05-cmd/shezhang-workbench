import json
import os
import secrets
import tempfile
from pathlib import Path
from urllib.parse import urlsplit


class Settings:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / 'config.json'
        token_path = self.root / 'session-token'
        if not token_path.exists():
            fd, temporary = tempfile.mkstemp(prefix='session-token-',suffix='.tmp',dir=self.root)
            temporary = Path(temporary)
            try:
                with os.fdopen(fd,'w',encoding='utf-8') as f:
                    f.write(secrets.token_urlsafe(32))
                temporary.chmod(0o600)
                # Publish only complete bytes, without replacing a concurrent winner.
                os.link(temporary,token_path)
            except FileExistsError:
                pass
            finally:
                temporary.unlink(missing_ok=True)
        self.token = token_path.read_text().strip()

    def read(self):
        data = json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}
        for field, env in [('base_url','TEACH_MODEL_URL'),('model','TEACH_MODEL_NAME'),
                           ('api_key','TEACH_API_KEY'),('manim_python','TEACH_MANIM_PYTHON'),
                           ('speech_base_url','TEACH_SPEECH_URL'),('speech_model','TEACH_SPEECH_MODEL'),
                           ('speech_voice','TEACH_SPEECH_VOICE'),('speech_api_key','TEACH_SPEECH_API_KEY')]:
            if os.environ.get(env):
                data[field] = os.environ[env]
        return data

    def public(self):
        data = self.read()
        return dict(base_url=data.get('base_url',''), model=data.get('model',''),
                    has_key=bool(data.get('api_key')), configured=bool(data.get('base_url') and data.get('model')),
                    max_tokens=data.get('max_tokens',12000), manim_python=data.get('manim_python',''),
                    speech_enabled=data.get('speech_enabled',False),speech_base_url=data.get('speech_base_url',''),
                    speech_model=data.get('speech_model',''),speech_voice=data.get('speech_voice',''),
                    speech_instructions=data.get('speech_instructions',False),has_speech_key=bool(data.get('speech_api_key')))

    def save(self, values):
        data = self.read()
        data.pop('animation_codex',None)
        data.pop('animation_model',None)
        if 'base_url' in values:
            url = urlsplit(values['base_url'])
            if url.username or url.password or url.query or url.fragment:
                raise ValueError('模型地址不能含账号、查询参数或片段')
            if url.scheme != 'https' and not (url.scheme == 'http' and url.hostname in ('127.0.0.1','localhost','::1')):
                raise ValueError('模型地址须使用 HTTPS，本机模型可使用 HTTP')
        if values.get('speech_base_url'):
            from .narration import validate_speech_url
            validate_speech_url(values['speech_base_url'])
        for key in ('speech_enabled','speech_instructions'):
            if key in values:
                if not isinstance(values[key],bool):raise ValueError('语音开关必须为布尔值')
                data[key]=values[key]
        for key in ('base_url','model','manim_python','speech_base_url','speech_model','speech_voice'):
            if key in values:
                data[key] = str(values[key]).strip()
        if values.get('api_key'):
            data['api_key'] = values['api_key'].strip()
        if values.get('clear_key'):
            data.pop('api_key', None)
        if values.get('speech_api_key'):data['speech_api_key']=str(values['speech_api_key']).strip()
        if values.get('clear_speech_key'):data.pop('speech_api_key',None)
        if data.get('speech_enabled'):
            from .narration import SpeechService
            SpeechService(data)
        if 'max_tokens' in values:
            count = int(values['max_tokens'])
            if not 1024 <= count <= 32000:
                raise ValueError('输出上限需在 1024 到 32000 之间')
            data['max_tokens'] = count
        temp = self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        temp.chmod(0o600)
        temp.replace(self.path)
        return self.public()
