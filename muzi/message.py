import re
from base64 import b64encode
from io import BytesIO
from json import JSONEncoder as BaseJSONEncoder
from pathlib import Path
from typing import Union

from PIL import Image


class CQcode:

    __slots__ = ('type', 'data')

    def __init__(self, type: str, data: dict = {}):
        self.type = type
        self.data = {k: self._escape(v) for k, v in data.items()}
    
    def __str__(self) -> str:
        return str(self.code)

    def __repr__(self) -> str:
        return str(self.message)

    def __add__(self, other: Union[str, 'CQcode', 'Message']):
        message = Message(self)
        if isinstance(other, str):
            message.data.extend(message._construct(other))
        elif isinstance(other, Message):
            message.data.extend(other.data)
        elif isinstance(other, CQcode):
            message.data.append(other)
        else:
            message.data.extend(message._construct(str(other)))
        return message

    def __radd__(self, other: Union[str, 'CQcode', 'Message']):
        message = Message(self)
        if isinstance(other, str):
            message.data.extend(message._construct(other))
        elif isinstance(other, Message):
            message.data.extend(other.data)
        elif isinstance(other, CQcode):
            message.data.append(other)
        else:
            message.data.extend(message._construct(str(other)))
        return message

    @staticmethod
    def _escape(v):
        if isinstance(v, str):
            v = v.replace('&', '&amp;').replace(',', '&#44;').replace('[', '&#91;').replace(']', '&#93;')
        return v

    @property
    def code(self):
        data = ','.join([f'{k}={v}' for k, v in self.data.items()])
        data = ',' + data if data else ''
        return f'[CQ:{self.type}{data}]'

    @property
    def message(self):
        return {'type': self.type, 'data': self.data}

    @staticmethod
    def text(text: str):
        return CQcode('text', {'text': text})

    @staticmethod
    def at(qq: str, name: str|None = None):
        if name:
            return CQcode('at', {'qq': qq, 'name': name})
        return CQcode('at', {'qq': qq})

    @staticmethod
    def face(id: str):
        return CQcode('face', {'id': id})

    @staticmethod
    def image(file: str|Path|bytes|Image.Image):
        if isinstance(file, bytes):
            file = 'base64://'+b64encode(file).decode()
        elif isinstance(file, Path):
            file = file.resolve().as_uri()
        elif isinstance(file, Image.Image):
            io = BytesIO()
            file.save(io, format='PNG')
            file = 'base64://'+b64encode(io.getvalue()).decode()
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
            return CQcode('record', {'file': file, 'magic': str(magic).lower(), 'url': url})
        return CQcode('record', {'file': file, 'magic': str(magic).lower(), 'cache': cache, 'proxy': proxy, 'timeout': timeout})
    
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

    @staticmethod
    def poke(qq: int):
        return CQcode('poke', {'qq': qq})

    @staticmethod
    def cardimage(file: str|Path|bytes|Image.Image, minwidth: int = 400, minheight: int = 400, maxwidth: int = 500, maxheight: int = 1000, source: str = '', icon: str = ''):
        if isinstance(file, bytes):
            file = 'base64://'+b64encode(file).decode()
        elif isinstance(file, Path):
            file = file.resolve().as_uri()
        elif isinstance(file, Image.Image):
            io = BytesIO()
            file.save(io, format='PNG')
            file = 'base64://'+b64encode(io.getvalue()).decode()
        return CQcode('cardimage', {'file': file, 'minwidth': minwidth, 'minheight': minheight, 'maxwidth': maxwidth, 'maxheight': maxheight, 'source': source, 'icon': icon})

    @staticmethod
    def tts(text: str):
        return CQcode('tts', {'text': text})


class Message:
    
    __slots__ = ('data')

    def __init__(self, message: Union[str, CQcode, 'Message', None] = None):
        self.data: list[CQcode] = []
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
                if seq < (k := cqcode.start()):
                    yield 'text', message[seq : k]
                yield cqcode.group('type'), cqcode.group('data') or ''
                seq = cqcode.end()
            if seq+1 < len(message):
                yield 'text', message[seq:]
        for type_, data in _iter_message(message):
            if type_ == 'text':
                yield CQcode(type_, {'text': data})
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