from types import TracebackType


def get_exception_local(e: Exception):
    local = []
    def tb_next(tb: TracebackType):
        file = tb.tb_frame.f_globals['__file__'] if tb else 'Unknown'
        line = tb.tb_lineno if tb else 'Unknown'
        local.append(f'File: {file}  Line: {line}')
        if tb.tb_next:
            tb_next(tb.tb_next)
    tb_next(e.__traceback__) # type: ignore
    return local
