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
    version: str
    usage_text: str
    usage_image_path: str
    status_tracing: Callable|None
    type: int
    hide: bool

    @property
    def available(self) -> bool:
        if self.status_tracing:
            return self.status_tracing().get('available', True)
        else:
            return True

    @property
    def risk(self) -> bool:
        if self.status_tracing:
            return self.status_tracing().get('risk', False)
        else:
            return False

    @property
    def status(self):
        if self.status_tracing:
            return self.status_tracing()
        else:
            return {}

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
        default_metadata = {'name': path, 'version': '1.0', 'usage_text': 'None', 'usage_image_path': '', 'status_tracing': None, 'type': 0, 'hide': False}
        if custom_metadata := getattr(module, '__metadata__', None):
            default_metadata.update(custom_metadata)
            metadata = PluginMetadata(**default_metadata)
        else:
            metadata = PluginMetadata(**default_metadata)
        return Plugin(path, triggers, metadata)

def load_plugin(path: str):
    if plugin := get_plugin(path):
        bot = current_bot.get()
        bot.plugins.append(plugin)
        bot.plugins.sort(key=lambda p: p.metadata.name)
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