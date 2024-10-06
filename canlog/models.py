from canlog import *
from django.db import models
from canlog import config as cfg
from candb.models import Profile
from canlog import common as _common
from django.contrib.postgres.fields import ArrayField

class ExceptionModel(models.Model):
    # where x=Exception, this should be f"{x.__module__}.{x.__name__}.
    exceptionClass = models.CharField(help_text="Name and path of the exception class that was raised.", max_length=cfg.ExceptionModel.MAXIMUM_EXCEPTION_CLASS_NAME_LENGTH, null=False, blank=False)
    # where x=Exception, this should be x.__str__()
    message = models.CharField(help_text="Message of the exception", max_length=cfg.ExceptionModel.MAXIMUM_EXCEPTION_MESSAGE_LENGTH, null=False, blank=False)
    # where x=Exception, this should be traceback.format_tb(x.__traceback__)
    tbList = ArrayField(
        models.TextField(max_length=cfg.ExceptionModel.MAXIMUM_EACH_TB_LIST_STRING_LENGTH, help_text="One line of the exception traceback formatted"),
        size=cfg.ExceptionModel.MAXIMUM_TB_LIST_ARRAY_LENGTH
    )
    # TODO: add more details



# Create your models here.
class Logs(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Unique Log ID, same across databases", null=False, blank=False)
    logType = models.CharField(max_length=cfg.Logs.MAXIMUM_LENGTH_OF_LOGTYPE_CHOICES, help_text="Log Type", null=False, blank=False, choices=_common.LOG_TYPE_AS_DICT)
    logEvent = models.IntegerField(help_text="Log Event NUmber", null=False, blank=False)
    logMessage = models.TextField(help_text="Log Message", null=False, blank=False, max_length=cfg.Logs.MAXIMUM_MESSAGE_LENGTH)
    logUser = models.ForeignKey(Profile, on_delete=models.SET_NULL, help_text="User", default=-1, null=True, blank=False)
    origin = models.CharField(max_length=cfg.Logs.ORIGIN_MAXIMUM_LENGTH, help_text="Log Origin", null=True, blank=False, default=None)
    exceptionObject = models.ForeignKey(to=ExceptionModel, on_delete=models.CASCADE, help_text="Linked Exception Object", default=-1, null=True, blank=True)
    additionalData = models.JSONField(help_text="Additional Data", null=True, blank=False, default=None)
    logTime = models.DateTimeField(auto_now_add=True, help_text="Log Time", null=False, blank=False)


    @classmethod
    def write(cls, logType: _common.LogType, logMessage: str | bool, event: _common.Event, logUser: Profile | None = None,
              origin: str | bool = True, exceptionObject: BaseException = None, additionalData: dict = None,
              customTime: datetime = None, severity: int = None) -> Self:
        """
        Write a log to the database
        :param logType: The type of log
        :param logMessage: The message of the log. When True, auto-generate. When False, None, or any Falsey value, no message.
        :param event: The event of the log
        :param logUser: The user who wrote the log
        :param origin: The origin of the log. When True, auto-generate. When False, None, or any Falsey value, no origin.
        :param exceptionObject: The exception object
        :param additionalData: Additional data
        :param customTime: The time of the log
        :param severity: The severity of the log. If None, no severity, just log.
        :return: The log object created
        """
        if severity is not None and severity <= cfg.MINIMUM_SEVERITY_LEVEL:
            return None
        excObj = None
        if exceptionObject:
            excObj = ExceptionModel.objects.create(
                exceptionClass=f"{exceptionObject.__module__}.{exceptionObject.__name__}",
                message=exceptionObject.__str__(),
                tbList=list(traceback.format_tb(exceptionObject.__traceback__))
            )

        msg = ""
        if logMessage == True:
            msg = f"{_common.EVENT_TO_NAME[event]} occurred"
        elif logMessage:
            msg = logMessage
        return cls.objects.create(
            id="LOG-" + uuid.uuid4().hex,
            logType=logType,
            logEvent=event,
            logMessage=msg,
            logUser=logUser,
            origin=origin,
            exceptionObject=excObj,
            additionalData=additionalData,
            logTime=customTime if customTime else datetime.now()
        )

    @classmethod
    def writeRequest(cls, request: HttpRequest, logType: _common.LogType, logMessage: str | bool, event: _common.Event, logUser: Profile | None = None,
              origin: str | bool = True, exceptionObject: BaseException = None, additionalData: dict = None,
              customTime: datetime = None, severity: int = None) -> Self:
        """
        Write a log to the database with request information
        :param request: The request object
        :param logType: The type of log
        :param logMessage: The message of the log. When True, auto-generate. When False, None, or any Falsey value, no message.
        :param event: The event of the log
        :param logUser: The user who wrote the log
        :param origin: The origin of the log. When True, auto-generate. When False, None, or any Falsey value, no origin.
        :param exceptionObject: The exception object
        :param additionalData: Additional data
        :param customTime: The time of the log
        :param severity: The severity of the log. If None, no severity, just log.
        :return: The log object created
        """
        return cls.write(
            logType=logType,
            logMessage=logMessage,
            event=event,
            logUser=logUser,
            origin=origin,
            exceptionObject=exceptionObject,
            additionalData={**cls.generateRequestInfo(request), **(additionalData if additionalData else {})},
            customTime=customTime,
            severity=severity
        )


    @staticmethod
    def generateRequestInfo(request: HttpRequest) -> dict:
        return {
            "request": {
                "method": request.method,
                "path": request.path,
                "scheme": request.scheme,
                "GET": dict(request.GET),
                "POST": dict(request.POST),
                "COOKIES": dict(request.COOKIES),
                "META": dict(request.META),
                "FILES": dict(request.FILES),
            }
        }
