"""Rebuild the offline catalog and notice-complete downloads from pinned local archives.

Run from the repository: python scripts/build_experiment_catalog.py
Does not download, run or modify upstream source code.
"""
import hashlib
import html
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from teach_agent.experiments import ExperimentLibrary


def main():
    library = ExperimentLibrary()
    rows = []
    for item in library.entries:
        if item['status'] == 'source_archive':
            if item['id'] == 'pfalstad--ripplegl' or item['id'].startswith('virtual-labs--'):
                # These need notices additional to the untouched upstream archive.
                result = library.export(item['id'], library.root / 'downloads')
                download = library.root / 'downloads' / (item['id'] + '.zip')
                Path(result['path']).replace(download)
                item['download'] = download.relative_to(library.root).as_posix()
                item['download_sha256'] = hashlib.sha256(download.read_bytes()).hexdigest()
            else:
                item['download'] = item['archive']
                item['download_sha256'] = item['sha256']
        else:
            item['setup'] = '仅保存参考链接；本项目未收录该源码。'
        links = '<a href="' + html.escape(item['origin'], quote=True) + '">原项目</a>'
        if item['status'] == 'source_archive':
            links += ' · <a href="' + item['download'] + '">下载源码（含许可声明）</a>'
            links += ' · ' + ' · '.join('<a href="'+p+'">声明 '+str(i+1)+'</a>'
                                       for i,p in enumerate(item['license_files']))
        status = '已保存源码' if item['status'] == 'source_archive' else '仅参考链接'
        rows.append('<article><h2>'+html.escape(item['name'])+'</h2><p>'+html.escape(item['license'])+
                    ' · '+status+'</p><p>'+html.escape(item['setup'])+'</p><p>'+html.escape(item['usage'])+'</p>'+links+'</article>')
    page = '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>实验源码与参考</title><style>body{font:18px/1.7 system-ui,sans-serif;background:#f6f9f6;color:#193e35;max-width:1000px;margin:auto;padding:24px}article{background:white;padding:20px;margin:18px 0;border:1px solid #d9e4da;border-radius:12px}a{color:#176b59}h2{font-size:22px}</style></head><body>
<h1>实验源码与参考</h1><p>32 个项目，其中 27 个已保存源码（原始快照约 104 MB）。这是供查阅和开发的独立源码，实验尚未逐项构建或接入。下载包含适用的许可声明。WorkBuddy 也可查找和导出这些资源。</p>
'''+ '\n'.join(rows) + '\n</body></html>'
    (library.root / 'catalog.json').write_text(json.dumps(library.entries, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (library.root / 'index.html').write_text(page, encoding='utf-8')


if __name__ == '__main__':
    main()
