from rest_framework import serializers
from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    formatted_price = serializers.SerializerMethodField()
    currency_symbol = serializers.SerializerMethodField()
    
    class Meta:
        model = Plan
        fields = ['id', 'name', 'description', 'price', 'formatted_price', 'currency_symbol', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'features', 'is_active']
    
    def get_formatted_price(self, obj):
        return obj.get_price_display()
    
    def get_currency_symbol(self, obj):
        from finance.models import Currency
        base = Currency.get_base_currency()
        return base.symbol if base else 'تومان'


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
