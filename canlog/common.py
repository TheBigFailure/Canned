class LogType:
    Debug = "D"  # Debugging information
    Info = "I"  # Informational log
    Warning = "W"  # Warning log
    Error = "E"  # Error log
    Critical = "C"  # Critical error log


LOG_TYPE_AS_DICT = dict({k: v for k, v in LogType.__dict__.items() if not k.startswith("__")})


class Event:
    API_REQUEST: int = 0
    LOGIN: int = 1
    DATABASE_WRITE: int = 2
    DATABASE_READ: int = 3
    DATABASE_DELETE: int = 4
    DATABASE_EDIT: int = 5
    EXCEPTION: int = 6


EVENT_TO_NAME: dict[Event: str] = dict({v: k.replace('_', ' ').capitalize() for k, v in Event.__dict__.items() if not k.startswith("__")})
