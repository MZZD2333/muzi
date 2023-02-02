from functools import partial
from typing import Any, Coroutine, Callable

import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseSettings

from .event import Event, get_event, log_event
from .exception import ExecuteDone, ExecuteError, PreExecuteError, ConnectionFailed
from .log import logger
from .plugin import Plugin, Executor

try:
    import ujson as json
except:
    import json

ApiCall = partial[Coroutine[Any, Any, None]]

class BotSettings(BaseSettings):
    host: str = '127.0.0.1'
    port: int = 5700
    ws_path: str = ''
    superuser: set[int] = set()

class Bot:
    qid: int
    superuser: set[int]
    plugins_path: list[str] = []
    plugins: list[Plugin] = []

    def __init__(self, setting: BotSettings) -> None:
        self.setting = setting
        self.server = Server(self)
        self.server.set_websocket(setting.ws_path)
    
        self.superuser = setting.superuser

    def __getattr__(self, name: str) -> ApiCall:
        return partial(self.call_api, name)

    async def call_api(self, api: str, **data):
        await self.server.call_api(api, **data)

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
                    data = await websocket.receive_json()
                    if event := get_event(data):
                        await self.bot.handle_event(event)
            except:
                await self.on_bot_disconnect()
                
        self._server_app.add_api_websocket_route(path, handle_ws)

    async def call_api(self, api, **data):
        json_data = json.dumps({'action': api, 'params': data})
        await self._send(json_data)

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