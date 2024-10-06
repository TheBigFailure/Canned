raise RuntimeError("this module is deprecated. Anti-racing is neither complete, nor necessary (using django-concurrency instead, for optimistic locking)")

from candb import *
from candb.models import Profile, Product, Order, OrderLine
from django.db import models  # Needs to be EXPLICITLY imported after candb.models because weird Python bullsh*t


__forwardsMapExample = {
    OrderLine: (
        {
            "fieldName": "linkedOrder",
            "primaryKey": "id",
            "model": Order,
        },
        {
            "fieldName": "linkedProduct",
            "primaryKey": "id",
            "model": Product,
        }
    )
}

__backwardsMapExample = {
    Order: (
        {
            "fieldName": "orderLines",
            "primaryKey": "id",
            "model": OrderLine,
        }
    ),
    Product: (
        {
            "fieldName": "orderLines",
            "primaryKey": "id",
            "model": OrderLine,
        }
    )
}

"""
The tree is as follows:

OrderLine
|  Order
---|  Profile
|  Product

This module is designed to intelligently lock database rows to prevent race conditions from occuring.
To ensure both security and performance, the module will predetermine the relationships between models and use a forward
and backwards map to determine which rows to lock when a row is locked.
"""
del __forwardsMapExample, __backwardsMapExample


type ModelMap = dict[models.Model, tuple[dict[str, str | models.Model]]]

FORWARD_MAP: ModelMap = dict()
BACKWARD_MAP: ModelMap = dict()

def generateForwards(model: models.Model, onlyInclude: Iterable[models.Model] = None, excludeSelf: bool = True) -> tuple[dict[str, str | models.Model]]:
    """
    Generate the forwards map for a model
    :param model: The model to generate the forwards map for
    :param onlyInclude: To perform a forward lookup on fields for a model, only include the models to search for references to model in
    :param excludeSelf: Exclude the model itself from the forwards map
    :return: The forwards map
    """
    fields = model._meta.get_fields()
    forwards = []
    for field in fields:
        field: models.Field
        if isinstance(field, models.fields.related.ForeignKey):
            if (onlyInclude and field.related_model not in onlyInclude) or (excludeSelf and field.related_model == model):
                continue
            forwards.append({
                "fieldName": field.name,
                "primaryKey": field.related_model._meta.pk.name,
                "model": field.related_model,
            })
    return tuple(forwards)


def generateBackwards(model: models.Model, onlyInclude: Iterable[models.Model], excludeSelf: bool = True) -> tuple[dict[str, str | models.Model]]:
    """
    Generate the backwards map for a model
    :param model: The model to generate the backwards map for
    :param onlyInclude: Only look for references to model in these models
    :return: The backwards map
    """
    fields = model._meta.get_fields()
    backwards = []
    for field in fields:
        field: models.Field
        if isinstance(field, models.fields.reverse_related.ManyToOneRel):
            if (onlyInclude and field.related_model not in onlyInclude) or (
                    excludeSelf and field.related_model == model):
                continue
            backwards.append({
                "fieldName": field.name,
                "primaryKey": field.related_model._meta.pk.name,
                "model": field.related_model,
            })
    return tuple(backwards)

def generateMaps(models: Iterable[models.Model]) -> None:
    """
    Generate the forwards and backwards maps for a collection of models
    :param models: The models to generate the maps for
    """
    global FORWARD_MAP, BACKWARD_MAP
    for model in models:
        FORWARD_MAP[model] = generateForwards(model, onlyInclude=models)
        BACKWARD_MAP[model] = generateBackwards(model, models)


if __name__ == "__main__":
    warnings.warn("This module is not meant to be run as a script. It should ONLY be imported.", RuntimeWarning)

generateMaps([Profile, Product, Order, OrderLine])


@contextmanager
def kidnapSelfAndBestie[T: Any](model: models.Model, *args: T, **kwargs: T) -> models.QuerySet:
    """
    'Kidnap' a row from the database and its related rows
    (i.e. lock the row and its related rows.) :D (please don't call the AFP)
    :param model: root model. Must be in FORWARD_MAP AND BACKWARD_MAP.
    :param args: args to pass to model.objects.get
    :param kwargs: kwargs to pass to model.objects.get
    :return: QuerySet of what model.objects.get(*args, **kwargs) returns.
    """
    with transaction.atomic():
        modelInstance = models.objects.get(*args, **kwargs)
        yield modelInstance
        modelInstance.save()

