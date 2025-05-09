from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    UserAccount, Product, Transaction, Inventory,
    Customer, Cart, Order, OrderItem, Payment
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name')
        extra_kwargs = {'password': {'write_only': True}}

class UserAccountSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = UserAccount
        fields = ('id', 'user', 'balance', 'created_at', 'updated_at')

class ProductSerializer(serializers.ModelSerializer):
    seller = UserSerializer(read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'seller', 'title', 'selling_price', 'description',
                 'category', 'product_image', 'quantity', 'status',
                 'created_at', 'updated_at')

class TransactionSerializer(serializers.ModelSerializer):
    buyer = UserSerializer(read_only=True)
    seller = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Transaction
        fields = ('id', 'buyer', 'seller', 'product', 'amount',
                 'transaction_type', 'status', 'created_at')

class InventorySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Inventory
        fields = ('id', 'user', 'product', 'quantity', 'type',
                 'created_at', 'updated_at')

class CustomerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Customer
        fields = ('id', 'user', 'name', 'email', 'phone', 'address',
                 'created_at', 'updated_at')

class CartSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    product = ProductSerializer(read_only=True)

    class Meta:
        model = Cart
        fields = ('id', 'user', 'product', 'quantity', 'created_at', 'updated_at')

class OrderItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'quantity', 'price', 'created_at')

class OrderSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    customer = CustomerSerializer(read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'customer', 'total_amount', 'status',
                 'items', 'created_at', 'updated_at')

class PaymentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    order = OrderSerializer(read_only=True)

    class Meta:
        model = Payment
        fields = ('id', 'user', 'order', 'amount', 'payment_method',
                 'status', 'transaction_id', 'created_at') 