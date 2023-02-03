from .plugin import Condition
from .event import *
from .bot import Bot


async def _is_superuser(bot: Bot, event: MessageEvent):
    return event.user_id in bot.superusers

async def _is_to_me(event: Event):
    return event.to_me

async def _is_friend(event: PrivateMessageEvent):
    return event.sub_type == 'friend'

async def _is_group_owner(event: MessageEvent):
    return event.sender.role == 'owner'

async def _is_group_admin(event: MessageEvent):
    return event.sender.role == 'admin' or event.sender.role == 'owner'

async def _is_group_member(event: MessageEvent):
    return event.sender.role == 'member' or event.sender.role == 'admin' or event.sender.role == 'owner'

SUPERUSER = Condition(_is_superuser)

TO_ME = Condition(_is_to_me)

FRIEND = Condition(_is_friend)

GROUP_OWNER = Condition(_is_group_owner)
GROUP_ADMIN = Condition(_is_group_admin)
GROUP_MEMBER = Condition(_is_group_member)