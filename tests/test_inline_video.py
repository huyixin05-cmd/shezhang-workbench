import pytest
from teach_agent.artifacts import assemble_page


def test_blob_video_api_is_not_misread_as_a_css_url():
    page='<html><head></head><body><video></video><script>const src=URL.createObjectURL(new Blob([]));URL.revokeObjectURL(src);</script></body></html>'
    assert 'createObjectURL' in assemble_page(page)


@pytest.mark.parametrize('source',[
    '<style>body{background:url(https://example.test/a.png)}</style>',
    '<style>@import "https://example.test/a.css";</style>',
    '<div style="background:url(https://example.test/a.png)"></div>',
    '<svg><rect fill="url(https://example.test/p.svg#paint)"/></svg>',
    '<svg><path marker-end="url(https://example.test/p.svg#arrow)"/></svg>',
])
def test_external_css_still_rejected(source):
    with pytest.raises(ValueError):
        assemble_page('<html><head></head><body>'+source+'</body></html>')
