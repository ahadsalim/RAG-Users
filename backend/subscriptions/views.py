from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta

from .models import Plan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from .usage import UsageService, UsageLog
from .auto_renewal import AutoRenewalService
from .reports import UsageReportService
from .notification_service import SubscriptionNotificationService


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """API endpoints for viewing subscription plans"""
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        """فیلتر کردن پلن‌ها بر اساس نوع کاربر"""
        queryset = Plan.objects.filter(is_active=True)
        
        # اگر کاربر لاگین کرده، فقط پلن‌های مناسب نوع کاربر را نمایش بده
        if self.request.user.is_authenticated:
            user_type = self.request.user.user_type
            queryset = queryset.filter(plan_type=user_type)
        
        return queryset.order_by('price')


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
        
        # Send subscription activated notification
        try:
            SubscriptionNotificationService.notify_subscription_activated(subscription)
        except Exception:
            pass
        
        return Response({'message': 'اشتراک فعال شد'})
    
    @action(detail=True, methods=['post'])
    def enable_auto_renewal(self, request, pk=None):
        """Enable auto-renewal for subscription"""
        subscription = self.get_object()
        AutoRenewalService.enable_auto_renewal(subscription)
        return Response({'message': 'تمدید خودکار فعال شد', 'auto_renew': True})
    
    @action(detail=True, methods=['post'])
    def disable_auto_renewal(self, request, pk=None):
        """Disable auto-renewal for subscription"""
        subscription = self.get_object()
        AutoRenewalService.disable_auto_renewal(subscription)
        return Response({'message': 'تمدید خودکار غیرفعال شد', 'auto_renew': False})
    
    @action(detail=True, methods=['get'])
    def renewal_status(self, request, pk=None):
        """Check renewal eligibility"""
        subscription = self.get_object()
        status_info = AutoRenewalService.check_renewal_eligibility(subscription)
        return Response(status_info)
    
    @action(detail=True, methods=['post'])
    def renew(self, request, pk=None):
        """Manually renew subscription"""
        subscription = self.get_object()
        
        if subscription.status != 'active' and subscription.end_date > timezone.now():
            return Response(
                {'error': 'این اشتراک قابل تمدید نیست'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success = AutoRenewalService.renew_subscription(subscription)
        
        if success:
            serializer = self.get_serializer(subscription)
            return Response({
                'message': 'اشتراک با موفقیت تمدید شد',
                'subscription': serializer.data
            })
        else:
            return Response(
                {'error': 'تمدید اشتراک ناموفق بود. لطفاً موجودی کیف پول را بررسی کنید.'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def usage(self, request):
        """Get current usage statistics"""
        user = request.user
        
        # دریافت اشتراک فعال
        subscription = user.subscriptions.filter(
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        # اگر اشتراک فعال نیست، اطلاعات پیش‌فرض برگردان
        if not subscription:
            # تلاش برای پیدا کردن آخرین اشتراک
            last_subscription = user.subscriptions.order_by('-created_at').first()
            
            return Response({
                'subscription': {
                    'plan': last_subscription.plan.name if last_subscription else 'بدون اشتراک',
                    'status': 'inactive',
                    'start_date': last_subscription.start_date if last_subscription else None,
                    'end_date': last_subscription.end_date if last_subscription else None,
                    'days_remaining': 0
                },
                'usage': {
                    'daily_used': 0,
                    'daily_limit': 0,
                    'daily_remaining': 0,
                    'monthly_used': 0,
                    'monthly_limit': 0,
                    'monthly_remaining': 0
                },
                'quota_percentage': {'daily': 0, 'monthly': 0},
                'can_query': False,
                'message': 'اشتراک فعالی ندارید',
                'stats': {},
                'user': {
                    'date_joined': user.date_joined
                }
            })
        
        # دریافت آمار مصرف
        can_query, message, usage_info = UsageService.check_quota(user, subscription)
        stats = UsageService.get_usage_stats(user, days=30)
        quota_percentage = UsageService.get_quota_percentage(user)
        
        return Response({
            'subscription': {
                'plan': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'days_remaining': (subscription.end_date - timezone.now()).days
            },
            'usage': usage_info,
            'quota_percentage': quota_percentage,
            'can_query': can_query,
            'message': message if not can_query else None,
            'stats': stats,
            'user': {
                'date_joined': user.date_joined
            }
        })


class UsageView(APIView):
    """API endpoint for current usage - direct path /usage/"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current usage statistics"""
        user = request.user
        
        # دریافت اشتراک فعال
        subscription = user.subscriptions.filter(
            status__in=['active', 'trial'],
            end_date__gt=timezone.now()
        ).first()
        
        # اگر اشتراک فعال نیست، اطلاعات پیش‌فرض برگردان
        if not subscription:
            last_subscription = user.subscriptions.order_by('-created_at').first()
            
            return Response({
                'subscription': {
                    'plan': last_subscription.plan.name if last_subscription else 'بدون اشتراک',
                    'status': 'inactive',
                    'start_date': last_subscription.start_date if last_subscription else None,
                    'end_date': last_subscription.end_date if last_subscription else None,
                    'days_remaining': 0
                },
                'usage': {
                    'daily_used': 0,
                    'daily_limit': 0,
                    'daily_remaining': 0,
                    'monthly_used': 0,
                    'monthly_limit': 0,
                    'monthly_remaining': 0
                },
                'quota_percentage': {'daily': 0, 'monthly': 0},
                'can_query': False,
                'message': 'اشتراک فعالی ندارید',
                'stats': {},
                'user': {
                    'date_joined': user.date_joined
                }
            })
        
        # دریافت آمار مصرف
        can_query, message, usage_info = UsageService.check_quota(user, subscription)
        stats = UsageService.get_usage_stats(user, days=30)
        quota_percentage = UsageService.get_quota_percentage(user)
        
        return Response({
            'subscription': {
                'plan': subscription.plan.name,
                'status': subscription.status,
                'start_date': subscription.start_date,
                'end_date': subscription.end_date,
                'days_remaining': (subscription.end_date - timezone.now()).days
            },
            'usage': usage_info,
            'quota_percentage': quota_percentage,
            'can_query': can_query,
            'message': message if not can_query else None,
            'stats': stats,
            'user': {
                'date_joined': user.date_joined
            }
        })


class UsageStatsView(APIView):
    """API endpoint for detailed usage statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get detailed usage statistics"""
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        # دریافت اشتراک فعال
        subscription = user.subscriptions.filter(
            status__in=['active', 'trial'],
            end_date__gt=timezone.now()
        ).first()
        
        # آمار کلی
        stats = UsageService.get_usage_stats(user, days=days)
        
        # آمار امروز
        today_queries = UsageService.get_daily_usage(user)
        today_tokens = UsageService.get_tokens_used_today(user)
        
        # آمار این ماه
        month_queries = UsageService.get_monthly_usage(user)
        month_tokens = UsageService.get_tokens_used_month(user)
        
        # درصد مصرف
        quota_percentage = UsageService.get_quota_percentage(user)
        
        # محدودیت‌ها از پلن
        if subscription and subscription.plan:
            features = subscription.plan.features or {}
            daily_limit = features.get('max_queries_per_day', subscription.plan.max_queries_per_day or 10)
            monthly_limit = features.get('max_queries_per_month', subscription.plan.max_queries_per_month or 200)
        else:
            daily_limit = 10
            monthly_limit = 200
        
        return Response({
            'today': {
                'queries': today_queries,
                'tokens': today_tokens
            },
            'month': {
                'queries': month_queries,
                'tokens': month_tokens
            },
            'quota_percentage': quota_percentage,
            'period_stats': stats,
            'subscription': {
                'plan': subscription.plan.name if subscription else 'رایگان',
                'status': subscription.status if subscription else 'active',
                'start_date': subscription.start_date if subscription else None,
                'end_date': subscription.end_date if subscription else None,
                'days_remaining': (subscription.end_date - timezone.now()).days if subscription else 0
            },
            'usage': {
                'daily_used': today_queries,
                'daily_limit': daily_limit,
                'daily_remaining': max(0, daily_limit - today_queries),
                'monthly_used': month_queries,
                'monthly_limit': monthly_limit,
                'monthly_remaining': max(0, monthly_limit - month_queries)
            },
            'stats': {
                'total_queries': stats.get('total_queries', 0),
                'total_tokens': stats.get('total_tokens', 0)
            },
            'user': {
                'date_joined': user.date_joined
            }
        })


class UsageReportView(APIView):
    """API endpoint for usage reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get usage report"""
        user = request.user
        report_type = request.query_params.get('type', 'daily')
        
        if report_type == 'daily':
            date_str = request.query_params.get('date')
            if date_str:
                from datetime import datetime
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date = None
            report = UsageReportService.get_user_daily_report(user, date)
            
        elif report_type == 'monthly':
            year = request.query_params.get('year')
            month = request.query_params.get('month')
            year = int(year) if year else None
            month = int(month) if month else None
            report = UsageReportService.get_user_monthly_report(user, year, month)
            
        elif report_type == 'period':
            from datetime import datetime
            start_str = request.query_params.get('start_date')
            end_str = request.query_params.get('end_date')
            
            if not start_str or not end_str:
                return Response(
                    {'error': 'start_date و end_date الزامی است'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
            report = UsageReportService.get_user_period_report(user, start_date, end_date)
            
        elif report_type == 'subscription':
            subscription = user.subscriptions.filter(
                status='active',
                end_date__gt=timezone.now()
            ).first()
            
            if not subscription:
                return Response(
                    {'error': 'اشتراک فعالی ندارید'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            report = UsageReportService.get_subscription_usage_report(subscription)
        else:
            return Response(
                {'error': 'نوع گزارش نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(report)


class UsageReportExportView(APIView):
    """API endpoint for exporting usage reports"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Export usage report as CSV"""
        from datetime import datetime
        from django.http import HttpResponse
        
        user = request.user
        start_str = request.query_params.get('start_date')
        end_str = request.query_params.get('end_date')
        
        if not start_str or not end_str:
            # پیش‌فرض: 30 روز اخیر
            end_date = timezone.now().date()
            start_date = end_date - timedelta(days=30)
        else:
            start_date = datetime.strptime(start_str, '%Y-%m-%d').date()
            end_date = datetime.strptime(end_str, '%Y-%m-%d').date()
        
        csv_content = UsageReportService.export_user_report_csv(user, start_date, end_date)
        
        response = HttpResponse(csv_content, content_type='text/csv; charset=utf-8')
        response['Content-Disposition'] = f'attachment; filename="usage_report_{start_date}_{end_date}.csv"'
        
        return response


class AdminReportView(APIView):
    """API endpoint for admin reports"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        """Get admin overview report"""
        days = int(request.query_params.get('days', 30))
        report = UsageReportService.get_admin_overview_report(days)
        return Response(report)
