from rest_framework import serializers
from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    formatted_price = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()
    display_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'formatted_price', 'currency_symbol', 'display_price', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'features', 'is_active']
    
    def _get_user_currency(self):
        """دریافت ارز انتخابی کاربر یا تومان به عنوان پیش‌فرض"""
        from finance.models import Currency
        
        request = self.context.get('request')
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if hasattr(request.user, 'preferred_currency') and request.user.preferred_currency:
                return request.user.preferred_currency
        
        # پیش‌فرض: تومان
        toman = Currency.objects.filter(code='IRT', is_active=True).first()
        if toman:
            return toman
        
        # اگر تومان نبود، ارز پایه
        return Currency.get_base_currency()
    
    def get_formatted_price(self, obj):
        """قیمت فرمت شده در ارز کاربر"""
        currency = self._get_user_currency()
        return obj.get_formatted_price(currency)
    
    def get_currency_symbol(self, obj):
        """نماد ارز کاربر"""
        currency = self._get_user_currency()
        return currency.symbol if currency else 'تومان'
    
    def get_display_price(self, obj):
        """قیمت عددی در ارز کاربر (برای محاسبات فرانت‌اند)"""
        from finance.models import Currency
        currency = self._get_user_currency()
        if currency and not currency.is_base:
            return float(currency.convert_from_base(obj.price))
        return float(obj.price)


class SubscriptionSerializer(serializers.ModelSerializer):
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.filter(is_active=True), 
        source='plan', 
        write_only=True
    )
    is_active_subscription = serializers.BooleanField(source='is_active', read_only=True)
    
    class Meta:
        model = Subscription
        fields = [
            'id', 'user', 'plan', 'plan_id', 'status', 
            'start_date', 'end_date', 'auto_renew',
            'created_at', 'updated_at', 'is_active_subscription'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
