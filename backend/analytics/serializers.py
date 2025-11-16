from rest_framework import serializers
from .models import (
    DailyMetric, UserAnalytics, RevenueAnalytics,
    SystemMetrics
)


class DailyMetricSerializer(serializers.ModelSerializer):
    """Serializer برای متریک روزانه"""
    
    metric_type_display = serializers.CharField(
        source='get_metric_type_display',
        read_only=True
    )
    
    class Meta:
        model = DailyMetric
        fields = [
            'id', 'date', 'metric_type', 'metric_type_display',
            'count', 'sum_value', 'avg_value', 'min_value', 'max_value',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer برای تحلیل کاربران"""
    
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    days_since_registration = serializers.SerializerMethodField()
    activity_status = serializers.SerializerMethodField()
    
    class Meta:
        model = UserAnalytics
        fields = [
            'user', 'user_email', 'user_name',
            'total_queries', 'total_tokens', 'total_conversations', 'total_spent',
            'last_query_at', 'last_payment_at', 'active_days',
            'avg_queries_per_day', 'avg_tokens_per_query', 'avg_response_time',
            'engagement_score', 'value_score',
            'preferred_model', 'preferred_response_mode',
            'days_since_registration', 'activity_status',
            'first_activity', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def get_days_since_registration(self, obj):
        """محاسبه روزهای از زمان ثبت‌نام"""
        from django.utils import timezone
        return (timezone.now() - obj.created_at).days
    
    def get_activity_status(self, obj):
        """تعیین وضعیت فعالیت"""
        from django.utils import timezone
        from datetime import timedelta
        
        if not obj.last_query_at:
            return 'inactive'
        
        days_since_last = (timezone.now() - obj.last_query_at).days
        
        if days_since_last <= 7:
            return 'active'
        elif days_since_last <= 30:
            return 'moderate'
        else:
            return 'inactive'


class RevenueAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer برای تحلیل درآمد"""
    
    period_type_display = serializers.CharField(
        source='get_period_type_display',
        read_only=True
    )
    period_duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = RevenueAnalytics
        fields = [
            'id', 'period_type', 'period_type_display',
            'period_start', 'period_end', 'period_duration',
            'total_revenue', 'subscription_revenue', 'one_time_revenue',
            'total_transactions', 'successful_transactions', 'failed_transactions',
            'success_rate', 'new_customers', 'returning_customers',
            'avg_transaction_value', 'avg_customer_value',
            'conversion_rate', 'churn_rate', 'growth_rate',
            'gateway_breakdown', 'plan_breakdown',
            'metadata', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_period_duration(self, obj):
        """محاسبه مدت دوره"""
        return (obj.period_end - obj.period_start).days + 1
    
    def get_success_rate(self, obj):
        """محاسبه نرخ موفقیت"""
        total = obj.total_transactions
        if total == 0:
            return 0
        return round((obj.successful_transactions / total) * 100, 2)


class SystemMetricsSerializer(serializers.ModelSerializer):
    """Serializer برای متریک‌های سیستم"""
    
    health_status = serializers.SerializerMethodField()
    performance_score = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemMetrics
        fields = [
            'timestamp',
            'cpu_usage', 'memory_usage', 'disk_usage',
            'active_connections', 'request_per_second', 'avg_response_time',
            'error_count', 'error_rate',
            'queue_size', 'queue_processing_time',
            'cache_hit_rate',
            'health_status', 'performance_score'
        ]
    
    def get_health_status(self, obj):
        """تعیین وضعیت سلامت سیستم"""
        if obj.cpu_usage > 90 or obj.memory_usage > 90 or obj.error_rate > 10:
            return 'critical'
        elif obj.cpu_usage > 70 or obj.memory_usage > 70 or obj.error_rate > 5:
            return 'warning'
        else:
            return 'healthy'
    
    def get_performance_score(self, obj):
        """محاسبه امتیاز عملکرد"""
        # امتیاز بر اساس معیارهای مختلف
        cpu_score = max(0, 100 - obj.cpu_usage)
        memory_score = max(0, 100 - obj.memory_usage)
        error_score = max(0, 100 - obj.error_rate * 10)
        response_score = max(0, 100 - (obj.avg_response_time / 10))  # فرض: 1000ms = 0 امتیاز
        cache_score = obj.cache_hit_rate
        
        # میانگین وزن‌دار
        total_score = (
            cpu_score * 0.25 +
            memory_score * 0.25 +
            error_score * 0.20 +
            response_score * 0.20 +
            cache_score * 0.10
        )
        
        return round(total_score, 2)


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer برای خلاصه داشبورد"""
    
    period_days = serializers.IntegerField()
    
    users = serializers.DictField()
    revenue = serializers.DictField()
    usage = serializers.DictField()
    subscriptions = serializers.DictField()
    system = serializers.DictField()


class ChartDataSerializer(serializers.Serializer):
    """Serializer برای داده‌های نمودار"""
    
    type = serializers.CharField()  # line, bar, pie, area
    title = serializers.CharField()
    data = serializers.ListField()
    
    # فیلدهای اختیاری
    series = serializers.ListField(required=False)
    labels = serializers.ListField(required=False)
    total = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)


class UserSegmentSerializer(serializers.Serializer):
    """Serializer برای بخش‌بندی کاربران"""
    
    active = serializers.IntegerField()
    inactive = serializers.IntegerField()
    new = serializers.IntegerField()
    vip = serializers.IntegerField()
    at_risk = serializers.IntegerField()


class RevenueComparisonSerializer(serializers.Serializer):
    """Serializer برای مقایسه درآمد"""
    
    current = serializers.DictField()
    previous = serializers.DictField()
    changes = serializers.DictField()


class SystemAlertSerializer(serializers.Serializer):
    """Serializer برای هشدارهای سیستم"""
    
    type = serializers.ChoiceField(choices=['info', 'warning', 'critical'])
    message = serializers.CharField()
    timestamp = serializers.DateTimeField(required=False)
    metadata = serializers.DictField(required=False)
