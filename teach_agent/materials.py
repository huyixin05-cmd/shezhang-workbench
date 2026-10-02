import base64
import json
import re
from functools import cached_property
from pathlib import Path

VENDOR = Path(__file__).parent / 'vendor'


class Materials:
    def __init__(self):
        self.items = {}
        for path in (VENDOR / 'olc/components').rglob('*.html'):
            text = path.read_text(encoding='utf-8')
            match = re.search(r'<!--\s*@cmp-manifest\s*(\{.*?\})\s*-->', text, re.S)
            meta = json.loads(match.group(1))
            self.items[meta['id']] = (meta, path)

    def catalog(self):
        return [dict(id=m['id'], name=m['name'], category=m['category']) for m, _ in self.items.values()]

    def descriptions(self, ids):
        if len(ids) > 8 or any(i not in self.items for i in ids):
            raise ValueError('方案引用了未知或过多的器材组件')
        return [self.items[i][0] for i in ids]

    @cached_property
    def math_bundle(self):
        root = VENDOR / 'katex/dist'
        css = (root / 'katex.min.css').read_text(encoding='utf-8')
        def font(match):
            filename = match.group(1).strip('"\'')
            path = root / filename
            mime = {'.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf'}[path.suffix]
            return 'url(data:' + mime + ';base64,' + base64.b64encode(path.read_bytes()).decode() + ')'
        css = re.sub(r'url\(([^)]+)\)', font, css)
        scripts = []
        for file in ('katex.min.js', 'contrib/mhchem.min.js', 'contrib/auto-render.min.js'):
            script = (root / file).read_text(encoding='utf-8')
            script = re.sub('</script', r'<\/script', script, flags=re.I)
            scripts.append('<script>' + script + '</script>')
        helper = r'''<script>
window.renderFormula=function(el,tex,display=true){katex.render(tex,el,{displayMode:display,throwOnError:true,trust:false});};
document.addEventListener('DOMContentLoaded',()=>{renderMathInElement(document.body,{delimiters:[{left:'$$',right:'$$',display:true},{left:'\\(',right:'\\)',display:false},{left:'\\[',right:'\\]',display:true}],throwOnError:true});});
</script>'''
        return '<style>' + css + '</style>' + ''.join(scripts) + helper

    def expand(self, html, ids):
        self.descriptions(ids)
        used = set()
        def component(match):
            ident = match.group(1)
            if ident not in ids:
                raise ValueError('生成内容引用了方案以外的器材')
            if ident in used:
                raise ValueError('同一器材 ID 只能插入一次')
            used.add(ident)
            raw = self.items[ident][1].read_text(encoding='utf-8')
            payload = json.dumps(raw, ensure_ascii=False).replace('<', '\\u003c')
            return '<div data-teach-component="'+ident+'"></div><script>registerComponent('+json.dumps(ident)+','+payload+');</script>'
        html = re.sub(r'\{\{component:([^}]+)\}\}', component, html)
        if used:
            runtime = (VENDOR / 'olc/lib/runtime.js').read_text(encoding='utf-8')
            helper = '''<script>(()=>{const module={exports:{}};
''' + runtime + '''
const entries=new Map();
window.registerComponent=(id,source)=>{
 const container=document.querySelector('[data-teach-component="'+id+'"]');
 entries.set(id,{container,source,props:{}});module.exports.mount(source,container,{});
};
window.updateComponent=(id,props)=>{
 const item=entries.get(id);if(!item)throw new Error('Unknown component: '+id);
 item.props={...item.props,...props};module.exports.mount(item.source,item.container,item.props);
 return item.container;
};})();</script>'''
            if re.search(r'<head\b[^>]*>',html,re.I):
                html=re.sub(r'(<head\b[^>]*>)',lambda m:m.group()+helper,html,count=1,flags=re.I)
            else:
                html=helper+html
        if '{{component:' in html:
            raise ValueError('器材占位符不完整')
        if '<!--TEACH_MATH-->' in html:
            html = html.replace('<!--TEACH_MATH-->', self.math_bundle, 1).replace('<!--TEACH_MATH-->', '')
        if '<!--TEACH_INTERACTION-->' in html:
            script = (Path(__file__).parent / 'static/interaction.js').read_text(encoding='utf-8')
            script = re.sub('</script', r'<\\/script', script, flags=re.I)
            html = html.replace('<!--TEACH_INTERACTION-->', '<script>'+script+'</script>', 1).replace('<!--TEACH_INTERACTION-->', '')
        return html
