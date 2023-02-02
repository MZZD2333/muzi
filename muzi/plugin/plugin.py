import importlib
import inspect
import os
from dataclasses import dataclass
from typing import Callable

from ..log import logger
from .trigger import Trigger, current_bot


@dataclass()
class PluginMetadata:
    name: str
    version: str = '1.0'
    usage_text: str = 'None'
    usage_image_path: str|None = None
    status_tracing: Callable|None = None
    type: int = 0


@dataclass(eq=False)
class Plugin:
    module_path: str
    triggers: list[Trigger]

    metadata: PluginMetadata


def get_plugin(path: str):
    module = importlib.import_module(path)
    if instances := inspect.getmembers(module, lambda x: (isinstance(x, Trigger))):
        for name, trigger in instances:
            trigger.__instance_name__ = name
        triggers:list[Trigger] = sorted([t[1] for t in instances], key=lambda t: t.priority)
        if custom := getattr(module, '__metadata__', None):
            metadata = PluginMetadata(**custom)
        else:
            metadata = PluginMetadata(name=path)
        return Plugin(path, triggers, metadata)

def load_plugin(path: str):
    if plugin := get_plugin(path):
        bot = current_bot.get()
        bot.plugins.append(plugin)
        
        logger.success(f'<g>Plugin</g> [<y>{path}</y>] loads successfully!')
    else:
        logger.warning(f'<g>Plugin</g> [<y>{path}</y>] loads unsuccessfully!')

def load_plugin_dir(path: str):
    file_list = os.listdir(path)
    module_path = path.rstrip('/').replace('/', '.')+'.'
    for file in file_list:
        if not file.startswith('__'):
            if file.endswith('.py'):
                load_plugin(module_path+file[:-3])
            else:
                load_plugin(module_path+file)


__all__ = [
    'Plugin',
    'PluginMetadata',
    'load_plugin',
    'load_plugin_dir',
]