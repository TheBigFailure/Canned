import django.db.models

from candb import *
from candb import config as cfg
from candb import common as _common
from candb.common import qtyGoE
from django.contrib.auth.models import AbstractUser
from concurrency.fields import IntegerVersionField
from concurrency.exceptions import RecordModifiedError

class IntegerSet(models.Field):
    description = "Class for Custom Field that stores and retrieves a set of integers from a database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def from_db_value(self, value, expression, connection) -> set[int] | None:
        if value is None: return None
        vals = set(map(int, value.split(',')))
        self._checkValsAccepted(vals)
        return vals

    def to_python(self, value) -> set[int] | None:
        if value is None: return None
        vals = set(map(int, value.split(',')))
        self._checkValsAccepted(vals)
        # If anything but 0, 1, 2, 3, 4, 5 or 6 is in vals, raise Error
        return vals

    def _checkValsAccepted(self, value: set[int]):
        if not not (value - {0, 1, 2, 3, 4, 5, 6}):
            raise ValueError("IntegerSet only accepts values in range of 0-6, inclusive")

    def get_prep_value(self, value) -> str | None:
        if value is None: return None
        self._checkValsAccepted(value)
        return ','.join(map(str, value))


# Create your models here.
class Profile(AbstractUser):
    """
    The model for a user profile. Inherits from Django's Abstract
    """
    phone = models.CharField(max_length=22, help_text="Phone Number", null=True, blank=True)  # Uses format +CCCCC/NNNNNNNNNNNNNNN where CC is country code and NNNNNNNNNNNNNNN is the phone number
    image = models.ImageField(default='default.jpg', upload_to='profile_pics', blank=True, null=True)
    balance = models.DecimalField(max_digits=cfg.Profile.MAXIMUM_BALANCE_DIGITS, decimal_places=cfg.Profile.BALANCE_DECIMAL_DIGITS, help_text="User Balance", null=False, blank=False, default=0)
    adminNotes = models.TextField(help_text="Admin Notes", null=True, blank=False, default=None, max_length=cfg.Profile.MAXIMUM_ADMIN_NOTES_LENGTH)
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")

    @classmethod
    def create(cls: Union[Self, Callable], username: str, first_name: str = None, last_name: str = None, *_, email: str = None,
               phoneNCountryCode: str = None, pNumber: str = None, password: str = None, is_staff: bool = False,
               is_superuser: bool = False, image: str = None, adminNotes: str = None, overrideBalance: float = None,
               forceID: int = None, requireSecurePassword: bool = True,
               autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """
        Create a new user profile
        """
        if _: raise ValueError("positional arguments given are not permitted")
        if forceID is not None:
            if not isinstance(forceID, int):
                raise TypeError("bad type for forceID")
            if forceID < 0:
                raise ValueError("forceID must be non-negative")
            if Profile.objects.filter(id=forceID).exists():
                raise ValueError("forceID already exists")
        if not isinstance(username, str):
            raise TypeError("bad type for username")
        if not isinstance(first_name, str) and first_name is not None:
            raise TypeError("bad type for first_name")
        if not isinstance(last_name, str) and last_name is not None:
            raise TypeError("bad type for last_name")
        if not isinstance(email, str) and email is not None:
            raise TypeError("bad type for email")
        if not isinstance(phoneNCountryCode, str) and phoneNCountryCode is not None:
            raise TypeError("bad type for phoneNCountryCode")
        if not isinstance(pNumber, str) and pNumber is not None:
            raise TypeError("bad type for pNumber")
        if not (not phoneNCountryCode and not pNumber) or (phoneNCountryCode and pNumber):
            raise ValueError("phoneNCountryCode and pNumber must be either both None or both not None")
        # Noinspection due to PyCharm bug
        # noinspection PyUnresolvedReferences
        if phoneNCountryCode is not None and (phoneNCountryCode.__len__() > 5 or 3 > pNumber.__len__() > 15):
            raise ValueError("phoneNCountryCode must no more than 5 characters long, and pNumber must be between 3 and 15 characters long")
        if not isinstance(is_staff, bool):
            raise TypeError("bad type for is_staff")
        if not isinstance(is_superuser, bool):
            raise TypeError("bad type for is_superuser")
        if not isinstance(image, str) and image is not None:
            raise TypeError("bad type for image")
        # Force staff and superusers to use secure passwords
        if (is_staff or is_superuser) and not requireSecurePassword:
            raise PermissionError("superusers and staff must use secure passwords")
        # Confirm superuser creation. Also require another superuser to confirm.
        if adminNotes is not None and not isinstance(adminNotes, str):
            raise TypeError("bad type for adminNotes")
        if overrideBalance is not None and not isinstance(overrideBalance, float):
            raise TypeError("bad type for overrideBalance")
        if is_superuser:
            match input("WARNING: You are creating a superuser account. This is VERY dangerous. Are you sure? (y/[N] - case-sensitive) > "):
                case 'y':
                    print("To confirm, please log in as another superuser to create this account.")
                    username = input("Username: ")
                    password = getpass("Password: ")
                    if not Profile.objects.filter(username=username).exists():
                        raise PermissionError("superuser creation cancelled as no user exists with that username")
                    supposedSuperuser = Profile.objects.get(username=username)
                    if not supposedSuperuser.is_superuser:
                        raise PermissionError("superuser creation cancelled as user is not superuser")
                    if not supposedSuperuser.check_password(password):
                        raise PermissionError("superuser creation cancelled as password is incorrect")
                case _:
                    raise ValueError("superuser creation cancelled as per user request. Again: this is not recommended.")
        if requireSecurePassword:
            if password is None:
                raise ValueError("password is required")
            validate_password(password)
        phone = None
        if phoneNCountryCode is not None:
            phone = f'+{phoneNCountryCode}/{pNumber}'
        # Done to allow for blank fields, not just None
        kwargs = {n: v for n, v in {"username": username, "first_name": first_name, "last_name": last_name,
                                    "email": email, "is_staff": is_staff,
                                    "is_superuser": is_superuser, "image": image, "phone": phone,
                                    "adminNotes": adminNotes, "balance": overrideBalance}.items()
                  if v is not None}
        if forceID is not None:
            kwargs["id"] = forceID
        pf = cls(**kwargs)
        pf.set_password(password)
        if autosave: pf.save()
        return pf

    def compareVersionWithSelf(self: Self, other: Self, raiseException: bool = True) -> bool:
        """
        Compare the version of this object with another object
        """
        if self._saveVersion == other._saveVersion:  # Remember, _saveVersion doesn't change until self.save() is called
            return True
        if raiseException:
            raise RecordModifiedError(f"version mismatch between {self.__repr__()} and {other.__repr__()}")





    def _checkBalance(self: Self, amount: float | Decimal,
                      overrideAllowNegativeBalance: bool = cfg.Profile.ALLOW_NEGATIVE_BALANCE,
                      overrideMaximumNegativeBalance: float | Decimal = cfg.Profile.MAXIMUM_NEGATIVE_BALANCE) -> bool:
        """
        Check if the user has enough balance
        """
        if amount < 0:
            raise ValueError("amount must be non-negative")
        if overrideAllowNegativeBalance:
            return self.balance - amount >= overrideMaximumNegativeBalance
        return self.balance >= amount

    def subtractBalance(self: Self, amount: float | Decimal, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE,
                        raiseException: bool = True, overrideAllowNegativeBalance: bool = cfg.Profile.ALLOW_NEGATIVE_BALANCE,
                      overrideMaximumNegativeBalance: float | Decimal = cfg.Profile.MAXIMUM_NEGATIVE_BALANCE) -> bool | NoReturn:
        """
        Subtract balance from the user

        :param amount: Amount to subtract (as a positive float/Decimal)
        :param autosave: Save the user after subtracting the balance
        :param raiseException: Raise an exception if the operation fails. Otherwise, return False. Recommended to be True.
        :param overrideAllowNegativeBalance: Override the ALLOW_NEGATIVE_BALANCE config
        :param overrideMaximumNegativeBalance: Override the MAXIMUM_NEGATIVE_BALANCE config
        :return: True if the operation was successful, False otherwise. If raiseException is True, then an exception is raised if the operation fails.
        """
        if not self._checkBalance(amount, overrideAllowNegativeBalance=overrideAllowNegativeBalance, overrideMaximumNegativeBalance=overrideMaximumNegativeBalance):
            if raiseException:
                raise _common.InsufficientFunds(f"insufficient funds to subtract {amount} from {self.__repr__()}")
            return False
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.balance -= amount
        if autosave: self.save()
        return True

    def addBalance(self, amount: float, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> NoReturn | None:
        """
        Add balance to the user
        """
        if amount < 0:
            raise ValueError("amount must be non-negative")
        self.balance += amount
        if autosave: self.save()

    def __str__(self):
        return f'<User {self.last_name.upper()}, {self.first_name}: {self.username} with ID {self.id}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} \'{self.last_name.upper()}, {self.first_name}\': {self.username}; ID {self.id}>'


class Order(models.Model):
    """
    The model for a user order. Linked to multiple orderLines.
    """
    id = models.CharField(primary_key=True, editable=False, help_text="Unique Order ID, same across databases", null=False, blank=False, unique=True, max_length=42)  # ORDER-UUID4 (len 42)
    orderTime = models.DateTimeField(help_text="Order Time", null=False, blank=False)
    overrideCost = models.DecimalField(max_digits=cfg.Order.MAXIMUM_COST_DIGITS, decimal_places=cfg.Order.COST_DECIMAL_DIGITS, help_text="Override Cost", null=True, blank=False, default=None)  # If None, means not overridden.
    totalCost = models.DecimalField(max_digits=cfg.Order.MAXIMUM_COST_DIGITS, decimal_places=cfg.Order.COST_DECIMAL_DIGITS, help_text="Order Total Practical Price", null=True)  # If None, means not calculated yet.
    totalPaid = models.DecimalField(max_digits=cfg.Order.MAXIMUM_COST_DIGITS, decimal_places=cfg.Order.COST_DECIMAL_DIGITS, help_text="Total Paid", null=False, blank=False, default=0)  # Total amount paid by the user
    notes = models.TextField(help_text="Order Notes", null=True, blank=False, default=None, max_length=cfg.Order.MAXIMUM_NOTES_LENGTH)
    user = models.ForeignKey(help_text="User ID", blank=False, null=False, on_delete=models.CASCADE, to=Profile)


    class Meta:
        ordering = ['-orderTime', 'id']
        db_table_comment = "Orders"
        permissions = [("view_any_order", "Can view any order regardless of its owner"), ("change_any_order", "Can change any orders regardless of its owner"), ("delete_any_order", "Can delete orders regardless of its owner"), ("add_any_order", "Can add any order regardless of its owner"), ("change_any_order_but_overridecost", "Can change orders regardless of its owner, but cannot override the cost")]
        indexes = [models.Index(fields=["id",], name="CanDB_Order_ID_Index")]
        verbose_name = "Order"
        verbose_name_plural = "Orders"
        constraints = [
            models.UniqueConstraint(fields=["id",], name="CanDB_Order_ID_User_Unique"),
            models.CheckConstraint(check=models.Q(totalCost__gte=0), name="CanDB_Order_TotalCost_NonNegative", violation_error_code="ORDER-TOTALCOST-1", violation_error_message="Total cost of an order cannot negative"),
            models.CheckConstraint(check=models.Q(overrideCost__gte=0), name="CanDB_Order_OverrideCost_NonNegative",
                                   violation_error_code="ORDER-OVERRIDE-1",
                                   violation_error_message="Total cost of an order cannot negative"),
            models.CheckConstraint(check=models.Q(id__startswith="ORDER-"), name="CanDB_Order_ID_Prefix", violation_error_code="ORDER-ID-1", violation_error_message="Order ID must start with 'ORDER-'"),
            models.CheckConstraint(check=models.Q(id__len=42), name="CanDB_Order_ID_Len", violation_error_code="ORDER-ID-2", violation_error_message="Order ID must be 42 characters long"),
        ]


    @classmethod
    def create(cls: Union[Self, Callable], profile: Profile, notes: str = None, overwriteTime: datetime = None,
               autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """negative
        Create a new order
        """
        if overwriteTime is None:
            overwriteTime = datetime.now(tz=TZ_INFO)
        uid = f'ORDER-{uuid.uuid4()}'
        od = cls(
            id=uid,
            user=profile,
            notes=notes,
            orderTime=overwriteTime
        )
        if autosave: od.save()
        return od


    def cancel(self: Self, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> NoReturn | None | bool:
        """
        Cancels the order (and hence all orderlines).
        If specific orderlines need to be cancelled, then the orderlines must be cancelled individually using the orderline.cancel() method.

        An exception MUST be raised to exit an atomic transaction in the case of a bad operation.
        IF THE EXCEPTION IS CAUGHT, DO NOT CALL order.save UNDER ANY CIRCUMSTANCE
        """
        with transaction.atomic():
            for ol in self.orderline_set.all():
                ol.cancel(raiseException=True, autosave=autosave, autostartTransaction=False)
            if autosave: self.save()



    def calculateTotalCost(self: Self, raiseException: bool = False, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> float | NoReturn | bool:
        """
        Calculates the total cost of the order
        :param raiseException: Raise an exception if the operation fails. Otherwise, return False.
        :param autosave: Save the order after calculating the total cost
        :return: The total cost of the order. Returns False if the operation fails and raiseException is False.
        """
        total = 0
        for ol in self.orderline_set.all():
            try:
                total += ol.getPracticalItemCost()
            except _common.CostNotCalculated as _e:
                if raiseException:
                    raise _e
                return False
        if total < 0:
            if raiseException:
                raise ValueError("total cost cannot be negative")
            return False
        self.totalCost = total
        if autosave: self.save()
        return total

    def __str__(self):
        return f'<Order {self.id} by {self.user.username} at {self.orderTime}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id} by {self.user.username} at {self.orderTime}>'


class Product(models.Model):
    """
    The model for a product
    """
    id = models.CharField(max_length=44, primary_key=True, help_text="Unique Product ID, same across databases", null=False, blank=False, unique=True)  # PRODUCT-UUID4 (len 44)
    name = models.CharField(max_length=cfg.Product.MAXIMUM_NAME_LENGTH, help_text="Product Name", null=False, blank=False)
    price = models.DecimalField(max_digits=cfg.Product.MAXIMUM_COST_DIGITS, decimal_places=cfg.Product.COST_DECIMAL_DIGITS, help_text="Product Price", null=False, blank=False)
    description = models.TextField(max_length=cfg.Product.MAXIMUM_DESCRIPTION_LENGTH, help_text="Product Description", null=True, blank=False)
    image = models.ImageField(upload_to="product_images", help_text="Product Image", null=True)
    # Available stock is equal to physicalStock - reservedStock.
    availability = models.JSONField(help_text="Product Availability Configuration", null=True, blank=False, default=None, encoder=_common.DateTimeEncoder, decoder=_common.DateTimeDecoder)  # Use None for no availability: always use model stock.
    # New availability function as follows:
    """
    ```python
    stockConfig: dict[str: bool | int] = {
        "available":        bool,   # [REQUIRED] Specify if product is available during time period. Ignores all other fields if False.pp
        "reference":        int,    # Specify if stock configuration should inherit from another stock configuration by ID. Ignores all other fields but available. Not required. MUST BE A VALID REFERENCE IF SPECIFIED.
        "useModelStock":    bool,   # Specify if stock is to be used from the Product model fields (physicalStock, reservedStock)
        "infinite":         bool,   # Specify if stock is infinite (ignores "stock"). E.g., something made to order may use this
        "physicalStock":    int,    # Specify number of stock available during time period
        "reservedStock":    int,    # Specify number of stock reserved during time period
    }
    ```
    ```python
    availability: dict[
        int: tuple[
            tuple[
                datetime.datetime | datetime.date | int] | str, 
                dict[str: bool | int]
            ]
        ]
    ] = 
    {
        id[int]:    ((from[datetime.datetime], until[datetime.datetime]),    stockConfig)[tuple], 
        id[int]:    ((from[datetime.date], until[datetime.date]),            stockConfig)[tuple], 
        id[int]:    ((from[int], until[int]),                                stockConfig)[tuple], # e.g., 0 = Monday, 1 = Tuesday, etc., 6 = Sunday. Inclusive.
        id[int]:    ("default"[Literal],                                     stockConfig)[tuple], # Default option, if availability is not specified for a day this is used.
    }
    ```
    Please note timestamps are inclusive.
    It is recommended to use one type of availability for one product. For example, use only datetime, or only
        datetime.date, or only day[int], then use "default".
    [IMPORTANT]: When CanDB checks the availability of a product, it will use the first availability configuration that matches the current time by default.
            At least one timestamp must apply to the current time. If no timestamp applies, then the "default" configuration will be used.
            However, if no "default" configuration is specified, then a NoAvailabilityError will be raised. 
                For example, if both configuration 1 and 2 fits the timeframe and configuration 1 indicates there is no stock remaining, even if 
                configuration 2 indicates there is stock remaining, CanDB will use configuration 1.
            To avoid this behaviour, specify True for "attemptUntilStockFound" in the checkProductStock function.
    [IMPORTANT]: When CanDB checks the stock configuration of an availability configuration, it will prioritise arguments in the following order:
                1. "available"
                2. "reference"
                3. "useModelStock"
                4. "infinite"
                5. "physicalStock" and "reservedStock".
            CanDB will IGNORE all other arguments if the higher priority arguments can determine the stock quantity.
            This means if there is a conflict between arguments, the higher priority arguments will be used and the conflict will NOT be detected.
            For example, if "available" is False, then the product is not available, regardless of the other arguments.
            
    If availability is None, then the product uses stock as the only availability. If stock is None, then the product is always available.
    """
    notes = models.TextField(help_text="Product Notes", null=True, blank=False, default=None, max_length=cfg.Product.MAXIMUM_NOTES_LENGTH)
    tags = models.JSONField(max_length=cfg.Product.MAXIMUM_PRODUCT_TAGS, help_text="Product Tags", null=False, blank=True)
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")


    class Meta:
        ordering = ['name', 'id']
        db_table_comment = "Product"
        permissions = list()
        indexes = [models.Index(fields=["id",], name="CanDB_Product_OLD_ID_Index")]
        verbose_name = "Product"
        verbose_name_plural = "Products"
        constraints = [
            models.CheckConstraint(check=models.Q(id__startswith="PRODUCT-"), name="CanDB_Product_ID_Prefix",
                                   violation_error_code="PRODUCT-ID-1",
                                   violation_error_message="Product ID must start with 'PRODUCT-'"),
            models.CheckConstraint(check=models.Q(id__len=44), name="CanDB_Product_ID_Len",
                                   violation_error_code="PRODUCT-ID-2",
                                   violation_error_message="Product ID must be 44 characters long"),
            # Check that if physicalStock is None, reservedStock must be None
            models.CheckConstraint(check=models.Q(physicalStock__isnull=False) | (models.Q(physicalStock__isnull=True) & ~ models.Q(reservedStock__isnull=True)),
                                   name="CanDB_Product_Stock_Null",
                                   violation_error_code="PRODUCT-STOCK-1",
                                   violation_error_message="If physical stock is None, reserved stock must be None"),
            # Reserve stock must be smaller or equal to physical stock
            models.CheckConstraint(check=models.Q(reservedStock__lte=models.F("physicalStock")),
                                   name="CanDB_Product_Stock_Reserve",
                                   violation_error_code="PRODUCT-STOCK-2",
                                   violation_error_message="Reserved stock must be smaller or equal to physical stock"),
        ]


    @classmethod
    def create(cls: Union[Self, Callable], name: str, price: float, description: str, image: str = None, physicalStock: int | None = 0,
               reservedStock: int | None = 0, notes: str = None, tags: list[str] | tuple[str] = None,
               autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """
        Create a new product
        """
        uid = f'PRODUCT-{uuid.uuid4()}'
        if physicalStock is None:
            if reservedStock is not None:
                raise ValueError("reserved stock must be None when physical stock is None as None indicates infinite stock")
        elif not isinstance(physicalStock, int):
            raise TypeError("bad type for physicalStock")
        elif isinstance(reservedStock, int):
            if reservedStock > physicalStock:
                raise ValueError("reservedStock must be smaller or equal to physicalStock")
        else:
            raise TypeError("bad type for reservedStock%s" % (" (hint: reservedStock must be int if physicalStock is int)" if physicalStock is not None else ''))

        if physicalStock != '' and physicalStock < 0:
            raise ValueError("physicalStock must be a non-negative integer")
        if reservedStock is not None and reservedStock < 0:
            raise ValueError("reservedStock must be a non-negative integer")
        if tags is not None and not isinstance(tags, (list, tuple)):
            raise TypeError("bad type for tags")
        if tags is None: tags = list()

        prod = cls(
            id=uid,
            name=name,
            price=price,
            description=description,
            image=image,
            physicalStock=physicalStock,
            reservedStock=reservedStock,
            notes=notes,
            tags=tags
        )
        if autosave: prod.save()
        return prod



    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def _modelStockAvailable(self) -> int | bool:
        """
        Internal function used for checking stock availability for the model stock
        :return: stock available. If False, then stock is not available. If True, then stock is infinite. Otherwise,
                    the stock available is returned.
        """
        # If None, then stock is infinite
        if self.physicalStock is None:
            return True
        # If two fields are equal, then no stock is available
        if self.physicalStock == self.reservedStock:
            return False
        # Should never happen. Used to catch bugs or accidents
        if self.physicalStock - self.reservedStock < 0:
            raise _common.DatabaseBug("reserved stock must be smaller or equal to physical stock")
        return self.physicalStock - self.reservedStock

    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def _stockAvailableForStockConfig(self, _config: _common.AvailabilityConfiguration) -> _common.AvailabilityIndicator:
        """
        Internal function used for checking stock availability for a specific stock configuration
        :param _config: Stock configuration to check stock available for
        :return: stock available. If False, then stock is not available. If True, then stock is infinite. Otherwise,
                    the stock available is returned.
        """
        # If not available, override all.
        if not _config["available"]:
            return False
        # If reference, override below and use ID reference
        if "reference" in _config:
            return self._stockAvailableForID(_config["reference"])
        # If useModelStock, override below and use model stock
        if "useModelStock" in _config and _config["useModelStock"]:
            return self._modelStockAvailable()
        # If infinite, override below and return True regardless
        if "infinite" in _config and _config["infinite"]:
            return True
        # If reserveStock is equal to physicalStock, then no stock is available.
        if _config["physicalStock"] == _config["reservedStock"]:
            return False
        # Should never happen. Used to catch bugs or accidents
        if _config["physicalStock"] - _config["reservedStock"] < 0:
            raise _common.DatabaseBug("reserved stock must be smaller or equal to physical stock")
        # Return qty
        return _config["physicalStock"] - _config["reservedStock"]


    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def _stockAvailableForID(self, refID: int) -> _common.AvailabilityIndicator:
        """
        Internal function used for checking stock availability for a specific availability reference ID
        :param refID: RefID to check stock available for
        :return: stock available. If False, then stock is not available. If True, then stock is infinite. Otherwise,
                    the stock available is returned.
        """
        try:
            return self._stockAvailableForStockConfig(self.availability[refID][1])
        except KeyError as _e:
            raise _common.AvailabilityIDNotFound(f"availability ID {refID} not found") from _e


    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    @staticmethod
    def _checkIfTimeInRange(time: datetime, timerange: _common.TimeRange) -> bool:
        """
        Check if a time is in a timerange
        :param time: Time to check
        :param timerange: Timerange to check
        :return: True if time is in timerange, False otherwise
        """
        # Self-explanatory
        if isinstance(timerange[0], datetime):
            return timerange[0] <= time <= timerange[1]
        if isinstance(timerange[0], date):
            return timerange[0] <= time.date() <= timerange[1]
        if isinstance(timerange[0], int):
            return timerange[0] <= time.weekday() <= timerange[1]
        raise TypeError("bad type for timerange")

    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    @staticmethod
    def canContributeQty(offer: _common.AvailabilityConfiguration, maximum: _common.AvailabilityConfiguration) -> int:
        """
        Check how much an '`offer`' can contribute towards a total (i.e., `maximum`).

        :param offer: How much is available
        :param maximum: The target value to reach. Even if offer can't reach maximum, it should still contribute as much as possible.
        :return: How much `offer` can contribute towards `maximum`.
        """
        if maximum is False or offer is False:
            return 0
        if offer is True:
            return maximum
        if maximum is True:
            return offer
        return min(offer, maximum)

    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def checkProductStock(self, quantityRequired: int, attemptUntilStockFound: bool = False, findMaximum: bool = False,
                          prioritiseInfinite: bool = False, overrideTime: datetime = None
                          ) -> tuple[bool, int | bool | None, dict[int: int] | None]:
        """
        Check if the product has enough stock to sell.
        This function will search through the availability configurations IN THE ORDER THEY ARE DEFINED in the availability field.
        THIS MEANS EVEN IF ONE CONFIGURATION CAN FULFILL THE QUANTITY REQUIRED, THE FUNCTION WILL STILL USE PREVIOUS CONFIGURATIONS TO SUM UP THE TOTAL STOCK AVAILABLE.
        HOWEVER: There is an exception when `prioritiseInfinite` is `True`. If `True`, then infinite stock configurations will be prioritised over finite stock configurations.

        For example:    if `refID` `1` has 5 stock available, and `refID` `2` has 7 stock available, and `quantityRequired` is 7,
                        even when `findMaximum` if `False`, the function will return `(True, 7, {1: 5, 2: 2})`, not `(True, 7, {2: 7})`.
                        It will always include previous configurations in the contributions REGARDLESS of whether one configuration can
                        fulfill the quantity required by itself.


        :param quantityRequired: Minimum quantity required
        :param attemptUntilStockFound: Will keep searching applicable availability configurations until one is found with enough stock. If `False`, only the first applicable configuration is used.
            When `False`, as only one configuration is used, the contributions (at return tuple index 2) will return None.
        :param findMaximum: Will keep searching applicable availability configurations until the maximum stock available is found. If `False`, only enough stock to fulfill `quantityRequired` is found.
        :param prioritiseInfinite: Will prioritise infinite stock configurations over finite stock configurations. If `True`, infinite stock configurations will be used first. This means that if an infinite stock configuration is found, only it will be present in the contributions.
        :param overrideTime: Override the current time for checking availability. If `None`, use the current time. Should rarely be changed from the default.

        :return: `(True, stockAvailable, contributions)` if the product has enough stock to sell, `(False, None, None)` otherwise.
        `stockAvailabile` is the stock available in total of the configurations searched (i.e., the sum of all of the keys of `contributions`). However, when `findMaximum`, it is the total of all configurations
        `stockAvailable` is in the `_common.AvailabilityIndicator` format.
        `contributions` is a dictionary of the reference IDs of the availability configurations used. In format {refID: quantityReserved}.
        NOTE: contributions may not always return every availability configuration used. It will only return the configurations that contributed to reaching a maximum theoretical stock.
        For example, if `refID` 4 has infinite stock, and `refID` `5` has 5 stock available, `contributions` will ignore `refID` `5`.
        """
        if overrideTime is None: overrideTime = datetime.now(tz=TZ_INFO)

        if findMaximum and not attemptUntilStockFound:
            warnings.warn("findMaximum is True but attemptUntilStockFound is False. The function's programming means that it will imply attemptUntilStockFound is True, even though it is not.", Warning)

        # No availability config, use model stock
        if self.availability is None:
            stkAvlforCfg = self._modelStockAvailable()
            available = qtyGoE(stkAvlforCfg, quantityRequired)
            return available, stkAvlforCfg if available else None, {None: stkAvlforCfg}

        atLeastOneConfigApplicable = False
        qtyFound = 0  # Total amount of stock found
        contributions: dict[int: int] = dict()
        # Check availability configurations
        for refID, (timerange, _config) in self.availability.items():
            if timerange != "default":
                if not self._checkIfTimeInRange(overrideTime, timerange):
                    # Next configuration
                    continue
                atLeastOneConfigApplicable = True  # Set to avoid exception
            else:
                atLeastOneConfigApplicable = True  # Set to avoid exception

            # Now check stock available for the stock configuration
            stkAvlforCfg = self._stockAvailableForStockConfig(_config)
            if not stkAvlforCfg:  # I.e., 0 or False,
                continue
            if stkAvlforCfg is True:  # Infinite stock
                # If prioritiseInfinite, return immediately
                if prioritiseInfinite:
                    return True, True, {refID: True}
                # Regardless of findMaximum, if infinite stock is found, return True. However, also return PREVIOUS contributions.
                return True, True, {**contributions, refID: True}

            # If findMaximum, then don't find canContribute, just add stkAvlforCfg to qtyFound
            if findMaximum:
                qtyFound += stkAvlforCfg
                contributions[refID] = stkAvlforCfg
                continue

            # Otherwise, Check how much this configuration can contribute to the total stock
            maxQtyRequired = quantityRequired - qtyFound
            qtyCfgCanContribute: int = self.canContributeQty(stkAvlforCfg, maxQtyRequired)
            if qtyCfgCanContribute == 0:  # Don't bother if it can't contribute
                continue

            qtyFound += qtyCfgCanContribute
            contributions[refID] = qtyCfgCanContribute


            # Finally, check if qtyFound (made up of multiple refIDs) is adequate to fulfill quantityRequired
            if quantityRequired == qtyFound:  # If the amount found is equal to the maximum quantity required, then it means that the stock is adequate.
                return True, qtyFound, contributions

            if not attemptUntilStockFound:  # Should go through ONLY first configuration if attemptUntilStockFound is False, so if the first configuration is not enough, return False.
                return False, None, None

        else:  # If naturally exited loop (i.e., no break)
            # If no timerange was found
            if not atLeastOneConfigApplicable:
                raise _common.NoTimerangeApplicable(
                    f"no availability configuration applicable for {overrideTime}",
                    hint="ensure at least one availability configuration applies, or set a default",
                    modelObj=self
                )
            if not findMaximum:  # Indicates that the function has gone through all configurations and hasn't found enough stock
                return False, None, None
            # If qtyFound is NOT adequate to fulfill quantityRequired
            if qtyFound < quantityRequired:
                # Only reachable when inadequate stock and at least one stock configuration applicable
                return False, None, None
            return True, qtyFound, contributions

    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def _modifyRsrvStock(self: Self, usingRefID: int | None, by: int) -> None | NoReturn:
        """
        Internal function to modify the stock of the product
        :param usingRefID: Reference ID to use for stock modification in availability. If None, use model stock.
        :param by: Amount to modify stock by. Positive to increase, negative to decrease.
        :return: None. Raises an exception if the operation fails.
        """
        # If no availability config, use model stock
        if usingRefID is None:
            if self.physicalStock is None: return  # Unlimited stock; ignore reserve
            # If the proposed reserved stock exceeds the physical stock, raise an exception
            if self.reservedStock + by > self.physicalStock:
                raise _common.InsufficientStock("reserved stock cannot exceed physical stock")
            # Should never happen. Used to catch bugs or accidents. Functions should check before calling this function to avoid this from occurring.
            elif self.reservedStock + by < 0:
                raise _common.DatabaseBug("stock cannot be negative")
            self.reservedStock += by
            return
        try:
            _config = self.availability[usingRefID][1]
        except KeyError as _e:
            raise _common.AvailabilityIDNotFound(f"availability ID {usingRefID} not found") from _e
        if "reference" in _config:
            return self._modifyRsrvStock(_config["reference"], by)
        if "useModelStock" in _config and _config["useModelStock"]:
            return self._modifyRsrvStock(None, by)
        if "infinite" in _config and _config["infinite"]:
            return
        if _config["physicalStock"] + by < 0:
            raise _common.InsufficientStock("stock cannot be negative")
        _config["physicalStock"] += by

    @deprecated(details="Stock is now managed by TimeBracket and StockConfig")
    def modifyReservedStock(self: Self, usingRefID: int | None, by: int, raiseException: bool = False, autostartTransaction: bool = True, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> bool | NoReturn:
        """
        Modifies the stock of the product

        :param usingRefID: Reference ID to use for stock modification in availability. If None, use model stock.
        :param by: Amount to modify stock by. Positive to increase amount reserved (i.e., decrease available amount), vice versa
        :param raiseException: Raise an exception if the operation fails. Otherwise, return False.
        :param autostartTransaction: Start a transaction for the operation. If False, no inner atomic transaction is started. HIGHLY RECOMMENDED TO KEEP THIS TRUE.
        :param autosave: Save the product after the operation.
        :return: True if stock was successfully modified, False otherwise. If raiseException is True, then an exception is raised if the operation fails.
        """
        if not isinstance(usingRefID, int) and usingRefID is not None:
            raise TypeError("bad type for usingRefID")
        if not isinstance(by, int):
            raise TypeError("bad type for by")
        if not autostartTransaction:
            _common.checkAtomicForDangerousOperations()  # Check if the operation is atomic in case exceptions are raised
        try:
            if autostartTransaction:
                with transaction.atomic():
                    self._modifyRsrvStock(usingRefID, by)
                    if autosave: self.save()
            else:
                self._modifyRsrvStock(usingRefID, by)
                if autosave: self.save()
        except Exception as _e:
            if raiseException:
                raise _e
            return False
        return True



    def __str__(self):
        return f'<Product {self.id}: {self.name}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id}: {self.name}>'



class Vendor(models.Model):
    """
    Product vendors.
    """
    id = models.CharField(max_length=43, primary_key=True, help_text="Unique Vendor ID", null=False, blank=False, unique=True)  # VENDOR-UUID (len 43)
    name = models.CharField(max_length=cfg.Vendor.MAXIMUM_NAME_LENGTH, help_text="Vendor Name", null=False, blank=False)
    vendorAdmin = models.ForeignKey(help_text="Administrator account for vendor", to=Profile, blank=False, null=False, on_delete=models.PROTECT)
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")

    class Meta:
        db_table_comment = "Vendors"
        permissions = [
            ("view_any_vendor", "Can view all vendors"),
            ("change_any_vendor", "Can change any vendor configuration"),
            ("delete_any_vendor", "Can delete any vendor"),
            ("create_any_vendor", "Can create any vendor and assign it to any administrator")
        ]
        indexes = [models.Index(fields=["id", "name"], name="CanDB_Vendor_Index")]
        verbose_name = "Vendor"
        verbose_name_plural = "Vendors"
        constraints = [
            models.CheckConstraint(check=models.Q(id__startswith="VENDOR-"), name="CanDB_Vendor_ID_Prefix",
                                   violation_error_code="VENDOR-ID-1",
                                   violation_error_message="Vendor ID must start with 'VENDOR-'"),
            models.CheckConstraint(check=models.Q(id__len=43), name="CanDB_Vendor_ID_Len",
                                   violation_error_code="VENDOR-ID-2",
                                   violation_error_message="Vendor ID must be 43 characters long"),
        ]


class StockConfig(models.Model):
    """
    Stock configurations for a product

    When a field is not required, ensure null=False, but blank=True.
    """
    id = models.CharField(max_length=42, primary_key=True, help_text="Unique Stock Configuration ID, same across databases", null=False, blank=False, unique=True)  # STOCK-UUID4 (len 42)
    vendor = models.ForeignKey(help_text="Vendor ID", blank=True, null=True, on_delete=models.CASCADE, to=Vendor)
    available = models.BooleanField(help_text="Product Availability", null=False, blank=False, default=True)
    reference = models.ForeignKey(help_text="Reference to another Stock Configuration", blank=True, null=True, on_delete=models.CASCADE, to="self")  # Not required
    infinite = models.BooleanField(help_text="Infinite Stock", null=True, blank=True)  # Not required
    physicalStock = models.PositiveIntegerField(help_text="Physical Stock", null=True, blank=True)  # Not required
    remainingStock = models.PositiveIntegerField(help_text="Remaining Stock", null=True, blank=True)  # Not required
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")

    class Meta:
        db_table_comment = "Stock Configurations"
        permissions = [
            ("view_any_configuration", "Can view all stock configurations"),
            ("change_any_configuration", "Can change any stock configuration regardless of its vendor"),
            ("delete_any_configuration", "Can delete any stock configurations regardless of its vendor"),
            ("add_any_configuration", "Can add stock configurations and assign it to any owner")
        ]
        indexes = [models.Index(fields=["id",], name="CanDB_StockConfig_ID_Index")]
        verbose_name = "Stock Configuration"
        verbose_name_plural = "Stock Configurations"
        constraints = [
            models.CheckConstraint(check=models.Q(id__startswith="STOCK-"), name="CanDB_StockConfig_ID_Prefix",
                                   violation_error_code="STOCKCONFIG-ID-1",
                                   violation_error_message="Stock Configuration ID must start with 'STOCK-'"),
            models.CheckConstraint(check=models.Q(id__len=42), name="CanDB_StockConfig_ID_Len",
                                   violation_error_code="STOCKCONFIG-ID-2",
                                   violation_error_message="Stock Configuration ID must be 42 characters long"),
            # TODO: Write constraints
        ]


    @classmethod
    def create(cls: Union[Self, Callable], *_, vendor: Vendor = None, available: bool = True,
               reference: Self = None, useModelStock: bool = None, infinite: bool = None, physicalStock: int = None,
               remainingStock: int = None, forceID: str = None, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        if _:
            raise TypeError("additional positional arguments provided when not accepted")
        # Available
        if not isinstance(available, bool):
            raise TypeError("expected type bool for available")

        # Check forceID
        if forceID is not None:
            if not isinstance(forceID, str):
                raise TypeError("bad type for forceID")
            if not forceID.startswith("STOCK-"):
                raise ValueError("forceID must start with 'STOCK-'")
            if cls.objects.filter(id=forceID).exists():
                raise ValueError("forced ID already exists")
            if len(forceID) != 42:
                raise ValueError("forceID must be 42 characters long")


        # At least one detail (infinite, use model, reference, phy/rev stock) is present
        atLeastOneDetailPresent: bool = False

        # Infinite
        if infinite is not None:
            if not isinstance(infinite, bool):
                raise TypeError("expected type bool for infinite")
            atLeastOneDetailPresent = True

        # Use Model Stock
        if useModelStock is not None:
            if not isinstance(useModelStock, bool):
                raise TypeError("expected type bool for useModelStock")
            atLeastOneDetailPresent = True

        # Check physicalStock and remainingStock
        if physicalStock is not None:
            if not isinstance(physicalStock, int):
                raise TypeError("expected type int for physicalStock when not None")
            if remainingStock is None or not isinstance(remainingStock, int):
                raise TypeError("expected type int for reserveStock when physicalStock is int")
            if remainingStock > physicalStock or remainingStock < 0:
                raise ValueError("remainingStock must not be smaller than 0 and not larger than physicalStock")
            if physicalStock < 0:
                raise ValueError("physicalStock cannot be smaller than 0")
            atLeastOneDetailPresent = True
        elif remainingStock is not None:
            raise TypeError("remainingStock must be None when physicalStock is None")

        if not atLeastOneDetailPresent:
            raise _common.NoStockTypeSpecified("expected at least one stock specified in stock configuration creation",
                                               hint="specify at least one setting (i.e., reference, useModelStock, infinite, physicalStock/reserveStock)")

        if reference is not None and not isinstance(reference, cls):
            raise TypeError("bad type for reference")

        stockConfig = cls(
            available=available,
            id=f"STOCK-{uuid.uuid4()}" if forceID is None else forceID,
            vendor=vendor,
            reference=reference,
            useModelStock=useModelStock,
            infinite=infinite,
            physicalStock=physicalStock,
            remainingStock=remainingStock
        )
        if autosave: stockConfig.save()
        return stockConfig


    def modifyStock(self: Self, by: int = None, autosave: bool = True) -> NoReturn | None:
        """
        Modifies the stock config to reserve a certain amount of stock.
        :param by: How much to modify the stock config by
        :param autosave: autosave if operation successful
        :return: NoReturn. Raises exception if error, otherwise returns None
        """
        if by == 0:
            return
        qtyAv = self.qtyAvailable()
        if by < 0:  # Reserving Stock
            if not _common.qtyGoE(qtyAv, -by):
                raise _common.InsufficientStock(f"insufficient stock to modify stock by {by}")
            self._stockModifierForce(by)
        else:  # Returning Stock
            ...  # TODO: Program logic for returning stock via Transactions
        if autosave: self.save()


    def _stockModifierForce(self: Self, by: int = None) -> None:
        """
        Modifies stock of StockConfig by a number. Does NOT perform checks.
        ALSO DOES NOT AUTOSAVE. self.save MUST BE CALLED EXTERNALLY TO COMMIT CHANGES.
        :param by: how much to modify remaining stock by.
        :return: None
        """
        if self.reference:
            self.reference._stockModifierForce(by=by)
            return
        if self.infinite:
            return
        self.remainingStock += by


    def _modifyRemainingStock(self: Self, by: int = None, autosave: bool = True) -> int:
        """
        Modify remaining stock.
        :param by: Positive to add, negative to subtract from remainingStock.
        :param autosave: automatically save operation
        :return: Remaining stock after modification
        """
        if not isinstance(self.physicalStock, int) or not isinstance(self.remainingStock, int):
            raise _common.IncorrectStockTypeSpecified("expected physicalStock and remainingStock to be type int",
                                                      hint="is this StockConfig using the correct config type?")
        if not isinstance(by, int):
            raise TypeError("expected type int for by")
        if by > 0:
            if self.remainingStock + by > self.physicalStock:
                raise _common.ExceedsModelLimits("remainingStock cannot exceed physicalStock under any circumstance",
                                                 hint=f"did you mean to deduct {by} from remainingStock? (If so, use {-by}.)")
        else:
            if self.remainingStock + by < 0:
                raise _common.InsufficientStock("insufficient stock to fulfill modification")
        self.remainingStock += by
        if autosave: self.save()
        return self.remainingStock


    def _modifyPhysicalStock(self: Self, by: int = None, autosave: bool = True) -> int:
        """
        Modify physical stock.
        :param by: Positive to add, negative to subtract from physicalStock.
        :param autosave: automatically save operation
        :return: Physical stock after modification
        """
        if not isinstance(self.physicalStock, int) or not isinstance(self.remainingStock, int):
            raise _common.IncorrectStockTypeSpecified("expected physicalStock and remainingStock to be type int",
                                                      hint="is this StockConfig using the correct config type?")
        if not isinstance(by, int):
            raise TypeError("expected type int for by")
        if by < 0 and (self.physicalStock + by) < 0 or (self.physicalStock + by) < self.remainingStock:
            raise _common.ExceedsModelLimits("physicalStock must be larger or equal to remainingStock and cannot be smaller than 0")
        self.physicalStock += by
        if autosave: self.save()
        return self.physicalStock


    def qtyAvailable(self: Self) -> int | bool:
        """
        Check stock quantity available
        :return: `True` for infinite, `False` for not available, otherwise a numeric quantity
        """
        if not self.available:
            return False
        if self.reference is not None:
            return self.reference.qtyAvailable()
        if self.infinite:
            return True
        elif isinstance(self.physicalStock, int) and isinstance(self.remainingStock, int):
            if self.remainingStock > 0:
                return self.remainingStock
        else:
            raise _common.NoStockTypeSpecified("expected at least one stock configuration type to be specified",
                                               hint="did you include at least one of these - reference, infinite, (physicalStock and remainingStock) - in the StockConfig? Are both physicalStock and remainingStock type int?")
        return False


    def qtyOriginal(self: Self) -> int | bool:
        """
        Check stock quantity was available before reservations (i.e., physicalStock/infinite)
        :return: `True` for infinite, `False` for None, otherwise a numeric quantity
        """
        if not self.available:
            return False
        if self.reference is not None:
            return self.reference.qtyOriginal()
        if self.infinite:
            return True
        elif isinstance(self.physicalStock, int) and isinstance(self.remainingStock, int):
            if self.physicalStock <= 0:
                return self.physicalStock
        else:
            raise _common.NoStockTypeSpecified("expected at least one stock configuration type to be specified",
                                               hint="did you include at least one of these - reference, infinite, (physicalStock and remainingStock) - in the StockConfig? Are both physicalStock and remainingStock type int?")
        return False


class TimeBracket(models.Model):
    """
    Time brackets where a stock configuration applies
    """

    class BracketType(models.IntegerChoices):
        DATETIME: tuple[int, str] = 1, "Datetime"
        WEEKDAY: tuple[int, str] = 2, "Weekday"
        DEFAULT: tuple[int, str] = 0, "Default"

    class Weekday(models.IntegerChoices):
        MONDAY:     tuple[int, str] = 0, "Monday"
        TUESDAY:    tuple[int, str] = 1, "Tuesday"
        WEDNESDAY:  tuple[int, str] = 2, "Wednesday"
        THURSDAY:   tuple[int, str] = 3, "Thursday"
        FRIDAY:     tuple[int, str] = 4, "Friday"
        SATURDAY:   tuple[int, str] = 5, "Saturday"
        SUNDAY:     tuple[int, str] = 6, "Sunday"


    id = models.CharField(max_length=44, primary_key=True, null=False, blank=False, unique=True,
                          help_text="Unique Time Bracket ID, same across databases")  # BRACKET-UUID4 (len 44)
    linkedProduct = models.ForeignKey(Product, on_delete=models.CASCADE, null=False, blank=False,
                                      help_text="Linked Product which Bracket Applies To")
    linkedStockConfig = models.ForeignKey(StockConfig, on_delete=models.PROTECT, null=False, blank=False,
                                          help_text="Linked Stock Configuration which applies to time bracket",)
    bracketType = models.PositiveSmallIntegerField(choices=BracketType.choices, null=False, blank=False,
                                                   help_text="Format type for Bracket")
    priority = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Priority for Bracket")

    # ===========================================================
    startDatetime = models.DateTimeField(null=True, blank=True,
                                         help_text="When bracketType is DATETIME, this is the start datetime for the bracket.")
    endDatetime = models.DateTimeField(null=True, blank=True,
                                       help_text="When bracketType is DATETIME, this is the end datetime for the bracket.")

    applicableWeekdays = IntegerSet(null=True, blank=True,
                              help_text="When bracketType is WEEKDAY, this is a set of weekdays which the bracket applies for.")
    # ===========================================================


    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")


    class Meta:
        db_table_comment = "Time Bracket for Stock Configurations"
        permissions = [
            ("view_any_bracket", "Can view all brackets"),
            ("change_any_bracket", "Can change any time bracket regardless of its vendor"),
            ("delete_any_bracket", "Can delete any time bracket regardless of its vendor"),
            ("add_any_bracket", "Can add time brackets and assign it to any vendor")
        ]
        indexes = [models.Index(fields=["id", "linkedProduct"], name="CanDB_TimeBracket_Index")]
        verbose_name = "Time Bracket"
        verbose_name_plural = "Time Brackets"
        constraints = [
            models.CheckConstraint(check=models.Q(id__startswith="BRACKET-"), name="CanDB_Bracket_ID_Prefix",
                                   violation_error_code="TIMEBRACKET-ID-1",
                                   violation_error_message="Time Bracket ID must start with 'BRACKET-'"),
            models.CheckConstraint(check=models.Q(id__len=44), name="CanDB_Bracket_ID_Len",
                                   violation_error_code="TIMEBRACKET-ID-2",
                                   violation_error_message="Time Bracket ID must be 44 characters long"),
        ]


    @classmethod
    def create(cls: Union[Self, Callable], linkedProduct: Product, linkedStockConfig: StockConfig, bracketType: BracketType,
               *_, priority: int = None, startDatetime: datetime = None, endDatetime: datetime = None,
               applicableWeekdays: set[int] = None, forceID: str = None, enableWarnings: bool = True,
               autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """
        Create new timebracket.

        :param linkedProduct: linked product
        :param linkedStockConfig: linked stock configuration
        :param bracketType: type for bracket. Takes `BracketType`.
        :param priority: priority from `0` to `32767`. When None, always prioritised after any numbered priority.
        :param startDatetime: when `bracketType == BracketType.DATETIME`, specify start datetime for bracket
        :param endDatetime: when `bracketType == BracketType.DATETIME`, specify end datetime for bracket
        :param applicableWeekdays: when `bracketType == BracketType.WEEKDAY`, specify set of weekdays bracket applies to,
            where Monday == `0`, Tuesday == `1`, ..., Sunday == `6`
        :param forceID: force ID for timebracket
        :param enableWarnings: enable warnings in case of unstable or bad arguments
        :param autosave: autosave timebracket upon creation
        :return: created timebracket
        """
        if _:
            raise TypeError("additional positional arguments provided when not accepted")
        # Check forceID
        if forceID is not None:
            if not isinstance(forceID, str):
                raise TypeError("bad type for forceID")
            if not forceID.startswith("BRACKET-"):
                raise ValueError("forceID must start with 'BRACKET-'")
            if cls.objects.filter(id=forceID).exists():
                raise ValueError("forced ID already exists")
            if len(forceID) != 44:
                raise ValueError("forceID must be 44 characters long")
        if priority is not None:
            if not isinstance(priority, int):
                raise TypeError("expected type int for priority")
            if not 0 <= priority <= 32767:
                raise _common.ExceedsModelLimits("priority exceeds the value limits for PositiveSmallIntegerField",
                                                 hint="priority needs to be within range of 0 to 32767")
            if enableWarnings and cls.objects.filter(linkedProduct=linkedProduct, priority=priority).exists():
                warnings.warn("Another TimeBracket with the same linkedProduct and the same priority level already exists. "
                              "This should never happen, even when using the same linkedStockConfig and with non-overlapping timestamps "
                              "as it could result in unexpected behaviour.", Warning)

        additionalKwargs: dict[str: datetime | set[int]] = dict()

        match bracketType:
            case cls.BracketType.DATETIME:
                if startDatetime is None or endDatetime is None:
                    raise TypeError("startDatetime and endDatetime must be specified when bracketType is DATETIME")
                if not isinstance(startDatetime, datetime) or not isinstance(endDatetime, datetime):
                    raise TypeError("expected type datetime for startDatetime and endDatetime")
                if startDatetime > endDatetime:
                    raise ValueError("startDatetime must be before or equal to endDatetime, not after")
                additionalKwargs["startDatetime"] = startDatetime
                additionalKwargs["endDatetime"] = endDatetime
            case cls.BracketType.WEEKDAY:
                if not not (applicableWeekdays - {0, 1, 2, 3, 4, 5, 6}):
                    raise ValueError("applicableWeekdays only accepts values in range of 0-6, inclusive")
                additionalKwargs["applicableWeekdays"] = applicableWeekdays
            case cls.BracketType.DEFAULT:
                if cls.objects.filter(linkedProduct=linkedProduct, bracketType=cls.BracketType.DEFAULT).exists():
                    raise _common.MultipleDefaultBrackets("brackets linked to given product can only have one default bracket",
                                                          hint="is there a bracket with linkedProduct that is already using DEFAULT bracketType?")
                if enableWarnings and priority == 0:
                    warnings.warn("TimeBracket with bracketType DEFAULT should never be first priority bracket (it should be a fallback). "
                                  "It is recommended to use None instead of 0, as 0 forces the TimeBracket to always take first priority.",
                                  Warning)
            case _:
                raise ValueError(f"bad value for bracketType: '{bracketType}'")

        bracket = cls(
            id=f"BRACKET-{uuid.uuid4()}" if forceID is None else forceID,
            linkedProduct=linkedProduct,
            linkedStockConfig=linkedStockConfig,
            bracketType=bracketType,
            priority=priority,
            **additionalKwargs
        )
        if autosave: bracket.save()

        return bracket

    @classmethod
    def applicableBracketsForProduct(cls: Self, product: Product, overrideTimestamp: datetime = None) -> tuple[Self]:
        """
        Returns time bracket with foreign-key reference to `product`, where `linkedStockConfig.available == True` and
         within datetime range or is default bracket. Ordered by priority, ascending.
        :param product: Product to find brackets of
        :param overrideTimestamp: By default, `timestamp` is `datetime.datetime.now()`.
            Override by specifying datetime as this argument
        :return: Tuple of applicable Timebrackets
        """
        if overrideTimestamp:
            if not isinstance(overrideTimestamp, datetime):
                raise TypeError(f"expected overrideTimestamp to be type datetime, not {overrideTimestamp.__class__}")
            tmstmp: datetime = overrideTimestamp
        else:
            tmstmp: datetime = datetime.now(tz=TZ_INFO)
        brackets = cls.objects.filter(linkedProduct=product, linkedStockConfig__available=True).order_by("priority")
        applicable: list[Self] = list()
        for brkt in brackets:
            if brkt._checkIsApplicableAtTime(tmstmp):
                applicable.append(brkt)
            # match brkt.bracketType:
            #     case cls.BracketType.DATETIME:
            #         if brkt.startDatetime <= tmstmp <= brkt.endDatetime:
            #             return True
            #     case cls.BracketType.WEEKDAY:
            #         if tmstmp.weekday() in brkt.applicableWeekdays:
            #             return True
            #     case cls.BracketType.DEFAULT:
            #         return True
            #     case _:  # Theoretically unreachable due to Django model-level validation (choices)
            #         raise ValueError(f"bad value for bracketType: '{brkt.bracketType}'")

        return tuple(applicable)


    def modifyWeekday(self: Self, add: set[int] = None, subtract: set[int] = None, autosave: bool = True) -> set[int]:
        """
        Modify applicable weekdays for bracket.

        :param add: set of weekdays to add
        :param subtract: set of weekdays to subtract
        :param autosave: autosave bracket after modification
        :return: modified set of new applicable weekdays
        """
        if self.bracketType != self.BracketType.WEEKDAY or not isinstance(self.applicableWeekdays, set):
            raise _common.IncorrectBracketType("modifyWeekday can only be used for WEEKDAY bracketType")
        if add is not None:
            if not isinstance(add, set):
                raise TypeError("expected type set for add")
            if not not (add - {0, 1, 2, 3, 4, 5, 6}):
                raise ValueError("add only accepts values in range of 0-6, inclusive")
            self.applicableWeekdays |= add
        if subtract is not None:
            if not isinstance(subtract, set):
                raise TypeError("expected type set for subtract")
            if not not (subtract - {0, 1, 2, 3, 4, 5, 6}):
                raise ValueError("subtract only accepts values in range of 0-6, inclusive")
            self.applicableWeekdays -= subtract
        if autosave: self.save()
        return self.applicableWeekdays


    def _checkIsApplicableAtTime(self: Self, timestamp: datetime = None) -> bool:
        """
        Check if bracket is applicable at given time.

        :param timestamp: timestamp to check. Defaults to `datetime.now()`
        :return: True if applicable, False otherwise
        """
        timestamp = timestamp or datetime.now(tz=TZ_INFO)
        match self.bracketType:
            case self.__class__.BracketType.DATETIME:
                if self.startDatetime <= timestamp <= self.endDatetime:
                    return True
            case self.__class__.BracketType.WEEKDAY:
                if timestamp.weekday() in self.applicableWeekdays:
                    return True
            case self.__class__.BracketType.DEFAULT:
                return True
            case _:  # Theoretically unreachable due to Django model-level validation (choices)
                raise ValueError(f"bad value for bracketType: '{self.bracketType}'")
        return False





class OrderLine(models.Model):
    """
    Interchange layer between Order and Product
    """
    id = models.CharField(primary_key=True, help_text="Unique OrderLine ID, same across databases", null=False, blank=False, unique=True, max_length=46)  # ORDERLINE-UUID4 (len 46)
    linkedOrder = models.ForeignKey(Order, on_delete=models.CASCADE, help_text="Order ID", default=-1, null=False, blank=False)
    linkedProduct = models.ForeignKey(Product, on_delete=models.CASCADE, help_text="Product ID", default=-1, null=False, blank=False)
    quantity = models.PositiveIntegerField(help_text="Quantity", null=False, blank=False, default=1)
    quantityReserved = models.PositiveIntegerField(help_text="Quantity Reserved", null=False, blank=False, default=0)
    persistentCost = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Persistent Cost", null=True, blank=False)  # When None, use linkedProduct.price. Means transaction has not been calculated yet; the customer is still shopping. Price of EACH product object.
    itemCost = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Total Cost", null=True, blank=False, default=0)  # Cost of entire orderline (i.e., quantity * persistentCost, but overridden by forcePrice). When None, indicates a persistent cost has not been calculated yet. Separate from forcePrice (often still calculated, even if forcePrice set)
    # When using forcePrice, the persistentCost should still be set in case force price is retracted
    forcePrice = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Force Price of Entire OrderLine", null=True, blank=False, default=None)  # Same as persistent cost, however, set when the price is overridden by an admin. Ignores quantity (i.e., the total cost of the orderline, not of each product object). If None, use persistentCost.
    costPaid = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Cost Paid", null=False, blank=False, default=0)  # Total amount paid by the user for this orderline
    status = models.CharField(max_length=cfg.OrderLine.MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES, choices=ORDERLINE_STATUS_AS_DICT, default=cfg.OrderLine.DEFAULT_STATUS, help_text="Order Status", null=True, blank=False)
    notes = models.TextField(max_length=cfg.OrderLine.MAXIMUM_NOTES_LENGTH, help_text="Order Line Notes", null=True, blank=False, default=None)
    stockContributions = models.JSONField(help_text="ID of Stock Configurations used in linked Product for availability", null=True, blank=False, default=None)
    """
    Uses format:
    ```python
    {
        "id": int,  # ID of the availability configuration used in the linked product (refID), and quantity reserved from refID (in AvailabilityIndicator format).
    }
    """
    # Similar to the ID system used in stock configs in Product model, None means use model stock, -1 means not set
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")


    class Meta:
        ordering = ['id',]
        db_table_comment = "Order Lines"
        permissions = [
            ("view_any_orderline", "Can view any orderline regardless of its owner"),
            ("change_any_orderline", "Can change any orderlines regardless of its owner"),
            ("change_any_orderline_but_forceprice", "Can change any orderlines regardless of its owner, but cannot force a price"),
            ("delete_any_orderline", "Can delete any orderlines regardless of its owner"),
            ("add_any_orderline", "Can add orderlines regardless of its owner")
        ]
        indexes = [models.Index(fields=["id", "linkedOrder"], name="CanDB_OrderLine_ID_Index")]
        verbose_name = "OrderLine"
        verbose_name_plural = "OrderLines"
        constraints = [
            models.UniqueConstraint(fields=["id",], name="CanDB_OrderLines_ID_User_Unique"),
            models.CheckConstraint(check=models.Q(id__len=46),
                                   name="CanDB_OrderLine_ID_Len",
                                   violation_error_code="ORDERLINE-ID-1",
                                   violation_error_message="OrderLine ID must be 46 characters long"),
            # Check quantity reserved is not higher than quantity
            models.CheckConstraint(check=models.Q(quantityReserved__lte=models.F("quantity")),
                                   name="CanDB_OrderLine_Quantity_Reserve",
                                   violation_error_code="ORDERLINE-QUANTITY-1",
                                   violation_error_message="Reserved quantity must be smaller or equal to quantity"),
            # Check persistent cost is not negative
            models.CheckConstraint(check=models.Q(persistentCost__gte=0),
                                   name="CanDB_OrderLine_PersistentCost_NonNegative",
                                   violation_error_code="ORDERLINE-PERSISTENTCOST-1",
                                   violation_error_message="Persistent cost must not be negative"),
            # Check item cost is not negative
            models.CheckConstraint(check=models.Q(itemCost__gte=0),
                                   name="CanDB_OrderLine_ItemCost_NonNegative",
                                   violation_error_code="ORDERLINE-ITEMCOST-1",
                                   violation_error_message="Item cost must not be negative"),
            # Check force price is not negative
            models.CheckConstraint(check=models.Q(forcePrice__gte=0),
                                   name="CanDB_OrderLine_ForcePrice_NonNegative",
                                   violation_error_code="ORDERLINE-FORCEPRICE-1",
                                   violation_error_message="Forced price must not be negative"),
            # Check cost paid is not negative
            models.CheckConstraint(check=models.Q(costPaid__gte=0),
                                   name="CanDB_OrderLine_CostPaid_NonNegative",
                                   violation_error_code="ORDERLINE-COSTPAID-1",
                                   violation_error_message="Cost paid must not be negative"),
        ]


    @classmethod
    def create(cls: Union[Self, Callable], linkedOrder: Order, linkedProduct: Product, quantity: int, persistentCost: float = None,
               itemCost: float = None, forcePrice: float = None, status: str = cfg.OrderLine.DEFAULT_STATUS,
               notes: str = None, stockContributions: dict | None = None, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """
        Create a new order line
        Where itemCost is None, it is NOT auto-calculated
        """
        uid = f"ORDERLINE-{uuid.uuid4()}"

        if (not (isinstance(quantity, int) and (isinstance(persistentCost, (int, float)) or persistentCost is None) and
                (isinstance(itemCost, (int, float)) or persistentCost is None) and
                isinstance(forcePrice, (int, float)) or forcePrice is None)):
            raise TypeError("bad type for quantity, persistentCost, itemCost or forcePrice")
        if ((persistentCost is not None and persistentCost < 0) or (itemCost is not None and itemCost < 0) or
                (forcePrice is not None and forcePrice < 0)):
            raise ValueError("persistentCost, itemCost and forcePrice must not be negative")

        if stockContributions is not None and not isinstance(stockContributions, dict):
            raise TypeError("bad type for availabilityID")
        if not isinstance(status, str):
            raise TypeError("bad type for status")
        if notes is not None and not isinstance(notes, str):
            raise TypeError("bad type for notes")

        # Remember, itemCost is ONLY auto-calculated if persistentCost is set. This means it is NOT calculated even when forcePrice is set.
        if itemCost is None and persistentCost is not None:
            itemCost = quantity * persistentCost

        ol = cls(
            id=uid,
            linkedOrder=linkedOrder,
            linkedProduct=linkedProduct,
            quantity=quantity,
            persistentCost=persistentCost,
            itemCost=itemCost,
            forcePrice=forcePrice,
            status=status,
            notes=notes,
            stockContributions=stockContributions
        )
        if autosave: ol.save()
        return ol


    def _checkNotLocked(self: Self, raiseException: bool = True) -> NoReturn | bool:
        """
        Check if the orderline is locked.
        Raises _common.Locked if the orderline is locked.
        If raiseException is False, then returns False if the orderline is locked.

        :param raiseException: Raise an exception if the orderline is locked. Otherwise, return False.
        :return: None or raises an exception
        """
        if self.status in _common.OrderLineStatus.Locked:
            if raiseException:
                raise _common.Locked(f"orderline is locked", hint="check if the orderline is locked before performing operations",
                                     modelObj=self)
            return False
        return True


    def calculateItemCost(self: Self, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> float:
        """
        Calculates the item cost.
        Ignores forcePrice. If forcePrice is set, then the item cost will still be persistentCost * quantity.
        :return: The item cost, as a float
        """
        self._checkNotLocked()

        if isinstance(self.persistentCost, Decimal):
            self.itemCost = self.quantity * self.persistentCost
        else:
            if self.status not in cfg.OrderLine.CONFIRMED_STATUSES:
                raise ValueError("persistentCost or forcePrice must be set to a valid figure")
            self.persistentCost = self.linkedProduct.price
            return self.calculateItemCost(autosave=autosave)
        if autosave: self.save()
        return float(self.itemCost)

    def getPracticalItemCost(self: Self) -> float | NoReturn:
        """
        Get the practical item cost. If order is cancelled, already delivered or has been returned, then return 0.
        This is to ensure that the customer does not pay for an order that has been cancelled, delivered or returned.
        This is particularly useful when an order has been partially fulfilled (e.g., some items have been delivered/returned/cancelled, some have not).

        The practical item cost is the amount the customer has to actually pay for the orderline.
        This would in turn, return an override price if set, or the item cost if set, or the product price if set.

        :return: The practical item cost, as a float. Raises an exception if the item cost is required yet not set.
        """

        if self.status in cfg.OrderLine.NON_PAYABLE_STATUSES:
            return 0
        return self.getItemCost()


    def getItemCost(self: Self) -> float:
        """
        Get the item cost. Does not calculate the item cost if it is not set.
        :return: The item cost, as a float
        """
        if self.forcePrice is not None:
            return float(self.forcePrice)
        if self.itemCost is not None:
            return float(self.itemCost)
        raise _common.CostNotCalculated("item cost not yet calculated", modelObj=self,
                                        hint="calculate the item cost using self.calculateItemCost first")


    def _cancel(self: Self, raiseExcPasson: bool, autosavePasson: bool) -> NoReturn | None | bool:
        """
        Internal function to cancel the orderline.
        DOES NOT COMMIT ROLLBACKS IF AN EXCEPTION IS RAISED. THIS IS THE CALLER'S RESPONSIBILITY.

        :return: None. Raises an exception if the operation fails if raiseExcPasson is True. Otherwise, returns False if the operation fails.
        """
        self.status = _common.OrderLineStatus.Cancelled
        # Then, release the reserved stock.
        if self.availabilityID == -1:
            if self.quantityReserved != 0:  # If availabilityID not set but there is quantity reserved (should NEVER happen)
                raise _common.AvailabilityReferenceNotSet("availability reference not set", modelObj=self, hint="is self.availabilityID set? Has the stock been reserved properly?")
        elif not self.linkedProduct.modifyReservedStock(self.availabilityID, -self.quantityReserved, raiseException=raiseExcPasson,
                                                        autostartTransaction=False, autosave=autosavePasson):
            return False
        # As the order is still cancellable at this point, the Profile has not been charged yet. However, to be safe, the Profile should be refunded the amount indicated by self.costPaid
        if self.costPaid != 0:
            self.linkedOrder.user.addBalance(self.costPaid, autosave=autosavePasson)
            # TODO: recalculate self.linkedOrder.totalPaid
            self.costPaid = 0
        self.quantityReserved = 0
        if autosavePasson: self.save()
        if not self.linkedOrder.calculateTotalCost(raiseException=raiseExcPasson, autosave=autosavePasson):
            return False
        return True


    def cancel(self: Self, autostartTransaction: bool = True, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> NoReturn | bool:
        """
        Cancels the orderline

        An exception MUST be raised to exit an atomic transaction in the case of a bad operation.
        IF THE EXCEPTION IS CAUGHT, DO NOT CALL orderline.save UNDER ANY CIRCUMSTANCE


        :param autostartTransaction: Start a transaction for the operation. If False, no inner atomic transaction is started. HIGHLY RECOMMENDED TO KEEP THIS TRUE.
                If this is False, then the caller is responsible for rolling back a transaction if an exception is raised.
        :param autosave: Save the orderline after the operation.
        :return: True if the orderline was successfully cancelled, False otherwise.
        """
        self._checkNotLocked(raiseException=True)
        if self.status not in cfg.OrderLine.CANCELLABLE_STATUSES:
            raise _common.StatusNotCancellable(f"orderline is not cancellable", modelObj=self,
                                               hint="check if the orderline is cancellable before performing operations")
        if not autostartTransaction:
            _common.checkAtomicForDangerousOperations()  # Check if atomic operations are enabled. Dangerous operations are not allowed outside atomic operations.
        if autostartTransaction:
            with transaction.atomic():
                self._cancel(raiseExcPasson=True, autosavePasson=autosave)
                if autosave: self.save()
        else:
            self._cancel(raiseExcPasson=True, autosavePasson=autosave)
            if autosave:
                self.save()
        return True



    def _reserveStock(self: Self, forceAll: bool = False, atLeast: int = None, atMost: int = None,
                      exact: int = None, overrideAttemptUntilStockFound: bool = None,
                      overrideFindMaximumStockAvailable: bool = None, autosavePasson: bool = cfg.DEFAULT_AUTOSAVE_MODE,
                      ) -> int | NoReturn:
        """
        TODO: Implement new multi-timestamp reservation
        Internal function to reserve stock from the linked product. Raises an exception if the operation fails.
        Assumes an atomic transaction has been checked for, the orderline is not locked or cancelled and the argument have been validated.
        By design, this function will try to reserve as much stock as possible, up to the maximum available stock (if given).
        For example, if given a minimum of 24 and a maximum 32, and only 30 stock is available, it will reserve 30 stock, NOT 24.

        :param forceAll: force the full amount to be reserved, otherwise raise an exception if not enough stock is available. If False, it will reserve as much as possible.
        :param atLeast: the minimum amount of stock that must be reserved.
            If not enough stock is available, it will raise an exception. forceAll must be False regardless.
        :param atMost: the maximum amount of stock that can be reserved.
            Defaults to `orderline.quantity`. Must be larger than (not equal to) `atLeast` (if specified). Automatically assumes `findMaximumStockAvailable` is `True`.
        :param exact: the exact amount of stock to be reserved. Cannot be used with `atLeast` or `atMost`.
        :param overrideAttemptUntilStockFound: override the `attemptUntilStockFound` parameter in `checkProductStock`. If `None`, use the default (`True`).
        :param overrideFindMaximumStockAvailable: override the `findMaximumStockAvailable` parameter in `checkProductStock`. If `None`, use the default (`True`).
        :param autosavePasson: pass-on for autosaving operations
        :return: the amount of stock reserved (NOT orderline.quantityReserved, rather the actual quantity reserved by the function call).
                If the operation fails, it will raise an exception.
        """
        minQty = None
        _actualExact = None  # Final value to reserve
        if forceAll:
            minQty = self.quantity
            _actualExact = minQty  # Anything to avoid race conditions. :)
        elif atLeast is not None:
            minQty = atLeast
        elif exact is not None:
            minQty = exact
            _actualExact = exact
        if minQty is None:
            minQty = 0  # Means that forceAll, atLeast and exact are not set. Therefore, minQty is 0.
        elif minQty < 0:
            raise ValueError("atLeast must be non-negative")
        available, qty, contributions = self.linkedProduct.checkProductStock(
            quantityRequired=minQty,
            attemptUntilStockFound=overrideAttemptUntilStockFound if overrideAttemptUntilStockFound is not None else True,
            findMaximum=overrideFindMaximumStockAvailable if overrideFindMaximumStockAvailable is not None else True
        )
        if not available:
            raise _common.InsufficientStock(f"insufficient stock to satisfy minimum quantity requirements of {self.__repr__()} (with minimum quantity requirement of {minQty})")
        if _actualExact is None:
            # If _actualExact is not set, then either atMost, atLeast or both are set.
            # If atMost is set, simply reserve atMost if qty >= atMost, or otherwise, reserve qty (remember, qty >= minQty as stock was checked by self.linkedProduct.checkProductStock).
            # If only atLeast is set, then reserve qty.
            # TODO: fix
            if atMost is not None:  # Assumes atMost <= self.quantity, should've been checked by the caller
                if _common.qtyGoE(qty, atMost):
                    _actualExact = atMost
                else:
                    _actualExact = qty
            else:
                # First, check that qty <= self.quantity. This would NOT be checked by the caller, as the caller is not aware of the return of self.linkedProduct.checkProductStock.
                if qty > self.quantity:
                    _actualExact = self.quantity
                else: _actualExact = qty

        # Now perform actual reserve operation. Here comes the fun part :). Prepare to get complaints from the merchants about exceeding stock limits.
        # If you do, it's probably because of the code below in this function. Again, :)
        remaining = _actualExact
        for refID, qty in contributions.items():
            if not self.linkedProduct.modifyReservedStock(
                    usingRefID=refID,
                    by=_actualExact,
                    raiseException=True,  # Always raise exceptions in a critical function under an atomic block
                    autostartTransaction=False,  # Remember, a transaction should have already been started by the caller.
                    autosave=autosavePasson
            ):
                # This should never be reached, as the function should raise an exception if the operation fails. But for safety reasons, it is needed.
                raise RuntimeError(f"critical error in stock reservation; False returned but no exception raised (while reserving stock for {self.__repr__()})? This should NEVER occur")
        self.quantityReserved += _actualExact
        if refID in self.stockContributions:
            self.stockContributions[refID] = _actualExact
        else:
            self.stockContributions[refID] = _actualExact
        if autosavePasson: self.save()
        return _actualExact

    # noinspection PySimplifyBooleanCheck
    def reserveStockFromProduct(self: Self, *_, forceAll: bool = False, atLeast: int = None, atMost: int = None,
                                exact: int = None, overrideAttemptUntilStockFound: bool = None, overrideFindMaximumStockAvailable: bool = None,
                                autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE, autostartTransaction: bool = True) -> int | NoReturn:
        """
        Attempts to reserve of linked product. If it fails, it will raise an exception.

        The default functionality of the function (when no arguments are passed) is to reserve the maximum possible stock available, up to at most orderline.quantity.

        `atLeast`, `atMost` and `exact` are to determine a numeric quantity to reserve.
        If the conditions set out by the three arguments cannot be met, an exception (_common.InsufficientStock) will be raised.
        These arguments can NOT be used when forceAll is True.

        :param forceAll: force the full amount to be reserved, otherwise raise an exception if not enough stock is available. If False, it will reserve as much as possible.
        :param autosave: save the order after reserving stock
        :param autostartTransaction: start a transaction if one is not already started
        :param atLeast: the minimum amount of stock to be reserved.
        :param atMost: the maximum amount of stock to be reserved. Defaults to orderline.quantity. Must be larger than (not equal to) atLeast.
        :param exact: the exact amount of stock to be reserved. Cannot be used with atLeast or atMost.
        :param overrideAttemptUntilStockFound: override the attemptUntilStockFound parameter in checkProductStock. If None, use the default.
        :param overrideFindMaximumStockAvailable: override the findMaximumStockAvailable parameter in checkProductStock. If None, use the default.

        :return: the amount of stock reserved. If the operation fails, it will raise an exception.
        """
        if _: raise TypeError("reserveStockFromProduct does not take any positional arguments")
        del _
        self._checkNotLocked(raiseException=True)
        if not autostartTransaction:
            _common.checkAtomicForDangerousOperations()  # Check if the operation is atomic
        if (atLeast is not None or atMost is not None or exact is not None) and forceAll:
            raise ValueError("atLeast, atMost and exact cannot be used when forceAll is True")
        if atLeast is not None and atLeast > self.quantity:
            raise ValueError("atLeast must be less thanFalse or equal to the orderline quantity")
        if atMost is not None:
            if atLeast is not None and atMost <= atLeast:
                raise ValueError("atMost must be larger than atLeast")
            if overrideFindMaximumStockAvailable is False:  # Please use 'overrideFindMaximumStockAvailable == False' instead of 'not overrideAttemptUntilStockFound' as while the first only checks for False, the second checks for False and None.
                warnings.warn("atMost is set, but overrideFindMaximumStockAvailable is False. This will break the functionality. It is highly recommended to set overrideFindMaximumStockAvailable to True, or None (default) so all stock configurations are queried.", Warning)
        if overrideAttemptUntilStockFound is False and (atLeast is not None or atMost is not None):  # Please keep '== False'. Same comment as above.
            warnings.warn("atMost and/or atLeast is set, but overrideAttemptUntilStockFound is False. This will break the functionality. It is highly recommended to set overrideAttemptUntilStockFound to True, or None (default) so all stock configurations are queried.", Warning)
        if (atLeast is not None and atMost is not None) and exact is not None:
            raise ValueError("atLeast, atMost and exact cannot be used together")
        if not autostartTransaction:
            _common.checkAtomicForDangerousOperations()
        if autostartTransaction:
            with transaction.atomic():
                return self._reserveStock(
                    forceAll=forceAll,
                    atLeast=atLeast,
                    atMost=atMost,
                    exact=exact,
                    overrideAttemptUntilStockFound=overrideAttemptUntilStockFound,
                    overrideFindMaximumStockAvailable=overrideFindMaximumStockAvailable,
                    autosavePasson=autosave
                )
        return self._reserveStock(forceAll=forceAll, atLeast=atLeast, atMost=atMost, exact=exact,
                                  overrideAttemptUntilStockFound=overrideAttemptUntilStockFound,
                                  overrideFindMaximumStockAvailable=overrideFindMaximumStockAvailable,
                                  autosavePasson=autosave)


    def _paymentManager(self: Self, autosavePasson: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> None | NoReturn:
        """
        Internal function to manage the payment for OrderLine.
        Assumes the orderline is not locked.
        Raises exception if any operation fails

        :param autosavePasson: pass-on for autosaving operations
        :return: None. Raises an exception if the operation fails.
        """
        due = self.getPracticalItemCost()
        if due == 0:
            return
        self.linkedOrder.user.subtractBalance(due, autosave=autosavePasson, raiseException=True)


    def _confirmOrderLn(self: Self, confirmedStatus: _common.OrderLineStatus, allowUnpaid: bool,
                        unpaidConfirmedStatus: _common.OrderLineStatus,
                        autosavePasson: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> None | NoReturn:
        """
        Internal function to confirm the orderline. Raises an exception if the operation fails.
        Assumes the orderline is not locked and is confirmable. Also assumes an atomic transaction has been started.

        :param autosavePasson: pass-on for autosaving operations
        :param confirmedStatus: Confirmed Status. If None, use the default.status
        :param allowUnpaid: the configuration to allow/deny unpaid orderlines. If None, use the default.
        :param unpaidConfirmedStatus: Unpaid confirmed status. If None, use the default.
        :return: None. Raises an exception if the operation fails.
        """
        if self.quantity != self.quantityReserved:
            raise _common.InsufficientStock("insufficient stock reserved",
                                            hint="reserve full quantity before confirming order", modelObj=self)
        try:
            self._paymentManager(autosavePasson=autosavePasson)
        except _common.InsufficientFunds as e:
            if not allowUnpaid:
                raise e
            self.status = unpaidConfirmedStatus
            return
        self.status = confirmedStatus





    def doConfirm(self: Self, *_, autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE, autostartTransaction: bool = True,
                  overrideConfirmedStatus: _common.OrderLineStatus = None, overrideAllowUnapid: bool = None,
                  overrideUnpaidConfirmedStatus: _common.OrderLineStatus = None
                  ) -> bool | NoReturn:
        """
        Sets the orderline status to the specified status. Raises an exception if the operation fails.

        :param autosave: Save the orderline after the operation.
        :param autostartTransaction: Start a transaction for the operation. If False, no inner atomic transaction is started. HIGHLY RECOMMENDED TO KEEP THIS TRUE.
        :param overrideConfirmedStatus: Override the confirmed status. If None, use the default.status
        :param overrideAllowUnapid: Override the configuration to allow/deny unpaid orderlines. If None, use the default.
        :param overrideUnpaidConfirmedStatus: Override the unpaid confirmed status. If None, use the default.
        :return: True if the operation was successful, False otherwise.
        """
        if _: raise TypeError("confirmOrder does not take any positional arguments")
        del _
        self._checkNotLocked(raiseException=True)
        if not autostartTransaction:
            _common.checkAtomicForDangerousOperations()  # Check if the operation is already atomic
        if self.status not in cfg.OrderLine.CONFIRMABLE_STATUSES:
            raise _common.StatusNotConfirmable("orderline is not confirmable", modelObj=self,
                                               hint="check if the orderline status is in candb.config.OrderLine.CONFIRMABLE_STATUSES")
        if overrideConfirmedStatus is None:
            overrideConfirmedStatus = cfg.OrderLine.DEFAULT_CONFIRMED_STATUS
        if overrideAllowUnapid is None:
            overrideAllowUnapid = cfg.OrderLine.ALLOW_UNPAID_CONFIRMED
        if overrideUnpaidConfirmedStatus is None:
            overrideUnpaidConfirmedStatus = cfg.OrderLine.DEFAULT_UNPAID_CONFIRMED_STATUS
            # Bug check: when configuration is not set because it should never be used, however, it is used anyway, raise an exception
            if overrideUnpaidConfirmedStatus is None:
                raise ValueError(
                    "overrideUnpaidConfirmedStatus must be set in config or manually if cfg.OrderLine.DEFAULT_UNPAID_CONFIRMED_STATUS is None")
        if autostartTransaction:
            with transaction.atomic():
                self._confirmOrderLn(confirmedStatus=overrideConfirmedStatus, allowUnpaid=overrideAllowUnapid,
                                     unpaidConfirmedStatus=overrideUnpaidConfirmedStatus, autosavePasson=autosave)
                if autosave: self.save()
        else:
            self._confirmOrderLn(confirmedStatus=overrideConfirmedStatus, allowUnpaid=overrideAllowUnapid,
                                 unpaidConfirmedStatus=overrideUnpaidConfirmedStatus, autosavePasson=autosave)
            if autosave: self.save()
        return True






    def __str__(self):
        return f'<OrderLine {self.id} of {self.linkedProduct.name} in Order {self.linkedOrder.id}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id} of {self.linkedProduct.name} in Order {self.linkedOrder.id}>'


class Transaction(models.Model):
    """
    A transaction is opened when a user has decided to purchase a product and the linkedOrderLine is confirmed.
    From this stage, the stock needs to be reserved and managed. This is done with a transaction.
    Once an OrderLine is waiting to be fulfilled or is actively being fulfilled, this is when a transaction should be used.
    I.e., the user needs to have placed and finalised an OrderLine to reach the stage where a Transaction becomes necessary
    """
    class Status(models.TextChoices):
        CONFIRMED = 'C', "Confirmed"
        FULFILLED = 'F', "Fulfilled"
        WAITING_FOR_STOCK = 'W', "Waiting for Stock"
        CANCELLED = 'X', "Cancelled"
        WAITING_FOR_APPROVAL = 'A', "Waiting for Approval"
        RETURNED = 'R', "Returned"


    id = models.CharField(max_length=45, primary_key=True, null=False, blank=False, unique=True,
                          help_text="Unique Transaction ID, same across databases")  # TRANSACT-UUID4 (len 45)
    linkedOrderLine = models.ForeignKey(OrderLine, on_delete=models.CASCADE, help_text="OrderLine ID", default=-1, null=False, blank=False)
    linkedStockConfig = models.ForeignKey(StockConfig, on_delete=models.PROTECT, help_text="Stock Configuration ID", default=-1, null=False, blank=False)
    quantityReserved = models.PositiveIntegerField(help_text="Quantity Reserved from linkedStockConfig", null=False, blank=False, default=0)
    status = models.CharField(max_length=1, choices=Status.choices, default=Status.CONFIRMED, blank=False, null=False)
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")

    class Meta:
        ordering = ['id',]
        db_table_comment = "Records of confirmed and completed transactions"
        permissions = []  # Permissions should carry on from OrderLine model Permissions
        indexes = [models.Index(fields=["id", "linkedOrderLine"], name="CanDB_Transaction_ID_and_OrderLine_Index")]
        verbose_name = "Transaction"
        verbose_name_plural = "Transactions"
        constraints = [
            models.CheckConstraint(check=models.Q(id__len=45),
                                   name="CanDB_Transaction_ID_Len",
                                   violation_error_code="TRANSACT-ID-1",
                                   violation_error_message="Transaction ID must be 45 characters long"),
            # TODO: Write constraint to ensure quantityReserved <= linkedOrderLine.quantity
            # models.CheckConstraint(check=models.Q(quantityReserved__lte=models.F("linkedOrderLine.quantity")),
            #                        name="CanDB_OrderLine_Quantity_Reserve",
            #                        violation_error_code="ORDERLINE-QUANTITY-1",
            #                        violation_error_message="Reserved quantity must be smaller or equal to quantity")
        ]

    @classmethod
    def create(cls: Union[Self, Callable], linkedOrderLine: OrderLine, linkedStockConfig: StockConfig,
               quantityReserved: int, *_, status: Status = Status.CONFIRMED, forceID: str = None,
               autosave: bool = cfg.DEFAULT_AUTOSAVE_MODE) -> Self:
        """
        Create new Transaction.

        :param linkedOrderLine: linked order line
        :param linkedStockConfig: linked stock configuration
        :param quantityReserved: quantity reserved for the `linkedOrderLine` from the `linkedStockConfig`.
        :param status: status of the transaction. Defaults to `Status.CONFIRMED`
        :param forceID: force ID for transaction
        :param autosave: autosave transaction upon creation
        :return: created transaction
        """
        if _:
            raise TypeError("additional positional arguments provided when not accepted")
        if not isinstance(quantityReserved, int):
            raise TypeError("bad type for quantityReserved")
        if quantityReserved < 0 or quantityReserved > linkedOrderLine.quantity:
            raise ValueError("quantityReserved cannot exceed linkedOrderLine.quantity or recede 0")
        if forceID:
            if not isinstance(forceID, str):
                raise TypeError("bad type for forceID")
            if forceID.__len__() != 45 or not forceID.startswith("TRANSACT-"):
                raise ValueError("forceID must be 45 characters long and start with 'TRANSACT-'")
        else:
            forceID = f"TRANSACT-{uuid.uuid4()}"
        trnsction = cls(
            id=forceID,
            linkedOrderLine=linkedOrderLine,
            linkedStockConfig=linkedStockConfig,
            quantityReserved=quantityReserved,
            status=status
        )

        if autosave: trnsction.save()
        return trnsction


def __devEnvCreator() -> bool:
    """
    Used to create database entries for a development environment
    :return: True if successful
    """
    if not GLOBAL_SETTINGS.DEBUG:
        raise PermissionError("cannot create dev environment executable in debug mode")
    try:
        Profile.create(forceID=1, username="anony", first_name="Anony", last_name="Mous", email="anony@mous.com", password="1234", is_staff=False, is_superuser=False, image=None, requireSecurePassword=False)
    except (django.db.utils.IntegrityError, ValueError):
        print("Anony already exists; skipping")
    try:
        su = Profile.objects.create(id=0, username="superuser", is_superuser=True)
        su.set_password("1234")
        su.save()
    except (django.db.utils.IntegrityError, ValueError):
        print("Superuser already exists; skipping")
    try:
        stf = Profile.create(forceID=2, username="staff", first_name="Staff", last_name="Member", email="staff@candb.com", is_staff=True, is_superuser=False, image=None)
        stf.set_password("1234")
        stf.save()
    except (django.db.utils.IntegrityError, ValueError):
        print("Staff already exists; skipping")
    prodOrOrdFailed = False
    od, prod = None, None
    # Create a product
    try:
        # TODO: migrate availability to timebrackets and stockconfigs
        prod = Product.create(name="Test Product", price=1.00, description="Test Product", image=None, physicalStock=10, reservedStock=0, notes="Test Product", tags=["test"], autosave=True,
                              availability={
                                  1: ((datetime.now(tz=TZ_INFO), datetime.now(tz=TZ_INFO) + timedelta(days=1)), {"available": True, "physicalStock": 10, "reservedStock": 0, "infinite": False, "useModelStock": False}),
                              })
        prod = Product.create(name="Advanced Product 1", price=6.45, description="Test Product", image=None, physicalStock=13,
                              reservedStock=0, notes="Test Product", tags=["test"], autosave=True,
                              availability={
                                  1: (
                                      (datetime.now(tz=TZ_INFO), datetime.now(tz=TZ_INFO) + timedelta(days=3)),
                                      {"available": False, "physicalStock": 15, "reservedStock": 0, "infinite": False,
                                       "useModelStock": False}
                                  ),
                                  2: (
                                    (datetime.now(tz=TZ_INFO).now().date(), datetime.now(tz=TZ_INFO).date() + timedelta(days=3)),
                                    {"available": True, "infinite": True},
                                  ),
                                  3: (
                                    (datetime.now(tz=TZ_INFO).now().weekday(), datetime.now(tz=TZ_INFO).weekday()+2),
                                    {"available": True, "physicalStock": 3, "reservedStock": 3},
                                  ),
                                  4: (
                                    "default",
                                    {"available": True, "useModelStock": True},
                                  ),
                              })
    except django.db.utils.IntegrityError:
        print("Test Product already exists; skipping")
        prodOrOrdFailed = True
    # Create an order
    try:
        od = Order.create(profile=Profile.objects.get(username="anony"), notes="Test Order", overwriteTime=datetime.now(tz=TZ_INFO), autosave=True)
    except django.db.utils.IntegrityError:
        print("Test Order already exists; skipping")
        prodOrOrdFailed = True
    # Create an orderline
    try:
        if prodOrOrdFailed:
            print("Skipping OrderLine creation due to previous failure")
        else:
            OrderLine.create(linkedOrder=od, linkedProduct=prod, quantity=3, notes="Test OrderLine", autosave=True)
    except django.db.utils.IntegrityError:
        print("Test OrderLine already exists; skipping")
    return not prodOrOrdFailed
