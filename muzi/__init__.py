'''
# muzi bot
---
### 可在插件内添加 `__metadata__` 字段用于插件管理
* `name`: 插件名称 默认插件所在模块的路径
* `usage_text`: 插件文本说明
* `usage_image_path`: 插件图片说明路径
* `status_tracing`: 插件状态监测函数
* `type`: 插件类型 [0: 群聊|私聊][1: 群聊][2: 私聊][3: 非会话]
---
'''

from .bot import Bot, BotSettings
from .message import CQcode, Message
from .plugin import Condition, Trigger
from .plugin import current_bot as _current_bot
from .plugin import load_plugin, load_plugin_dir, on_event, on_regex
from .typing import Trigger_Data


def init(**kwargs):
    '''
    ## 初始化bot
    ---
    参数
    `host`: str 默认 '127.0.0.1'
    `port`: int 默认 5700
    `ws_path`: str 默认 '/ws'
    `superusers`: set[int] 默认 set()
    `api_timeout`: float 默认 15.0
    '''
    

    global _current_bot
    setting = BotSettings(**kwargs)
    bot = Bot(setting)
    _current_bot.set(bot)

    return bot


def get_bot():
    global _current_bot
    return _current_bot.get()

def run():
    global _current_bot
    _current_bot.get().run()
