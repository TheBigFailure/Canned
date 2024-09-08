import candb.common as _common


DEFAULT_MAXIMUM_NOTES_LENGTH: int = 500  # Default maximum length for notes
DEFAULT_MAXIMUM_NAME_LENGTH: int = 100  # Default maximum length for name
DEFAULT_MAXIMUM_COST_DIGITS: int = 10  # Default maximum digits for cost
DEFAULT_COST_DECIMAL_DIGITS: int = 2  # Default decimal digits for cost
DEFAULT_MAXIMUM_STATUS_INFORMATION_LENGTH: int = 500  # Default maximum length for status information


class Order:
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_COST_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_COST_DECIMAL_DIGITS

class Product:
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_NAME_LENGTH: int = DEFAULT_MAXIMUM_NAME_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_COST_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_COST_DECIMAL_DIGITS

class OrderLine:
    DEFAULT_STATUS: str = _common.OrderLineStatus.Pending
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_STATUS_INFORMATION_LENGTH: int = DEFAULT_MAXIMUM_STATUS_INFORMATION_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_COST_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_COST_DECIMAL_DIGITS
    _values = set()
    for _k, _v in _common._ORDERLINESTATUSASDICT.items():
        _values.add(_v.__len__())
        _values.add(_k.__len__())
    MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES: int = max(_values)  # Maximum length of log type choices
    del _values, _k, _v



class Logs:
    MAXIMUM_MESSAGE_LENGTH: int = 500
    ORIGIN_MAXIMUM_LENGTH: int = 500
    _values = set()
    for _k, _v in _common._LOGTYPEASDICT.items():
        _values.add(_v.__len__())
        _values.add(_k.__len__())
    MAXIMUM_LENGTH_OF_LOGTYPE_CHOICES: int = max(_values)  # Maximum length of log type choices
    del _values, _k, _v