from audioop import reverse
from django.db.models import Count, Q
from django.shortcuts import redirect, render 
from django.views import View
# import razorpay
from .models import Cart, Product,Customer,Payment,OrderPlaced
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.conf import settings
from .models import Product
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .forms import CustomerProfileForm, CustomerRegistrationForm
# Create your views here.

def home(request):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    return render(request, 'app/home.html',locals())

def about(request):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    return render(request, 'app/about.html',locals())

def contact(request):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    return render(request, 'app/contact.html',locals())

class CategoryView(View):
    def get(self, request,val):
        totalitem = 0
        if request.user.is_authenticated:
          totalitem = len(Cart.objects.filter(user=request.user))
        product = Product.objects.filter(category=val)
        title = Product.objects.filter(category=val).values('title')
        return render(request, "app/category.html",locals())
    
class CategoryTitle(View):
    def get(self, request,val):
        product = Product.objects.filter(title=val)
        title = Product.objects.filter(category=product[0].category).values('title')
        totalitem = 0
        if request.user.is_authenticated:
          totalitem = len(Cart.objects.filter(user=request.user)) 
        return render(request, "app/category.html",locals())
    
class ProductDetail(View):
    def get(self, request, pk):
        product = Product.objects.get(pk=pk)
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user))
        return render(request, 'app/productdetail.html', locals())
    
# add customer registeration view   

class CustomerRegistrationView(View):
    def get(self,request):
        form = CustomerRegistrationForm()
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user))  
        return render(request,'app/customerregistration.html',locals())
    def post(self,request):
        form = CustomerRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request,"User Register Successfully")
        else:
            messages.warning(request,"Invalid Input Data")
        return render(request,'app/customerregistration.html',locals())

# add one class profile view 

class ProfileView(View):
    def get(self, request):
        form = CustomerProfileForm()
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user))
        return render(request, 'app/profile.html', locals())

    def post(self, request):
        form = CustomerProfileForm(request.POST)
        if form.is_valid():
            user = request.user
            name = form.cleaned_data['name']
            locality = form.cleaned_data['locality']
            city = form.cleaned_data['city']
            mobile = form.cleaned_data['mobile']
            state = form.cleaned_data['state']
            zipcode = form.cleaned_data['zipcode']

            reg = Customer.objects.create(user=user, name=name, locality=locality, mobile=mobile, city=city, state=state, zipcode=zipcode)
            messages.success(request, "Profile saved successfully")
            return render(request, 'app/profile.html', {'form': form, 'success': True})
        else:
            messages.warning(request, "Invalid input data")
        return render(request, 'app/profile.html', {'form': form})

class AddressView(View):
    def get(self, request):
        add = Customer.objects.filter(user=request.user)
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user))
        return render(request, 'app/address.html', {'add': add})
    
class updateAddress(View):
    def get(self,request,pk):
        add=Customer.objects.get(pk=pk)
        form=CustomerProfileForm(instance=add)
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user)) 
        return render(request,'app/updateAddress.html',locals())
    def post(self,request,pk):
        form=CustomerProfileForm(request.POST)
        if form.is_valid():
            add=Customer.objects.get(pk=pk)
            add.user = request.user
            add.name = form.cleaned_data['name']
            add.locality = form.cleaned_data['locality']
            add.city = form.cleaned_data['city']
            add.mobile = form.cleaned_data['mobile']
            add.state = form.cleaned_data['state']
            add.zipcode = form.cleaned_data['zipcode']
            add.save()
            messages.success(request, "Profile updated successfully")
        else:
            messages.warning(request, "Invalid input data")
        return redirect("address")

        
def add_to_cart(request):
    user=request.user
    if (request.user.is_anonymous):
        return redirect("/accounts/login/")
    product_id=request.GET.get('prod_id')
    product = Product.objects.get(id=product_id)
    try:
        Cart.objects.get(Q(product=product_id) & Q(user=request.user))
    except:
        Cart(user=user, product=product).save()
    return redirect("/cart")
    
def show_cart(request):
    user = request.user
    if (request.user.is_anonymous):
        return redirect("/accounts/login/")      
    cart = Cart.objects.filter(user=user)
    amount = 0
    for p in cart:
        value = p.quantity * p.product.discounted_price
        amount = amount + value
    totalamount = amount + 20
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user)) 
    return render(request, 'app/addtocart.html', locals())
class checkout(View):
    def get(self,request):
        totalitem = 0
        if request.user.is_authenticated:
            totalitem = len(Cart.objects.filter(user=request.user)) 
        user=request.user
        add=Customer.objects.filter(user=user)
        cart_items=Cart.objects.filter(user=user)
        famount=0
        for p in cart_items:
            value=p.quantity*p.product.discounted_price
            famount=famount+value
        totalamount= famount+40
        return render(request, 'app/checkout.html',locals())
    
def test(request):
    user = request.user
    customer = Customer.objects.filter(user=user).first()
    cart_items = Cart.objects.filter(user=user)
    error_message = None
    all_available = True  # Flag to track if all quantities are available
    
    # Check if all quantities are available
    for cart_item in cart_items:
        product = cart_item.product
        if product.Quantity < cart_item.quantity:
            all_available = False
            message = f"The available quantity for {product.title} is only {product.Quantity}. Please remove it from your cart or reduce the quantity."
            break
    
    # If all quantities are available, deduct from the database
    if all_available:
        for cart_item in cart_items:
            product = cart_item.product
            product.Quantity -= cart_item.quantity
            product.save()

            message = f"Payment successful."
            
        # custid=request.GET.get('custid')
        customer=Customer.objects.get(id=customer.id)
        for c in cart_items:
            OrderPlaced(user=user,customer=customer, product=c.product,quantity=c.quantity).save()
            # c.delete()
        cart_items.delete()
        # Display success message
        return JsonResponse({'message': message}, status=200)
    else:
        # Display error message

        return JsonResponse({'message': message}, status=400)


def payment_done(request):
  
    return render(request, 'app/paymenttemplatetest.html',locals())    
    

def search(request):
    query = request.GET['search']
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user))
    product = Product.objects.filter(Q(title__icontains=query))
    return render (request,"app/search.html",locals())


def orders(request):
    totalitem = 0
    if request.user.is_authenticated:
        totalitem = len(Cart.objects.filter(user=request.user)) 
    order_placed=OrderPlaced.objects.filter(user=request.user) 
    return render(request , 'app/orders.html',locals())
    
    
def plus_cart(request):
    if request.method == 'GET':
        prod_id=request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity += 1
        c.save()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 20
        data = {
            'quantity':c.quantity,
            'amount':amount,
            'totalamount':totalamount,
        }
        return JsonResponse(data)
def minus_cart(request):
    if request.method == 'GET':
        prod_id=request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.quantity = max(c.quantity - 1, 0)
        c.save()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 20
        data = {
            'quantity':c.quantity,
            'amount':amount,
            'totalamount':totalamount,
        }
    
        return JsonResponse(data)
        
def remove_cart(request):
    if request.method == 'GET':
        prod_id=request.GET['prod_id']
        c = Cart.objects.get(Q(product=prod_id) & Q(user=request.user))
        c.delete()
        user = request.user
        cart = Cart.objects.filter(user=user)
        amount = 0
        for p in cart:
            value = p.quantity * p.product.discounted_price
            amount = amount + value
        totalamount = amount + 20
        data = {
            'amount':amount,
            'totalamount':totalamount,
        }
        return JsonResponse(data)
