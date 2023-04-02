import asyncio
import re
from contextvars import ContextVar
from typing import TYPE_CHECKING, Callable, Iterable, NoReturn, Type

from ..event import Event, MessageEvent
from ..exception import ExecuteDone
from ..message import CQcode, Message
from .condition import Condition
from .executor import Executor

if TYPE_CHECKING:
    from ..bot import Bot

current_bot: ContextVar['Bot'] = ContextVar('current_bot')
current_event: ContextVar[Event] = ContextVar('current_event')
current_result: ContextVar[dict] = ContextVar('current_result')

class Trigger:

    __slots__ = ('detector', 'event', 'condition', 'priority', 'block', 'executors', '_instance_name')

    def __init__(self, detector: Callable[..., bool], event: Type[Event] = Event, condition: Condition|None = None, priority: int = 1, block: bool = False):
        self.detector = Executor.new(detector)
        self.event: Type[Event] = event
        self.condition: Condition = condition or Condition()
        self.priority: int = priority
        self.executors: list[Executor]  = []
        self._instance_name: str = ''
        self.block: bool = block

    def excute(self, pre_excute: Iterable[Callable]|None = None):
        def wrap(func):
            self._append_executor(func, pre_excute)
            return func
        return wrap

    def _append_executor(self, func, pre_excute):
        executor = Executor.new(func, pre_excute)
        self.executors.append(executor)

    async def _check(self, event: Event):
        bot = current_bot.get()
        if not isinstance(event, self.event):
            return
        if not await self.condition(bot, event):
            return
        if not await self.detector(bot, event):
            return
        current_event.set(event)
        
        return True

    async def execute_functions(self):
        bot = current_bot.get()
        event = current_event.get()
        result = current_result.get()
        for executor in self.executors:
            if executor.validate(self, bot, event, result):
                try:
                    await executor(self, bot, event, result)
                except ExecuteDone:
                    break

    @classmethod
    def _new(cls, detector: Callable[..., bool], event: Type[Event] = Event, condition: Condition|None = None, priority: int = 1, block: bool = False):
        return cls(detector, event, condition, priority, block)

    async def send(self, message: Message|str|CQcode, at_sender: bool = False):
        bot = current_bot.get()
        event = current_event.get()
        event_dict = event.dict()
        params = {}

        group_id = event_dict.get('group_id', None)
        user_id = event_dict.get('user_id', None)
        if group_id:
            params['group_id'] = group_id
        elif user_id:
            params['user_id'] = user_id
        else:
            return
        message = Message() + message
        if at_sender and group_id and user_id:
            message = CQcode.at(str(user_id)) + message
        params['message'] = message.message
        
        await bot.send(**params)

    async def call_api(self, name, **kwargs):
        bot = current_bot.get()

        await bot.call_api(name, **kwargs)     

    async def done(self, message: Message|str|None = None, at_sender: bool = False) -> NoReturn:
        if message:
            await self.send(message, at_sender)

        raise ExecuteDone




def on_event(event: Type[Event], condition: Condition|None = None, priority: int = 1, block: bool = False):
    def detector():
        current_result.set(dict())
        return True
    return Trigger._new(detector, event, condition, priority, block)


def on_regex(pattern: str|re.Pattern, flags: re.RegexFlag = re.S, condition: Condition|None = None, priority: int = 1, block: bool = False):
    def detector(e: MessageEvent):
        if match_ := re.search(pattern, e.raw_message, flags):
            current_result.set({'matched_groupdict': match_.groupdict(), 'matched_groups': match_.groups(), 'mateched_text': match_.string})
            return True
        return False
    return Trigger._new(detector, MessageEvent, condition, priority, block)

__all__ = [
    'Trigger',
    'on_event',
    'on_regex',
    'current_bot',
    
]