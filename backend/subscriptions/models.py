from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
import uuid


class Plan(models.Model):
    """مدل پلن اشتراک"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_("نام پلن"), max_length=100)
    description = models.TextField(_("توضیحات"), blank=True)
    price = models.DecimalField(_("قیمت"), max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(_("مدت به روز"), default=30)
    max_queries_per_day = models.IntegerField(_("سوال/روز"), default=10)
    max_queries_per_month = models.IntegerField(_("سوال/ماه"), default=300)
    features = models.JSONField(_("ویژگی‌ها"), default=dict, blank=True)
    is_active = models.BooleanField(_("فعال"), default=True)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ به‌روزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("پلن")
        verbose_name_plural = _("پلن‌ها")
        ordering = ['price']
    
    def __str__(self):
        return self.name


class Subscription(models.Model):
    """مدل اشتراک کاربر"""
    
    STATUS_CHOICES = [
        ('active', _('فعال')),
        ('expired', _('منقضی شده')),
        ('cancelled', _('لغو شده')),
        ('pending', _('در انتظار')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_("کاربر")
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_("پلن")
    )
    status = models.CharField(_("وضعیت"), max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateTimeField(_("تاریخ شروع"), default=timezone.now)
    end_date = models.DateTimeField(_("تاریخ پایان"))
    auto_renew = models.BooleanField(_("تمدید خودکار"), default=False)
    created_at = models.DateTimeField(_("تاریخ ایجاد"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاریخ به‌روزرسانی"), auto_now=True)
    
    class Meta:
        verbose_name = _("اشتراک کاربر")
        verbose_name_plural = _("اشتراک کاربران")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.plan.name}"
    
    @property
    def is_active(self):
        """بررسی فعال بودن اشتراک"""
        return self.status == 'active' and self.end_date > timezone.now()
    
    def activate(self):
        """فعال‌سازی اشتراک"""
        self.status = 'active'
        self.save()
    
    def cancel(self):
        """لغو اشتراک"""
        self.status = 'cancelled'
        self.auto_renew = False
        self.save()
    
    def can_query(self):
        """
        بررسی اینکه آیا کاربر می‌تواند query بفرستد
        
        Returns:
            tuple: (can_query: bool, message: str)
        """
        # بررسی فعال بودن اشتراک
        if not self.is_active:
            return False, "اشتراک شما منقضی شده است"
        
        # دریافت محدودیت‌ها از features
        features = self.plan.features or {}
        max_queries_per_day = features.get('max_queries_per_day', 10)
        max_queries_per_month = features.get('max_queries_per_month', 300)
        
        # برای الان همیشه True برمی‌گردانیم
        # TODO: باید usage tracking اضافه شود
        return True, "OK"
    
    @property
    def queries_used_today(self):
        """تعداد query های امروز - TODO: باید implement شود"""
        return 0
    
    @property
    def queries_used_month(self):
        """تعداد query های این ماه - TODO: باید implement شود"""
        return 0
