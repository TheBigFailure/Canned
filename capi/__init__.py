from collections.abc import Callable
from typing import Any
from NewCanned import *
from canlog.common import (Event, LogType)
from functools import wraps
from django.http import HttpRequest, HttpResponse
from rest_framework import (serializers as rest_serializers, permissions)
from django.db.models import QuerySet
from json import JSONDecoder, JSONEncoder