
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
