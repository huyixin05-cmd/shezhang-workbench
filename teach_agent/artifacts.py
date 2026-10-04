import html as html_module
import re
import zipfile
from html.parser import HTMLParser
from pathlib import Path
from .materials import VENDOR

CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; media-src 'self' blob:; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'; frame-src 'none'; worker-src 'none'"


class ResourceCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.styles = []
        self.in_style = False

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == 'style':
            self.in_style = True
        if values.get('style'):
            self.styles.append(values['style'])
        # SVG paint servers and effects use CSS URL syntax outside style="...".
        for key in ('fill','stroke','filter','clip-path','mask','cursor','marker',
                    'marker-start','marker-mid','marker-end'):
            if values.get(key):
                self.styles.append(values[key])
        if tag in ('animate','set') and values.get('attributename','').lower() in (
                'fill','stroke','filter','clip-path','mask','cursor','marker',
                'marker-start','marker-mid','marker-end','style'):
            self.styles.extend(values[k] for k in ('from','to','values') if values.get(k))
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

    def handle_data(self, data):
        if self.in_style:
            self.styles.append(data)

    def handle_endtag(self, tag):
        if tag == 'style':
            self.in_style = False


class DocumentPrefix(HTMLParser):
    """Require a simple real document prefix; insert policy by parser position."""
    def __init__(self, source):
        super().__init__()
        self.source=source
        self.root_seen=False
        self.head_end=None

    def handle_starttag(self, tag, attrs):
        if self.head_end is not None:
            return
        if tag=='html' and not self.root_seen:
            if any(k.lower().startswith('on') for k,_ in attrs):
                raise ValueError('html 根节点不能包含事件处理器')
            self.root_seen=True
        elif tag=='head' and self.root_seen:
            if attrs:
                raise ValueError('head 请使用无属性标签')
            line,col=self.getpos()
            self.head_end=sum(len(x) for x in self.source.splitlines(keepends=True)[:line-1])+col+len(self.get_starttag_text())
        else:
            raise ValueError('文档必须依次以 doctype（可选）、html、head 开始，脚本放在 head 内或之后')

    def handle_data(self,data):
        if self.head_end is None and data.strip():
            raise ValueError('head 之前不能有正文或其他内容')

    def handle_comment(self,data):
        if self.head_end is None:
            raise ValueError('请将注释放在 head 内或之后')

    def handle_decl(self,decl):
        if self.head_end is None and (self.root_seen or decl.lower()!='doctype html'):
            raise ValueError('请使用标准 HTML doctype')

    def handle_pi(self,data):
        if self.head_end is None:
            raise ValueError('head 之前不能有处理指令')

    def handle_endtag(self,tag):
        if self.head_end is None:
            raise ValueError('文档开头结构不完整')


def assemble_page(html):
    if not isinstance(html, str) or not html.strip() or len(html) > 8_000_000:
        raise ValueError('课件为空或超过大小限制')
    if not re.search(r'<html[\s>]', html, re.I) or not re.search(r'</html\s*>', html, re.I):
        raise ValueError('课件缺少完整 HTML 结构')
    if not re.search(r'<head[\s>]', html, re.I):
        raise ValueError('课件缺少 head')
    resources = ResourceCheck()
    resources.feed(html)
    prefix=DocumentPrefix(html)
    prefix.feed(html)
    prefix.close()
    if prefix.head_end is None:
        raise ValueError('课件缺少实际的 head 标签')
    css = '\n'.join(resources.styles)
    for url in re.findall(r'url\(\s*[\"\']?([^\)\"\']+)', css, re.I):
        if not url.startswith(('data:', '#')):
            raise ValueError('样式引用了未打包资源')
    if re.search(r'@import\s', css, re.I):
        raise ValueError('样式不能在线导入')
    tag = '<meta http-equiv="Content-Security-Policy" content="' + html_module.escape(CSP, quote=True) + '">'
    return html[:prefix.head_end]+tag+html[prefix.head_end:]


def notices():
    return '\n\n'.join([
        'Teach Agent includes Open Lab Components, KaTeX and Math-To-Manim (Sol workflow). Original license notices follow.',
        (VENDOR / 'math_to_manim/LICENSE').read_text(encoding='utf-8'),
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
        allowed += ['animation/'+name for name in ['sol_scene.py','video_guard.py','VIDEO_WORKFLOW.md',
            'approved_plan.json','01_intent.json','02_knowledge_map.json','03_curriculum.json',
            '04_math_dossier.json','05_shot_list.json','06_scene_spec.json','review.json','validation.json','repairs.json',
            'narration-script.json','narration-timeline.json','narration-report.json','narration-review.json']]
        allowed += [p.relative_to(folder).as_posix() for p in (folder/'animation/speech').glob('*.wav')]
        allowed += [p.relative_to(folder).as_posix() for p in (folder/'animation/review_frames').rglob('*')
                    if p.suffix == '.png' or p.name == 'timestamps.json']
    with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as z:
        for relative in allowed:
            path = folder / relative
            if path.is_file() and not path.is_symlink():
                if not path.resolve().is_relative_to(folder.resolve()):
                    continue
                z.write(path, relative)
    return output
