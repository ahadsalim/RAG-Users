"""
سرویس‌های ارسال اعلان از طریق کانال‌های مختلف
"""
import requests
import logging
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.core.mail import EmailMultiAlternatives, send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import (
    Notification, NotificationTemplate, NotificationPreference,
    NotificationLog, NotificationChannel, DeviceToken
)

logger = logging.getLogger(__name__)


class NotificationService:
    """سرویس اصلی مدیریت اعلان‌ها"""
    
    @staticmethod
    def create_notification(
        user,
        template_code: str,
        context: Dict[str, Any],
        channels: Optional[List[str]] = None,
        priority: str = 'normal'
    ) -> Notification:
        """ایجاد و ارسال اعلان"""
        
        try:
            # دریافت قالب
            template = NotificationTemplate.objects.get(code=template_code, is_active=True)
        except NotificationTemplate.DoesNotExist:
            logger.error(f"Template not found: {template_code}")
            raise ValueError(f"قالب '{template_code}' یافت نشد")
        
        # رندر کردن محتوا
        rendered = template.render(context)
        
        # تعیین کانال‌ها
        if channels is None:
            channels = template.channels or ['in_app']
        
        # بررسی تنظیمات کاربر
        try:
            prefs = user.notification_preferences
        except NotificationPreference.DoesNotExist:
            prefs = NotificationPreference.objects.create(user=user)
        
        # فیلتر کانال‌ها بر اساس تنظیمات
        if not prefs.is_category_enabled(template.category):
            logger.info(f"Category {template.category} disabled for user {user.email}")
            channels = ['in_app']  # فقط in-app
        
        filtered_channels = [
            ch for ch in channels
            if prefs.is_channel_enabled(ch)
        ]
        
        # ایجاد اعلان
        notification = Notification.objects.create(
            user=user,
            template=template,
            title=rendered['title'],
            body=rendered['body'],
            category=template.category,
            priority=priority,
            action_url=rendered.get('action_url', ''),
            action_text=rendered.get('action_text', ''),
            channels=filtered_channels,
            metadata=context
        )
        
        # ارسال به کانال‌های مختلف
        if prefs.should_send_now():
            NotificationService._send_to_channels(notification, rendered, prefs)
        else:
            logger.info(f"Notification queued for later (quiet hours): {notification.id}")
        
        return notification
    
    @staticmethod
    def _send_to_channels(notification, rendered_content, preferences):
        """ارسال اعلان به کانال‌های مختلف"""
        
        channels = notification.channels
        
        # Email
        if 'email' in channels and preferences.email_enabled:
            EmailService.send(notification, rendered_content)
        
        # SMS
        if 'sms' in channels and preferences.sms_enabled:
            SMSService.send(notification, rendered_content)
        
        # Push Notification
        if 'push' in channels and preferences.push_enabled:
            PushService.send(notification, rendered_content)
        
        # WebSocket (Real-time)
        if 'websocket' in channels:
            WebSocketService.send(notification)
    
    @staticmethod
    def mark_all_as_read(user):
        """علامت‌گذاری همه اعلان‌ها به عنوان خوانده شده"""
        Notification.objects.filter(
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    
    @staticmethod
    def delete_old_notifications(days=30):
        """حذف اعلان‌های قدیمی"""
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted_count = Notification.objects.filter(
            created_at__lt=cutoff_date,
            is_read=True
        ).delete()[0]
        
        logger.info(f"Deleted {deleted_count} old notifications")
        return deleted_count


class EmailService:
    """سرویس ارسال ایمیل"""
    
    @staticmethod
    def send(notification: Notification, rendered_content: Dict[str, Any]) -> bool:
        """ارسال ایمیل"""
        
        user = notification.user
        
        # ایجاد لاگ
        log = NotificationLog.objects.create(
            notification=notification,
            channel=NotificationChannel.EMAIL,
            recipient=user.email,
            status='pending'
        )
        
        try:
            # موضوع
            subject = rendered_content.get('email_subject', notification.title)
            
            # متن HTML
            if 'email_html' in rendered_content:
                html_content = rendered_content['email_html']
            else:
                # استفاده از قالب پیش‌فرض
                html_content = render_to_string('notifications/email_base.html', {
                    'title': notification.title,
                    'body': notification.body,
                    'action_url': notification.action_url,
                    'action_text': notification.action_text,
                    'user': user
                })
            
            # متن plain
            text_content = strip_tags(html_content)
            
            # ارسال
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            
            # به‌روزرسانی وضعیت
            notification.sent_via_email = True
            notification.save(update_fields=['sent_via_email'])
            
            log.status = 'sent'
            log.sent_at = timezone.now()
            log.save()
            
            logger.info(f"Email sent to {user.email}: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {user.email}: {e}")
            
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            
            notification.error_log['email'] = str(e)
            notification.save(update_fields=['error_log'])
            
            return False


class SMSService:
    """سرویس ارسال پیامک"""
    
    # تنظیمات Kavenegar
    KAVENEGAR_API_KEY = getattr(settings, 'KAVENEGAR_API_KEY', '')
    KAVENEGAR_API_URL = 'https://api.kavenegar.com/v1/{}/sms/send.json'
    
    @staticmethod
    def send(notification: Notification, rendered_content: Dict[str, Any]) -> bool:
        """ارسال پیامک"""
        
        user = notification.user
        
        # بررسی شماره تلفن
        if not user.phone_number:
            logger.warning(f"No phone number for user {user.email}")
            return False
        
        # ایجاد لاگ
        log = NotificationLog.objects.create(
            notification=notification,
            channel=NotificationChannel.SMS,
            recipient=user.phone_number,
            status='pending'
        )
        
        try:
            # متن پیامک
            sms_text = rendered_content.get('sms_text', notification.body)
            
            # محدودیت 500 کاراکتر
            if len(sms_text) > 500:
                sms_text = sms_text[:497] + '...'
            
            # ارسال از طریق Kavenegar
            if SMSService.KAVENEGAR_API_KEY:
                result = SMSService._send_via_kavenegar(user.phone_number, sms_text)
            else:
                # برای تست
                result = {'success': True, 'messageid': 'test'}
            
            if result.get('success'):
                # به‌روزرسانی وضعیت
                notification.sent_via_sms = True
                notification.save(update_fields=['sent_via_sms'])
                
                log.status = 'sent'
                log.sent_at = timezone.now()
                log.provider_message_id = str(result.get('messageid', ''))
                log.provider_response = result
                log.save()
                
                logger.info(f"SMS sent to {user.phone_number}: {notification.title}")
                return True
            else:
                raise Exception(result.get('error', 'Unknown error'))
                
        except Exception as e:
            logger.error(f"Failed to send SMS to {user.phone_number}: {e}")
            
            log.status = 'failed'
            log.error_message = str(e)
            log.save()
            
            notification.error_log['sms'] = str(e)
            notification.save(update_fields=['error_log'])
            
            return False
    
    @staticmethod
    def _send_via_kavenegar(phone_number: str, message: str) -> Dict[str, Any]:
        """ارسال از طریق Kavenegar"""
        
        url = SMSService.KAVENEGAR_API_URL.format(SMSService.KAVENEGAR_API_KEY)
        
        data = {
            'receptor': phone_number,
            'message': message,
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            result = response.json()
            
            if result.get('return', {}).get('status') == 200:
                return {
                    'success': True,
                    'messageid': result['entries'][0]['messageid']
                }
            else:
                return {
                    'success': False,
                    'error': result.get('return', {}).get('message', 'Unknown error')
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class PushService:
    """سرویس ارسال Push Notification"""
    
    # تنظیمات Firebase
    FIREBASE_SERVER_KEY = getattr(settings, 'FIREBASE_SERVER_KEY', '')
    FCM_API_URL = 'https://fcm.googleapis.com/fcm/send'
    
    @staticmethod
    def send(notification: Notification, rendered_content: Dict[str, Any]) -> bool:
        """ارسال Push Notification"""
        
        user = notification.user
        
        # دریافت توکن‌های دستگاه
        device_tokens = DeviceToken.objects.filter(
            user=user,
            is_active=True
        )
        
        if not device_tokens.exists():
            logger.warning(f"No device tokens for user {user.email}")
            return False
        
        success_count = 0
        
        for device in device_tokens:
            log = NotificationLog.objects.create(
                notification=notification,
                channel=NotificationChannel.PUSH,
                recipient=device.token,
                status='pending'
            )
            
            try:
                # ارسال به Firebase
                if PushService.FIREBASE_SERVER_KEY:
                    result = PushService._send_via_firebase(
                        device.token,
                        notification.title,
                        notification.body,
                        notification.action_url
                    )
                else:
                    # برای تست
                    result = {'success': True}
                
                if result.get('success'):
                    success_count += 1
                    
                    log.status = 'sent'
                    log.sent_at = timezone.now()
                    log.provider_response = result
                    log.save()
                    
                    device.last_used_at = timezone.now()
                    device.save()
                else:
                    raise Exception(result.get('error', 'Unknown error'))
                    
            except Exception as e:
                logger.error(f"Failed to send push to {device.token}: {e}")
                
                log.status = 'failed'
                log.error_message = str(e)
                log.save()
        
        if success_count > 0:
            notification.sent_via_push = True
            notification.save(update_fields=['sent_via_push'])
            
            logger.info(f"Push sent to {success_count} devices for user {user.email}")
            return True
        
        return False
    
    @staticmethod
    def _send_via_firebase(token: str, title: str, body: str, action_url: str = '') -> Dict[str, Any]:
        """ارسال از طریق Firebase Cloud Messaging"""
        
        headers = {
            'Authorization': f'key={PushService.FIREBASE_SERVER_KEY}',
            'Content-Type': 'application/json',
        }
        
        payload = {
            'to': token,
            'notification': {
                'title': title,
                'body': body,
                'sound': 'default',
                'badge': 1,
            },
            'data': {
                'action_url': action_url,
            },
            'priority': 'high'
        }
        
        try:
            response = requests.post(
                PushService.FCM_API_URL,
                json=payload,
                headers=headers,
                timeout=10
            )
            result = response.json()
            
            if result.get('success', 0) > 0:
                return {'success': True, 'message_id': result.get('results', [{}])[0].get('message_id')}
            else:
                return {'success': False, 'error': result.get('results', [{}])[0].get('error', 'Unknown error')}
        except Exception as e:
            return {'success': False, 'error': str(e)}


class WebSocketService:
    """سرویس ارسال Real-time از طریق WebSocket"""
    
    @staticmethod
    def send(notification: Notification) -> bool:
        """ارسال اعلان Real-time"""
        
        try:
            channel_layer = get_channel_layer()
            
            # ارسال به کانال مخصوص کاربر
            async_to_sync(channel_layer.group_send)(
                f"user_{notification.user.id}",
                {
                    'type': 'notification_message',
                    'notification': {
                        'id': str(notification.id),
                        'title': notification.title,
                        'body': notification.body,
                        'category': notification.category,
                        'priority': notification.priority,
                        'action_url': notification.action_url,
                        'action_text': notification.action_text,
                        'created_at': notification.created_at.isoformat(),
                    }
                }
            )
            
            logger.info(f"WebSocket notification sent to user {notification.user.email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send WebSocket notification: {e}")
            return False


class NotificationScheduler:
    """زمان‌بندی و ارسال دسته‌جمعی اعلان‌ها"""
    
    @staticmethod
    def send_digest_notifications():
        """ارسال خلاصه اعلان‌های روزانه"""
        
        from datetime import timedelta
        
        # کاربرانی که خلاصه فعال دارند
        preferences = NotificationPreference.objects.filter(
            digest_enabled=True,
            email_enabled=True
        )
        
        for pref in preferences:
            try:
                # اعلان‌های 24 ساعت اخیر
                yesterday = timezone.now() - timedelta(days=1)
                unread_notifications = Notification.objects.filter(
                    user=pref.user,
                    is_read=False,
                    created_at__gte=yesterday
                ).order_by('-created_at')
                
                if unread_notifications.count() > 0:
                    NotificationScheduler._send_digest_email(pref.user, unread_notifications)
                    
            except Exception as e:
                logger.error(f"Failed to send digest for user {pref.user.email}: {e}")
    
    @staticmethod
    def _send_digest_email(user, notifications):
        """ارسال ایمیل خلاصه"""
        
        subject = f"خلاصه اعلان‌های شما - {notifications.count()} اعلان جدید"
        
        html_content = render_to_string('notifications/email_digest.html', {
            'user': user,
            'notifications': notifications,
            'count': notifications.count()
        })
        
        text_content = strip_tags(html_content)
        
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Digest email sent to {user.email} with {notifications.count()} notifications")
    
    @staticmethod
    def retry_failed_notifications(max_retries=3):
        """تلاش مجدد برای ارسال اعلان‌های ناموفق"""
        
        failed_logs = NotificationLog.objects.filter(
            status='failed',
            retry_count__lt=max_retries
        )
        
        for log in failed_logs:
            try:
                notification = log.notification
                
                # تلاش مجدد بر اساس کانال
                if log.channel == NotificationChannel.EMAIL:
                    EmailService.send(notification, {'email_subject': notification.title})
                elif log.channel == NotificationChannel.SMS:
                    SMSService.send(notification, {'sms_text': notification.body})
                elif log.channel == NotificationChannel.PUSH:
                    PushService.send(notification, {})
                
                log.retry_count += 1
                log.save()
                
            except Exception as e:
                logger.error(f"Retry failed for log {log.id}: {e}")
