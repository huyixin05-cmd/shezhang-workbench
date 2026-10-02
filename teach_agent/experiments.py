"""Independent, licensed upstream snapshots. Never execute or auto-embed them."""
import hashlib
import json
import shutil
import zipfile
from pathlib import Path
from uuid import uuid4


class ExperimentLibrary:
    def __init__(self):
        self.root = Path(__file__).parent / 'experiment_library'
        self.entries = json.loads((self.root / 'catalog.json').read_text(encoding='utf-8'))

    def search(self, query=''):
        terms = str(query).lower().split()
        return [dict(item) for item in self.entries
                if all(term in json.dumps(item, ensure_ascii=False).lower() for term in terms)]

    def export(self, resource_id, destination_root):
        item = next((e for e in self.entries if e['id'] == resource_id), None)
        if not item or item['status'] != 'source_archive':
            raise ValueError('该项目没有可导出的授权源码，仅可查看参考链接')
        source = self.root / item['archive']
        if hashlib.sha256(source.read_bytes()).hexdigest() != item['sha256']:
            raise ValueError('源码快照校验失败，请重新安装资源包')
        destination_root = Path(destination_root).resolve()
        destination_root.mkdir(parents=True, exist_ok=True)
        path = destination_root / (item['id'] + '-' + uuid4().hex[:8] + '.zip')
        shutil.copyfile(source, path)
        with zipfile.ZipFile(path, 'a', compression=zipfile.ZIP_DEFLATED) as archive:
            prefix = 'TEACH_AGENT_RESOURCE_NOTICES/'
            source_record = {key:value for key,value in item.items() if not key.startswith('download')}
            archive.writestr(prefix + 'SOURCE.json', json.dumps(source_record, ensure_ascii=False, indent=2))
            for filename in item['license_files']:
                archive.write(self.root / filename, prefix + Path(filename).name)
        return dict(path=str(path), bytes=path.stat().st_size, name=item['name'],
                    license=item['license'], usage=item['usage'], setup=item['setup'])
