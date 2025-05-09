from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.throttling import UserRateThrottle
from app.models import Product, Transaction, UserAccount
from .serializers import ProductSerializer, TransactionSerializer, UserAccountSerializer
from django.db.models import Sum

class UserRateThrottle(UserRateThrottle):
    rate = '100/hour'

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        queryset = Product.objects.all()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset

    @action(detail=True, methods=['post'])
    def purchase(self, request, pk=None):
        product = self.get_object()
        buyer = request.user
        
        if product.status != 'available':
            return Response({'error': 'Product is not available'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            buyer_account = UserAccount.objects.get(user=buyer)
            if buyer_account.balance < product.selling_price:
                return Response({'error': 'Insufficient balance'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Create transaction
            transaction = Transaction.objects.create(
                buyer=buyer,
                seller=product.seller,
                product=product,
                amount=product.selling_price,
                transaction_type='purchase',
                status='completed'
            )
            
            # Update balances
            buyer_account.balance -= product.selling_price
            buyer_account.save()
            
            seller_account = UserAccount.objects.get(user=product.seller)
            seller_account.balance += product.selling_price
            seller_account.save()
            
            # Update product
            product.quantity -= 1
            if product.quantity == 0:
                product.status = 'sold'
            product.save()
            
            return Response({'message': 'Purchase successful'}, status=status.HTTP_200_OK)
            
        except UserAccount.DoesNotExist:
            return Response({'error': 'User account not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        return Transaction.objects.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def summary(self, request):
        transactions = self.get_queryset()
        total_spent = transactions.filter(transaction_type='purchase').aggregate(total=Sum('amount'))['total'] or 0
        total_earned = transactions.filter(transaction_type='sale').aggregate(total=Sum('amount'))['total'] or 0
        
        return Response({
            'total_spent': total_spent,
            'total_earned': total_earned,
            'net_balance': total_earned - total_spent
        })

class UserAccountViewSet(viewsets.ModelViewSet):
    serializer_class = UserAccountSerializer
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]

    def get_queryset(self):
        return UserAccount.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        account = self.get_object()
        amount = request.data.get('amount')
        
        if not amount or float(amount) <= 0:
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Create transaction
            Transaction.objects.create(
                user=account.user,
                amount=amount,
                transaction_type='wallet',
                status='completed'
            )
            
            # Update balance
            account.balance += float(amount)
            account.save()
            
            return Response({'message': 'Deposit successful'}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST) 