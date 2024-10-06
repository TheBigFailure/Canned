from capi import *
from capi import serializers as modelSerializers
from candb.models import Profile, Order, OrderLine, Product
from capi.security import apiMethod
from capi.common import StandardResponse
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import viewsets, generics, mixins
from rest_framework.authentication import TokenAuthentication


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Profile.objects.all().order_by('-date_joined')
    serializer_class = modelSerializers.ProfileSerializer

    permission_classes = [permissions.IsAuthenticated, permissions.IsAdminUser]


class OrderViewSet(viewsets.GenericViewSet, generics.RetrieveUpdateDestroyAPIView, generics.CreateAPIView):
    """
    API endpoint that allows orders to be viewed or edited.
    """
    def get_queryset(self: Self) -> QuerySet:

        return Order.objects.all().order_by('-orderTime')

    queryset = Order.objects.all().order_by('-orderTime')
    serializer_class = modelSerializers.OrderSerializer

    permission_classes = [permissions.IsAuthenticated, ]


# Create your views here.
# class RouterBase:
#     name = "RouterBase"
#
#
#     @apiMethod(allowMethods={"GET",}, requireLogin=True, logEvents={Event.API_REQUEST,}, logMessage=True)
#     def check(self, request: HttpRequest, *args: Any, **kwargs: Any) -> HttpResponse:
#         return StandardResponse.OK
#
#     @classmethod
#     def uponRequest(cls: Self, request: HttpRequest, endpoint: str, *args: Any, **kwargs: Any) -> HttpResponse:
#         if endpoint in cls.routingMap:
#             func = cls.routingMap[endpoint]
#             return func(request, *args, **kwargs)
#         else:
#             return StandardResponse.NotFound
#
#     routingMap: dict[PathType: Callable] = {
#         "check": check,
#     }
#
#
#
#
# class TestAPI(RouterBase):
#     name = "TestAPI"



