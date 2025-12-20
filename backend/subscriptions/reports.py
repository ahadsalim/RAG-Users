"""
سرویس گزارش‌گیری مصرف
"""
import logging
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.db.models.functions import TruncDate, TruncHour, TruncMonth
from datetime import timedelta
from decimal import Decimal

logger = logging.getLogger(__name__)


class UsageReportService:
    """سرویس گزارش‌گیری مصرف"""
    
    @staticmethod
    def get_user_daily_report(user, date=None) -> dict:
        """گزارش روزانه کاربر"""
        from .usage import UsageLog
        
        if date is None:
            date = timezone.now().date()
        
        logs = UsageLog.objects.filter(
            user=user,
            created_at__date=date
        )
        
        # آمار کلی
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # توزیع ساعتی
        hourly_stats = logs.filter(action_type='query').annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('hour')
        
        # مدل‌های استفاده شده
        models_used = logs.filter(action_type='query').values(
            'metadata__model'
        ).annotate(count=Count('id')).order_by('-count')
        
        return {
            'date': str(date),
            'total_queries': total_queries,
            'total_tokens': total_tokens,
            'hourly_stats': list(hourly_stats),
            'models_used': list(models_used),
        }
    
    @staticmethod
    def get_user_monthly_report(user, year=None, month=None) -> dict:
        """گزارش ماهانه کاربر"""
        from .usage import UsageLog
        
        now = timezone.now()
        if year is None:
            year = now.year
        if month is None:
            month = now.month
        
        logs = UsageLog.objects.filter(
            user=user,
            created_at__year=year,
            created_at__month=month
        )
        
        # آمار کلی
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # توزیع روزانه
        daily_stats = logs.filter(action_type='query').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('date')
        
        # میانگین روزانه
        days_in_month = len(set(log['date'] for log in daily_stats))
        avg_daily_queries = total_queries / days_in_month if days_in_month > 0 else 0
        avg_daily_tokens = total_tokens / days_in_month if days_in_month > 0 else 0
        
        # مدل‌های استفاده شده
        models_used = logs.filter(action_type='query').values(
            'metadata__model'
        ).annotate(count=Count('id')).order_by('-count')
        
        return {
            'year': year,
            'month': month,
            'total_queries': total_queries,
            'total_tokens': total_tokens,
            'avg_daily_queries': round(avg_daily_queries, 1),
            'avg_daily_tokens': round(avg_daily_tokens, 1),
            'active_days': days_in_month,
            'daily_stats': list(daily_stats),
            'models_used': list(models_used),
        }
    
    @staticmethod
    def get_user_period_report(user, start_date, end_date) -> dict:
        """گزارش دوره‌ای کاربر"""
        from .usage import UsageLog
        
        logs = UsageLog.objects.filter(
            user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        )
        
        # آمار کلی
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # توزیع روزانه
        daily_stats = logs.filter(action_type='query').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used')
        ).order_by('date')
        
        # تعداد روزهای فعال
        active_days = len(set(log['date'] for log in daily_stats))
        total_days = (end_date - start_date).days + 1
        
        return {
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_days': total_days,
            'active_days': active_days,
            'total_queries': total_queries,
            'total_tokens': total_tokens,
            'avg_daily_queries': round(total_queries / total_days, 1) if total_days > 0 else 0,
            'daily_stats': list(daily_stats),
        }
    
    @staticmethod
    def get_subscription_usage_report(subscription) -> dict:
        """گزارش مصرف یک اشتراک"""
        from .usage import UsageLog
        
        user = subscription.user
        start_date = subscription.start_date
        end_date = subscription.end_date or timezone.now()
        
        logs = UsageLog.objects.filter(
            user=user,
            subscription=subscription
        )
        
        # آمار کلی
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # محدودیت‌های پلن
        features = subscription.plan.features or {}
        max_daily = features.get('max_queries_per_day', 10)
        max_monthly = features.get('max_queries_per_month', subscription.plan.max_queries_per_month or 200)
        
        # درصد مصرف
        from .usage import UsageService
        daily_used = UsageService.get_daily_usage(user)
        monthly_used = UsageService.get_monthly_usage(user)
        
        return {
            'subscription_id': str(subscription.id),
            'plan_name': subscription.plan.name,
            'start_date': str(start_date.date()) if start_date else None,
            'end_date': str(end_date.date()) if end_date else None,
            'total_queries': total_queries,
            'total_tokens': total_tokens,
            'limits': {
                'daily': max_daily,
                'monthly': max_monthly,
            },
            'current_usage': {
                'daily': daily_used,
                'monthly': monthly_used,
            },
            'percentage': {
                'daily': min(100, int((daily_used / max_daily) * 100)) if max_daily > 0 else 0,
                'monthly': min(100, int((monthly_used / max_monthly) * 100)) if max_monthly > 0 else 0,
            }
        }
    
    @staticmethod
    def get_admin_overview_report(days: int = 30) -> dict:
        """گزارش کلی برای ادمین"""
        from .usage import UsageLog
        from .models import Subscription
        from accounts.models import User
        
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار کاربران
        total_users = User.objects.count()
        active_users = UsageLog.objects.filter(
            created_at__gte=start_date
        ).values('user').distinct().count()
        
        # آمار اشتراک‌ها
        total_subscriptions = Subscription.objects.count()
        active_subscriptions = Subscription.objects.filter(
            status='active',
            end_date__gt=timezone.now()
        ).count()
        
        # آمار مصرف
        logs = UsageLog.objects.filter(created_at__gte=start_date)
        total_queries = logs.filter(action_type='query').count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        
        # توزیع روزانه
        daily_stats = logs.filter(action_type='query').annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id'),
            tokens=Sum('tokens_used'),
            users=Count('user', distinct=True)
        ).order_by('date')
        
        # پرمصرف‌ترین کاربران
        top_users = logs.filter(action_type='query').values(
            'user__phone_number', 'user__email'
        ).annotate(
            query_count=Count('id'),
            token_count=Sum('tokens_used')
        ).order_by('-query_count')[:10]
        
        # توزیع پلن‌ها
        plan_distribution = Subscription.objects.filter(
            status='active'
        ).values('plan__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        return {
            'period_days': days,
            'users': {
                'total': total_users,
                'active': active_users,
            },
            'subscriptions': {
                'total': total_subscriptions,
                'active': active_subscriptions,
            },
            'usage': {
                'total_queries': total_queries,
                'total_tokens': total_tokens,
                'avg_daily_queries': round(total_queries / days, 1) if days > 0 else 0,
            },
            'daily_stats': list(daily_stats),
            'top_users': list(top_users),
            'plan_distribution': list(plan_distribution),
        }
    
    @staticmethod
    def export_user_report_csv(user, start_date, end_date) -> str:
        """خروجی CSV گزارش کاربر"""
        import csv
        from io import StringIO
        from .usage import UsageLog
        
        logs = UsageLog.objects.filter(
            user=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).order_by('created_at')
        
        output = StringIO()
        writer = csv.writer(output)
        
        # Header
        writer.writerow([
            'تاریخ', 'ساعت', 'نوع عملیات', 'توکن مصرفی', 'مدل', 'IP'
        ])
        
        # Data
        for log in logs:
            writer.writerow([
                log.created_at.strftime('%Y-%m-%d'),
                log.created_at.strftime('%H:%M:%S'),
                log.get_action_type_display(),
                log.tokens_used,
                log.metadata.get('model', '-'),
                log.ip_address or '-',
            ])
        
        return output.getvalue()
