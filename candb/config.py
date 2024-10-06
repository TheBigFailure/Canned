# <Initfile>
import candb.common as _common
from NewCanned import *

INSECURE_SUPERUSERS_ACTIVE: bool = True  # During development, some superusers created with insecure passwords or authentication methods. This needs to be False before deployment.

DEFAULT_MAXIMUM_NOTES_LENGTH: int = 500  # Default maximum length for notes
DEFAULT_MAXIMUM_NAME_LENGTH: int = 100  # Default maximum length for name
DEFAULT_MAXIMUM_PRICE_DIGITS: int = 10  # Default maximum digits for cost
DEFAULT_PRICE_DECIMAL_DIGITS: int = 2  # Default decimal digits for cost
DEFAULT_MAXIMUM_PRODUCT_TAGS: int = 64  # Default maximum number of tags for a product
DEFAULT_MAXIMUM_PRODUCT_TAG_LENGTH: int = 64  # Default maximum length for each tags on a product
DEFAULT_MAXIMUM_DESCRIPTION_LENGTH: int = 1024  # Default maximum length for description

class Order:
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS


class Product:
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_NAME_LENGTH: int = DEFAULT_MAXIMUM_NAME_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS
    MAXIMUM_PRODUCT_TAGS: int = DEFAULT_MAXIMUM_PRODUCT_TAGS
    MAXIMUM_PRODUCT_TAG_LENGTH: int = DEFAULT_MAXIMUM_PRODUCT_TAG_LENGTH
    MAXIMUM_DESCRIPTION_LENGTH: int = DEFAULT_MAXIMUM_DESCRIPTION_LENGTH

class OrderLine:
    DEFAULT_STATUS: str = _common.OrderLineStatus.Pending
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS
    _values = set()
    for _k, _v in _common.ORDERLINE_STATUS_AS_DICT.items():
        _values.add(_v.__len__())
        _values.add(_k.__len__())
    MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES: int = max(_values)  # Maximum length of log type choices
    del _values, _k, _v


class Profile:
    __INACCESSIBLE_SUPERUSER_ID__: int = 0  # The ID of the superuser that cannot be accessed
    __ALLOW_SCRIPTS_TO_ACCESS_SUPERUSER__: bool = True  # If scripts can access the superuser
    __SCRIPTS_PERMITTED_TO_ACCESS_SUPERUSER__: set[PathType] = {str(BASE_DIR / "internal" / "security.py"),}  # Scripts that are permitted to access the superuser
    __FUNCTIONS_PERMITTED_TO_ACCESS_SUPERUSER__: set[str] = {"__get_inaccessible_superuser__"}  # Functions that are permitted to access the superuser

    MAXIMUM_BALANCE_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS  # Maximum digits for balance
    BALANCE_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS  # Decimal digits for balance
    MAXIMUM_ADMIN_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH  # Maximum length for admin notes

