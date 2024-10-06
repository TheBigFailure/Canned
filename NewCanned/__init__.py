from time import sleep
from datetime import datetime, date, timedelta, timezone
from dataclasses import dataclass
from os import PathLike
from typing import (Union, TypeVar, Any, Generic, Self, NoReturn,)
from collections.abc import (Callable, Iterable)
from types import SimpleNamespace, ModuleType
import sys
import uuid
from NewCanned.settings import BASE_DIR, TZ_INFO
from NewCanned import settings as GLOBAL_SETTINGS
from NewCanned.baseSecurity import *
import warnings
import django
from django.db import transaction
import traceback


from contextlib import contextmanager


PathType = Union[str, bytes, PathLike]


@dataclass
class SessionInformation:
    sessionID: uuid.UUID
    sessionName: str
    sessionApplication: str
    initFile: PathType
    implementation: SimpleNamespace
    executable: PathType
    executable_prefix: PathType
    sessionStartTime: datetime
    sessionDescription: str | None
    sessionTags: set[str]


ACTIVE_SESSIONS: dict[str: SessionInformation] = dict()  # {sessionID: sessionDetails}


def appendSession(name: str, application: str, initFile: PathType, implementation: SimpleNamespace,
                  executable: PathType, executable_prefix: PathType, description: str = None,
                  tags: set[str] = None) -> uuid.UUID:
    timeNow = datetime.now()
    sessionUUID = uuid.uuid4()
    global ACTIVE_SESSIONS
    ACTIVE_SESSIONS[sessionUUID.__str__()] = SessionInformation(
        sessionID=sessionUUID,
        sessionName=name,
        sessionApplication=application,
        implementation=implementation,
        initFile=initFile,
        executable=executable,
        executable_prefix=executable_prefix,
        sessionStartTime=timeNow,
        sessionDescription=description,
        sessionTags=tags if tags else set()
    )
    return sessionUUID
