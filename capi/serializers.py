from . import *
from candb.models import Profile, Order, OrderLine, Product

class ProfileSerializer(rest_serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Profile
        fields = ['username', 'first_name', 'last_name']

class OrderSerializer(rest_serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['id', 'orderTime', 'totalCost', 'notes', 'user']
