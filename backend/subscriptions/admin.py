from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django import forms
from decimal import Decimal
from .models import Plan, Subscription
from .usage import UsageLog
from core.models import Currency, SiteSettings


class PlanAdminForm(forms.ModelForm):
    """فرم سفارشی برای ورود قیمت با انتخاب ارز"""
    
    # فیلد برای ورود قیمت به ارز دلخواه
    price_in_currency = forms.DecimalField(
        label='قیمت',
        max_digits=15,
        decimal_places=2,
        required=False,
        help_text='قیمت را به ارز انتخابی وارد کنید'
    )
    
    # فیلد انتخاب ارز
    input_currency = forms.ModelChoiceField(
        queryset=Currency.objects.filter(is_active=True),
        label='ارز قیمت',
        required=False,
        help_text='ارز برای محاسبه و نمایش قیمت'
    )
    
    class Meta:
        model = Plan
        fields = '__all__'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # اگر در حال ویرایش هستیم
        if self.instance.pk:
            # نمایش قیمت به ارز انتخابی پلن یا ارز پایه
            target_currency = self.instance.currency
            if not target_currency:
                settings = SiteSettings.get_settings()
                target_currency = settings.base_currency
            
            if target_currency:
                # تبدیل قیمت از base به ارز هدف
                converted_price = target_currency.convert_from_base(self.instance.price)
                self.fields['price_in_currency'].initial = converted_price
                self.fields['input_currency'].initial = target_currency
        else:
            # برای پلن جدید، ارز پیش‌فرض را تنظیم کن
            settings = SiteSettings.get_settings()
            if settings.base_currency:
                self.fields['input_currency'].initial = settings.base_currency
        
        # پنهان کردن فیلد price (چون به صورت خودکار محاسبه می‌شود)
        self.fields['price'].widget = forms.HiddenInput()
        self.fields['price'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        price_in_currency = cleaned_data.get('price_in_currency')
        input_currency = cleaned_data.get('input_currency')
        
        # اگر قیمت وارد شده
        if price_in_currency is not None:
            if not input_currency:
                # اگر ارز انتخاب نشده، از ارز پایه استفاده کن
                settings = SiteSettings.get_settings()
                input_currency = settings.base_currency
                cleaned_data['input_currency'] = input_currency
            
            if input_currency:
                # تبدیل به واحد پایه (استفاده از Decimal برای دقت بالا)
                exchange_rate = Decimal(str(input_currency.exchange_rate))
                base_price = price_in_currency / exchange_rate
                cleaned_data['price'] = base_price
                cleaned_data['currency'] = input_currency
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # اگر ارز انتخاب شده، آن را در پلن ذخیره کن
        if self.cleaned_data.get('input_currency'):
            instance.currency = self.cleaned_data['input_currency']
        
        if commit:
            instance.save()
        return instance


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    form = PlanAdminForm
    list_display = ['name', 'plan_type', 'formatted_price', 'duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_organization_members', 'is_active', 'colored_status']
    list_filter = ['plan_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['duration_days', 'max_queries_per_day', 'max_queries_per_month', 'max_organization_members', 'is_active']
    ordering = ['plan_type', 'price']
    
    fieldsets = (
        ('اطلاعات پایه', {
            'fields': ('name', 'description', 'plan_type', 'input_currency', 'price_in_currency', 'price', 'duration_days', 'is_active'),
            'description': 'قیمت را به ارز انتخابی وارد کنید. خودکار به واحد پایه تبدیل می‌شود.'
        }),
        ('محدودیت‌های استفاده', {
            'fields': ('max_queries_per_day', 'max_queries_per_month'),
        }),
        ('تنظیمات سازمانی (فقط برای پلن‌های حقوقی)', {
            'fields': ('max_organization_members',),
            'description': 'حداکثر تعداد اعضای سازمان برای پلن‌های حقوقی'
        }),
        ('ویژگی‌های اضافی', {
            'fields': ('features',),
            'classes': ('collapse',),
            'description': 'تنظیمات JSON اضافی. مثال: {"gpt_3_5_access": true, "gpt_4_access": false}'
        }),
    )
    
    def formatted_price(self, obj):
        """Display price with currency formatting"""
        return obj.get_formatted_price()
    formatted_price.short_description = 'قیمت'
    
    def colored_status(self, obj):
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> فعال')
        return format_html('<span style="color: red;">●</span> غیرفعال')
    colored_status.short_description = 'وضعیت'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'plan', 'colored_status', 'start_date', 'end_date', 'days_remaining', 'auto_renew']
    list_filter = ['status', 'plan', 'auto_renew', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    list_editable = ['auto_renew']
    readonly_fields = ['created_at', 'updated_at', 'days_remaining']
    
    fieldsets = (
        ('اطلاعات کاربر', {
            'fields': ('user', 'plan')
        }),
        ('وضعیت اشتراک', {
            'fields': ('status', 'start_date', 'end_date', 'auto_renew')
        }),
        ('اطلاعات سیستمی', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_subscription', 'cancel_subscription', 'extend_subscription']
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def colored_status(self, obj):
        colors = {
            'active': 'green',
            'expired': 'red',
            'cancelled': 'gray',
            'pending': 'orange',
        }
        color = colors.get(obj.status, 'gray')
        status_fa = dict(obj.STATUS_CHOICES).get(obj.status, obj.status)
        return format_html('<span style="color: {};">●</span> {}', color, status_fa)
    colored_status.short_description = 'وضعیت'
    
    def days_remaining(self, obj):
        if obj.status == 'active' and obj.end_date:
            delta = obj.end_date - timezone.now()
            days = delta.days
            if days > 0:
                return format_html('<span style="color: green;">{} روز</span>', days)
            else:
                return format_html('<span style="color: red;">منقضی شده</span>')
        return '-'
    days_remaining.short_description = 'باقیمانده'
    
    def activate_subscription(self, request, queryset):
        count = 0
        for sub in queryset:
            sub.activate()
            count += 1
        self.message_user(request, f'{count} اشتراک فعال شد.')
    activate_subscription.short_description = 'فعال‌سازی اشتراک'
    
    def cancel_subscription(self, request, queryset):
        count = 0
        for sub in queryset:
            sub.cancel()
            count += 1
        self.message_user(request, f'{count} اشتراک لغو شد.')
    cancel_subscription.short_description = 'لغو اشتراک'
    
    def extend_subscription(self, request, queryset):
        from datetime import timedelta
        count = 0
        for sub in queryset:
            sub.end_date = sub.end_date + timedelta(days=30)
            sub.save()
            count += 1
        self.message_user(request, f'{count} اشتراک 30 روز تمدید شد.')
    extend_subscription.short_description = 'تمدید 30 روزه'


@admin.register(UsageLog)
class UsageLogAdmin(admin.ModelAdmin):
    list_display = ['user_info', 'action_type', 'tokens_used', 'subscription_plan', 'created_at']
    list_filter = ['action_type', 'created_at']
    search_fields = ['user__email', 'user__phone_number', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = ['id', 'user', 'subscription', 'action_type', 'tokens_used', 'metadata', 'ip_address', 'user_agent', 'created_at']
    
    def user_info(self, obj):
        return format_html(
            '<strong>{}</strong><br/><small>{}</small>',
            obj.user.get_full_name() or obj.user.email or obj.user.phone_number,
            obj.user.phone_number or obj.user.email
        )
    user_info.short_description = 'کاربر'
    
    def subscription_plan(self, obj):
        # اول از plan_name ذخیره شده استفاده کن (نام پلن در زمان ثبت)
        if obj.plan_name:
            return obj.plan_name
        # اگر نبود، از اشتراک فعلی بخوان (برای لاگ‌های قدیمی)
        if obj.subscription:
            return obj.subscription.plan.name
        return '-'
    subscription_plan.short_description = 'پلن'
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
