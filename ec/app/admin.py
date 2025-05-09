from django.contrib import admin
from .models import *

# Register your models here.
@admin.register(Customer)
class CustomerModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'name', 'locality', 'city', 'phone', 'state', 'zipcode']
    search_fields = ['name', 'email', 'phone']
    list_filter = ['state', 'city']

@admin.register(Product)
class ProductModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'selling_price', 'category', 'product_image']
    search_fields = ['title', 'description']
    list_filter = ['category', 'status', 'seller']

@admin.register(Cart)
class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity']
    search_fields = ['user__username', 'product__title']
    list_filter = ['created_at']

@admin.register(Payment)
class PaymentModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'razorpay_order_id', 'razorpay_payment_status']
    search_fields = ['user__username', 'razorpay_order_id']
    list_filter = ['razorpay_payment_status', 'created_at']

@admin.register(Order)
class OrderModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'customer', 'total_amount', 'status', 'created_at']
    search_fields = ['user__username', 'customer__name']
    list_filter = ['status', 'created_at']

@admin.register(OrderItem)
class OrderItemModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'product', 'quantity', 'price', 'created_at']
    search_fields = ['order__id', 'product__title']
    list_filter = ['created_at']

@admin.register(Transaction)
class TransactionModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'transaction_type', 'status', 'created_at']
    list_filter = ['transaction_type', 'status', 'created_at']
    search_fields = ['user__username', 'amount', 'transaction_type']
    readonly_fields = ['created_at']

@admin.register(UserAccount)
class UserAccountModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'balance', 'created_at', 'updated_at']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(ProductImage)
class ProductImageModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'image', 'created_at']
    readonly_fields = ['created_at']

@admin.register(Inventory)
class InventoryModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'type', 'created_at', 'updated_at']
    search_fields = ['user__username', 'product__title']
    list_filter = ['type', 'created_at']

