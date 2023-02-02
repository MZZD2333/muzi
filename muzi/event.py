from typing import Optional

from pydantic import BaseModel, validator

from .log import logger
from .message import Message


class Sender(BaseModel):
    '''发送者'''
    user_id: Optional[int] = None
    nickname: Optional[str] = None
    sex: Optional[str] = None
    age: Optional[int] = None
    card: Optional[str] = None
    area: Optional[str] = None
    level: Optional[str] = None
    role: Optional[str] = None
    title: Optional[str] = None

class Status(BaseModel):
    '''状态'''
    app_initialized: bool
    app_enabled: bool
    app_good: bool
    online: bool
    good: bool

class Event(BaseModel):
    '''基础事件'''
    time: int
    self_id: int
    post_type: str

    class Config:
        arbitrary_types_allowed = True


# Message Event
class MessageEvent(Event):
    '''消息事件'''
    post_type: str = 'message_type'
    message_type: str
    sub_type: str

    message: Message
    raw_message: str
    message_id: int

    sender: Sender
    user_id: int

    to_me: bool = False
    
    @validator('message', pre=True)
    def msg(cls, str_):
        return Message(str_)

class GroupMessageEvent(MessageEvent):
    '''群消息事件'''
    message_type: str = 'group'
    sub_type: str

    group_id: int

class PrivateMessageEvent(MessageEvent):
    '''私聊消息事件'''
    message_type: str = 'private'
    sub_type: str

# Notice Event
class NoticeEvent(Event):
    '''通知事件'''
    post_type: str = 'notice_type'
    notice_type: str
    
class GroupUploadNoticeEvent(NoticeEvent):
    '''群文件上传事件'''

    notice_type: str = 'group_upload'
    user_id: int
    group_id: int


class GroupAdminNoticeEvent(NoticeEvent):
    '''群管理员变动事件'''

    notice_type: str = 'group_admin'
    sub_type: str
    user_id: int
    group_id: int


class GroupDecreaseNoticeEvent(NoticeEvent):
    '''群成员减少事件'''

    notice_type: str = 'group_decrease'
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int


class GroupIncreaseNoticeEvent(NoticeEvent):
    '''群成员增加事件'''

    notice_type: str = 'group_increase'
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int


class GroupBanNoticeEvent(NoticeEvent):
    '''群禁言事件'''

    notice_type: str = 'group_ban'
    sub_type: str
    user_id: int
    group_id: int
    operator_id: int
    duration: int

class FriendAddNoticeEvent(NoticeEvent):
    '''好友添加事件'''

    notice_type: str = 'friend_add'
    user_id: int


class GroupRecallNoticeEvent(NoticeEvent):
    '''群消息撤回事件'''

    notice_type: str = 'group_recall'
    user_id: int
    group_id: int
    operator_id: int
    message_id: int


class FriendRecallNoticeEvent(NoticeEvent):
    '''好友消息撤回事件'''

    notice_type: str = 'friend_recall'
    user_id: int
    message_id: int


class NotifyEvent(NoticeEvent):
    '''提醒事件'''

    notice_type: str = 'notify'
    sub_type: str
    user_id: int
    group_id: int


class PokeNotifyEvent(NotifyEvent):
    '''戳一戳提醒事件'''

    sub_type: str = 'poke'
    target_id: int
    group_id: Optional[int] = None


class LuckyKingNotifyEvent(NotifyEvent):
    '''群红包运气王提醒事件'''

    sub_type: str = 'lucky_king'
    target_id: int

class HonorNotifyEvent(NotifyEvent):
    '''群荣誉变更提醒事件'''

    sub_type: str = 'honor'
    honor_type: str


# Request Event
class RequestEvent(Event):
    '''请求事件'''
    post_type: str = 'request_type'
    request_type: str
    

# Meta Event
class MetaEvent(Event):
    '''元事件'''
    post_type: str = 'meta_event_type'
    meta_event_type: str
    
class HeartbeatMetaEvent(MetaEvent):
    '''心跳事件'''
    meta_event_type: str = 'heartbeat'

    interval: int

    status: Status

class LifecycleMetaEvent(MetaEvent):
    '''生命周期事件'''
    meta_event_type: str = 'lifecycle'
    sub_type: str


POST_TYPE = ['message_type', 'meta_event_type', 'notice_type', 'request_type']

def _get_all_subclass(obj):
    if isinstance(obj, list):
        return [_get_all_subclass(o) for o in obj]
    if c := obj.__subclasses__():
        return sum(_get_all_subclass(c), [obj])
    else:
        return [obj]

def _named_event(event: Event):
    name = ''
    sub_type = ''
    if _field := event.__fields__.get('sub_type', None):
        sub_type += (_field.default or '')
    for post_type in POST_TYPE:
        if _field := event.__fields__.get(post_type, None):
            name = '.'.join([post_type, (_field.default or ''), sub_type])
            break
    return name

EVENT_TYPE = {_named_event(event): event for event in _get_all_subclass(Event)}

def _get_event_model(json_data: dict):
    name = ''
    sub_type = json_data.get('sub_type', '') if json_data.get('notice_type', '') == 'notify' else ''
    for post_type in POST_TYPE:
        if _type := json_data.get(post_type, ''):
            name = '.'.join([post_type, _type, sub_type])
            break
    return EVENT_TYPE.get(name, Event) if name else None

def _check_to_me(event: MessageEvent):
    if event.message_type == 'group':
        event.to_me = f'[CQ:at,qq={event.self_id}]' in event.raw_message
    else:
        event.to_me = True

def get_event(json_data: dict) -> Event | None:
    if model := _get_event_model(json_data):
        event = model.parse_obj(json_data)
        if event.post_type == 'message':
            _check_to_me(event)
        return event
    else:
        return None

def log_event(event: Event):
    if isinstance(event, MetaEvent):
        return
    elif isinstance(event, MessageEvent):
        log = '<c>Message</c> '
        if isinstance(event, GroupMessageEvent):
            log += f'<g>[GID:{event.group_id}]</g>'
        log += f'<c>[UID:{event.user_id}]</c> {event.raw_message}'
        
    elif isinstance(event, NoticeEvent):
        log = '<y>Notice </y> '
        event_data = event.dict()
        if group_id := event_data.get('group_id', ''):
            log += f'<g>[GID:{group_id}]</g>'
        if user_id := event_data.get('user_id', ''):
            log += f'<c>[UID:{user_id}]</c>'
        if operator_id := event_data.get('operator_id', ''):
            log += f'<r>[OID:{operator_id}]</r>'
        elif target_id := event_data.get('target_id', ''):
            log += f'<r>[TID:{target_id}]</r>'
        log += f' {event.notice_type}'
    elif isinstance(event, RequestEvent):
        log = '<m>Request</m> '
    else:
        log = '<r>Unknown</r> '
        log += event.post_type
    
    logger.info(log)
