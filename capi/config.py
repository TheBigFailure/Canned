# <Initfile>
from capi import *
from django.contrib.auth.models import Permission

# Note: permission indicates permissions from the rest framework, Permission indicates permissions from the django auth system

class CommonAPI:
    @staticmethod
    def compilePerms(perms: list[Permission]) -> set[str]:
        return set({perm.codename for perm in perms})

    @staticmethod
    def compileImplies(imply: dict[Permission: tuple[Permission]]) -> dict[str: set[str]]:
        return dict({perm.codename: set({imp.codename for imp in implies}) for perm, implies in imply.items()})

    LOGIN_PERMISSION = permissions.IsAuthenticated
    ADMIN_PERMISSION = permissions.IsAdminUser

    OVERRIDE_WHEN_SUPERUSER: str = "__override_super__"  # allows superusers to not require permissions for a given action
    OVERRIDE_WHEN_STAFF: str = "__override_staff__"  # allows staff to not require permissions for a given action

    # Permission: Implied Permission(s)
    # SHOULD BE RARELY USED. Only should be used for rare cases where a permission is a subset of another permission.
    # Where possible, view, add, change, delete self and view, add, change, delete any should be separately added to a user's permissions

    IMPLY: dict[Permission: tuple[Permission]] = {
        Permission.objects.get(codename="change_any_order"): (
            Permission.objects.get(codename="change_any_order_but_overridecost"),),
        Permission.objects.get(codename="change_any_orderline"): (
            Permission.objects.get(codename="change_any_orderline_but_forceprice"),),
    }
    IMPLY = compileImplies(IMPLY)
    # Implied Permission: Permission(s)
    _LOOKUP_IMPLY: dict[str: list[str]] = dict()
    for perm, implies in IMPLY.items():
        for imply in implies:
            if imply not in _LOOKUP_IMPLY:
                _LOOKUP_IMPLY[imply] = list()
            _LOOKUP_IMPLY[imply].append(perm)

    _LOOKUP_IMPLY = dict({_k: set(_v) for _k, _v in _LOOKUP_IMPLY.items()})

class OrderAPI:
    REQUIRE_LOGIN = True
    VIEW_SELF_ORDER: list[Permission] = [
        Permission.objects.get(codename="view_orderline"),
        Permission.objects.get(codename="view_order"),
        Permission.objects.get(codename="view_product"),
        CommonAPI.OVERRIDE_WHEN_STAFF,
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    VIEW_ANY_ORDER: list[Permission] = [
        Permission.objects.get(codename="view_all_orderlines"),
        Permission.objects.get(codename="view_all_order"),
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    ADD_SELF_ORDER: list[Permission] = [
        Permission.objects.get(codename="add_order"),
        Permission.objects.get(codename="add_orderline"),
        Permission.objects.get(codename="view_product"),
        CommonAPI.OVERRIDE_WHEN_STAFF,
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    ADD_ANY_ORDER: list[Permission] = [
        Permission.objects.get(codename="add_any_order"),
        Permission.objects.get(codename="add_any_orderline"),
        Permission.objects.get(codename="view_product"),
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    CHANGE_SELF_ORDER: list[Permission] = [
        Permission.objects.get(codename="change_order"),
        Permission.objects.get(codename="change_orderline"),
        Permission.objects.get(codename="view_product"),
        CommonAPI.OVERRIDE_WHEN_STAFF,
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    CHANGE_ANY_ORDER: list[Permission] = [
        Permission.objects.get(codename="change_any_order_but_overridecost"),
        Permission.objects.get(codename="change_any_orderline_but_forceprice"),
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    CHANGE_ANY_ORDER_PRICE: list[Permission] = [
        Permission.objects.get(codename="change_any_order"),
        Permission.objects.get(codename="change_any_orderline"),
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    DELETE_SELF_ORDER: list[Permission] = [
        Permission.objects.get(codename="delete_order"),
        Permission.objects.get(codename="delete_orderline"),
        CommonAPI.OVERRIDE_WHEN_STAFF,
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    DELETE_ANY_ORDER: list[Permission] = [
        Permission.objects.get(codename="delete_any_order"),
        Permission.objects.get(codename="delete_any_orderline"),
        CommonAPI.OVERRIDE_WHEN_SUPERUSER
    ]
    VIEW_SELF_ORDER = CommonAPI.compilePerms(VIEW_SELF_ORDER)
    VIEW_ANY_ORDER = CommonAPI.compilePerms(VIEW_ANY_ORDER)
    ADD_SELF_ORDER = CommonAPI.compilePerms(ADD_SELF_ORDER)
    ADD_ANY_ORDER = CommonAPI.compilePerms(ADD_ANY_ORDER)
    CHANGE_SELF_ORDER = CommonAPI.compilePerms(CHANGE_SELF_ORDER)
    CHANGE_ANY_ORDER = CommonAPI.compilePerms(CHANGE_ANY_ORDER)
    CHANGE_ANY_ORDER_PRICE = CommonAPI.compilePerms(CHANGE_ANY_ORDER_PRICE)
    DELETE_SELF_ORDER = CommonAPI.compilePerms(DELETE_SELF_ORDER)
    DELETE_ANY_ORDER = CommonAPI.compilePerms(DELETE_ANY_ORDER)



