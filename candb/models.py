from candb import *
from candb import config as cfg
from candb import common as _common
from django.contrib.auth.models import AbstractUser
from concurrency.fields import IntegerVersionField



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
               autosave: bool = True) -> Self:
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
        if phoneNCountryCode is not None and (phoneNCountryCode.__len__() > 5 or 3 > pNumber.__len__() > 15):
            raise ValueError("phoneNCountryCode must no more than 5 characters long, and pNumber must be between 3 and 15 characters long")
        if not isinstance(is_staff, bool):
            raise TypeError("bad type for is_staff")
        if not isinstance(is_superuser, bool):
            raise TypeError("bad type for is_superuser")
        if not isinstance(image, str) and image is not None:
            raise TypeError("bad type for image")
        # Force staff and superusers to use secure passwords
        if is_staff or is_superuser and not requireSecurePassword:
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
                                    "email": email, "password": password, "is_staff": is_staff,
                                    "is_superuser": is_superuser, "image": image, "phone": phone,
                                    "adminNotes": adminNotes, "balance": overrideBalance}.items()
                  if v is not None}
        if forceID is not None:
            kwargs["id"] = forceID
        pf = cls(**kwargs)
        if autosave: pf.save()
        return pf


    def _checkBalance(self, amount: float) -> bool:
        """
        Check if the user has enough balance
        """
        if amount < 0:
            raise ValueError("amount must be non-negative")
        return self.balance >= amount

    def subtractBalance(self, amount: float, autosave: bool = True, raiseWhenInsufficientFunds: bool = True) -> bool | NoReturn:
        """
        Subtract balance from the user
        """
        if not self._checkBalance(amount):
            if raiseWhenInsufficientFunds:
                raise _common.InsufficientFunds(f"insufficient funds to subtract {amount} from {self.__repr__()}")
            return False
        self.balance -= amount
        if autosave: self.save()
        return True

    def addBalance(self, amount: float, autosave: bool = True) -> NoReturn:
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
    totalCost = models.DecimalField(max_digits=cfg.Order.MAXIMUM_COST_DIGITS, decimal_places=cfg.Order.COST_DECIMAL_DIGITS, help_text="Order Total", null=True)  # If None, means not calculated yet.
    notes = models.TextField(help_text="Order Notes", null=True, blank=False, default=None, max_length=cfg.Order.MAXIMUM_NOTES_LENGTH)
    user = models.ForeignKey(help_text="User ID", blank=False, null=False, on_delete=models.CASCADE, to=Profile)
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")


    class Meta:
        ordering = ['-orderTime', 'id']
        db_table_comment = "Orders"
        permissions = [("view_all_orders", "Can view orders regardless of its owner"), ("change_any_order", "Can change any orders regardless of its owner"), ("delete_any_order", "Can delete orders regardless of its owner"), ("add_any_order", "Can add any order regardless of its owner"), ("change_any_order_but_overridecost", "Can change orders regardless of its owner, but cannot override the cost")]
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
    def create(cls: Self, profile: Profile, notes: str = None, overwriteTime: datetime = None, autosave: bool = True) -> Self:
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
    # None: unlimited stock
    # 0: no stock
    # >0: stock
    # if physicalStock is None, reservedStock MUST be None.
    physicalStock = models.PositiveIntegerField(help_text="Product Physical Stock", null=True, blank=False)  # Null is allowed, as some products may be virtual and not have a stock. Alternatively, stock may be specified in availability.
    reservedStock = models.PositiveIntegerField(help_text="Product Reserved Stock", null=True, blank=False, default=0)  # Physical stock is how much stock is available, reserved stock is how much stock is already ordered
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
               reservedStock: int | None = 0, availability: dict = None, notes: str = None, tags: list[str] | tuple[str] = None,
               autosave: bool = True) -> Self:
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
        if availability is None and physicalStock == '':
            raise ValueError("either row-level (physicalStock and reservedStock) or parameter-level (availability) must be specified")
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
            availability=availability,
            notes=notes,
            tags=tags
        )
        if autosave: prod.save()
        return prod
    
    
    def _modelStockAvailable(self) -> int | bool:
        """
        Internal function used for checking stock availability for the model stock
        :return: stock available. If False, then stock is not available. If True, then stock is infinite. Otherwise,
                    the stock available is returned.
        """
        if self.physicalStock is None:
            return True
        if self.physicalStock - self.reservedStock == 0:
            return False
        if self.physicalStock - self.reservedStock < 0:  # Should never happen. Used to catch bugs or accidents
            raise ValueError("reserved stock must be smaller or equal to physical stock")
        return self.physicalStock - self.reservedStock
    

    def _stockAvailableForStockConfig(self, _config: _common.AvailabilityConfiguration) -> _common.AvailabilityIndicator:
        """
        Internal function used for checking stock availability for a specific stock configuration
        :param _config: Stock configuration to check stock available for
        :return: stock available. If False, then stock is not available. If True, then stock is infinite. Otherwise,
                    the stock available is returned.
        """
        if not _config["available"]:
            return False
        if "reference" in _config:
            return self._stockAvailableForID(_config["reference"])
        if "useModelStock" in _config and _config["useModelStock"]:
            return self._modelStockAvailable()
        if "infinite" in _config and _config["infinite"]:
            return True
        if _config["physicalStock"] - _config["reservedStock"] == 0:
            return False
        if _config["physicalStock"] - _config["reservedStock"] < 0:  # Should never happen. Used to catch bugs or accidents
            raise ValueError("reserved stock must be smaller or equal to physical stock")
        return _config["physicalStock"] - _config["reservedStock"]


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
            raise IndexError(f"availability ID {refID} not found") from _e


    @staticmethod
    def _checkIfTimeInRange(time: datetime, timerange: _common.TimeRange) -> bool:
        """
        Check if a time is in a timerange
        :param time: Time to check
        :param timerange: Timerange to check
        :return: True if time is in timerange, False otherwise
        """
        if isinstance(timerange[0], datetime):
            return timerange[0] <= time <= timerange[1]
        if isinstance(timerange[0], date):
            return timerange[0] <= time.date() <= timerange[1]
        if isinstance(timerange[0], int):
            return timerange[0] <= time.weekday() <= timerange[1]
        raise TypeError("bad type for timerange")


    @staticmethod
    def _compareStockQuantity(quantityRequired: int, availableQuantity: _common.AvailabilityIndicator) -> bool:
        """
        Compare the quantity required with the available quantity
        :param quantityRequired: Quantity required
        :param availableQuantity: Quantity available
        :return: True if quantity required is less than or equal to available quantity, False otherwise
        """
        if availableQuantity is True:
            return True
        if availableQuantity is False:
            return False
        return quantityRequired <= availableQuantity

    def checkProductStock(self, quantityRequired: int, attemptUntilStockFound: bool = False, overrideTime: datetime = None) -> bool:
        """
        Check if the product has enough stock to sell
        """
        if overrideTime is None: overrideTime = datetime.now(tz=TZ_INFO)

        # No availability config, use model stock
        if self.availability is None:
            return self._compareStockQuantity(quantityRequired, self._modelStockAvailable())

        atLeastOneConfigApplicable = False
        # Check availability configurations
        for _id, (timerange, _config) in self.availability.items():
            # First, check if timestamp is in timerange
            if timerange != "default":
                if not self._checkIfTimeInRange(overrideTime, timerange):
                    continue
                atLeastOneConfigApplicable = True
            else: atLeastOneConfigApplicable = True
            if self._compareStockQuantity(quantityRequired, self._stockAvailableForStockConfig(_config)):
                return True
            # If not found, attempt next configuration. But if only use the first configuration in timerange, then break.
            if not attemptUntilStockFound:
                return False
        if not atLeastOneConfigApplicable:
            raise _common.NoTimerangeApplicable(f"no availability configuration applicable for {overrideTime} and {self.__repr__()}")
        return False


    def __str__(self):
        return f'<Product {self.id}: {self.name}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id}: {self.name}>'

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
    itemCost = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Total Cost", null=True, blank=False, default=0)  # Cost of entire orderline (i.e., quantity * persistentCost, but overridden by forcePrice). When None, indicates a persistent cost has not been calculated yet.
    forcePrice = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Force Price of Entire OrderLine", null=True, blank=False, default=None)  # Same as persistent cost, however, set when the price is overridden by an admin. Ignores quantity (i.e., the total cost of the orderline, not of each product object). If None, use persistentCost.
    # When using forcePrice, the persistentCost still needs to be set, just instead to forcePrice instead of linkedProduct.price.
    status = models.CharField(max_length=cfg.OrderLine.MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES, choices=ORDERLINE_STATUS_AS_DICT, default=cfg.OrderLine.DEFAULT_STATUS, help_text="Order Status", null=True, blank=False)
    notes = models.TextField(max_length=cfg.OrderLine.MAXIMUM_NOTES_LENGTH, help_text="Order Line Notes", null=True, blank=False, default=None)
    availabilityID = models.IntegerField(help_text="ID of Stock Configuration used in linked Product for availability", null=True, blank=False, default=-1)  # Min -1, Max is limit of IntegerField (2147483647; see https://docs.djangoproject.com/en/5.1/ref/models/fields/#integerfield)
    # Similar to the ID system used in stock configs in Product model, None means use model stock, -1 means not set
    _saveVersion = IntegerVersionField(help_text="Save Version for Concurrency Control")


    class Meta:
        ordering = ['id',]
        db_table_comment = "Order Lines"
        permissions = [("view_any_orderline", "Can view any orderline regardless of its owner"), ("change_any_orderline", "Can change any orderlines regardless of its owner"), ("change_any_orderline_but_forceprice", "Can change any orderlines regardless of its owner, but cannot force a price"), ("delete_any_orderline", "Can delete any orderlines regardless of its owner"), ("add_any_orderline", "Can add orderlines regardless of its owner")]
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
            # Check availabilityID is not below -1
            models.CheckConstraint(check=models.Q(availabilityID__gte=-1),
                                   name="CanDB_OrderLine_AvailabilityID_NonNegative",
                                   violation_error_code="ORDERLINE-AVAILABILITYID-1",
                                   violation_error_message="Availability ID must not be below -1"),
        ]


    @classmethod
    def create(cls: Union[Self, Callable], linkedOrder: Order, linkedProduct: Product, quantity: int, persistentCost: float = None,
               itemCost: float = None, forcePrice: float = None, status: str = cfg.OrderLine.DEFAULT_STATUS,
               notes: str = None, availabilityID: int | None = -1, autosave: bool = True) -> Self:
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

        if availabilityID is not None and not isinstance(availabilityID, int):
            raise TypeError("bad type for availabilityID")
        if availabilityID is not None:
            if 2147483647 < availabilityID < -1:
                raise ValueError("availabilityID must not be below -1, or above 2147483647")
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
            availabilityID=availabilityID
        )
        if autosave: ol.save()
        return ol

    def calculateItemCost(self, autosave: bool = True) -> float:
        """
        Calculates the item cost.
        :return: The item cost, as a float
        """
        if isinstance(self.persistentCost, Decimal):
            self.itemCost = self.quantity * self.persistentCost
        elif isinstance(self.forcePrice, Decimal):
            self.itemCost = self.forcePrice
        else:
            raise ValueError("persistentCost or forcePrice must be set to a valid figure")
        if autosave: self.save()
        return float(self.itemCost)


    def __str__(self):
        return f'<OrderLine {self.id} for {self.linkedProduct.name} in Order {self.linkedOrder.id}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id} for {self.linkedProduct.name} in Order {self.linkedOrder.id}>'


def __devEnvCreator() -> bool:
    """
    Used to create database entries for a development environment
    :return: True if successful
    """
    if not GLOBAL_SETTINGS.DEBUG:
        raise PermissionError("cannot create dev environment executable in debug mode")
    try:
        Profile.objects.create(id=1, username="anony", first_name="Anony", last_name="Mous", email="anony@mous.com", password="1234", is_staff=False, is_superuser=False, image=None, phone=None)
    except django.db.utils.IntegrityError:
        print("Anony already exists; skipping")
    try:
        Profile.objects.create(id=0, username="superuser", first_name="Super", last_name="User", email="super@user.com", password="1234", is_staff=False, is_superuser=True, image=None, phone=None)
    except django.db.utils.IntegrityError:
        print("Superuser already exists; skipping")
    try:
        Profile.objects.create(id=2, username="staff", first_name="Staff", last_name="Member", email="staff@candb.com", password="1234", is_staff=True, is_superuser=False, image=None, phone=None)
    except django.db.utils.IntegrityError:
        print("Staff already exists; skipping")
    prodOrOrdFailed = False
    od, prod = None, None
    # Create a product
    try:
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
            OrderLine.create(linkedOrder=od, linkedProduct=prod, quantity=3, notes="Test OrderLine", availabilityID=-1, autosave=True)
    except django.db.utils.IntegrityError:
        print("Test OrderLine already exists; skipping")
    return not prodOrOrdFailed
