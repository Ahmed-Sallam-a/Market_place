from django.urls import reverse
from django.db.models import Count, Q, Sum
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.contrib.auth import login as auth_login, authenticate
from django.contrib.auth.views import LoginView
from .models import Cart, Product, Customer, Payment, Order, OrderItem, UserAccount, Transaction, ProductImage, CATEGORY_CHOICES, Inventory
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomerProfileForm, CustomerRegistrationForm, LoginForm, MyPasswordChangeForm, MyPasswordResetForm, MySetPasswordForm, ProductForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils import timezone
from decimal import Decimal
import json
import razorpay
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.files.storage import FileSystemStorage
import os
from django.core.exceptions import ValidationError
from django.db.models.fields.files import ImageFieldFile, ImageField, FileField, File
from django.db.models.functions import TruncMonth

def home(request):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    
    # Get all categories
    categories = dict(CATEGORY_CHOICES)
    
    # Get products for each category (limit to 4 per category)
    category_products = {}
    for category_code, category_name in CATEGORY_CHOICES:
        products = Product.objects.filter(
            category=category_code,
            status='available'
        ).order_by('-created_at')[:4]
        if products.exists():
            category_products[category_name] = products
    
    # Get featured products
    featured_products = Product.objects.filter(
        featured=True,
        status='available'
    ).order_by('-created_at')[:8]
    
    return render(request, "app/home.html", {
        'totalitem': totalitem,
        'categories': categories,
        'category_products': category_products,
        'featured_products': featured_products
    })

def about(request):
    return render(request, 'app/about.html')

def contact(request):
    return render(request, 'app/contact.html')

def search(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__icontains=query)
        ).filter(status='available')
    else:
        products = Product.objects.filter(status='available')
    
    context = {
        'products': products,
        'query': query
    }
    return render(request, 'app/search.html', context)

def category(request, category_name):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    
    # Convert category name to code
    category_code = None
    for code, name in CATEGORY_CHOICES:
        if name.lower() == category_name.lower() or code.lower() == category_name.lower():
            category_code = code
            break
    
    if category_code:
        products = Product.objects.filter(
            category=category_code,
            status='available'
        ).order_by('-created_at')
    else:
        products = Product.objects.none()
    
    return render(request, "app/category.html", {
        'totalitem': totalitem,
        'products': products,
        'category_name': category_name
    })

class CategoryTitle(View):
    def get(self, request, val):
        products = Product.objects.filter(category=val)
        return render(request, 'app/category.html', {'products': products})

def product_detail(request, pk):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    
    product = get_object_or_404(Product, pk=pk)
    # Increment view count
    product.increment_views()
    
    # Get additional images
    additional_images = ProductImage.objects.filter(product=product)
    
    context = {
        'product': product,
        'additional_images': additional_images,
        'totalitem': totalitem
    }
    return render(request, 'app/productdetail.html', context)

class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})
    
    def post(self, request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            messages.success(request, "Congratulations! User Registered Successfully")
            form.save()
        return render(request, 'app/customerregistration.html', {'form': form})

class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        return render(request, 'app/profile.html', {'form': form, 'active': 'btn-primary'})

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            usr = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']
            reg = Customer(user=usr, name=name, locality=locality, city=city, state=state, zipcode=zipcode)
            reg.save()
            messages.success(request, "Congratulations! Profile Updated Successfully")
        return render(request, 'app/profile.html', {'form': form, 'active': 'btn-primary'})

@login_required
def address(request):
    add = Customer.objects.filter(user=request.user)
    return render(request, 'app/address.html', {'add': add, 'active': 'btn-primary'})

@login_required
def add_address(request):
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            usr = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']
            reg = Customer(user=usr, name=name, locality=locality, city=city, state=state, zipcode=zipcode)
            reg.save()
            messages.success(request, "Congratulations! Address Added Successfully")
            return redirect('address')
        else:
            form = CustomerProfileForm()
    return render(request, 'app/add_address.html', {'form': form, 'active': 'btn-primary'})

@login_required
def delete_address(request, pk):
    address = get_object_or_404(Customer, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address deleted successfully!")
        return redirect('address')
    return render(request, 'app/delete_address.html', {'address': address})

@login_required
def edit_address(request, pk):
    address = get_object_or_404(Customer, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CustomerProfileForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully!")
            return redirect('address')
        else:
            form = CustomerProfileForm(instance=address)
    return render(request, 'app/edit_address.html', {'form': form, 'address': address})

@login_required
def checkout(request):
    try:
        user = request.user
        # Get cart items and calculate total
        cart_items = Cart.objects.filter(user=user)
        if not cart_items.exists():
            messages.warning(request, "Your cart is empty!")
            return redirect('show_cart')
        
        # Calculate amounts
        amount = sum(item.quantity * item.product.selling_price for item in cart_items)
        shipping_cost = 20 if cart_items.exists() else 0
        totalamount = amount + shipping_cost
        
        # Get user's addresses
        addresses = Customer.objects.filter(user=user)
        
        context = {
            'cart_items': cart_items,
            'totalamount': totalamount,
            'add': addresses
        }
        
        return render(request, 'app/checkout.html', context)
        
    except Exception as e:
        messages.error(request, f"Error during checkout: {str(e)}")
        return redirect('show_cart')

@login_required
def orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    order_items = {}
    for order in orders:
        order_items[order.id] = OrderItem.objects.filter(order=order)
    
    context = {
        'orders': orders,
        'order_items': order_items
    }
    return render(request, 'app/orders.html', context)

@login_required
def payment_done(request):
    if request.method == 'POST':
        try:
            # Get the selected address and payment method
            address_id = request.POST.get('address')
            payment_method = request.POST.get('payment_method')
            
            if not address_id:
                messages.error(request, 'Please select a shipping address')
                return redirect('checkout')
            
            # Get the customer address
            customer = Customer.objects.get(id=address_id)
            
            # Get cart items
            cart_items = Cart.objects.filter(user=request.user)
            if not cart_items.exists():
                messages.error(request, 'Your cart is empty')
                return redirect('show_cart')
            
            # Calculate total amount
            total_amount = sum(item.product.selling_price * item.quantity for item in cart_items)
            shipping_cost = 50  # Fixed shipping cost
            total_amount += shipping_cost
            
            # Handle wallet payment for credit/debit card
            if payment_method in ['credit_card', 'debit_card']:
                # Check if user has sufficient balance
                try:
                    user_account = UserAccount.objects.get(user=request.user)
                    if user_account.balance < total_amount:
                        messages.error(request, 'Insufficient wallet balance')
                        return redirect('checkout')
                    
                    # Create transaction record for buyer
                    Transaction.objects.create(
                        user=request.user,
                        amount=-total_amount,
                        transaction_type='purchase',
                        status='completed'
                    )
                    
                    # Update buyer's wallet balance
                    user_account.balance -= total_amount
                    user_account.save()
                    
                    # Create transaction records for sellers and update their balances
                    for cart_item in cart_items:
                        seller = cart_item.product.seller
                        if seller:
                            seller_account, _ = UserAccount.objects.get_or_create(user=seller)
                            item_total = cart_item.product.selling_price * cart_item.quantity
                            
                            # Create transaction record for seller
                            Transaction.objects.create(
                                user=seller,
                                buyer=request.user,
                                seller=seller,
                                product=cart_item.product,
                                amount=item_total,
                                transaction_type='sale',
                                status='completed'
                            )
                            
                            # Update seller's wallet balance
                            seller_account.balance += item_total
                            seller_account.save()
                    
                except UserAccount.DoesNotExist:
                    messages.error(request, 'User account not found')
                    return redirect('checkout')
            
            # Create order
            order = Order.objects.create(
                user=request.user,
                customer=customer,
                total_amount=total_amount,
                status='pending'
            )
            
            # Create order items and update product quantities
            for cart_item in cart_items:
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.product.selling_price
                )
                
                # Update product quantity
                product = cart_item.product
                product.quantity -= cart_item.quantity
                if product.quantity <= 0:
                    product.status = 'sold'
                product.save()
                
                # Create inventory record
                Inventory.objects.create(
                    user=request.user,
                    product=product,
                    quantity=cart_item.quantity,
                    type='purchased'
                )
                
                if product.seller:
                    Inventory.objects.create(
                        user=product.seller,
                        product=product,
                        quantity=cart_item.quantity,
                        type='sold'
                    )
            
            # Create payment record
            Payment.objects.create(
                user=request.user,
                amount=total_amount,
                order=order
            )
            
            # Clear the cart
            cart_items.delete()
            
            messages.success(request, 'Order placed successfully!')
            return redirect('orders')
            
        except Customer.DoesNotExist:
            messages.error(request, 'Invalid shipping address')
            return redirect('checkout')
        except Exception as e:
            messages.error(request, f'Error processing order: {str(e)}')
            return redirect('checkout')
    
    return redirect('checkout')

@login_required
def add_to_cart(request):
    user = request.user
    product_id = request.POST.get('prod_id') or request.GET.get('prod_id')
    
    if not product_id:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Product ID is required'
            })
        messages.error(request, "Product ID is required.")
        return redirect('home')
    
    try:
        product = Product.objects.get(id=product_id)
        
        # Check if product is available
        if product.status != 'available':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'error',
                    'message': 'This product is not available for purchase.'
                })
            messages.error(request, "This product is not available for purchase.")
            return redirect('product-detail', pk=product_id)
        
        # Check if product is already in cart
        cart_item, created = Cart.objects.get_or_create(
            user=user,
            product=product,
            defaults={'quantity': 1}
        )
        
        if not created:
            cart_item.quantity += 1
            cart_item.save()
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Product added to cart successfully!'
            })
        
        messages.success(request, "Product added to cart successfully!")
        return redirect('show_cart')
        
    except Product.DoesNotExist:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'error',
                'message': 'Product not found'
            })
        messages.error(request, "Product not found.")
        return redirect('home')

@login_required
def show_cart(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    amount = sum(item.quantity * item.product.selling_price for item in cart_items)
    shipping_cost = 50 if cart_items.exists() else 0
    totalamount = amount + shipping_cost
    
    context = {
        'cart': cart_items,
        'amount': amount,
        'totalamount': totalamount,
        'totalitem': len(cart_items)
    }
    return render(request, 'app/addtocart.html', context)

@login_required
def plus_cart(request):
    if request.method == 'POST':
        prod_id = request.POST.get('prod_id')
        try:
            cart_item = Cart.objects.get(user=request.user, product_id=prod_id)
            cart_item.quantity += 1
            cart_item.save()
            
            # Calculate totals
            cart_items = Cart.objects.filter(user=request.user)
            amount = sum(item.quantity * item.product.selling_price for item in cart_items)
            shipping_cost = 50 if cart_items.exists() else 0
            totalamount = amount + shipping_cost
            
            return JsonResponse({
                'status': 'success',
                'quantity': cart_item.quantity,
                'total': cart_item.quantity * cart_item.product.selling_price,
                'amount': amount,
                'totalamount': totalamount
            })
        except Cart.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Cart item not found'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def minus_cart(request):
    if request.method == 'POST':
        prod_id = request.POST.get('prod_id')
        try:
            cart_item = Cart.objects.get(user=request.user, product_id=prod_id)
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
                quantity = cart_item.quantity
            else:
                cart_item.delete()
                quantity = 0
            
            # Calculate totals
            cart_items = Cart.objects.filter(user=request.user)
            amount = sum(item.quantity * item.product.selling_price for item in cart_items)
            shipping_cost = 50 if cart_items.exists() else 0
            totalamount = amount + shipping_cost
            
            return JsonResponse({
                'status': 'success',
                'quantity': quantity,
                'total': quantity * cart_item.product.selling_price if quantity > 0 else 0,
                'amount': amount,
                'totalamount': totalamount
            })
        except Cart.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Cart item not found'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def remove_cart(request):
    if request.method == 'POST':
        prod_id = request.POST.get('prod_id')
        try:
            cart_item = Cart.objects.get(user=request.user, product_id=prod_id)
            cart_item.delete()
            
            # Calculate totals
            cart_items = Cart.objects.filter(user=request.user)
            amount = sum(item.quantity * item.product.selling_price for item in cart_items)
            shipping_cost = 50 if cart_items.exists() else 0
            totalamount = amount + shipping_cost
            
            return JsonResponse({
                'status': 'success',
                'amount': amount,
                'totalamount': totalamount
            })
        except Cart.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Cart item not found'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

@login_required
def seller_dashboard(request):
    # Get seller's products
    products = Product.objects.filter(seller=request.user).order_by('-created_at')
    total_products = products.count()
    
    # Get seller's orders through OrderItem
    order_items = OrderItem.objects.filter(product__seller=request.user)
    total_orders = order_items.count()
    
    # Get seller's wallet balance
    user_account = UserAccount.objects.get_or_create(user=request.user)[0]
    wallet_balance = user_account.balance
    
    # Get recent products (last 5)
    recent_products = products[:5]
    
    context = {
        'total_products': total_products,
        'total_orders': total_orders,
        'wallet_balance': wallet_balance,
        'recent_products': recent_products
    }
    
    return render(request, 'app/seller_dashboard.html', context)

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user
            product.save()

            # Handle additional images
            additional_images = request.FILES.getlist('additional_images')
            for image in additional_images:
                ProductImage.objects.create(
                    product=product,
                    image=image
                )
            
            messages.success(request, 'Product added successfully!')
            return redirect('seller-dashboard')
    else:
        form = ProductForm()
    return render(request, 'app/add_product.html', {'form': form})

@login_required
def edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, 'Product updated successfully!')
            return redirect('seller-dashboard')
    else:
        form = ProductForm(instance=product)
    return render(request, 'app/edit_product.html', {'form': form})

@login_required
def delete_product(request, pk):
    product = get_object_or_404(Product, pk=pk, seller=request.user)
    if request.method == 'POST':
        product.status = 'delisted'
        product.save()
        messages.success(request, 'Product has been delisted successfully.')
        return redirect('seller-dashboard')
    return render(request, 'app/delete_product.html', {'product': product})

@login_required
def wallet(request):
    user_account = UserAccount.objects.get_or_create(user=request.user)[0]
    transactions = Transaction.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).order_by('-created_at')
    return render(request, 'app/wallet.html', {
        'user_account': user_account,
        'transactions': transactions
    })

@login_required
def add_coins(request):
    if request.method == 'POST':
        amount = request.POST.get('amount')
        if amount:
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    messages.error(request, 'Amount must be greater than 0')
                    return redirect('wallet')
                
                # Create wallet transaction
                transaction = Transaction.objects.create(
                    user=request.user,
                    amount=amount,
                    transaction_type='wallet',
                    status='completed'
                )
                
                # Update user's wallet balance
                user_account, created = UserAccount.objects.get_or_create(user=request.user)
                user_account.balance += amount
                user_account.save()
                
                messages.success(request, f'Successfully added {amount} coins to your wallet')
            except (ValueError, InvalidOperation):
                messages.error(request, 'Invalid amount')
            except Exception as e:
                messages.error(request, f'Error adding coins: {str(e)}')
        else:
            messages.error(request, 'Please enter an amount')
    return redirect('wallet')

@login_required
def purchase_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        buyer_account = UserAccount.objects.get_or_create(user=request.user)[0]
        seller_account = UserAccount.objects.get_or_create(user=product.seller)[0]
        
        if buyer_account.balance >= product.selling_price:
            # Create transaction
            transaction = Transaction.objects.create(
                buyer=request.user,
                seller=product.seller,
                product=product,
                amount=product.selling_price,
                transaction_type='purchase',
                status='completed'
            )
            
            # Update balances
            buyer_account.balance -= product.selling_price
            seller_account.balance += product.selling_price
            
            buyer_account.save()
            seller_account.save()
            
            # Update product quantity
            product.quantity -= 1
            if product.quantity == 0:
                product.status = 'sold'
            product.save()
            
            messages.success(request, 'Purchase successful!')
            return redirect('wallet')
        else:
            messages.error(request, 'Insufficient balance!')
    return render(request, 'app/productdetail.html', {'product': product})

class MyPasswordChangeView(PasswordChangeView):
    form_class = MyPasswordChangeForm
    success_url = reverse_lazy('passwordchangedone')

def password_change(request):
    return MyPasswordChangeView.as_view()(request)

@login_required
def password_change_done(request):
    messages.success(request, 'Password changed successfully!')
    return render(request, 'app/passwordchangedone.html')

@login_required
def transaction_report(request):
    # Get all transactions for the user
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Calculate summary statistics
    total_spent = transactions.filter(transaction_type='purchase').aggregate(total=Sum('amount'))['total'] or 0
    total_earned = transactions.filter(transaction_type='sale').aggregate(total=Sum('amount'))['total'] or 0
    total_deposits = transactions.filter(transaction_type='wallet').aggregate(total=Sum('amount'))['total'] or 0
    
    # Get recent transactions
    recent_transactions = transactions[:10]
    
    # Get monthly statistics
    monthly_stats = transactions.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        total_spent=Sum('amount', filter=Q(transaction_type='purchase')),
        total_earned=Sum('amount', filter=Q(transaction_type='sale')),
        total_deposits=Sum('amount', filter=Q(transaction_type='wallet'))
    ).order_by('-month')
    
    context = {
        'transactions': recent_transactions,
        'total_spent': total_spent,
        'total_earned': total_earned,
        'total_deposits': total_deposits,
        'monthly_stats': monthly_stats,
    }
    
    return render(request, 'app/transaction_report.html', context)