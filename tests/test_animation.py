import pytest
from teach_agent.animation import validate_params, inspect_video


@pytest.mark.parametrize('params', [
    {'force1':float('nan')}, {'angle':181}, {'force2':-2}, {'hold':100},
    {'template':'arbitrary_python'}, {'force1':'__import__("os")'},
])
def test_untrusted_template_parameters_rejected(params):
    with pytest.raises(ValueError):
        validate_params(params)


def test_force_template_defaults_are_bounded():
    p=validate_params({'template':'force_composition','force1':3,'force2':4,'angle':90})
    assert p['force1']==3 and p['force2']==4 and p['angle']==90
    assert 1<=p['hold']<=5


def test_non_video_upload_is_rejected(tmp_path):
    path=tmp_path/'fake.mp4'
    path.write_bytes(b'not a video')
    with pytest.raises(ValueError):
        inspect_video(path)
