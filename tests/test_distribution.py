import hashlib
import json
from pathlib import Path


def test_vendored_source_matches_pinned_manifests():
    root=Path(__file__).resolve().parents[1]
    for name,count in [('olc',486),('katex',224)]:
        source=json.loads((root/'docs/provenance'/f'{name}-source.json').read_text(encoding='utf-8'))
        assert len(source['files'])==count
        for item in source['files']:
            path=root/'teach_agent/vendor'/name/item['path']
            assert path.is_file(),str(path)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==item['sha256'],str(path)
