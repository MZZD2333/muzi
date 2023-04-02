import inspect
from dataclasses import dataclass, field
from typing import Iterable, Callable

@dataclass(eq=False, frozen=True)
class Executor:
    func: Callable
    pre_excute: Iterable[Callable] = field(default_factory=list)
    params_annotation: Iterable = field(default_factory=tuple)

    async def __call__(self, *args):
        for pre in self.pre_excute:
            if inspect.iscoroutinefunction(pre):
                await pre(*(self.get_params(pre, args)))
            else:
                pre(*(self.get_params(pre, args)))

        if inspect.iscoroutinefunction(self.func):
            result = await self.func(*(self.get_params(self.func, args)))
        else:
            result = self.func(*(self.get_params(self.func, args)))
        return result

    @classmethod
    def new(cls, func: Callable, pre_excute: Iterable[Callable]|None = None):
        pre_excute = list() if pre_excute is None else pre_excute
        params_annotation = tuple(cls.get_annotations(func))
        return cls(func, pre_excute, params_annotation)
    
    @staticmethod
    def get_annotations(func: Callable):
        return (p.annotation for p in inspect.signature(func).parameters.values())

    def get_params(self, func: Callable, args: tuple):
        def get(t):
            for arg in args:
                if isinstance(arg, t):
                    return arg
        return tuple(get(t) for t in self.get_annotations(func))

    def validate(self, *args) -> bool:
        return all(any(isinstance(arg, t) for arg in args) for t in self.params_annotation)

__all__ = [
    'Executor',
]