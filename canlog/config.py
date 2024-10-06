from canlog import common as _common


MINIMUM_SEVERITY_LEVEL: int = 5
# 5: All
# 4: Info
# 3: Important Events
# 2: Warning
# 1: Critical
# 0: Exception



DEFAULT_LOG_SET: set[_common.Event] = {_common.Event.API_REQUEST, _common.Event.LOGIN}


class Logs:
    MAXIMUM_MESSAGE_LENGTH: int = 500
    ORIGIN_MAXIMUM_LENGTH: int = 500
    _values = set()
    for _k, _v in _common.LOG_TYPE_AS_DICT.items():
        _values.add(_v.__len__())
        _values.add(_k.__len__())
    MAXIMUM_LENGTH_OF_LOGTYPE_CHOICES: int = max(_values)  # Maximum length of log type choices
    del _values, _k, _v



class ExceptionModel:
    MAXIMUM_EXCEPTION_CLASS_NAME_LENGTH: int = 128  # Maximum length of the exception module + classname
    MAXIMUM_EXCEPTION_MESSAGE_LENGTH: int = 2048  # Maximum length of the exception message
    MAXIMUM_TB_LIST_ARRAY_LENGTH: int = 64  # Maximum length of the TB list
    MAXIMUM_EACH_TB_LIST_STRING_LENGTH: int = 1024  # Maximum length for each element/string in the TB list
