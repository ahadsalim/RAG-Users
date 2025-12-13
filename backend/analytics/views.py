from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from datetime import datetime, timedelta, date
from decimal import Decimal
import logging

from .models import (
    DailyMetric, UserAnalytics, RevenueAnalytics,
    SystemMetrics, MetricType
)
from .serializers import (
    DailyMetricSerializer, UserAnalyticsSerializer,
    RevenueAnalyticsSerializer, SystemMetricsSerializer,
    DashboardSummarySerializer, ChartDataSerializer
)
from admin_panel.permissions import IsAdminUser, HasAdminPermission

logger = logging.getLogger(__name__)


class DashboardSummaryView(APIView):
    """خلاصه داشبورد"""
    
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('view_analytics')]
    
    def get(self, request):
        """دریافت خلاصه آمار داشبورد"""
        
        # بازه زمانی
        period = request.query_params.get('period', '30')  # روز
        try:
            days = int(period)
        except:
            days = 30
        
        start_date = timezone.now() - timedelta(days=days)
        
        # آمار کاربران
        from accounts.models import User
        total_users = User.objects.filter(is_active=True).count()
        new_users = User.objects.filter(date_joined__gte=start_date).count()
        active_users = User.objects.filter(last_login__gte=start_date).count()
        
        # آمار مالی
        from payments.models import Transaction, PaymentStatus
        transactions = Transaction.objects.filter(created_at__gte=start_date)
        total_revenue = transactions.filter(
            status=PaymentStatus.SUCCESS
        ).aggregate(total=Sum('amount'))['total'] or 0
        
        # آمار چت
        from chat.models import Message
        total_messages = Message.objects.filter(created_at__gte=start_date).count()
        total_tokens = Message.objects.filter(
            created_at__gte=start_date
        ).aggregate(total=Sum('tokens'))['total'] or 0
        
        # آمار اشتراک
        from subscriptions.models import Subscription
        active_subscriptions = Subscription.objects.filter(
            status='active',
            end_date__gte=timezone.now().date()
        ).count()
        
        # محاسبه رشد
        def calculate_growth(current, previous_start):
            previous = User.objects.filter(
                date_joined__gte=previous_start,
                date_joined__lt=start_date
            ).count()
            if previous > 0:
                return ((current - previous) / previous) * 100
            return 100 if current > 0 else 0
        
        previous_start = start_date - timedelta(days=days)
        user_growth = calculate_growth(new_users, previous_start)
        
        # آمار سیستم
        latest_metrics = SystemMetrics.objects.order_by('-timestamp').first()
        
        data = {
            'period_days': days,
            'users': {
                'total': total_users,
                'new': new_users,
                'active': active_users,
                'growth': round(user_growth, 2)
            },
            'revenue': {
                'total': float(total_revenue),
                'transactions': transactions.count(),
                'successful': transactions.filter(status=PaymentStatus.SUCCESS).count(),
                'conversion_rate': self._calculate_conversion_rate(transactions)
            },
            'usage': {
                'messages': total_messages,
                'tokens': total_tokens,
                'avg_tokens_per_message': total_tokens / total_messages if total_messages > 0 else 0
            },
            'subscriptions': {
                'active': active_subscriptions,
                'trial': Subscription.objects.filter(status='trial').count(),
                'expired': Subscription.objects.filter(status='expired').count()
            },
            'system': {
                'cpu_usage': float(latest_metrics.cpu_usage) if latest_metrics else 0,
                'memory_usage': float(latest_metrics.memory_usage) if latest_metrics else 0,
                'disk_usage': float(latest_metrics.disk_usage) if latest_metrics else 0,
                'active_connections': latest_metrics.active_connections if latest_metrics else 0
            }
        }
        
        return Response(data)
    
    def _calculate_conversion_rate(self, transactions):
        """محاسبه نرخ تبدیل"""
        from payments.models import PaymentStatus
        
        total = transactions.count()
        if total == 0:
            return 0
        
        successful = transactions.filter(status=PaymentStatus.SUCCESS).count()
        return round((successful / total) * 100, 2)


class ChartDataView(APIView):
    """داده‌های نمودار"""
    
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('view_analytics')]
    
    def get(self, request):
        """دریافت داده‌های نمودار"""
        
        chart_type = request.query_params.get('type', 'revenue')
        period = request.query_params.get('period', '30')
        
        try:
            days = int(period)
        except:
            days = 30
        
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        if chart_type == 'revenue':
            data = self._get_revenue_chart(start_date, end_date)
        elif chart_type == 'users':
            data = self._get_users_chart(start_date, end_date)
        elif chart_type == 'usage':
            data = self._get_usage_chart(start_date, end_date)
        elif chart_type == 'subscriptions':
            data = self._get_subscriptions_chart(start_date, end_date)
        else:
            return Response(
                {'error': 'نوع نمودار نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response(data)
    
    def _get_revenue_chart(self, start_date, end_date):
        """نمودار درآمد"""
        from payments.models import Transaction, PaymentStatus
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            daily_revenue = Transaction.objects.filter(
                created_at__date=current_date,
                status=PaymentStatus.SUCCESS
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'value': float(daily_revenue),
                'label': f'{daily_revenue:,.0f} تومان'
            })
            
            current_date += timedelta(days=1)
        
        return {
            'type': 'line',
            'title': 'درآمد روزانه',
            'data': data,
            'total': sum(d['value'] for d in data)
        }
    
    def _get_users_chart(self, start_date, end_date):
        """نمودار کاربران"""
        from accounts.models import User
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            new_users = User.objects.filter(
                date_joined__date=current_date
            ).count()
            
            active_users = User.objects.filter(
                last_login__date=current_date
            ).count()
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'new': new_users,
                'active': active_users
            })
            
            current_date += timedelta(days=1)
        
        return {
            'type': 'bar',
            'title': 'کاربران',
            'data': data,
            'series': ['new', 'active'],
            'labels': ['کاربران جدید', 'کاربران فعال']
        }
    
    def _get_usage_chart(self, start_date, end_date):
        """نمودار مصرف"""
        from chat.models import Message
        
        data = []
        current_date = start_date
        
        while current_date <= end_date:
            messages = Message.objects.filter(
                created_at__date=current_date,
                role='user'
            ).count()
            
            tokens = Message.objects.filter(
                created_at__date=current_date
            ).aggregate(total=Sum('tokens'))['total'] or 0
            
            data.append({
                'date': current_date.strftime('%Y-%m-%d'),
                'messages': messages,
                'tokens': tokens
            })
            
            current_date += timedelta(days=1)
        
        return {
            'type': 'area',
            'title': 'مصرف سیستم',
            'data': data,
            'series': ['messages', 'tokens'],
            'labels': ['پیام‌ها', 'توکن‌ها']
        }
    
    def _get_subscriptions_chart(self, start_date, end_date):
        """نمودار اشتراک‌ها"""
        from subscriptions.models import Subscription, Plan
        
        # تعداد اشتراک‌ها بر اساس پلن
        plans = Plan.objects.filter(is_active=True)
        data = []
        
        for plan in plans:
            count = Subscription.objects.filter(
                plan=plan,
                status__in=['active', 'trial'],
                created_at__date__gte=start_date,
                created_at__date__lte=end_date
            ).count()
            
            data.append({
                'name': plan.name,
                'value': count,
                'color': plan.badge_color or '#4CAF50'
            })
        
        return {
            'type': 'pie',
            'title': 'توزیع اشتراک‌ها',
            'data': data
        }


class UserAnalyticsViewSet(viewsets.ModelViewSet):
    """مدیریت تحلیل کاربران"""
    
    queryset = UserAnalytics.objects.all()
    serializer_class = UserAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('view_analytics')]
    
    @action(detail=False, methods=['get'])
    def top_users(self, request):
        """کاربران برتر"""
        
        metric = request.query_params.get('metric', 'queries')  # queries, tokens, spent, engagement
        limit = int(request.query_params.get('limit', 10))
        
        if metric == 'queries':
            users = UserAnalytics.objects.order_by('-total_queries')[:limit]
        elif metric == 'tokens':
            users = UserAnalytics.objects.order_by('-total_tokens')[:limit]
        elif metric == 'spent':
            users = UserAnalytics.objects.order_by('-total_spent')[:limit]
        elif metric == 'engagement':
            users = UserAnalytics.objects.order_by('-engagement_score')[:limit]
        else:
            users = UserAnalytics.objects.order_by('-total_queries')[:limit]
        
        serializer = self.get_serializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def user_segments(self, request):
        """بخش‌بندی کاربران"""
        
        # کاربران فعال، غیرفعال، جدید، VIP
        segments = {
            'active': UserAnalytics.objects.filter(
                last_query_at__gte=timezone.now() - timedelta(days=7)
            ).count(),
            'inactive': UserAnalytics.objects.filter(
                Q(last_query_at__lt=timezone.now() - timedelta(days=30)) |
                Q(last_query_at__isnull=True)
            ).count(),
            'new': UserAnalytics.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=30)
            ).count(),
            'vip': UserAnalytics.objects.filter(
                value_score__gte=80
            ).count(),
            'at_risk': UserAnalytics.objects.filter(
                engagement_score__lt=30,
                last_query_at__lt=timezone.now() - timedelta(days=14)
            ).count()
        }
        
        return Response(segments)


class RevenueAnalyticsViewSet(viewsets.ModelViewSet):
    """مدیریت تحلیل درآمد"""
    
    queryset = RevenueAnalytics.objects.all()
    serializer_class = RevenueAnalyticsSerializer
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('view_financial')]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """خلاصه درآمد"""
        
        period = request.query_params.get('period', 'monthly')
        
        # دوره جاری
        if period == 'daily':
            start_date = timezone.now().date()
            end_date = start_date
        elif period == 'weekly':
            start_date = timezone.now().date() - timedelta(days=timezone.now().weekday())
            end_date = start_date + timedelta(days=6)
        elif period == 'monthly':
            start_date = timezone.now().replace(day=1).date()
            if start_date.month == 12:
                end_date = start_date.replace(year=start_date.year + 1, month=1)
            else:
                end_date = start_date.replace(month=start_date.month + 1)
            end_date -= timedelta(days=1)
        else:
            start_date = timezone.now().date() - timedelta(days=30)
            end_date = timezone.now().date()
        
        # محاسبه آمار
        analytics = RevenueAnalytics.calculate_for_period(period, start_date, end_date)
        serializer = self.get_serializer(analytics)
        
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def comparison(self, request):
        """مقایسه درآمد"""
        
        # مقایسه با دوره قبل
        current = RevenueAnalytics.objects.filter(
            period_type='monthly',
            period_start=timezone.now().replace(day=1).date()
        ).first()
        
        previous_date = (timezone.now().replace(day=1) - timedelta(days=1)).replace(day=1).date()
        previous = RevenueAnalytics.objects.filter(
            period_type='monthly',
            period_start=previous_date
        ).first()
        
        if not current or not previous:
            return Response({
                'error': 'داده کافی برای مقایسه وجود ندارد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # محاسبه تغییرات
        revenue_change = 0
        if previous.total_revenue > 0:
            revenue_change = ((current.total_revenue - previous.total_revenue) / 
                            previous.total_revenue * 100)
        
        data = {
            'current': {
                'period': f"{current.period_start} - {current.period_end}",
                'revenue': float(current.total_revenue),
                'transactions': current.total_transactions,
                'conversion_rate': float(current.conversion_rate)
            },
            'previous': {
                'period': f"{previous.period_start} - {previous.period_end}",
                'revenue': float(previous.total_revenue),
                'transactions': previous.total_transactions,
                'conversion_rate': float(previous.conversion_rate)
            },
            'changes': {
                'revenue': round(revenue_change, 2),
                'transactions': current.total_transactions - previous.total_transactions,
                'conversion_rate': float(current.conversion_rate - previous.conversion_rate)
            }
        }
        
        return Response(data)


class SystemMetricsViewSet(viewsets.ModelViewSet):
    """مدیریت متریک‌های سیستم"""
    
    queryset = SystemMetrics.objects.all()
    serializer_class = SystemMetricsSerializer
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('view_analytics')]
    
    @action(detail=False, methods=['get'])
    def realtime(self, request):
        """متریک‌های بلادرنگ"""
        
        # آخرین متریک‌ها
        latest = SystemMetrics.objects.order_by('-timestamp').first()
        
        if not latest:
            return Response({
                'error': 'متریکی یافت نشد'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # متریک‌های 5 دقیقه اخیر برای نمودار
        recent = SystemMetrics.objects.filter(
            timestamp__gte=timezone.now() - timedelta(minutes=5)
        ).order_by('timestamp')
        
        data = {
            'current': self.get_serializer(latest).data,
            'history': self.get_serializer(recent, many=True).data,
            'alerts': self._check_alerts(latest)
        }
        
        return Response(data)
    
    def _check_alerts(self, metrics):
        """بررسی هشدارها"""
        alerts = []
        
        if metrics.cpu_usage > 80:
            alerts.append({
                'type': 'critical' if metrics.cpu_usage > 90 else 'warning',
                'message': f'مصرف CPU بالا: {metrics.cpu_usage}%'
            })
        
        if metrics.memory_usage > 80:
            alerts.append({
                'type': 'critical' if metrics.memory_usage > 90 else 'warning',
                'message': f'مصرف RAM بالا: {metrics.memory_usage}%'
            })
        
        if metrics.disk_usage > 80:
            alerts.append({
                'type': 'critical' if metrics.disk_usage > 90 else 'warning',
                'message': f'فضای دیسک کم: {metrics.disk_usage}% استفاده شده'
            })
        
        if metrics.error_rate > 5:
            alerts.append({
                'type': 'warning',
                'message': f'نرخ خطا بالا: {metrics.error_rate}%'
            })
        
        return alerts


class MetricsExportView(APIView):
    """خروجی گرفتن از متریک‌ها"""
    
    permission_classes = [permissions.IsAuthenticated, HasAdminPermission('export_data')]
    
    def post(self, request):
        """تولید گزارش"""
        
        report_type = request.data.get('type', 'summary')
        format = request.data.get('format', 'json')  # json, csv, pdf
        start_date = request.data.get('start_date')
        end_date = request.data.get('end_date')
        
        # اعتبارسنجی تاریخ‌ها
        try:
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            else:
                start_date = timezone.now().date() - timedelta(days=30)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            else:
                end_date = timezone.now().date()
        except ValueError:
            return Response(
                {'error': 'فرمت تاریخ نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تولید گزارش
        if report_type == 'summary':
            data = self._generate_summary_report(start_date, end_date)
        elif report_type == 'users':
            data = self._generate_users_report(start_date, end_date)
        elif report_type == 'revenue':
            data = self._generate_revenue_report(start_date, end_date)
        else:
            return Response(
                {'error': 'نوع گزارش نامعتبر است'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # تبدیل فرمت
        if format == 'csv':
            import csv
            import io
            from django.http import HttpResponse
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # نوشتن header و data بر اساس نوع گزارش
            if 'users' in data:
                writer.writerow(['نام', 'ایمیل', 'تعداد سوال', 'آخرین فعالیت'])
                for user in data.get('users', []):
                    writer.writerow([user.get('name', ''), user.get('email', ''), 
                                   user.get('query_count', 0), user.get('last_active', '')])
            else:
                writer.writerow(['کلید', 'مقدار'])
                for key, value in data.items():
                    writer.writerow([key, value])
            
            response = HttpResponse(output.getvalue(), content_type='text/csv; charset=utf-8')
            response['Content-Disposition'] = f'attachment; filename="report_{report_type}.csv"'
            return response
        
        return Response(data)
    
    def _generate_summary_report(self, start_date, end_date):
        """تولید گزارش خلاصه"""
        from accounts.models import User
        from payments.models import Transaction, PaymentStatus
        from chat.models import Message
        
        users_count = User.objects.filter(date_joined__range=[start_date, end_date]).count()
        active_users = User.objects.filter(last_login__range=[start_date, end_date]).count()
        
        transactions = Transaction.objects.filter(
            created_at__range=[start_date, end_date],
            status=PaymentStatus.SUCCESS
        )
        total_revenue = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        messages_count = Message.objects.filter(created_at__range=[start_date, end_date]).count()
        
        return {
            'report': 'summary',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'new_users': users_count,
            'active_users': active_users,
            'total_revenue': float(total_revenue),
            'messages_count': messages_count,
            'transactions_count': transactions.count()
        }
    
    def _generate_users_report(self, start_date, end_date):
        """تولید گزارش کاربران"""
        from accounts.models import User
        from chat.models import Message
        from django.db.models import Count
        
        users = User.objects.filter(
            date_joined__range=[start_date, end_date]
        ).annotate(
            query_count=Count('conversations__messages', filter=Q(conversations__messages__role='user'))
        ).values('id', 'email', 'first_name', 'last_name', 'date_joined', 'last_login', 'query_count')[:100]
        
        return {
            'report': 'users',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'total': len(users),
            'users': list(users)
        }
    
    def _generate_revenue_report(self, start_date, end_date):
        """تولید گزارش درآمد"""
        from payments.models import Transaction, PaymentStatus
        from django.db.models.functions import TruncDate
        
        transactions = Transaction.objects.filter(
            created_at__range=[start_date, end_date],
            status=PaymentStatus.SUCCESS
        )
        
        daily_revenue = transactions.annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            total=Sum('amount'),
            count=Count('id')
        ).order_by('date')
        
        total = transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        return {
            'report': 'revenue',
            'period': {'start': start_date.isoformat(), 'end': end_date.isoformat()},
            'total_revenue': float(total),
            'transactions_count': transactions.count(),
            'daily_breakdown': list(daily_revenue)
        }
