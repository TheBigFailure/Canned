from django.urls import path, include
from rest_framework import routers
from . import apis

ROUTER = routers.DefaultRouter()
ROUTER.register(r'users', apis.ProfileViewSet)
ROUTER.register(r'orders', apis.OrderViewSet)

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("auth/", include("dj_rest_auth.urls")),
    path('', include(ROUTER.urls)),
]
# urlpatterns = [
#     path('test/<path:endpoint>', TestAPI.uponRequest),
# ]