from capi import *
from capi import serializers as modelSerializers
from capi.security import standardViewsetWrapper
from capi import config as cfg
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


class ProductViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows products to be viewed or edited.
    """
    queryset = Product.objects.all().order_by('name')
    serializer_class = modelSerializers.ProductSerializer

    permission_classes = [permissions.IsAuthenticated]


class OrderViewSet(viewsets.GenericViewSet, generics.RetrieveUpdateDestroyAPIView, generics.CreateAPIView):
    """
    API endpoint that allows orders to be viewed or edited.
    """
    @staticmethod
    @standardViewsetWrapper(actionForSelf=cfg.OrderAPI.VIEW_SELF_ORDER, actionForAny=cfg.OrderAPI.VIEW_ANY_ORDER,
                            logEvents={Event.API_REQUEST,}, logMessage=True)
    def retrieve(actionAny: bool, request: RestRequest, *args, **kwargs) -> QuerySet:
        # Note: actionAny is handled by the wrapper.
        querySet = None
        if actionAny:
            querySet = Order.objects.all()
        else:
            querySet = Order.objects.filter(user=request.user)
        data = modelSerializers.OrderSerializer(querySet, many=True).data
        return Response(data=data)

    @staticmethod
    @standardViewsetWrapper(actionForSelf=cfg.OrderAPI.DELETE_SELF_ORDER, actionForAny=cfg.OrderAPI.DELETE_ANY_ORDER,
                            logEvents={Event.API_REQUEST,}, logMessage=True)
    def destroy(actionAny: bool, request: RestRequest, *args, **kwargs):
        # Note: actionAny is handled by the wrapper.
        instance = Order.objects.get(id=kwargs["pk"])
        instance.cancel()
        return Response(status=204)

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



