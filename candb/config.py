# <Initfile>
import candb.common as _c
from NewCanned import *

# Alias for .common.OrderLineStatus
OlStat = _c.OrderLineStatus

INSECURE_SUPERUSERS_ACTIVE: bool = True  # During development, some superusers created with insecure passwords or authentication methods. This needs to be False before deployment.
DEFAULT_AUTOSAVE_MODE: bool = True  # Default autosave mode for all models

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
    USE_ANY_AVAILABILITY: bool = True  # By default, check all applicable availabilities for a product, and only then, raise InsufficientStock

class OrderLine:
    DEFAULT_STATUS: str = _c.OrderLineStatus.Pending
    MAXIMUM_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH
    MAXIMUM_COST_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS
    COST_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS
    _values = set()
    for _k, _v in _c.ORDERLINE_STATUS_AS_DICT.items():
        _values.add(_v.__len__())
        _values.add(_k.__len__())
    MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES: int = max(_values)  # Maximum length of log type choices
    del _values, _k, _v

    CANCELLABLE_STATUSES: set[str] = {OlStat.Open, OlStat.Pending, OlStat.Waiting_for_Balance, OlStat.Standing_by_for_Stock}  # Statuses where the orderline can be cancelled
    CONFIRMED_STATUSES: set[str] = {OlStat.Confirmed, OlStat.In_Production, OlStat.Delivered, OlStat.Standing_by_for_Stock_But_Locked}  # Statuses where the orderline is confirmed (i.e. the purchase is guaranteed)
    CONFIRMABLE_STATUSES: set[str] = {OlStat.Open, OlStat.Pending, OlStat.Standing_by_for_Stock}  # Statuses where the orderline can be moved to confirmed
    LOCKED_STATUSES: set[str] = {OlStat.Locked, OlStat.Standing_by_for_Stock_But_Locked, OlStat.In_Production, OlStat.Delivered, OlStat.Returned}  # Statuses where the orderline is locked
    NON_PAYABLE_STATUSES: set[str] = {OlStat.Delivered, OlStat.Returned, OlStat.Cancelled}  # Statuses where the orderline should not be paid for because it is fulfilled, returned or cancelled

    DEFAULT_CONFIRMED_STATUS: str = OlStat.Confirmed  # Default status for confirmed orderlines
    ALLOW_UNPAID_CONFIRMED: bool = False  # If confirmed orderlines can be unpaid but confirmed (recommended to be False)
    DEFAULT_UNPAID_CONFIRMED_STATUS: str = None  # Default status for confirmed orderlines that are not paid for




class Profile:
    __INACCESSIBLE_SUPERUSER_ID__: int = 0  # The ID of the superuser that cannot be accessed
    __ALLOW_SCRIPTS_TO_ACCESS_SUPERUSER__: bool = True  # If scripts can access the superuser
    __SCRIPTS_PERMITTED_TO_ACCESS_SUPERUSER__: set[PathType] = {str(BASE_DIR / "internal" / "security.py"),}  # Scripts that are permitted to access the superuser
    __FUNCTIONS_PERMITTED_TO_ACCESS_SUPERUSER__: set[str] = {"__get_inaccessible_superuser__"}  # Functions that are permitted to access the superuser

    MAXIMUM_BALANCE_DIGITS: int = DEFAULT_MAXIMUM_PRICE_DIGITS  # Maximum digits for balance
    BALANCE_DECIMAL_DIGITS: int = DEFAULT_PRICE_DECIMAL_DIGITS  # Decimal digits for balance
    MAXIMUM_ADMIN_NOTES_LENGTH: int = DEFAULT_MAXIMUM_NOTES_LENGTH  # Maximum length for admin notes
    ALLOW_NEGATIVE_BALANCE: bool = False  # If negative balance is allowed. Recommended to be False
    MAXIMUM_NEGATIVE_BALANCE: Decimal = Decimal(0)  # Maximum negative balance allowed


class Vendor:
    MAXIMUM_NAME_LENGTH: int = DEFAULT_MAXIMUM_NAME_LENGTH



