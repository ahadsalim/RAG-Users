from django.utils import timezone
from django.http import JsonResponse
from rest_framework import status
from .models import Subscription
from .usage import UsageService
import json
import logging

logger = logging.getLogger(__name__)


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
        '/api/v1/chat/query/',
        '/api/v1/chat/query/stream/',
        '/ws/chat/',
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
        
        # Check if path requires query quota
        is_query_path = any(request.path.startswith(path) for path in self.QUERY_PATHS)
        
        # For superusers, skip quota check but still log usage
        if request.user.is_superuser:
            response = self.get_response(request)
            
            # Log usage for superusers too
            if is_query_path and request.method == 'POST' and response.status_code == 200:
                try:
                    UsageService.log_usage(
                        user=request.user,
                        action_type='query',
                        tokens_used=0,
                        subscription=None,
                        metadata={
                            'path': request.path,
                            'is_superuser': True
                        },
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    logger.info(f"Query logged for superuser {request.user}")
                except Exception as e:
                    logger.error(f"Error logging usage for superuser: {e}")
            
            return response
        
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
            
            # Check if user can query using UsageService
            can_query, message, usage_info = UsageService.check_quota(request.user, subscription)
            if not can_query:
                return JsonResponse(
                    {
                        'error': message,
                        'code': 'QUOTA_EXCEEDED',
                        'usage': usage_info
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
                    model_used = 'unknown'
                    if hasattr(response, 'data') and isinstance(response.data, dict):
                        tokens = response.data.get('metadata', {}).get('tokens', 0)
                        model_used = response.data.get('metadata', {}).get('model_used', 'unknown')
                    
                    # Log usage using UsageService
                    UsageService.log_usage(
                        user=request.user,
                        action_type='query',
                        tokens_used=tokens,
                        subscription=request.subscription,
                        metadata={
                            'path': request.path,
                            'model': model_used
                        },
                        ip_address=self.get_client_ip(request),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    logger.info(f"Query logged for user {request.user.phone_number}: {tokens} tokens")
                    
                except Exception as e:
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
