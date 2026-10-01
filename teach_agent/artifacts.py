import html as html_module
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from .materials import VENDOR

CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; media-src 'self' blob:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; worker-src 'none'"


class ResourceCheck(HTMLParser):
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag in ('iframe', 'object', 'embed', 'base', 'form'):
            raise ValueError('课件包含不允许的外部容器或表单')
        if tag == 'meta' and values.get('http-equiv', '').lower() in ('refresh', 'content-security-policy'):
            raise ValueError('课件不能自设跳转或安全策略')
        for key, value in attrs:
            if key in ('src', 'href', 'xlink:href', 'action', 'poster', 'srcset') and value:
                if value.startswith('#') or (key in ('src', 'poster', 'href', 'xlink:href') and value.startswith('data:image/')):
                    continue
                if tag in ('video', 'source') and value == 'assets/clip.mp4':
                    continue
                raise ValueError('课件资源必须内嵌，不能依赖外网或本机路径')


def assemble_page(html):
    if not isinstance(html, str) or not html.strip() or len(html) > 8_000_000:
        raise ValueError('课件为空或超过大小限制')
    if not re.search(r'<html[\s>]', html, re.I) or not re.search(r'</html\s*>', html, re.I):
        raise ValueError('课件缺少完整 HTML 结构')
    if not re.search(r'<head[\s>]', html, re.I):
        raise ValueError('课件缺少 head')
    ResourceCheck().feed(html)
    for url in re.findall(r'url\(\s*[\"\']?([^\)\"\']+)', html, re.I):
        if not url.startswith(('data:', '#')):
            raise ValueError('样式引用了未打包资源')
    if re.search(r'@import\s', html, re.I):
        raise ValueError('样式不能在线导入')
    tag = '<meta http-equiv="Content-Security-Policy" content="' + html_module.escape(CSP, quote=True) + '">'
    return re.sub(r'(<head\b[^>]*>)', lambda m: m.group(1) + tag, html, count=1, flags=re.I)


def notices():
    return '\n\n'.join([
        'Teach Agent includes Open Lab Components and KaTeX. Original license notices follow.',
        (VENDOR / 'olc/LICENSE').read_text(encoding='utf-8'),
        (VENDOR / 'katex/LICENSE').read_text(encoding='utf-8'),
        'mhchem upstream: Copyright (c) 2011-2015 The MathJax Consortium; Copyright (c) 2015-2018 Martin Hensel. KaTeX adaptation is MIT; retain upstream Apache-2.0 notice.',
        (VENDOR / 'katex-licenses/Apache-2.0.txt').read_text(encoding='utf-8')])


def add_notices(page):
    # Comments preserve attribution without adding unrelated content to the lesson.
    return page + '\n<!--\n' + notices().replace('--', '—') + '\n-->\n'


def bundle(folder: Path, output: Path, editable=False):
    allowed = ['index.html', 'report.json', 'THIRD_PARTY_NOTICES.txt', 'assets/clip.mp4']
    if editable:
        allowed += ['plan.json', 'source.json']
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for relative in allowed:
            path = folder / relative
            if path.is_file() and not path.is_symlink():
                z.write(path, relative)
    return output
