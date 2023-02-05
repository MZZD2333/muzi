import asyncio
import json
import time
from functools import partial
from typing import Any, Callable, Coroutine

import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseSettings

from .event import Event, get_event, log_event
from .exception import ConnectionFailed, ExecuteError, PreExecuteError
from .log import logger
from .plugin import Executor, Plugin
from .message import JSONEncoder

ApiCall = partial[Coroutine[Any, Any, Any]]

class BotSettings(BaseSettings):
    host: str = '127.0.0.1'
    port: int = 5700
    ws_path: str = '/ws'
    superusers: set[int] = set()
    api_timeout: float = 15.0
    

class Bot:
    qid: int
    superusers: set[int]
    plugins_path: list[str] = []
    plugins: list[Plugin] = []

    def __init__(self, setting: BotSettings) -> None:
        self.setting = setting
        self.server = Server(self)
        self.server.set_websocket(setting.ws_path)
    
        self.superusers = setting.superusers

    def __getattr__(self, name: str) -> ApiCall:
        return partial(self.call_api, name)

    async def call_api(self, api: str, **data):
        return await self.server.call_api(api, **data)

    def run(self):
        uvicorn.run(self.server.asgi, host=self.setting.host, port=self.setting.port)

    def reload(self):...

    async def handle_event(self, event: Event):
        log_event(event)
        for plugin in self.plugins:
            for trigger in plugin.triggers:
                if await trigger._check(event):
                    logger.info(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger.__instance_name__}</g>] will be executed.')
                    try:
                        await trigger.execute_functions()
                    except (PreExecuteError, ExecuteError) as e:
                        logger.error(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger.__instance_name__}</g>] <r>catch an exception.</r> {e.info}')
                    else:
                        logger.success(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger.__instance_name__}</g>] execute complete.')


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

class Server:
    bot: Bot
    websocket: WebSocket

    _on_bot_connect: list[Executor] = []
    _on_bot_disconnect: list[Executor] = []

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
            else:
                raise ConnectionFailed

            await self.on_bot_connect()

            try:
                while True:
                    data: dict = await websocket.receive_json()
                    if 'post_type' in data:
                        if event := get_event(data):
                            asyncio.create_task(self.bot.handle_event(event))
                    else:
                        self._store_api_result(data)
            except:
                await self.on_bot_disconnect()
                
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
        feture = self._api_result[echo]
        feture.set_result(data)

    async def _fetch_api_result(self, echo):
        future = asyncio.get_event_loop().create_future()
        self._api_result[echo] = future
        try:
            data = await asyncio.wait_for(future, timeout=self.bot.setting.api_timeout)
            if not isinstance(data, dict):
                pass
            elif data['status'] == 'failed':
                pass
            return data
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

    @property
    def asgi(self):
        return self._server_app
    
__all__ = [
    'Bot',
    'BaseSettings'
]