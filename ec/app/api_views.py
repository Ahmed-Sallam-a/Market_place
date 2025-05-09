from rest_framework import viewsets, status, permissions, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Sum, Count
from .models import (
    UserAccount, Product, Transaction, Inventory,
    Customer, Cart, Order, OrderItem, Payment
)
from .serializers import (
    UserSerializer, UserAccountSerializer, ProductSerializer,
    TransactionSerializer, InventorySerializer, CustomerSerializer,
    CartSerializer, OrderSerializer, OrderItemSerializer, PaymentSerializer
)

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        UserAccount.objects.create(user=user)
        Customer.objects.create(
            user=user,
            name=f"{user.first_name} {user.last_name}",
            email=user.email
        )

class UserAccountViewSet(viewsets.ModelViewSet):
    queryset = UserAccount.objects.all()
    serializer_class = UserAccountSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return UserAccount.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def deposit(self, request):
        amount = request.data.get('amount')
        if not amount or float(amount) <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)

        user_account = self.get_queryset().first()
        if not user_account:
            user_account = UserAccount.objects.create(user=request.user)

        user_account.balance += float(amount)
        user_account.save()

        # Create transaction record
        Transaction.objects.create(
            buyer=request.user,
            seller=request.user,
            product=None,
            amount=float(amount),
            transaction_type='deposit',
            status='completed'
        )

        return Response(self.get_serializer(user_account).data)

    @action(detail=False, methods=['get'])
    def balance(self, request):
        user_account = self.get_queryset().first()
        if not user_account:
            return Response({'balance': 0})
        return Response({'balance': user_account.balance})

    @action(detail=False, methods=['get'])
    def inventory_summary(self, request):
        inventory = Inventory.objects.filter(user=request.user)
        summary = {
            'purchased': inventory.filter(type='purchased').aggregate(
                total_items=Count('id'),
                total_quantity=Sum('quantity')
            ),
            'selling': inventory.filter(type='selling').aggregate(
                total_items=Count('id'),
                total_quantity=Sum('quantity')
            ),
            'sold': inventory.filter(type='sold').aggregate(
                total_items=Count('id'),
                total_quantity=Sum('quantity')
            )
        }
        return Response(summary)

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(title__icontains=search)
        
        return queryset

    def perform_create(self, serializer):
        product = serializer.save(seller=self.request.user)
        # Create inventory entry for the seller
        Inventory.objects.create(
            user=self.request.user,
            product=product,
            quantity=product.quantity,
            type='selling'
        )

    @action(detail=True, methods=['post'])
    def update_quantity(self, request, pk=None):
        product = self.get_object()
        if product.seller != request.user:
            return Response({'error': 'Not authorized'}, status=status.HTTP_403_FORBIDDEN)

        quantity = request.data.get('quantity')
        if not quantity or int(quantity) < 0:
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

        product.quantity = int(quantity)
        product.save()

        # Update inventory
        inventory = Inventory.objects.get(user=request.user, product=product, type='selling')
        inventory.quantity = int(quantity)
        inventory.save()

        return Response(self.get_serializer(product).data)

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        product = self.get_object()
        quantity = int(request.data.get('quantity', 1))
        
        if quantity <= 0 or quantity > product.quantity:
            return Response({'error': 'Invalid quantity'}, status=status.HTTP_400_BAD_REQUEST)

        buyer_account = UserAccount.objects.get_or_create(user=request.user)[0]
        seller_account = UserAccount.objects.get_or_create(user=product.seller)[0]
        total_amount = product.selling_price * quantity

        if buyer_account.balance < total_amount:
            return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)

        with transaction.atomic():
            # Update balances
            buyer_account.balance -= total_amount
            seller_account.balance += total_amount
            buyer_account.save()
            seller_account.save()

            # Update product quantity
            product.quantity -= quantity
            product.save()

            # Create transaction record
            Transaction.objects.create(
                buyer=request.user,
                seller=product.seller,
                product=product,
                amount=total_amount,
                transaction_type='purchase',
                status='completed'
            )

            # Update inventory
            Inventory.objects.create(
                user=request.user,
                product=product,
                quantity=quantity,
                type='purchased'
            )

            Inventory.objects.create(
                user=product.seller,
                product=product,
                quantity=quantity,
                type='sold'
            )

        return Response({'message': 'Purchase successful'})

class TransactionViewSet(viewsets.ModelViewSet):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(
            buyer=self.request.user
        ) | Transaction.objects.filter(
            seller=self.request.user
        )

    @action(detail=False, methods=['get'])
    def history(self, request):
        transactions = self.get_queryset().order_by('-created_at')
        return Response(self.get_serializer(transactions, many=True).data)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        transactions = self.get_queryset()
        total_spent = sum(t.amount for t in transactions if t.buyer == request.user)
        total_earned = sum(t.amount for t in transactions if t.seller == request.user)
        
        return Response({
            'total_spent': total_spent,
            'total_earned': total_earned,
            'net_balance': total_earned - total_spent
        })

    @action(detail=False, methods=['get'])
    def detailed_report(self, request):
        transactions = self.get_queryset()
        
        # Daily transactions
        daily_transactions = transactions.values('created_at__date').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-created_at__date')

        # Transaction types
        transaction_types = transactions.values('transaction_type').annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        )

        # Top products
        top_products = transactions.exclude(product=None).values(
            'product__title'
        ).annotate(
            total_amount=Sum('amount'),
            count=Count('id')
        ).order_by('-total_amount')[:5]

        return Response({
            'daily_transactions': daily_transactions,
            'transaction_types': transaction_types,
            'top_products': top_products
        }) 