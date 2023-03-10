import importlib
import inspect
import os
from dataclasses import dataclass
from typing import Callable

from ..log import logger
from .trigger import Trigger, current_bot

@dataclass(eq=False)
class PluginMetadata:
    name: str
    version: str
    usage_text: str
    usage_image_path: str
    status_tracing: Callable[..., dict]|None
    type: int
    hide: bool

    @property
    def status(self):
        return self.status_tracing() if self.status_tracing else {}

    @property
    def available(self) -> bool:
        return self.status.get('available', True)

    @property
    def risk(self) -> bool:
        return self.status.get('risk', False)


@dataclass(eq=False)
class Plugin:
    module_path: str
    triggers: list[Trigger]

    metadata: PluginMetadata


def get_plugin(path: str):
    try:
        module = importlib.import_module(path)
        if instances := inspect.getmembers(module, lambda x: (isinstance(x, Trigger))):
            for name, trigger in instances:
                trigger._instance_name = name
            triggers:list[Trigger] = sorted([t[1] for t in instances], key=lambda t: t.priority)
            default_metadata = {'name': path, 'version': '1.0', 'usage_text': 'None', 'usage_image_path': '', 'status_tracing': None, 'type': 0, 'hide': False}
            if custom_metadata := getattr(module, '__metadata__', None):
                default_metadata.update(custom_metadata)
            metadata = PluginMetadata(**default_metadata)
            return Plugin(path, triggers, metadata)
        else:
            logger.warning(f'<g>Plugin</g> [<y>{path}</y>] 0 triggers detected!')
    except:
        logger.error(f'<g>Plugin</g> [<y>{path}</y>] Initialization failed!')

def load_plugin(path: str):
    if plugin := get_plugin(path):
        bot = current_bot.get()
        bot.plugins.append(plugin)
        bot.plugins.sort(key=lambda p: p.metadata.name)
        logger.success(f'<g>Plugin</g> [<y>{path}</y>] loads successfully!')

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