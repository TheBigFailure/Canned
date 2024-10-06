from NewCanned import *
from django.contrib.postgres.fields import ArrayField
from django.db.models.functions import Length
import sys
import pickle
from django.db import models
from getpass import getpass
from django.contrib.auth.password_validation import validate_password
from django.core.serializers.json import DjangoJSONEncoder
from candb import config as _cfg
from decimal import Decimal



if _cfg.INSECURE_SUPERUSERS_ACTIVE:
    if not GLOBAL_SETTINGS.DEBUG:
        raise InsecureDeploymentException("insecure superusers are not allowed in production.")
    else:
        warnings.warn("Insecure superusers are active. This is not recommended for production use.", InsecureEnvironmentWarning)


__SID__ = appendSession("CanDB Application", "candb", __file__, implementation=sys.implementation, executable=sys.executable, executable_prefix=sys.exec_prefix, description="CanDB application for database management", tags={'db', 'critical', 'highsec'})


print(f"{__SID__}: Welcome to CanDB. Please wait for initialisation...")

from candb.common import ORDERLINE_STATUS_AS_DICT
import candb.common as com
import candb.config as cfg


F = TypeVar('F', bound=Callable[..., Any])

models.CharField.register_lookup(Length, 'len')


class useTypeSignature(Generic[F]):  # https://github.com/python/typing/issues/270#issuecomment-555966301
    def __init__(self, target: F) -> None: ...
    def __call__(self, wrapped: Callable[..., Any]) -> F: ...


print(f"{__SID__}: CanDB: Initialisation complete. Ready for use.")