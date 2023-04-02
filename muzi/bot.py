import asyncio
import atexit
import json
import sys
import time
from functools import partial
from typing import Any, Callable, Coroutine

import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseSettings

from .event import Event, HeartbeatMetaEvent, MetaEvent, get_event, log_event
from .exception import ActionFailed, ConnectionFailed, ExecuteDone
from .log import logger
from .message import JSONEncoder
from .plugin import Executor, Plugin
from .utils import get_exception_local

ApiCall = partial[Coroutine[Any, Any, Any]]

class BotSettings(BaseSettings):
    host: str = '127.0.0.1'
    port: int = 5700
    ws_path: str = '/ws'
    superusers: set[int] = set()
    api_timeout: float = 15.0
    auto_reconnect: bool = False
    default_receive_timeout = 120

class Bot:
    qid: int
    superusers: set[int]
    auto_reconnect: bool

    plugins: list[Plugin] = []

    connected: bool = False

    _reboot: bool = False

    def __init__(self, setting: BotSettings) -> None:
        self.setting = setting
        self.superusers = setting.superusers
        self.auto_reconnect = setting.auto_reconnect

        self.server = Server(self)
        self.server.set_websocket(setting.ws_path)
    
    def __getattr__(self, name: str) -> ApiCall:
        return partial(self.call_api, name)

    async def call_api(self, api: str, **data):
        return await self.server.call_api(api, **data)

    def on_startup(self, func: Callable):
        self.server._server_app.on_event('startup')(func)
        return func
    
    def on_shutdown(self, func: Callable):
        self.server._server_app.on_event('shutdown')(func)
        return func
    
    def on_connect(self, func: Callable):
        excutor = Executor.new(func)
        self.server._on_bot_connect.append(excutor)
        return func

    def on_disconnect(self, func: Callable):
        excutor = Executor.new(func)
        self.server._on_bot_disconnect.append(excutor)
        return func

    def on_connect_temp(self, func: Callable):
        excutor = Executor.new(func)
        self.server._on_bot_connect_temp.append(excutor)
        return func

    def on_disconnect_temp(self, func: Callable):
        excutor = Executor.new(func)
        self.server._on_bot_disconnect_temp.append(excutor)
        return func

    def run(self):
        uvicorn.run(self.server.asgi, host=self.setting.host, port=self.setting.port)

    def reboot(self):
        self.connected = False
        self._reboot = True
        logger.warning(f'<y>Bot is rebooting now.</y>')

    async def handle_event(self, event: Event):
        if isinstance(event, MetaEvent):
            if isinstance(event, HeartbeatMetaEvent):
                if not event.status.online:
                    self._connected = False
                    return
        else:
            log_event(event)
            for plugin in self.plugins:
                if not plugin.enable:
                    continue
                for trigger in plugin.triggers:
                    if not await trigger._check(event):
                        continue
                    logger.info(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] will be executed.')
                    try:
                        await trigger.execute_functions()
                    except ExecuteDone:
                        logger.success(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] execute complete.')
                    except Exception as e:
                        local = '\n'.join(get_exception_local(e))
                        logger.error(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] <r>catch an exception.</r>\n{local}\n<r>{e}</r>')
                    else:
                        logger.success(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] execute complete.')
                    if trigger.block:
                        break
                else:
                    continue
                break


class Server:
    bot: Bot
    websocket: WebSocket

    _on_bot_connect: list[Executor] = []
    _on_bot_disconnect: list[Executor] = []

    _on_bot_connect_temp: list[Executor] = []
    _on_bot_disconnect_temp: list[Executor] = []

    _api_result: dict[str, asyncio.Future] = {}

    def __init__(self, bot) -> None:
        self.bot = bot
        self._server_app = FastAPI()
        
    def set_websocket(self, path):
        async def handle_ws(websocket: WebSocket):
            await websocket.accept()

            self.websocket = websocket
            if qid := websocket.headers.get('x-self-id', None):
                self.bot.qid = int(qid)
                self.bot.connected = True
            else:
                raise ConnectionFailed

            await self.on_bot_connect()
            await self.on_bot_connect_temp()

            try:
                while self.bot.connected:
                    data = await websocket.receive_json()
                    if 'post_type' in data:
                        if event := get_event(data):
                            asyncio.create_task(self.bot.handle_event(event))
                    else:
                        self._store_api_result(data)
                if self.bot._reboot:
                    self.bot._reboot = False
                    atexit.register(self.bot.run)
                await self.websocket.close()
                await self.on_bot_disconnect()
                await self.on_bot_disconnect_temp()
                sys.exit()
            except:
                pass

        self._server_app.add_api_websocket_route(path, handle_ws)

    async def call_api(self, api, **data):
        echo = str(time.time()) 
        json_data = json.dumps({'action': api, 'params': data, 'echo': echo}, cls=JSONEncoder)
        await self._send(json_data)
        try:
            return await self._fetch_api_result(echo)
        except asyncio.TimeoutError:
            return None

    def _store_api_result(self, data):
        echo = data.get('echo')
        if feture := self._api_result.get(echo, None):
            feture.set_result(data)

    async def _fetch_api_result(self, echo):
        future = asyncio.get_event_loop().create_future()
        self._api_result[echo] = future
        try:
            data = await asyncio.wait_for(future, timeout=self.bot.setting.api_timeout)
            if data['status'] == 'failed':
                raise ActionFailed(data)
            return data.get('data', dict())
        finally:
            del self._api_result[echo]

    async def _send(self, data):
        await self.websocket.send({'type': 'websocket.send', 'text': data})

    async def on_bot_connect(self):
        for exc in self._on_bot_connect:
            await exc(self.bot)

    async def on_bot_disconnect(self):
        for exc in self._on_bot_disconnect:
            await exc()

    async def on_bot_connect_temp(self):
        for exc in self._on_bot_connect_temp:
            await exc(self.bot)
        self._on_bot_connect_temp.clear()

    async def on_bot_disconnect_temp(self):
        for exc in self._on_bot_disconnect_temp:
            await exc()
        self._on_bot_disconnect_temp.clear()

    @property
    def asgi(self):
        return self._server_app
    
__all__ = [
    'Bot',
    'BaseSettings'
]