import asyncio
from typing import Callable

from .executor import Executor

Checker = Callable[..., bool]

class Condition:

    __slots__ = ('checkers')
    
    def __init__(self, *checkers: Checker|Executor):
        self.checkers = [checker if isinstance(checker, Executor) else Executor.new(checker) for checker in checkers] #type: ignore
    
    async def __call__(self, *args):
        try:
            result = all(await asyncio.gather(*(exc(*args) for exc in self.checkers)))
        except Exception:
            result = False
        return result
    
    def __and__(self, other):
        if other is None:
            return self
        elif isinstance(other, Condition):
            return Condition(*self.checkers, *other.checkers)
        else:
            return Condition(*self.checkers, other)
        
    def __rand__(self, other):
        if other is None:
            return self
        elif isinstance(other, Condition):
            return Condition(*other.checkers, *self.checkers)
        else:
            return Condition(other, *self.checkers)

__all__ = [
    'Condition',
]