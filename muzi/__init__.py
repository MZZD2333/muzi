import json

from .bot import Bot, BotConfig
from .message import CQcode, Message
from .plugin import Condition, Trigger
from .plugin import current_bot as _current_bot
from .plugin import load_plugin, load_plugin_dir, on_event, on_regex

DEFAULT_EXTRA_CONFIG = {
    'allow_load_plugin_without_trigger': False,
    'hide_plugin_without_trigger': True,
}

DEFAULT_CONFIG = {
    'host': '127.0.0.1',
    'port': 5700,
    'ws_path': '/ws',

    'superusers': list(),

    'api_timeout': 15.0,
    'auto_reconnect': False,

    'data_path': './data',
    'config_path': './config.json',
}

def init(config: dict|str = dict()):
    '''
    ## 初始化bot
    '''
    global _current_bot
    _config = DEFAULT_CONFIG
    _extra_config = DEFAULT_EXTRA_CONFIG
    if isinstance(config, str):
        with open(config, 'r', encoding='UTF-8') as f:
            config_ = json.load(f)
    else:
        config_ = config
    _extra_config.update(config_.pop('extra_config', {}))
    _config.update(config_)
    _config['extra_config'] = _extra_config
    botconfig = BotConfig(**_config)
    bot = Bot(botconfig)
    _current_bot.set(bot)

    return bot

def get_bot():
    '''
    ## 获取当前bot
    '''
    global _current_bot
    return _current_bot.get()

def run():
    '''
    ## 启动当前bot
    '''
    global _current_bot
    _current_bot.get().run()
