from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for viewing subscription plans"""
    queryset = Plan.objects.filter(is_active=True).order_by('price')
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """API endpoints for managing user subscriptions"""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current active subscription"""
        subscription = request.user.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        if subscription:
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        
        return Response(
            {'message': 'اشتراک فعالی ندارید'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        
        if subscription.status == 'cancelled':
            return Response(
                {'error': 'این اشتراک قبلاً لغو شده است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        subscription.cancel()
        
        return Response({'message': 'اشتراک لغو شد'})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate subscription"""
        subscription = self.get_object()
        subscription.activate()
        
        return Response({'message': 'اشتراک فعال شد'})
