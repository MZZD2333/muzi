

class ExecuteError(Exception):
    def __init__(self, info: str):
        self.info = info

class PreExecuteError(ExecuteError):...

class ExecuteDone(Exception):...

class ConnectionFailed(Exception):...