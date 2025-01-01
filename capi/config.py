# <Initfile>
import django.db.utils

from capi import *
from capi import common as _common
from candb.apps import CandbConfig as _app_CandbConfig
from candb.models import Profile
from django.contrib.auth.models import Permission

# Note: permission indicates permissions from the rest framework, Permission indicates permissions from the django auth system

try:
    Permission.objects.get(codename="change_any_order")

    class CommonAPI:
        @staticmethod
        def compilePerms(perms: list[Permission]) -> _common.CompiledPermissions:
            _compiled = set()
            for perm in perms:
                if isinstance(perm, Permission):
                    # A long story learnt, you need the appname and codename, not just the codename.
                    # It was fun reading django.contrib.auth.backends. Please buy me a coffee :)
                    # (or maybe pay for my therapy)
                    _compiled.add(f"{_app_CandbConfig.name}.{perm.codename}")
                elif isinstance(perm, str):
                    _compiled.add(perm)
                else:
                    raise TypeError(f"expected Permission or str, got {type(perm)}")
            return _compiled

        @staticmethod
        def compileImplies(imply: dict[Permission: tuple[Permission]]) -> dict[str: _common.CompiledPermissions]:
            return dict({perm.codename: set({imp.codename for imp in implies}) for perm, implies in imply.items()})

        LOGIN_PERMISSION = permissions.IsAuthenticated
        ADMIN_PERMISSION = permissions.IsAdminUser

        # Note, no OVERRIDE_WHEN_SUPERUSER, as superusers can do anything. This is implemented in django.contrib.auth.models.PermissionsMixin.has_perm, in which active superusers bypass permission checks.
        OVERRIDE_WHEN_STAFF: str = "__override_staff__"  # allows staff to not require permissions for a given action

        # SHOULD BE RARELY USED. Only should be used for rare cases where a permission is a subset of another permission.
        # Where possible, view, add, change, delete self and view, add, change, delete any should be separately added to a user's permissions

        # Permission: Implied Permission(s)
        IMPLY: dict[Permission: tuple[Permission]] = {
            Permission.objects.get(codename="change_any_order"): (
                Permission.objects.get(codename="change_any_order_but_overridecost"),),
            Permission.objects.get(codename="change_any_orderline"): (
                Permission.objects.get(codename="change_any_orderline_but_forceprice"),),
        }
        IMPLY = compileImplies(IMPLY)
        # Implied Permission: Permission(s) that imply it
        _LOOKUP_IMPLY: dict[str: list[str]] = dict()
        for perm, implies in IMPLY.items():
            for imply in implies:
                if imply not in _LOOKUP_IMPLY:
                    _LOOKUP_IMPLY[imply] = list()
                _LOOKUP_IMPLY[imply].append(perm)

        _LOOKUP_IMPLY = dict({_k: set(_v) for _k, _v in _LOOKUP_IMPLY.items()})

        @classmethod
        def userHasPerms(cls: Self, profile: Profile, perms: set[str]) -> bool:
            if profile.is_superuser:  # Rather than having django.contrib.auth.models.PermissionsMixin.has_perm do the work, we can just check if the user is a superuser here which will be faster
                return True
            if cls.OVERRIDE_WHEN_STAFF in perms:
                if profile.is_staff:
                    return True
                perms.remove(cls.OVERRIDE_WHEN_STAFF)
            # A for loop isn't actually as slow as you think it is, as the implementation of User.has_perm uses all(self.has_perm(perm, obj) for perm in perm_list) anyway
            for perm in perms:
                if not profile.has_perm(perm):
                    # First check implied permissions before returning False
                    if perm in cls._LOOKUP_IMPLY:
                        for imply in cls._LOOKUP_IMPLY[perm]:
                            if profile.has_perm(imply):
                                break
                        else:
                            return False
                    else:
                        return False
            return True


    class OrderAPI:
        REQUIRE_LOGIN = True
        VIEW_SELF_ORDER: list[Permission] = [
            Permission.objects.get(codename="view_orderline"),
            Permission.objects.get(codename="view_order"),
            Permission.objects.get(codename="view_product"),
            CommonAPI.OVERRIDE_WHEN_STAFF,
        ]
        VIEW_ANY_ORDER: list[Permission] = [
            Permission.objects.get(codename="view_any_orderline"),
            Permission.objects.get(codename="view_any_order"),
            Permission.objects.get(codename="view_product"),
        ]
        ADD_SELF_ORDER: list[Permission] = [
            Permission.objects.get(codename="add_order"),
            Permission.objects.get(codename="add_orderline"),
            Permission.objects.get(codename="view_product"),
            CommonAPI.OVERRIDE_WHEN_STAFF,
        ]
        ADD_ANY_ORDER: list[Permission] = [
            Permission.objects.get(codename="add_any_order"),
            Permission.objects.get(codename="add_any_orderline"),
            Permission.objects.get(codename="view_product"),
        ]
        CHANGE_SELF_ORDER: list[Permission] = [
            Permission.objects.get(codename="change_order"),
            Permission.objects.get(codename="change_orderline"),
            Permission.objects.get(codename="view_product"),
            CommonAPI.OVERRIDE_WHEN_STAFF,
        ]
        CHANGE_ANY_ORDER: list[Permission] = [
            Permission.objects.get(codename="change_any_order_but_overridecost"),
            Permission.objects.get(codename="change_any_orderline_but_forceprice"),
        ]
        CHANGE_ANY_ORDER_PRICE: list[Permission] = [
            Permission.objects.get(codename="change_any_order"),
            Permission.objects.get(codename="change_any_orderline"),
        ]
        DELETE_SELF_ORDER: list[Permission] = [
            Permission.objects.get(codename="delete_order"),
            Permission.objects.get(codename="delete_orderline"),
            CommonAPI.OVERRIDE_WHEN_STAFF,
        ]
        DELETE_ANY_ORDER: list[Permission] = [
            Permission.objects.get(codename="delete_any_order"),
            Permission.objects.get(codename="delete_any_orderline"),
        ]
        VIEW_SELF_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(VIEW_SELF_ORDER)
        VIEW_ANY_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(VIEW_ANY_ORDER)
        ADD_SELF_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(ADD_SELF_ORDER)
        ADD_ANY_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(ADD_ANY_ORDER)
        CHANGE_SELF_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(CHANGE_SELF_ORDER)
        CHANGE_ANY_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(CHANGE_ANY_ORDER)
        CHANGE_ANY_ORDER_PRICE: _common.CompiledPermissions = CommonAPI.compilePerms(CHANGE_ANY_ORDER_PRICE)
        DELETE_SELF_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(DELETE_SELF_ORDER)
        DELETE_ANY_ORDER: _common.CompiledPermissions = CommonAPI.compilePerms(DELETE_ANY_ORDER)


except Exception as e:
    warnings.warn("Permission database table failed to query. It may not have been created yet. This is normal if you are running migrations for the first time.\nFunctions requiring permissions will not work until the table is created and may raise exceptions.", RuntimeWarning)
    class CommonAPI:
        LOGIN_PERMISSION = None
        ADMIN_PERMISSION = None
        OVERRIDE_WHEN_STAFF = None
        IMPLY = None
        _LOOKUP_IMPLY = None
    class OrderAPI:
        REQUIRE_LOGIN = None
        VIEW_SELF_ORDER = None
        VIEW_ANY_ORDER = None
        ADD_SELF_ORDER = None
        ADD_ANY_ORDER = None
        CHANGE_SELF_ORDER = None
        CHANGE_ANY_ORDER = None
        CHANGE_ANY_ORDER_PRICE = None
        DELETE_SELF_ORDER = None
        DELETE_ANY_ORDER = None


