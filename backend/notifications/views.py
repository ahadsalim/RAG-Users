from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count, Q
from datetime import timedelta
import logging

from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    DeviceToken, NotificationLog
)
from .serializers import (
    NotificationSerializer, NotificationDetailSerializer,
    NotificationTemplateSerializer, NotificationPreferenceSerializer,
    DeviceTokenSerializer, RegisterDeviceSerializer,
    SendNotificationSerializer, NotificationStatsSerializer,
    MarkAsReadSerializer
)
from .services import NotificationService

logger = logging.getLogger(__name__)


class NotificationViewSet(viewsets.ModelViewSet):
    """مدیریت اعلان‌های کاربر"""
    
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر اعلان‌ها بر اساس کاربر جاری"""
        user = self.request.user
        queryset = Notification.objects.filter(user=user)
        
        # فیلترها
        category = self.request.query_params.get('category')
        is_read = self.request.query_params.get('is_read')
        priority = self.request.query_params.get('priority')
        
        if category:
            queryset = queryset.filter(category=category)
        
        if is_read is not None:
            is_read_bool = is_read.lower() == 'true'
            queryset = queryset.filter(is_read=is_read_bool)
        
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return NotificationDetailSerializer
        return NotificationSerializer
    
    def retrieve(self, request, *args, **kwargs):
        """دریافت جزئیات اعلان و علامت‌گذاری به عنوان خوانده شده"""
        instance = self.get_object()
        
        # علامت‌گذاری به عنوان خوانده شده
        if not instance.is_read:
            instance.mark_as_read()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        """تعداد اعلان‌های خوانده نشده"""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        
        return Response({'count': count})
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """آمار اعلان‌ها"""
        user = request.user
        
        # کل و خوانده نشده
        total = Notification.objects.filter(user=user).count()
        unread = Notification.objects.filter(user=user, is_read=False).count()
        
        # بر اساس دسته
        by_category = {}
        categories = Notification.objects.filter(user=user).values('category').annotate(
            count=Count('id')
        )
        for cat in categories:
            by_category[cat['category']] = cat['count']
        
        # بر اساس اولویت
        by_priority = {}
        priorities = Notification.objects.filter(user=user).values('priority').annotate(
            count=Count('id')
        )
        for pri in priorities:
            by_priority[pri['priority']] = pri['count']
        
        # اعلان‌های اخیر
        recent = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        recent_serializer = NotificationSerializer(recent, many=True)
        
        data = {
            'total': total,
            'unread': unread,
            'by_category': by_category,
            'by_priority': by_priority,
            'recent': recent_serializer.data
        }
        
        return Response(data)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """علامت‌گذاری به عنوان خوانده شده"""
        notification = self.get_object()
        notification.mark_as_read()
        
        return Response({'message': 'اعلان به عنوان خوانده شده علامت‌گذاری شد'})
    
    @action(detail=False, methods=['post'])
    def mark_multiple_as_read(self, request):
        """علامت‌گذاری چند اعلان به عنوان خوانده شده"""
        serializer = MarkAsReadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        if data.get('mark_all'):
            # علامت‌گذاری همه
            NotificationService.mark_all_as_read(request.user)
            return Response({'message': 'همه اعلان‌ها به عنوان خوانده شده علامت‌گذاری شدند'})
        
        # علامت‌گذاری لیست مشخص
        notification_ids = data.get('notification_ids', [])
        if notification_ids:
            Notification.objects.filter(
                id__in=notification_ids,
                user=request.user
            ).update(is_read=True, read_at=timezone.now())
            
            return Response({
                'message': f'{len(notification_ids)} اعلان به عنوان خوانده شده علامت‌گذاری شدند'
            })
        
        return Response(
            {'error': 'هیچ اعلانی مشخص نشده است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """تایید اعلان"""
        notification = self.get_object()
        notification.mark_as_confirmed()
        
        return Response({'message': 'اعلان تایید شد'})
    
    @action(detail=False, methods=['delete'])
    def delete_read(self, request):
        """حذف اعلان‌های خوانده شده"""
        deleted_count = Notification.objects.filter(
            user=request.user,
            is_read=True
        ).delete()[0]
        
        return Response({
            'message': f'{deleted_count} اعلان حذف شد',
            'count': deleted_count
        })


class NotificationPreferenceView(APIView):
    """مدیریت تنظیمات اعلان‌رسانی"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """دریافت تنظیمات"""
        try:
            preferences = request.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=request.user)
        
        serializer = NotificationPreferenceSerializer(preferences)
        return Response(serializer.data)
    
    def put(self, request):
        """به‌روزرسانی تنظیمات"""
        try:
            preferences = request.user.notification_preferences
        except NotificationPreference.DoesNotExist:
            preferences = NotificationPreference.objects.create(user=request.user)
        
        serializer = NotificationPreferenceSerializer(
            preferences,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data)
    
    def patch(self, request):
        """به‌روزرسانی جزئی تنظیمات"""
        return self.put(request)


class DeviceTokenViewSet(viewsets.ModelViewSet):
    """مدیریت توکن‌های دستگاه"""
    
    serializer_class = DeviceTokenSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر توکن‌ها بر اساس کاربر"""
        return DeviceToken.objects.filter(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        """ثبت توکن دستگاه جدید"""
        serializer = RegisterDeviceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # بررسی وجود توکن
        device, created = DeviceToken.objects.update_or_create(
            user=request.user,
            token=data['token'],
            defaults={
                'device_type': data['device_type'],
                'device_name': data.get('device_name', ''),
                'is_active': True,
                'last_used_at': timezone.now()
            }
        )
        
        response_serializer = DeviceTokenSerializer(device)
        
        return Response({
            'message': 'دستگاه با موفقیت ثبت شد' if created else 'دستگاه به‌روزرسانی شد',
            'device': response_serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        """غیرفعال کردن توکن"""
        device = self.get_object()
        device.is_active = False
        device.save()
        
        return Response({'message': 'توکن غیرفعال شد'})


class SendNotificationView(APIView):
    """ارسال اعلان (برای استفاده داخلی یا توسط ادمین)"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """ارسال اعلان به کاربر جاری"""
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        try:
            notification = NotificationService.create_notification(
                user=request.user,
                template_code=data['template_code'],
                context=data['context'],
                channels=data.get('channels'),
                priority=data.get('priority', 'normal')
            )
            
            response_serializer = NotificationDetailSerializer(notification)
            
            return Response({
                'message': 'اعلان با موفقیت ارسال شد',
                'notification': response_serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return Response(
                {'error': 'خطا در ارسال اعلان'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class NotificationTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """مشاهده قالب‌های اعلان (فقط خواندنی برای کاربران)"""
    
    queryset = NotificationTemplate.objects.filter(is_active=True)
    serializer_class = NotificationTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """فیلتر قالب‌ها"""
        queryset = super().get_queryset()
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset.order_by('category', 'name')


class TestNotificationView(APIView):
    """ارسال اعلان تستی (فقط در حالت DEBUG)"""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """ارسال اعلان تستی"""
        
        from django.conf import settings
        if not settings.DEBUG:
            return Response(
                {'error': 'این endpoint فقط در حالت DEBUG فعال است'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        channel = request.data.get('channel', 'in_app')
        
        try:
            # ایجاد اعلان تستی
            notification = Notification.objects.create(
                user=request.user,
                title='اعلان تستی',
                body='این یک اعلان تستی است',
                category='system',
                priority='normal',
                channels=[channel]
            )
            
            # ارسال
            if channel == 'email':
                from .services import EmailService
                EmailService.send(notification, {'email_subject': 'تست ایمیل'})
            elif channel == 'sms':
                from .services import SMSService
                SMSService.send(notification, {'sms_text': 'تست پیامک'})
            elif channel == 'push':
                from .services import PushService
                PushService.send(notification, {})
            elif channel == 'websocket':
                from .services import WebSocketService
                WebSocketService.send(notification)
            
            return Response({
                'message': f'اعلان تستی از طریق {channel} ارسال شد',
                'notification_id': str(notification.id)
            })
            
        except Exception as e:
            logger.error(f"Test notification failed: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
