import importlib
import inspect
import os
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from ..log import logger
from .trigger import Trigger, current_bot


@dataclass(eq=False)
class PluginMetadata:
    name: str
    version: str = ''
    usage_text: str = ''
    usage_image_path: str = ''
    status_tracing: Callable[..., dict]|None = None
    type: int = 0
    hide: bool = False

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
    module: ModuleType
    module_path: str
    triggers: list[Trigger]

    metadata: PluginMetadata

    enable: bool = True

    def reload(self):
        self.module = importlib.reload(self.module)
        logger.success(f'<g>Plugin</g> [<y>{self.module_path}</y>] reloads successfully!')

    def disable(self, v: bool = True):
        self.enable = not v


def get_plugin(path: str, allow_load_plugin_without_trigger: bool = False, hide_plugin_without_trigger: bool = True):
    try:
        module = importlib.import_module(path)
        if instances := inspect.getmembers(module, lambda x: (isinstance(x, Trigger))):
            for name, trigger in instances:
                trigger._instance_name = name
            default_metadata = {'name': path.split('.')[-1]}
            if custom_metadata := getattr(module, '__metadata__', None):
                default_metadata.update(custom_metadata)
            triggers:list[Trigger] = sorted([t[1] for t in instances], key=lambda t: t.priority)
            metadata = PluginMetadata(**default_metadata)
            return Plugin(module, path, triggers, metadata)
        elif allow_load_plugin_without_trigger:
            default_metadata = {'name': path.split('.')[-1], 'hide': len(instances)<=hide_plugin_without_trigger, 'enable': len(instances)>0}
            if custom_metadata := getattr(module, '__metadata__', None):
                default_metadata.update(custom_metadata)
            metadata = PluginMetadata(**default_metadata)
            return Plugin(module, path, list(), metadata)
        else:
            logger.warning(f'<g>Plugin</g> [<y>{path}</y>] 0 trigger was detected!')
    except:
        logger.error(f'<g>Plugin</g> [<y>{path}</y>] Initialization failed!')

def load_plugin(path: str):
    bot = current_bot.get()
    allow_load_plugin_without_trigger = bot.config.extra_config['allow_load_plugin_without_trigger']
    hide_plugin_without_trigger = bot.config.extra_config['hide_plugin_without_trigger']
    if plugin := get_plugin(path, allow_load_plugin_without_trigger, hide_plugin_without_trigger):
        bot.plugins.append(plugin)
        bot.plugins.sort(key=lambda p: p.metadata.name)
        logger.success(f'<g>Plugin</g> [<y>{path}</y>] loads successfully!')

def load_plugin_dir(path: str):
    file_list = os.listdir(path)
    module_path = path.rstrip('/').lstrip('.').replace('/', '.')+'.'
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