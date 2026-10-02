"""Start the shared local service on demand; no browser or stdout required."""
import asyncio
import json
import socket
from contextlib import nullcontext
from urllib.parse import urlsplit

import httpx
import uvicorn

from .app import create_app
from .config import Settings


class EmbeddedServer(uvicorn.Server):
    def capture_signals(self):
        # The stdio MCP host owns process signals.
        return nullcontext()

    async def serve(self, sockets=None):
        try:
            await super().serve(sockets=sockets)
        except SystemExit:
            # Uvicorn uses process exit for lifespan failure. In an MCP process,
            # a losing instance-lock race must allow reuse of the winning server.
            self.should_exit = True


class LocalRuntime:
    def __init__(self, root, app_factory=create_app):
        self.settings = Settings(root)
        self.app_factory = app_factory
        self.lock = asyncio.Lock()
        self.server = None
        self.task = None
        self.socket = None
        self.url = None

    async def existing_address(self):
        try:
            url = json.loads((self.settings.root/'server.json').read_text(encoding='utf-8'))['url']
            parsed = urlsplit(url)
            if (parsed.scheme != 'http' or parsed.hostname not in ('127.0.0.1','localhost','::1')
                    or parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment
                    or not parsed.port):
                return None
            async with httpx.AsyncClient(timeout=1, trust_env=False) as client:
                response = await client.get(url+'/api/status',
                    headers={'Authorization':'Bearer '+self.settings.token})
            if response.status_code == 200 and response.json().get('standalone_export') is True:
                return url
        except (OSError, ValueError, KeyError, TypeError, httpx.HTTPError):
            pass
        return None

    async def address(self):
        async with self.lock:
            if self.task and not self.task.done() and self.server.started:
                return self.url
            existing = await self.existing_address()
            if existing:
                return existing
            await self.close()
            app = self.app_factory(self.settings.root)
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.bind(('127.0.0.1', 0))
            self.url = 'http://127.0.0.1:'+str(self.socket.getsockname()[1])
            app.state.server_url = self.url
            self.server = EmbeddedServer(uvicorn.Config(app, log_level='warning', access_log=False,
                timeout_graceful_shutdown=5))
            self.task = asyncio.create_task(self.server.serve(sockets=[self.socket]))
            for _ in range(200):
                if self.server.started:
                    return self.url
                if self.task.done():
                    break
                await asyncio.sleep(.05)
            await self.close()
            # Another MCP process may have won the per-data-directory instance lock.
            for _ in range(10):
                existing = await self.existing_address()
                if existing:
                    return existing
                await asyncio.sleep(.1)
            raise RuntimeError('本地制作服务启动失败，请重新连接；已有作品已保留。')

    async def close(self):
        if self.server:
            self.server.should_exit = True
        if self.task:
            try:
                await asyncio.wait_for(asyncio.gather(self.task, return_exceptions=True), timeout=8)
            except asyncio.TimeoutError:
                self.task.cancel()
                await asyncio.gather(self.task, return_exceptions=True)
            finally:
                self.task = None
        if self.socket:
            self.socket.close()
        self.socket = self.server = None
