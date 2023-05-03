import asyncio
import atexit
import json
import sys
import time
from datetime import datetime
from functools import partial
from itertools import chain
from pathlib import Path
from typing import Any, Callable, Coroutine

import uvicorn
from fastapi import FastAPI, WebSocket
from pydantic import BaseSettings, Extra

from .event import Event, HeartbeatMetaEvent, MetaEvent, get_event, log_event
from .exception import ActionFailed, ConnectionFailed, ExecuteDone
from .log import logger
from .message import JSONEncoder
from .plugin import Executor, Plugin
from .utils import get_exception_local


ApiCall = partial[Coroutine[Any, Any, Any]]


class BotConfig(BaseSettings):
    host: str
    port: int
    ws_path: str
    superusers: list[int]
    api_timeout: float
    auto_reconnect: bool

    data_path: str
    config_path: str
    extra_config: dict

    class Config:
        extra = Extra.ignore

    def save(self):
        with open(self.config_path, 'w', encoding='UTF-8') as f:
            json.dump(self.dict(), f, ensure_ascii=False, indent=4)


class Bot:
    qid: int
    bootdate: datetime
    plugins: list[Plugin] = list()
    config: BotConfig

    _connected: bool = False
    _reboot: bool = False

    def __init__(self, config: BotConfig) -> None:
        self.config = config

        self.server = Server(self)
        self.server.set_websocket(config.ws_path)
        Path(self.config.data_path).mkdir(exist_ok=True, parents=True)
    
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
    
    def on_connect(self, func: Callable|None = None, temp: bool = False):
        def wrap(func):
            excutor = Executor.new(func)
            if temp:
                self.server._on_bot_connect_temp.append(excutor)
            else:
                self.server._on_bot_connect.append(excutor)
            return func
        return wrap(func) if func is not None else wrap

    def on_disconnect(self, func: Callable|None = None, temp: bool = False):
        def wrap(func):
            excutor = Executor.new(func)
            if temp:
                self.server._on_bot_disconnect_temp.append(excutor)
            else:
                self.server._on_bot_disconnect.append(excutor)
            return func
        return wrap(func) if func is not None else wrap

    def run(self):
        uvicorn.run(self.server.asgi, host=self.config.host, port=self.config.port)

    def reboot(self):
        self._connected = False
        self._reboot = True
        logger.warning(f'<y>Bot</y> [<c>{self.qid}</c>] <y>is rebooting.</y>')

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
                    logger.info(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] will handle this event.')
                    await logger.complete()
                    try:
                        await trigger.execute_functions()
                    except ExecuteDone:
                        pass
                    except Exception as e:
                        local = '\n'.join(get_exception_local(e))
                        logger.info(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] <r>catch an exception.</r>\n{local}\n<r>{e}</r>')
                        if trigger.block:
                            break
                        continue
                    logger.info(f'<y>Trigger</y> [<m>{plugin.module_path}</m>.<g>{trigger._instance_name}</g>] <c>execute completely</c>.')
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
                self.bot._connected = True
            else:
                raise ConnectionFailed
            
            self.bot.bootdate = datetime.now()

            asyncio.create_task(self.on_bot_connect())

            try:
                while self.bot._connected:
                    data = await websocket.receive_json()
                    if 'post_type' in data:
                        if event := get_event(data):
                            asyncio.create_task(self.bot.handle_event(event))
                    else:
                        self._store_api_result(data)
                if self.bot._reboot:
                    self.bot._reboot = False
                    atexit.register(self.bot.run)
                asyncio.create_task(self.on_bot_disconnect())
                await self.websocket.close()
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
            data = await asyncio.wait_for(future, timeout=self.bot.config.api_timeout)
            if data['status'] == 'failed':
                raise ActionFailed(data)
            return data.get('data', dict())
        finally:
            del self._api_result[echo]

    async def _send(self, data):
        await self.websocket.send({'type': 'websocket.send', 'text': data})

    async def on_bot_connect(self):
        for exc in chain(self._on_bot_connect, self._on_bot_connect_temp):
            try:
                await exc(self.bot)
            except ExecuteDone:
                pass
            except Exception as e:
                local = '\n'.join(get_exception_local(e))
                logger.info(f'<r>An exception occurred on bot connected</r>.\n{local}\n<r>{e}</r>')
        self._on_bot_connect_temp.clear()

    async def on_bot_disconnect(self):
        for exc in chain(self._on_bot_disconnect, self._on_bot_disconnect_temp):
            try:
                await exc()
            except ExecuteDone:
                pass
            except Exception as e:
                local = '\n'.join(get_exception_local(e))
                logger.info(f'<r>An exception occurred on bot disconnected</r>.\n{local}\n<r>{e}</r>')
        self._on_bot_disconnect_temp.clear()


    @property
    def asgi(self):
        return self._server_app
    
__all__ = [
    'Bot',
    'BotConfig'
]