from capi import *
from capi.common import StandardResponse
from canlog.models import Logs


def apiMethod(allowMethods: set[str], requireLogin: bool = True, expectPermissions: set[str] = None,
              expectGroup: set[str] = None, logEvents: set[Event] = None, logMessage: str | bool = True) -> Callable:
    """
    Decorator for API methods to enforce security and logging.

    :param allowMethods: Allow methods for the API
    :param requireLogin: If the user must login to access the API. If True, the user must be logged in. If False, the user must not be logged in.
    :param expectPermissions: The permission(s) the user must have to access the API. Not used if requireLogin is False.
    :param expectGroup: The group(s) the user must be in to access the API. Not used if requireLogin is False.
    :param logEvents: The events that must occur to write a log
    :param logMessage: The message to log. Use True for auto.
    :return: The decorator
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(request: HttpRequest, *args: Any, **kwargs: Any) -> Any:
            nonlocal logMessage
            if Event.API_REQUEST in logEvents:
                Logs.writeRequest(request=request, logType=LogType.Info, logMessage=logMessage,  # where logMessage is True, autohandled by Logs.writeRequest
                                  logUser=request.user if not (
                                              request.user.is_anonymous or not request.user.is_authenticated) else None,
                                  event=Event.API_REQUEST, origin=f"{func.__module__}.{func.__name__}", severity=4)
            if request.method not in allowMethods:
                return StandardResponse.MethodNotAllowed(expected_methods=allowMethods)
            if requireLogin:
                if request.user.is_anonymous:
                    return StandardResponse.Unauthorised()
                if (expectPermissions and not request.user.has_perms(expectPermissions)) or (
                        expectGroup and not request.user.groups.filter(name__in=expectGroup).exists()):
                    return StandardResponse.Unauthorised()
            return func(request, *args, **kwargs)

        return wrapper
    return decorator