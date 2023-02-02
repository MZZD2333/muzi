from .bot import Bot, BotSettings
from .plugin import current_bot as _current_bot
from .plugin import load_plugin, load_plugin_dir, on_event, on_regex
from .typing import Trigger_Data
from .message import Message, CQcode



def init(**kwargs):
    global _current_bot
    setting = BotSettings(**kwargs)
    bot = Bot(setting)
    _current_bot.set(bot)

    return bot


def get_bot():
    global _current_bot
    return _current_bot.get()