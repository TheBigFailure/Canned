# <Initfile>
from json import JSONEncoder, JSONDecoder
from datetime import datetime, date
from typing import Union
from django.db import transaction
from typing import NoReturn


class OrderLineStatus:
    Pending = "P"  # Pending confirmation (e.g. initial request made to server) . Also known as "Created"
    Open = "O"  # Open for changes
    Waiting_for_Balance = "W"  # A submitted payment without enough balance to pass on order to production
    Confirmed = "C"  # Confirmed by the server
    In_Production = "I"  # Actively being made
    Delivered = "D"  # Delivered to the user
    Returned = "R"  # Returned by the user: return was successful
    Cancelled = "X"  # Cancelled by the user
    Locked = "L"  # Cannot be edited by those without access
    Standing_by_for_Stock = "S"  # Standing by for when stock is available. Also known as "Backordered". This implies the order has NOT been confirmed or processed.
    Standing_by_for_Stock_But_Locked = "B"  # Standing by for when stock is available, however the order is guaranteed to be processed. This implies the order has been confirmed and is not modifiable.


ORDERLINE_STATUS_AS_DICT = dict({k: v for k, v in OrderLineStatus.__dict__.items() if not k.startswith("__")})


class DateTimeEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return "__datetime__", obj.isoformat()
        elif isinstance(obj, date):
            return "__date__", obj.toordinal()
        return super(self.__class__, self).default(obj)


class DateTimeDecoder(JSONDecoder):
    def __init__(self, *args, **kwargs):
        JSONDecoder.__init__(self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        new_obj = dict()
        for k, v in obj.items():
            k: str  # JSON keys are always strings
            if k.isdigit():
                # So, k: v
                # where v = [[start, end], stockConfig] or v = ['__default__', stockConfig]
                if isinstance(v[0][0], int):
                    v[0] = tuple(v[0])
                elif v[0] != "default":
                    start, end = v[0]
                    if start[0] == "__datetime__":
                        start = datetime.fromisoformat(start[1])
                        end = datetime.fromisoformat(end[1])
                    elif start[0] == "__date__":
                        start = date.fromordinal(start[1])
                        end = date.fromordinal(end[1])
                    v = (start, end), v[1]
                new_obj[int(k)] = tuple(v)
            else:  # For stockConfig
                new_obj[k] = v
        # Reorder the keys so that the lowest integer keys are first
        new_obj = dict(sorted(new_obj.items(), key=lambda _: _[0]))
        return new_obj


type StockConfiguration = dict[str: bool | int]
type TimeRange = tuple[datetime, datetime] | tuple[date, date] | tuple[int, int]
type AvailabilityConfiguration = dict[int: TimeRange | str, StockConfiguration]
type AvailabilityIndicator = int | bool  # int: a numeric quantity, True: infinite, False: unavailable


class OrderProcessingException(Exception):
    def __init__(self, message: str, hint: str = "", modelObj: object = None):
        if modelObj:
            message = f"in {modelObj.__repr__()}:\nthe exception \"{message}\" occurred."
        if hint:
            message += f"\n\nHint: {hint}"

        super().__init__(message)
    pass


class InvalidPriority(OrderProcessingException):
    pass

class NoStockTypeSpecified(OrderProcessingException):
    pass

class IncorrectStockTypeSpecified(OrderProcessingException):
    pass

class NoTimerangeApplicable(OrderProcessingException):
    pass

class InsufficientFunds(OrderProcessingException):
    pass

class InsufficientStock(OrderProcessingException):
    pass

class AvailabilityReferenceNotSet(OrderProcessingException):
    pass

class AlreadyCancelled(OrderProcessingException):
    pass

class StatusNotCancellable(OrderProcessingException):
    pass

class StatusNotConfirmable(OrderProcessingException):
    pass

class Locked(OrderProcessingException):
    pass

class CostNotCalculated(OrderProcessingException):
    pass

class AvailabilityIDNotFound(OrderProcessingException):
    pass

class ExceedsModelLimits(OrderProcessingException):
    pass

class MultipleDefaultBrackets(OrderProcessingException):
    pass

class IncorrectBracketType(OrderProcessingException):
    pass


# Not part of OrderProcessingException as it is a database error that should theoretically never occur.
class DatabaseBug(Exception):
    pass

# Again, should not be caught ever and should immediately exit before any further damage is done.
class AtomicTransactionRequired(Exception):
    pass


def checkAtomicForDangerousOperations() -> None | NoReturn:
    """
    Checks if the current transaction is atomic. If it is, it raises an error.
    """
    if not transaction.get_connection().in_atomic_block:
        raise AtomicTransactionRequired("the operation is dangerous and must be done within an atomic transaction")

def qtyGoE(qty: AvailabilityIndicator, minQty: AvailabilityIndicator) -> bool:
    if qty is False:
        return True
    if qty is True:
        return minQty is True
    if isinstance(minQty, bool):
        if minQty is False:
            return True
        # If minQty is True, then qty must be True to be greater than or equal to minQty.
        # However, this is already checked above. Therefore, return False
        return False
    return qty >= minQty




