"""Small, explicit selection from the pinned html-anything prompt snapshot."""
import hashlib
import re
from pathlib import Path

ROOT = Path(__file__).parent / 'prompt_library'
ORIGIN = 'https://github.com/clockless-org/html-anything'
COMMIT = '1896831a62670eed7424b8f8e37e56c66cbf2351'
SELECTION = {
    'teaching.md': ['Underlying System: Lesson Lab', 'Teaching Voice', 'Avoid'],
    '_system.md': ['Style Fidelity Contract', 'Interaction And Motion Contract', 'Anti-Slop Gate', 'UI Quality Gate'],
    '_design.md': ['Tone & rules'],
}


def section(filename, title):
    source = (ROOT / filename).read_text(encoding='utf-8')
    match = re.search(r'^## ' + re.escape(title) + r'\s*\n(.*?)(?=^## |\Z)', source, re.M | re.S)
    if not match:
        raise RuntimeError(f'Missing selected prompt section: {filename}/{title}')
    return '## ' + title + '\n' + match[1].strip()


def selected_rules(stage):
    if stage == 'plan':
        return section('teaching.md', 'Teaching Voice')
    parts = []
    for filename, headings in SELECTION.items():
        for heading in headings:
            content = section(filename, heading)
            if filename == '_design.md':
                # Keep reusable scales; do not inject Clockless branding or web fonts.
                bullets = re.split(r'\n(?=- )', content.partition('\n')[2])
                content = '## Tone & rules\n' + '\n'.join(
                    b for b in bullets if any(b.startswith('- **Use the '+s+' scale**') for s in ('spacing', 'radius', 'shadow')))
            parts.append(content)
    return '\n\n'.join(parts)


def prompt_sources(stage):
    selected = {'teaching.md': ['Teaching Voice']} if stage == 'plan' else SELECTION
    return [dict(origin=ORIGIN, commit=COMMIT, path='prompts/styles/'+name,
                 sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest(), sections=headings,
                 selection='spacing/radius/shadow scale bullets only' if name == '_design.md' else 'selected sections')
            for name, headings in selected.items()]


def interaction_sources():
    package = Path(__file__).parent
    return [dict(path=path, sha256=hashlib.sha256((package/path).read_bytes()).hexdigest(),
                 origin='Teach Agent original implementation; behavioral references in interaction-guide.md')
            for path in ('experiment_library/interaction-guide.md', 'static/interaction.js')]
