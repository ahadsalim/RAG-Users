from django.utils import timezone
from django.http import JsonResponse
from rest_framework import status
from .models import Subscription
import json


class SubscriptionMiddleware:
    """
    Middleware to check subscription limits for API calls
    """
    
    # Paths that don't require subscription check
    EXEMPT_PATHS = [
        '/api/v1/auth/',
        '/api/v1/plans/',
        '/api/v1/subscriptions/',
        '/api/v1/payments/',
        '/admin/',
        '/static/',
        '/media/',
        '/health/',
    ]
    
    # Paths that consume queries
    QUERY_PATHS = [
        '/api/v1/chat/query',
        '/api/v1/chat/query-stream',
        '/ws/chat',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for exempt paths
        for path in self.EXEMPT_PATHS:
            if request.path.startswith(path):
                return self.get_response(request)
        
        # Skip for anonymous users
        if not request.user.is_authenticated:
            return self.get_response(request)
        
        # Skip for superusers
        if request.user.is_superuser:
            return self.get_response(request)
        
        # Check if path requires query quota
        is_query_path = any(request.path.startswith(path) for path in self.QUERY_PATHS)
        
        if is_query_path and request.method == 'POST':
            # Get active subscription
            subscription = request.user.subscriptions.filter(
                status__in=['active', 'trial'],
                end_date__gt=timezone.now()
            ).first()
            
            if not subscription:
                return JsonResponse(
                    {
                        'error': 'اشتراک فعالی ندارید',
                        'code': 'NO_ACTIVE_SUBSCRIPTION',
                        'plans_url': '/api/v1/plans/'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Check if user can query
            can_query, message = subscription.can_query()
            if not can_query:
                return JsonResponse(
                    {
                        'error': message,
                        'code': 'QUOTA_EXCEEDED',
                        'usage': {
                            'daily_used': subscription.queries_used_today,
                            'daily_limit': subscription.plan.max_queries_per_day,
                            'monthly_used': subscription.queries_used_month,
                            'monthly_limit': subscription.plan.max_queries_per_month,
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            
            # Add subscription to request for later use
            request.subscription = subscription
        
        response = self.get_response(request)
        
        # Log successful query
        if is_query_path and request.method == 'POST' and response.status_code == 200:
            if hasattr(request, 'subscription'):
                try:
                    # Extract tokens from response if available
                    tokens = 0
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        tokens = response.data.get('metadata', {}).get('tokens', 0)
                    
                    # Increment usage
                    # request.subscription.increment_usage(tokens=tokens)
                    
                    # Log usage - TODO: Implement when UsageLog model is ready
                    # UsageLog.objects.create(
                    #     subscription=request.subscription,
                    #     user=request.user,
                    #     action_type='query',
                    #     tokens_used=tokens,
                    #     metadata={
                    #         'path': request.path,
                    #         'model': response.data.get('metadata', {}).get('model_used', 'unknown')
                    #     },
                    #     ip_address=self.get_client_ip(request),
                    #     user_agent=request.META.get('HTTP_USER_AGENT', '')
                    # )
                    pass
                except Exception as e:
                    # Don't break the response, just log the error
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.error(f"Error logging usage: {e}")
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
