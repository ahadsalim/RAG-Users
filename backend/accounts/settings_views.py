from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.exceptions import ValidationError
import json


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """
    GET: دریافت تنظیمات کاربر
    POST: بروزرسانی تنظیمات کاربر
    """
    user = request.user
    
    if request.method == 'GET':
        # برگرداندن تنظیمات فعلی
        return Response({
            'preferences': user.preferences or {},
        })
    
    elif request.method == 'POST':
        # بروزرسانی تنظیمات
        try:
            preferences = request.data.get('preferences', {})
            
            # اعتبارسنجی
            if not isinstance(preferences, dict):
                return Response(
                    {'error': 'preferences باید یک object باشد'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # ذخیره تنظیمات
            user.preferences = preferences
            user.save(update_fields=['preferences'])
            
            return Response({
                'message': 'تنظیمات با موفقیت ذخیره شد',
                'preferences': user.preferences,
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
