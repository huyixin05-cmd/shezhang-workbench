import pytest
from teach_agent.store import Store


def test_unconfirmed_and_stale_plans_cannot_build(tmp_path):
    s = Store(tmp_path)
    p = s.create_project('演示浮力', 'interactive')
    with pytest.raises(ValueError):
        s.new_job(p['id'], 'build', {'revision': 0})
    s.save_plan(p['id'], {'title': '浮力'}, 0)
    s.confirm(p['id'], 1)
    s.save_plan(p['id'], {'title': '排水体积'}, 1)
    with pytest.raises(ValueError):
        s.confirm(p['id'], 1)
    with pytest.raises(ValueError):
        s.new_job(p['id'], 'build', {'revision': 2})
    s.confirm(p['id'], 2)
    job = s.new_job(p['id'], 'build', {'revision': 2})
    assert job['input']['plan']['title'] == '排水体积'
    with pytest.raises(ValueError):
        s.new_job(p['id'], 'build', {'revision': 2})


def test_revision_conflicts_preserve_newest_plan(tmp_path):
    s = Store(tmp_path)
    p = s.create_project('力', 'interactive')
    s.save_plan(p['id'], {'title': '方案一'}, 0)
    with pytest.raises(ValueError):
        s.save_plan(p['id'], {'title': '过期修改'}, 0)
    assert s.project(p['id'])['plan']['title'] == '方案一'


def test_versions_survive_restart_and_jobs_are_interrupted(tmp_path):
    s = Store(tmp_path)
    p = s.create_project('力', 'interactive')
    job = s.new_job(p['id'], 'plan', {})
    v1 = s.save_version(p['id'], {'title': '第一版', 'kind': 'interactive'})
    v2 = s.save_version(p['id'], {'title': '第二版', 'kind': 'interactive'})
    s.recover()
    again = Store(tmp_path)
    assert again.job(job['id'])['status'] == 'interrupted'
    assert again.version(v1['id'])['title'] == '第一版'
    assert v1['id'] != v2['id']
    assert len(again.versions(p['id'])) == 2


def test_missing_records_do_not_leak_arbitrary_paths(tmp_path):
    s = Store(tmp_path)
    with pytest.raises(KeyError):
        s.version('../../config.json')
