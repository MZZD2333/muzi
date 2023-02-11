from types import TracebackType
def bool2str(v):
    return None if v is None else str(v).lower()

def escape(s: str) -> str:
    if isinstance(s, str):
        s = s.replace('&', '&amp;').replace('[', '&#91;').replace(']', '&#93;').replace(',', '&#44;')
    return s

def unescape(s: str) -> str:
    if isinstance(s, str):
        return s.replace('&#44;', ',').replace('&#91;', '[').replace('&#93;', ']').replace('&amp;', '&')
    return s


def get_exception_local(e: Exception):
    local = []
    def tb_next(tb: TracebackType):
        file = tb.tb_frame.f_globals['__file__'] if tb else 'Unknown'
        line = tb.tb_lineno if tb else 'Unknown'
        local.append(f'File: {file}  Line: {line}')
        if tb.tb_next:
            tb_next(tb.tb_next)
    tb_next(e.__traceback__)
    return local
