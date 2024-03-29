import asyncio
from datetime import datetime
from functools import partial
from typing import Any, Callable, Coroutine, Dict, List

from fastapi import FastAPI, WebSocket
from pydantic import BaseSettings

from .event import Event
from .message import Message
from .plugin import Executor, Plugin

ApiCall = partial[Coroutine[Any, Any, Any]]

class BotConfig(BaseSettings):
    host: str
    port: int
    ws_path: str
    superusers: list[int]
    api_timeout: float
    auto_reconnect: bool

    data_path: str
    config_path: str
    extra_config: dict
    
    def save(self):...

class Bot:
    qid: int
    bootdate: datetime
    plugins: List[Plugin]
    config: BotConfig

    def __init__(self, config: BotConfig):...
    def __getattr__(self, name: str) -> ApiCall:...
    async def call_api(self, api: str, **data):...
    def run(self):...
    def reboot(self):...
    async def handle_event(self, event: Event):...

    def on_startup(self, func: Callable) -> Callable:
        '''
        * 创建一个在`服务启动`时执行的函数
        '''
    def on_shutdown(self, func: Callable) -> Callable:
        '''
        * 创建一个在`服务关闭`时执行的函数
        '''
    def on_connect(self, func: Callable|None = None, temp: bool = False) -> Callable:
        '''
        * 创建一个在`bot连接成功`时执行的函数
        '''
    def on_disconnect(self, func: Callable|None = None, temp: bool = False) -> Callable:
        '''
        * 创建一个在`bot连接断开`时执行的函数
        '''
    async def _send_group_notice(self, *, group_id: int, content: str, image: str) -> None:
        '''
        ## 发送群公告
        ---
        ### 参数
        * `group_id`: 群号
        * `content`: 公告内容
        * `image`: 图片路径(可选)
        ---
        ### 响应数据
        * `None`
        '''
    async def can_send_image(self) -> Dict[str, Any]:
        '''
        ## 检查是否可以发送图片
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        * `yes`: 是或否
        '''
    async def can_send_record(self) -> Dict[str, Any]:
        '''
        ## 检查是否可以发送语音
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        * `yes`: 是或否
        '''
    async def create_group_file_folder(self, *, group_id: int, name: str, parent_id: str) -> None:
        '''
        ## 创建群文件文件夹
        ---
        ### 参数
        * `group_id`: 群号
        * `name`: 文件夹名称
        * `parent_id`: 仅能为`/`
        ---
        ### 响应数据
        * `None`
        '''
    async def delete_friend(self, *, user_id: int) -> None:
        '''
        ## 获取单向好友列表
        ---
        ### 参数
        * `user_id`: 好友QQ号
        ---
        ### 响应数据
        * `None`
        '''
    async def delete_group_file(self, *, group_id: int, file_id: str, busid: int) -> None:
        '''
        ## 删除群文件
        ---
        ### 参数
        * `group_id`: 群号
        * `file_id`: 文件ID
        * `busid`: 文件类型
        ---
        ### 响应数据
        * `None`
        '''
    async def delete_group_folder(self, *, group_id: int, folder_id: str) -> None:
        '''
        ## 删除群文件文件夹
        ---
        ### 参数
        * `group_id`: 群号
        * `folder_id`: 文件夹ID
        ---
        ### 响应数据
        * `None`
        '''
    async def delete_msg(self, *, message_id: int,) -> None:
        '''
        ## 撤回消息
        ---
        ### 参数
        * `message_id`: 消息 ID
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        '''
    async def delete_unidirectional_friend(self, *, user_id: int) -> None:
        '''
        ## 删除单向好友
        ---
        ### 参数
        * `user_id`: 单向好友QQ号
        ---
        ### 响应数据
        * `None`
        '''
    async def get_forward_msg(self, *, id: str,) -> None:
        '''
        ## 获取合并转发消息
        ---
        ### 参数
        * `id`: 合并转发 ID
        ---
        ### 响应数据
        * `messages`: 消息列表
        '''
    async def get_friend_list(self) -> List[Dict[str, Any]]:
        '''
        ## 获取好友列表
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        响应内容为 json 数组, 每个元素如下
        * `user_id`: QQ号
        * `nickname`: 昵称
        * `remark`: 备注名
        '''
    async def get_group_file_system_info(self, *, group_id: int) -> Dict[str, Any]:
        '''
        ## 获取群文件系统信息
        ---
        ### 参数
        * `group_id`: 群号
        ---
        ### 响应数据
        * `file_count`: 文件总数
        * `limit_count`: 文件上限
        * `used_space`: 已使用空间
        * `total_space`: 空间上限
        '''
    async def get_group_file_url(self, *, group_id: int, file_id: str, busid: int) -> None:
        '''
        ## 获取群文件资源链接
        ---
        ### 参数
        * `group_id`: 群号
        * `file_id`: 文件ID
        * `busid`: 文件类型
        ---
        ### 响应数据
        * `url`: 文件下载链接
        '''
    async def get_group_files_by_folder(self, *, group_id: int, folder_id: str) -> Dict[str, Any]:
        '''
        ## 获取群子目录文件列表
        ---
        ### 参数
        * `group_id`: 群号
        * `folder_id`: 文件夹ID
        ---
        ### 响应数据
        * `files`: 文件列表
        * `folders`: 文件夹列表
        '''
    async def get_group_honor_info(self, *, group_id: int, type: str = ...) -> Dict[str, Any]:
        '''
        ## 获取群荣誉信息
        ---
        ### 参数
        * `group_id`: 群号
        * `type`: 要获取的群荣誉类型,可传入 `talkative` `performer` `legend` `strong_newbie` `emotion` 以分别获取单个类型的群荣誉数据,或传入 `all` 获取所有数据
        ---
        ### 响应数据
        * `group_id`: 群号
        * `current_talkative`: 当前龙王, 仅 `type` 为 `talkative` 或 `all` 时有数据
        * `talkative_list`: 历史龙王, 仅 `type` 为 `talkative` 或 `all` 时有数据
        * `performer_list`: 群聊之火, 仅 `type` 为 `performer` 或 `all` 时有数据
        * `legend_list`: 群聊炽焰, 仅 `type` 为 `legend` 或 `all` 时有数据
        * `strong_newbie_list`: 冒尖小春笋, 仅 `type` 为 `strong_newbie` 或 `all` 时有数据
        * `emotion_list`: 快乐之源, 仅 `type` 为 `emotion` 或 `all` 时有数据
        '''
    async def get_group_info(self, *, group_id: int, no_cache: bool = ...) -> Dict[str, Any]:
        '''
        ## 获取群信息
        ---
        ### 参数
        * `group_id`: 群号
        * `no_cache`: 是否不使用缓存(使用缓存可能更新不及时,但响应更快)
        ---
        ### 响应数据
        如果机器人尚未加入群, `group_create_time`, `group_level`, `max_member_count` 和 `member_count` 将会为 `0`
        * `group_id`: 群号
        * `group_name`: 群名称
        * `group_memo` :群备注
        * `group_create_time`: 群创建时间
        * `group_level`: 群等级
        * `member_count`: 成员数
        * `max_member_count`: 最大成员数(群容量)
        '''
    async def get_group_list(self) -> List[Dict[str, Any]]:
        '''
        ## 获取群列表
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        响应内容为 json 数组, 每个元素如下
        * `group_id`: 群号
        * `group_name`: 群名称
        * `group_memo` :群备注
        * `group_create_time`: 群创建时间
        * `group_level`: 群等级
        * `member_count`: 成员数
        * `max_member_count`: 最大成员数(群容量)
        '''
    async def get_group_member_info(self, *, group_id: int, user_id: int, no_cache: bool = ...) -> Dict[str, Any]:
        '''
        ## 获取群成员信息
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: QQ号
        * `no_cache`: 是否不使用缓存(使用缓存可能更新不及时,但响应更快)
        ---
        ### 响应数据
        * `group_id`: 群号
        * `user_id`: QQ 号
        * `nickname`: 昵称
        * `card`: 群名片／备注
        * `sex`: 性别, `male` 或 `female` 或 `unknown`
        * `age`: 年龄
        * `area`: 地区
        * `join_time`: 加群时间戳
        * `last_sent_time`: 最后发言时间戳
        * `level`: 成员等级
        * `role`: 角色, `owner` 或 `admin` 或 `member`
        * `unfriendly`: 是否不良记录成员
        * `title`: 专属头衔
        * `title_expire_time`: 专属头衔过期时间戳
        * `card_changeable`: 是否允许修改群名片
        * `shut_up_timestamp`: 禁言到期时间
        '''
    async def get_group_member_list(self, *, group_id: int) -> List[Dict[str, Any]]:
        '''
        ## 获取群成员列表
        ---
        ### 参数
        * `group_id`: 群号
        ---
        ### 响应数据
        响应内容为 json 数组, 每个元素如下
        * `group_id`: 群号
        * `user_id`: QQ 号
        * `nickname`: 昵称
        * `card`: 群名片／备注
        * `sex`: 性别, `male` 或 `female` 或 `unknown`
        * `age`: 年龄
        * `area`: 地区
        * `join_time`: 加群时间戳
        * `last_sent_time`: 最后发言时间戳
        * `level`: 成员等级
        * `role`: 角色, `owner` 或 `admin` 或 `member`
        * `unfriendly`: 是否不良记录成员
        * `title`: 专属头衔
        * `title_expire_time`: 专属头衔过期时间戳
        * `card_changeable`: 是否允许修改群名片
        * `shut_up_timestamp`: 禁言到期时间
        '''
    async def get_group_root_files(self, *, group_id: int) -> Dict[str, Any]:
        '''
        ## 获取群根目录文件列表
        ---
        ### 参数
        * `group_id`: 群号
        ---
        ### 响应数据
        * `files`: 文件列表
        * `folders`: 文件夹列表
        '''
    async def get_login_info(self) -> Dict[str, Any]:
        '''
        ## 获取登录号信息
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        * `user_id`: QQ号
        * `nickname`: QQ 昵称
        '''
    async def get_msg(self, *, message_id: int,) -> Dict[str, Any]:
        '''
        ## 获取消息
        ---
        ### 参数
        * `message_id`: 消息 ID
        ---
        ### 响应数据
        * `group`: 是否是群消息
        * `group_id`: 是群消息时的群号(否则不存在此字段)
        * `message_id`: 消息 ID
        * `real_id`: 消息真实 ID
        * `message_type`: 群消息时为`group`, 私聊消息为`private`
        * `sender`: 发送者
        * `time`: 发送时间
        * `message`: 消息内容
        * `raw_message`: 原始消息内容
        '''
    async def get_stranger_info(self, *, user_id: int, no_cache: bool = ...) -> Dict[str, Any]:
        '''
        ## 获取陌生人信息
        ---
        ### 参数
        * `user_id`: QQ号
        * `no_cache`: 是否不使用缓存(使用缓存可能更新不及时,但响应更快)
        ---
        ### 响应数据
        * `user_id`: QQ号
        * `nickname`: 昵称
        * `sex`: 性别, `male` 或 `female` 或 `unknown`
        * `age`: 年龄
        * `qid`: qid ID身份卡
        * `level`: 等级
        * `login_days`: 等级
        '''
    async def get_unidirectional_friend_list(self) -> List[Dict[str, Any]]:
        '''
        ## 获取单向好友列表
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        响应内容为 json 数组, 每个元素如下
        * `user_id`: QQ号
        * `nickname`: 昵称
        * `source`: 来源
        '''
    async def get_version_info(self) -> Dict[str, Any]:
        '''
        ## 获取版本信息
        ---
        ### 参数
        * `None`
        ---
        ### 响应数据
        * `app_name`: 应用标识
        * `app_version`: 应用版本
        * `app_full_name`: 应用完整名称
        * `protocol_version`: OneBot标准版本
        * `runtime_version`
        * `runtime_os`
        * `version`: 应用版本
        * `protocol`: 当前登陆使用协议类型
        '''
    async def ocr_image(self, *, image: str) -> Dict[str, Any]:
        '''
        ## 图片 OCR
        ---
        ### 参数
        * `image`: 图片ID
        ---
        ### 响应数据
        * `texts`: OCR结果
        * `language`: 语言
        '''
    async def reload_event_filter(self, *, file: str) -> None:
        '''
        ## 重载事件过滤器
        ---
        ### 参数
        * `file`: 事件过滤器文件
        ---
        ### 响应数据
        * `None`
        '''
    async def send_msg(self, *, message_type: str = ..., user_id: int = ..., group_id: int = ..., message: str | Message, auto_escape: bool = ...) -> Dict[str, Any]:
        '''
        ## 发送消息
        ---
        ### 参数
        * `message_type`: 消息类型,支持 `private`,`group`,分别对应私聊,群组,讨论组,如不传入,则根据传入的 `*_id` 参数判断
        * `user_id`: 对方 QQ号(消息类型为 `private` 时需要)
        * `group_id`: 群号(消息类型为 `group` 时需要)
        * `message`: 要发送的内容
        * `auto_escape`: 消息内容是否作为纯文本发送(即不解析 CQ 码),只在 `message` 字段是字符串时有效
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        '''
    async def send_group_forward_msg(self, *, group_id: int, message: Message) -> Dict[str, Any]:
        '''
        ## 发送合并转发(群)
        ---
        ### 参数
        * `group_id`: 群号
        * `message`: 自定义转发消息, 具体看 [#CQcode](https://docs.go-cqhttp.org/cqcode/#%E5%90%88%E5%B9%B6%E8%BD%AC%E5%8F%91%E6%B6%88%E6%81%AF%E8%8A%82%E7%82%B9)
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        * `forward_id`: 转发消息 ID
        '''
    async def send_group_msg(self, *, group_id: int, message: str | Message, auto_escape: bool = ...) -> Dict[str, Any]:
        '''
        ## 发送群消息
        ---
        ### 参数
        * `group_id`: 群号
        * `message`: 要发送的内容
        * `auto_escape`: 消息内容是否作为纯文本发送(即不解析 CQ 码),只在 `message` 字段是字符串时有效
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        '''
    async def send_group_sign(self, *, group_id: int) -> None:
        '''
        ## 群打卡
        ---
        ### 参数
        * `group_id`: 群号
        ---
        ### 响应数据
        * `None`
        '''
    async def send_private_forward_msg(self, *, user_id: int, messages: Message) -> None:
        '''
        ## 发送合并转发(好友)
        ---
        ### 参数
        `user_id`: 好友QQ号
        `messages`: 自定义转发消息, 具体看 [#CQcode](https://docs.go-cqhttp.org/cqcode/#%E5%90%88%E5%B9%B6%E8%BD%AC%E5%8F%91%E6%B6%88%E6%81%AF%E8%8A%82%E7%82%B9)
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        * `forward_id`: 转发消息 ID
        '''
    async def send_private_msg(self, *, user_id: int, message: str | Message, auto_escape: bool = ...) -> Dict[str, Any]:
        '''
        ## 发送私聊消息
        ---
        ### 参数
        * `user_id`: 对方 QQ号
        * `message`: 要发送的内容
        * `auto_escape`: 消息内容是否作为纯文本发送(即不解析 CQ 码),只在 `message` 字段是字符串时有效
        ---
        ### 响应数据
        * `message_id`: 消息 ID
        '''
    async def set_friend_add_request(self, *, flag: str, approve: bool = ..., remark: str = ...) -> None:
        '''
        ## 处理加好友请求
        ---
        ### 参数
        * `flag`: 加好友请求的 flag(需从上报的数据中获得)
        * `approve`: 是否同意请求
        * `remark`: 添加后的好友备注(仅在同意时有效)
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_add_request(self, *, flag: str, sub_type: str, approve: bool = ..., reason: str = ...) -> None:
        '''
        ## 处理加群请求/邀请
        ---
        ### 参数
        * `flag`: 加群请求的 flag(需从上报的数据中获得)
        * `sub_type`: `add` 或 `invite`,请求类型(需要和上报消息中的 `sub_type` 字段相符)
        * `approve`: 是否同意请求/邀请
        * `reason`: 拒绝理由(仅在拒绝时有效)
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_admin(self, *, group_id: int, user_id: int, enable: bool = ...) -> None:
        '''
        ## 群组设置管理员
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: 要设置管理员的 QQ号
        * `enable`: `True` 为设置,`False` 为取消
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_anonymous(self, *, group_id: int, enable: bool = ...) -> None:
        '''
        ## 群组匿名
        ---
        ### 参数
        * `group_id`: 群号
        * `enable`: 是否允许匿名聊天
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_anonymous_ban(self, *, group_id: int, anonymous: Dict[str, Any] = ..., anonymous_flag: str = ..., duration: int = ...) -> None:
        '''
        ## 群组匿名用户禁言
        ---
        ### 参数
        * `group_id`: 群号
        * `anonymous`: 可选,要禁言的匿名用户对象(群消息上报的 `anonymous` 字段)
        * `anonymous_flag`: 可选,要禁言的匿名用户的 flag(需从群消息上报的数据中获得)
        * `duration`: 禁言时长,单位秒,无法取消匿名用户禁言
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_ban(self, *, group_id: int, user_id: int, duration: int = ...,) -> None:
        '''
        ## 群组单人禁言
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: 要禁言的 QQ号
        * `duration`: 禁言时长,单位秒,`0` 表示取消禁言
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_card(self, *, group_id: int, user_id: int, card: str = ...) -> None:
        '''
        ## 设置群名片(群备注)
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: 要设置的 QQ号
        * `card`: 群名片内容,不填或空字符串表示删除群名片
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_kick(self, *, group_id: int, user_id: int, reject_add_request: bool = ...,) -> None:
        '''
        ## 群组踢人
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: 要踢的 QQ号
        * `reject_add_request`: 拒绝此人的加群请求
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_leave(self, *, group_id: int, is_dismiss: bool = ...) -> None:
        '''
        ## 退出群组
        ---
        ### 参数
        * `group_id`: 群号
        * `is_dismiss`: 是否解散,如果登录号是群主,则仅在此项为 True 时能够解散
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_name(self, *, group_id: int, group_name: str) -> None:
        '''
        ## 设置群名
        ---
        ### 参数
        * `group_id`: 群号
        * `group_name`: 新群名
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_special_title(self, *, group_id: int, user_id: int, special_title: str = ..., duration: int = ...) -> None:
        '''
        ## 设置群组专属头衔
        ---
        ### 参数
        * `group_id`: 群号
        * `user_id`: 要设置的 QQ号
        * `special_title`: 专属头衔,不填或空字符串表示删除专属头衔
        * `duration`: 专属头衔有效期,单位秒,-1 表示永久
        ---
        ### 响应数据
        * `None`
        '''
    async def set_group_whole_ban(self, *, group_id: int, enable: bool = ...) -> None:
        '''
        ## 群组全员禁言
        ---
        ### 参数
        * `group_id`: 群号
        * `enable`: 是否禁言
        ---
        ### 响应数据
        * `None`
        '''
    async def set_login_info(self, *, nickname: str = ..., company: str = ..., email: str = ..., college: str = ..., personal_note: str = ...) -> Dict[str, Any]:
        '''
        ## 设置登录号资料
        ---
        ### 参数
        * `nickname`: 名称
        * `company`: 公司
        * `email`: 邮箱
        * `college`: 学校
        * `personal_note`: 个人说明
        ---
        ### 响应数据
        * `None`
        '''
    async def upload_group_file(self, *, user_id: int, file: str, name: str, folder: str = ...) -> None:
        '''
        ## 上传群文件
        ---
        ### 参数
        * `user_id`: 对方 QQ 号
        * `file`: 本地文件路径
        * `name`: 文件名称
        * `folder`:	父目录ID
        ---
        ### 响应数据
        * `None`
        '''
    async def upload_private_file(self, *, user_id: int, file: str, name: str) -> None:
        '''
        ## 上传私聊文件
        ---
        ### 参数
        * `user_id`: 对方 QQ 号
        * `file`: 本地文件路径
        * `name`: 文件名称
        ---
        ### 响应数据
        * `None`
        '''


        
class Server:
    bot: Bot
    websocket: WebSocket

    _on_bot_connect: List[Executor]
    _on_bot_disconnect: List[Executor]

    _api_result: Dict[str, asyncio.Future]

    def __init__(self, bot):...
    def set_websocket(self, path):...
    async def call_api(self, api, **data):...
    def _store_api_result(self, data):...
    async def _fetch_api_result(self, echo):...
    async def _send(self, data):...
    async def on_bot_connect(self):...
    async def on_bot_disconnect(self):...

    @property
    def asgi(self) -> FastAPI:...