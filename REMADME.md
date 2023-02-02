<!-- markdownlint-disable MD033 MD041 -->

<div align="center">

# muzi qq bot

</div>

一个基于FastAPI的轻量级的bot框架

---

## 简单使用

~~~{.python}
from muzi import Bot, on_regex, on_event, get_bot
from muzi.event import MessageEvent, NoticeEvent, PrivateMessageEvent
from muzi.message import CQcode, Message
~~~

### 事件触发器

~~~{.python}
trigger1 = on_event(MessageEvent)

@trigger1.excute()
async def func1(bot: Bot, event: MessageEvent):
    await trigger1.send_msg(str(event.sender.user_id))
    await trigger1.done(event.raw_message)

@trigger1.excute()
async def func2(bot: Bot, event: NoticeEvent):
    print('这是一个不会被执行的函数')
~~~

### 正则触发器

~~~{.python}
trigger2 = on_regex('echo(.*)')

@trigger2.excute()
async def func3(bot: Bot, event: PrivateMessageEvent, data: dict):
    await trigger2.send_msg(data['matched_groups'][0])

trigger3 = on_regex('图片测试')

@trigger3.excute()
async def func4(bot: Bot, event: PrivateMessageEvent, data: dict):
    await trigger3.send_msg(CQcode.image('./test.jpg'))
~~~

### 在bot连接断开时做些什么

~~~{.python}
bot = get_bot()

@bot.on_startup
async def func5():
    pass

@bot.on_shutdown
async def func6():
    pass

@bot.on_connect
async def func7(bot: Bot):
    pass

@bot.on_disconnect
async def func8():
    pass
~~~
