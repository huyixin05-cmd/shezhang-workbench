"""Build one offline lesson using the installed materials and interaction helper."""
import re
import sys
import base64
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from teach_agent.materials import Materials
from teach_agent.artifacts import assemble_page,add_notices


def build():
    here=Path(__file__).parent
    source=(here/'source.html').read_text(encoding='utf-8')
    cart=(ROOT/'teach_agent/vendor/olc/components/physics/mechanics/phy.mechanics.cart.dynamics.html').read_text(encoding='utf-8')
    # Preserve upstream cart geometry; this lesson controls only color and mass-slot visibility.
    svg=re.search(r'<svg\b[^>]*>(.*?)</svg>',cart,re.S).group(1)
    folder=ROOT/'dist/examples/acceleration'
    folder.mkdir(parents=True,exist_ok=True)
    video=folder/'加速度的影响因素-讲解.mp4'
    payload=base64.b64encode(video.read_bytes()).decode('ascii') if video.exists() else ''
    source=source.replace('{{CART_SVG}}',svg).replace('{{STYLE}}',(here/'style.css').read_text(encoding='utf-8')).replace('{{SCRIPT}}',(here/'lesson.js').read_text(encoding='utf-8')).replace('{{VIDEO_DATA}}',payload)
    page=add_notices(assemble_page(Materials().expand(source,[])))
    path=folder/'加速度的影响因素.html'
    path.write_text(page,encoding='utf-8')
    print(str(path))
    return path


if __name__=='__main__':build()
