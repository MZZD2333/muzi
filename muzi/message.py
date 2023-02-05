import re
from base64 import b64encode
from io import BytesIO
from json import JSONEncoder as BaseJSONEncoder
from pathlib import Path
from typing import Union

from .utils import bool2str, escape


class Text:

    __slots__ = ('data')

    def __init__(self, data: str = ''):
        self.data = data

    def __str__(self) -> str:
        return self.data

    def __repr__(self) -> str:
        return str(self.message)

    @property
    def code(self):
        return self.data

    @property
    def message(self):
        return {'type': 'text', 'data': {'text': self.data}}

class CQcode:

    __slots__ = ('type', 'data')

    def __init__(self, type: str, data: dict = {}):
        self.type = type
        self.data = {k: escape(v) for k, v in data.items()}
    
    def __str__(self) -> str:
        return str(self.code)

    def __repr__(self) -> str:
        return str(self.message)

    @property
    def code(self):
        data = ','.join([f'{k}={v}' for k, v in self.data.items()])
        data = ',' + data if data else ''
        return f'[CQ:{self.type}{data}]'

    @property
    def message(self):
        return {'type': self.type, 'data': self.data}

    @staticmethod
    def at(qq: str, name: str|None = None):
        if name:
            return CQcode('at', {'qq': qq, 'name': name})
        return CQcode('at', {'qq': qq})

    @staticmethod
    def face(id: str):
        return CQcode('face', {'id': str(id)})

    @staticmethod
    def image(file: str|Path|bytes):
        if isinstance(file, BytesIO):
            file = file.getvalue()
        if isinstance(file, bytes):
            file = 'base64://'+b64encode(file).decode()
        elif isinstance(file, Path):
            file = file.resolve().as_uri()
        return CQcode('image', {'file': file})

    @staticmethod
    def music(type: str, id: str):
        return CQcode('music', {'type': type, 'id': id})

    @staticmethod
    def music_custom(url: str, audio: str, title: str, content: str|None = None, image: str|None = None):
        return CQcode('music', {'type': 'custom', 'url': url, 'audio': audio, 'title': title, 'content': content, 'image': image})

    @staticmethod
    def record(file: str|Path|bytes, magic: bool = False, cache: bool = False, proxy: bool = False, timeout: int|None = None, url: str|None = None):
        if isinstance(file, BytesIO):
            file = file.getvalue()
        if isinstance(file, bytes):
            file = 'base64://'+b64encode(file).decode()
        elif isinstance(file, Path):
            file = file.resolve().as_uri()
        if url:
            return CQcode('face', {'file': file, 'magic': bool2str(magic), 'url': url})
        return CQcode('face', {'file': file, 'magic': bool2str(magic), 'cache': cache, 'proxy': proxy, 'timeout': timeout})
    
    @staticmethod
    def reply(id: str):
        return CQcode('reply', {'id': id})

    @staticmethod
    def share(url: str, title: str, content: str|None = None, image: str|None = None):
        return CQcode('share', {'url': url, 'title': title, 'content': content, 'image': image})

    @staticmethod
    def video(file: str|Path|bytes, cover: str|Path|bytes|None = None, c: int = 1):
        if isinstance(file, BytesIO):
            file = file.getvalue()
        if isinstance(file, bytes):
            file = 'base64://'+b64encode(file).decode()
        elif isinstance(file, Path):
            file = file.resolve().as_uri()
        if cover:
            if isinstance(cover, BytesIO):
                cover = cover.getvalue()
            if isinstance(cover, bytes):
                cover = 'base64://'+b64encode(cover).decode()
            elif isinstance(cover, Path):
                cover = cover.resolve().as_uri()
            return CQcode('video', {'file': file, 'cover': cover, 'c': c})
        return CQcode('video', {'file': file, 'c': c})


class Message:
    
    __slots__ = ('data')

    def __init__(self, message: Union[str, CQcode, 'Message', None] = None):
        self.data: list[CQcode|Text] = []
        if message is None:
            pass
        elif isinstance(message, Message):
            self.data.extend(message.data)
        elif isinstance(message, str):
            self.data.extend(self._construct(message))
        elif isinstance(message, CQcode):
            self.data.append(message)
        else:
            self.data.extend(self._construct(str(message)))

    @staticmethod
    def _construct(message: str):
        def _iter_message(message: str):
            seq = 0
            for cqcode in re.finditer(r'\[CQ:(?P<type>\w+),?(?P<data>(?:\w+=[^,\[\]]+,?)*)\]', message):
                yield 'text', message[seq : cqcode.start()]
                seq = cqcode.end()
                yield cqcode.group('type'), cqcode.group('data') or ''
            yield 'text', message[seq:]

        for type_, data in _iter_message(message):
            if type_ == 'text':
                if data:
                    yield Text(data)
            else:
                data = {k: v for k, v in [d.split('=', 1) for d in data.split(',') if d]}
                yield CQcode(type_, data)

    def __str__(self) -> str:
        return ''.join([str(d) for d in self.data])

    def __repr__(self) -> str:
        return str(self.message)

    def __add__(self, other: Union[str, CQcode, 'Message']):
        if isinstance(other, str):
            self.data.extend(self._construct(other))
        elif isinstance(other, Message):
            self.data.extend(other.data)
        elif isinstance(other, CQcode):
            self.data.append(other)
        else:
            self.data.extend(self._construct(str(other)))
        return self

    def __radd__(self, other: Union[str, CQcode, 'Message']):
        if isinstance(other, str):
            self.data.extend(self._construct(other))
        elif isinstance(other, Message):
            self.data.extend(other.data)
        elif isinstance(other, CQcode):
            self.data.append(other)
        else:
            self.data.extend(self._construct(str(other)))
        return self

    @property
    def message(self):
        return [d.message for d in self.data]

class JSONEncoder(BaseJSONEncoder):
    def default(self, o):
        if isinstance(o, Message):
            return o.message
        elif isinstance(o, CQcode):
            return Message(o).message
        return super().default(o)