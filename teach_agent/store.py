"""Small transactional store. IDs, not caller-supplied paths, address records."""
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def now():
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.db = self.root / 'workspace.sqlite3'
        with self.tx() as con:
            for table in ('projects', 'jobs', 'versions'):
                con.execute(f'CREATE TABLE IF NOT EXISTS {table} (id TEXT PRIMARY KEY, data TEXT NOT NULL)')

    @contextmanager
    def tx(self):
        con = sqlite3.connect(self.db, timeout=15)
        try:
            con.execute('BEGIN IMMEDIATE')
            yield con
            con.commit()
        except BaseException:
            con.rollback()
            raise
        finally:
            con.close()

    def _get(self, con, table, ident):
        row = con.execute(f'SELECT data FROM {table} WHERE id=?', (ident,)).fetchone()
        if not row:
            raise KeyError('记录不存在')
        return json.loads(row[0])

    def _put(self, con, table, value):
        con.execute(f'INSERT OR REPLACE INTO {table} VALUES (?,?)',
                    (value['id'], json.dumps(value, ensure_ascii=False)))

    def _all(self, con, table):
        return [json.loads(row[0]) for row in con.execute(f'SELECT data FROM {table} ORDER BY rowid DESC')]

    def get(self, table, ident):
        with self.tx() as con:
            return self._get(con, table, ident)

    def project(self, ident):
        return self.get('projects', ident)

    def job(self, ident):
        return self.get('jobs', ident)

    def version(self, ident):
        return self.get('versions', ident)

    def projects(self):
        with self.tx() as con:
            return self._all(con, 'projects')

    def versions(self, project_id):
        with self.tx() as con:
            return [v for v in self._all(con, 'versions') if v['project_id'] == project_id]

    def jobs(self, project_id=None):
        with self.tx() as con:
            return [v for v in self._all(con, 'jobs') if project_id is None or v['project_id'] == project_id]

    def create_project(self, request, kind):
        p = dict(id=uuid4().hex, request=request, kind=kind, title=request[:40],
                 plan=None, plan_revision=0, confirmed_revision=None, created_at=now())
        with self.tx() as con:
            self._put(con, 'projects', p)
        return p

    def save_plan(self, ident, plan, expected_revision):
        with self.tx() as con:
            p = self._get(con, 'projects', ident)
            if p['plan_revision'] != expected_revision:
                raise ValueError('方案已更新，请重新查看后再修改')
            p.update(plan=plan, plan_revision=expected_revision + 1,
                     confirmed_revision=None, title=plan['title'])
            self._put(con, 'projects', p)
            return p

    def confirm(self, ident, revision):
        with self.tx() as con:
            p = self._get(con, 'projects', ident)
            if not p['plan'] or revision != p['plan_revision']:
                raise ValueError('请确认当前版本的教学方案')
            p['confirmed_revision'] = revision
            self._put(con, 'projects', p)

    def new_job(self, project_id, kind, inputs):
        with self.tx() as con:
            p = self._get(con, 'projects', project_id)
            if any(j['project_id'] == project_id and j['status'] in ('queued', 'running')
                   for j in self._all(con, 'jobs')):
                raise ValueError('这个作品已有任务，请完成或取消后再操作')
            inputs = dict(inputs)
            if kind == 'build':
                revision = inputs.get('revision')
                if not p['plan'] or revision != p['plan_revision'] or revision != p['confirmed_revision']:
                    raise ValueError('方案尚未确认，不能开始制作')
                inputs['plan'] = p['plan']
            j = dict(id=uuid4().hex, project_id=project_id, kind=kind, input=inputs,
                     status='queued', stage='排队中', created_at=now(), updated_at=now(), error=None)
            self._put(con, 'jobs', j)
            return j

    def update_job(self, ident, **changes):
        with self.tx() as con:
            j = self._get(con, 'jobs', ident)
            j.update(changes, updated_at=now())
            self._put(con, 'jobs', j)
            return j

    def save_version(self, project_id, info):
        v = dict(info, id=uuid4().hex, project_id=project_id, created_at=now())
        with self.tx() as con:
            self._get(con, 'projects', project_id)
            self._put(con, 'versions', v)
        return v

    def recover(self):
        with self.tx() as con:
            for j in self._all(con, 'jobs'):
                if j['status'] in ('queued', 'running'):
                    j.update(status='interrupted', stage='服务重启，任务中断；可重新提交', updated_at=now())
                    self._put(con, 'jobs', j)
