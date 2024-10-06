from NewCanned import *
from django.http import HttpRequest

from django.db import connection
if connection.vendor.casefold() != "postgresql":
    raise SystemError(
        f"unsupported database vendor: {connection.vendor}. Requires PostgreSQL backend due to some fields only available on Postgres backend"
    )