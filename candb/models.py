from django.db import models
from django.contrib.auth.models import User
import candb.config as cfg
from candb.common import _ORDERLINESTATUSASDICT, _LOGTYPEASDICT

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.ImageField(default='default.jpg', upload_to='profile_pics', blank=True, null=True)

    def __str__(self):
        return f'<User {self.user.last_name.upper()}, {self.user.first_name}: {self.user.username} with ID {self.user.id}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} with {self.user.last_name.upper()}, {self.user.first_name}: {self.user.username}; ID {self.user.id}>'


class Order(models.Model):
    """
    The model for a user order. Linked to multiple orderLines.
    """

    id = models.CharField(primary_key=True, editable=False, help_text="Unique Order ID, same across databases", null=False, blank=False, unique=True, max_length=64)  # ORDER-UUID4 (len 42)
    orderTime = models.DateTimeField(auto_now_add=True, help_text="Order Time", null=False, blank=False)
    totalCost = models.DecimalField(max_digits=cfg.Order.MAXIMUM_COST_DIGITS, decimal_places=cfg.Order.COST_DECIMAL_DIGITS, help_text="Order Total", null=True)  # If None, means not calculated yet.
    notes = models.TextField(help_text="Order Notes", null=True, blank=False, default=None, max_length=cfg.Order.MAXIMUM_NOTES_LENGTH)
    user = models.ForeignKey(help_text="User ID", blank=False, null=False, on_delete=models.CASCADE, to=User)

    def __str__(self):
        return f'<Order {self.id} by {self.user.username} at {self.orderTime}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id} by {self.user.username} at {self.orderTime}>'


class Product(models.Model):
    """
    The model for a product
    """
    id = models.CharField(primary_key=True, help_text="Unique Product ID, same across databases", null=False, blank=False, unique=True, max_length=64)  # PRODUCT-UUID4 (len 44)
    name = models.CharField(max_length=cfg.Product.MAXIMUM_NAME_LENGTH, help_text="Product Name", null=False, blank=False)
    price = models.DecimalField(max_digits=cfg.Product.MAXIMUM_COST_DIGITS, decimal_places=cfg.Product.COST_DECIMAL_DIGITS, help_text="Product Price", null=False, blank=False)
    description = models.TextField(help_text="Product Description")
    image = models.ImageField(upload_to="product_images", help_text="Product Image", null=True)
    physicalStock = models.PositiveIntegerField(help_text="Product Physical Stock", null=True, blank=False)  # Null is allowed, as some products may be virtual and not have a stock. Alternatively, stock may be specified in availability.
    reservedStock = models.PositiveIntegerField(help_text="Product Reserved Stock", null=True, blank=False, default=0)  # Physical stock is how much stock is available, reserved stock is how much stock is already ordered
    # Available stock is equal to physicalStock - reservedStock.
    rawAvailability = models.BinaryField(help_text="Product Availability Configuration", null=True, blank=False, default=None)  # Use None for no availability: always use model stock.
    # New availability function as follows:
    """
    ```python
    stockConfig: dict[str: bool | int] = {
        "reference":        int,    # Specify if stock configuration should inherit from another stock configuration by ID. Ignores all other fields. Not required. Ignored if not type int.
        "available":        bool,   # Specify if product is available during time period. Ignores all other fields (except reference) if False. REQUIRED.
        "physicalStock":    int,    # Specify number of stock available during time period
        "reservedStock":    int,    # Specify number of stock reserved during time period
        "infinite":         bool,   # Specify if stock is infinite (ignores "stock"). E.g., something made to order may use this
        "useModelStock":    bool,   # Specify if stock is to be used from the Product model fields (physicalStock, reservedStock)
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
        id[int]:    ((from[int], until[int]),                                stockConfig)[tuple], # e.g., 0 = Monday, 1 = Tuesday, etc., 6 = Sunday
        id[int]:    ("default"[Literal],                                     stockConfig)[tuple], # Defualt option, if availability is not specified for a day this is used.
    }
    ```
    Please note timestamps are inclusive.
    The script will follow the conditions in this order: datetime, datetime.date, day[int], then finally, "default"
    Due to how api.databaseOperations.checkProductSellable is written, it is recommended to use one type of availability for one product. For example, use only datetime, or only datetime.date, or only day[int], then use "default".
    If availability is None, then the product uses stock as the only availability. If stock is None, then the product is always available.
    """
    notes = models.TextField(help_text="Product Notes", null=True, blank=False, default=None, max_length=cfg.Product.MAXIMUM_NOTES_LENGTH)
    tags = models.JSONField(help_text="Product Tags", null=True, blank=False, default=None)

    def __str__(self):
        return f'<Product {self.id}: {self.name}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id}: {self.name}>'

class OrderLine(models.Model):
    """
    Interchange layer between Order and Product
    """
    id = models.CharField(primary_key=True, help_text="Unique OrderLine ID, same across databases", null=False, blank=False, unique=True, max_length=64)  # ORDERLINE-UUID4 (len 46)
    linkedOrder = models.ForeignKey(Order, on_delete=models.CASCADE, help_text="Order ID", default=-1, null=False, blank=False)
    linkedProduct = models.ForeignKey(Product, on_delete=models.CASCADE, help_text="Product ID", default=-1, null=False, blank=False)
    quantity = models.PositiveIntegerField(help_text="Quantity", null=False, blank=False, default=1)
    quantityReserved = models.PositiveIntegerField(help_text="Quantity Reserved", null=False, blank=False, default=0)
    persistentCost = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Persistent Cost", null=False, blank=False)
    itemCost = models.DecimalField(max_digits=cfg.OrderLine.MAXIMUM_COST_DIGITS, decimal_places=cfg.OrderLine.COST_DECIMAL_DIGITS, help_text="Total Cost", null=False, blank=False, default=0)
    status = models.CharField(max_length=cfg.OrderLine.MAXIMUM_LENGTH_OF_ORDERLINE_STATUS_CHOICES, choices=_ORDERLINESTATUSASDICT, default=cfg.OrderLine.DEFAULT_STATUS, help_text="Order Status", null=True, blank=False)
    statusInformation = models.TextField(help_text="Status Information", null=True, default=None, max_length=cfg.OrderLine.MAXIMUM_STATUS_INFORMATION_LENGTH)
    notes = models.TextField(help_text="Order Line Notes", null=True, blank=False, default=None, max_length=cfg.OrderLine.MAXIMUM_NOTES_LENGTH)
    availabilityID = models.IntegerField(help_text="ID of Stock Configuration used in linked Product for availability", null=True, blank=False, default=-1)
    # Similar to the ID system used in stock configs in Product model, None means use model stock.

    def __str__(self):
        return f'<OrderLine {self.id} for {self.linkedProduct.name} in Order {self.linkedOrder.id}>'

    def __repr__(self):
        return f'<{self.__class__.__qualname__} {self.id} for {self.linkedProduct.name} in Order {self.linkedOrder.id}>'


class Logs(models.Model):
    id = models.BigAutoField(primary_key=True, help_text="Unique Log ID, same across databases", null=False, blank=False)
    logType = models.CharField(max_length=cfg.Logs.MAXIMUM_LENGTH_OF_LOGTYPE_CHOICES, help_text="Log Type", null=False, blank=False, choices=_LOGTYPEASDICT)
    logMessage = models.TextField(help_text="Log Message", null=False, blank=False, max_length=cfg.Logs.MAXIMUM_MESSAGE_LENGTH)
    logUser = models.ForeignKey(User, on_delete=models.CASCADE, help_text="User", default=-1, null=True, blank=False)
    origin = models.CharField(max_length=cfg.Logs.ORIGIN_MAXIMUM_LENGTH, help_text="Log Origin", null=True, blank=False, default=None)
    exceptionObject = models.BinaryField(help_text="Exception", null=True, blank=False, default=None)
    additionalData = models.JSONField(help_text="Additional Data", null=True, blank=False, default=None)
    logTime = models.DateTimeField(auto_now_add=True, help_text="Log Time", null=False, blank=False)
