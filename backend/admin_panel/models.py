from django.db import models
from django.contrib.auth.models import Permission
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class Role(models.Model):
    """مدل نقش‌های کاربری"""
    
    ROLE_TYPES = [
        ('super_admin', 'مدیر ارشد'),
        ('admin', 'مدیر'),
        ('moderator', 'ناظر'),
        ('support', 'پشتیبانی'),
        ('finance', 'مالی'),
        ('content', 'محتوا'),
        ('analyst', 'تحلیل‌گر'),
        ('custom', 'سفارشی'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='نام نقش'
    )
    role_type = models.CharField(
        max_length=20,
        choices=ROLE_TYPES,
        default='custom',
        verbose_name='نوع نقش'
    )
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    permissions = models.ManyToManyField(
        Permission,
        blank=True,
        verbose_name='دسترسی‌ها'
    )
    
    # محدودیت‌های نقش
    can_view_all_users = models.BooleanField(default=False, verbose_name='مشاهده همه کاربران')
    can_edit_users = models.BooleanField(default=False, verbose_name='ویرایش کاربران')
    can_delete_users = models.BooleanField(default=False, verbose_name='حذف کاربران')
    can_view_financial = models.BooleanField(default=False, verbose_name='مشاهده امور مالی')
    can_manage_financial = models.BooleanField(default=False, verbose_name='مدیریت امور مالی')
    can_view_analytics = models.BooleanField(default=False, verbose_name='مشاهده گزارشات')
    can_export_data = models.BooleanField(default=False, verbose_name='خروجی داده')
    can_manage_content = models.BooleanField(default=False, verbose_name='مدیریت محتوا')
    can_manage_system = models.BooleanField(default=False, verbose_name='مدیریت سیستم')
    can_view_logs = models.BooleanField(default=False, verbose_name='مشاهده لاگ‌ها')
    
    # تنظیمات
    priority = models.IntegerField(default=0, verbose_name='اولویت')
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_default = models.BooleanField(default=False, verbose_name='پیش‌فرض')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_roles',
        verbose_name='ایجادکننده'
    )
    
    class Meta:
        verbose_name = 'نقش'
        verbose_name_plural = 'نقش‌ها'
        ordering = ['-priority', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_role_type_display()})"
    
    def get_all_permissions(self):
        """دریافت همه دسترسی‌های نقش"""
        perms = list(self.permissions.all())
        
        # افزودن دسترسی‌های سفارشی بر اساس فیلدها
        custom_perms = []
        if self.can_view_all_users:
            custom_perms.append('view_all_users')
        if self.can_edit_users:
            custom_perms.append('edit_users')
        if self.can_delete_users:
            custom_perms.append('delete_users')
        if self.can_view_financial:
            custom_perms.append('view_financial')
        if self.can_manage_financial:
            custom_perms.append('manage_financial')
        if self.can_view_analytics:
            custom_perms.append('view_analytics')
        if self.can_export_data:
            custom_perms.append('export_data')
        if self.can_manage_content:
            custom_perms.append('manage_content')
        if self.can_manage_system:
            custom_perms.append('manage_system')
        if self.can_view_logs:
            custom_perms.append('view_logs')
            
        return perms, custom_perms


class AdminUser(models.Model):
    """کاربران ادمین با نقش‌های مختلف"""
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='admin_profile',
        verbose_name='کاربر'
    )
    
    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name='نقش‌ها'
    )
    
    # اطلاعات اضافی
    department = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='بخش/دپارتمان'
    )
    employee_id = models.CharField(
        max_length=50,
        blank=True,
        unique=True,
        null=True,
        verbose_name='کد پرسنلی'
    )
    
    # محدودیت‌های زمانی دسترسی
    access_start_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='ساعت شروع دسترسی'
    )
    access_end_time = models.TimeField(
        null=True,
        blank=True,
        verbose_name='ساعت پایان دسترسی'
    )
    
    # محدودیت IP
    allowed_ips = models.TextField(
        blank=True,
        verbose_name='IP های مجاز',
        help_text='هر IP در یک خط'
    )
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    last_activity = models.DateTimeField(null=True, blank=True, verbose_name='آخرین فعالیت')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='تاریخ به‌روزرسانی')
    
    class Meta:
        verbose_name = 'کاربر ادمین'
        verbose_name_plural = 'کاربران ادمین'
    
    def __str__(self):
        return f"{self.user.get_full_name() or self.user.email}"
    
    def has_permission(self, permission_code):
        """بررسی دسترسی"""
        if not self.is_active:
            return False
            
        # بررسی محدودیت زمانی
        if self.access_start_time and self.access_end_time:
            from datetime import datetime
            now = datetime.now().time()
            if not (self.access_start_time <= now <= self.access_end_time):
                return False
        
        # بررسی دسترسی‌ها
        for role in self.roles.filter(is_active=True):
            perms, custom_perms = role.get_all_permissions()
            
            # چک دسترسی‌های Django
            for perm in perms:
                if perm.codename == permission_code:
                    return True
            
            # چک دسترسی‌های سفارشی
            if permission_code in custom_perms:
                return True
        
        return False
    
    def get_all_permissions(self):
        """دریافت همه دسترسی‌های کاربر"""
        all_perms = set()
        all_custom_perms = set()
        
        for role in self.roles.filter(is_active=True):
            perms, custom_perms = role.get_all_permissions()
            all_perms.update(perms)
            all_custom_perms.update(custom_perms)
        
        return list(all_perms), list(all_custom_perms)


class AdminAction(models.Model):
    """لاگ اقدامات ادمین‌ها"""
    
    ACTION_TYPES = [
        ('login', 'ورود'),
        ('logout', 'خروج'),
        ('view', 'مشاهده'),
        ('create', 'ایجاد'),
        ('update', 'به‌روزرسانی'),
        ('delete', 'حذف'),
        ('export', 'خروجی'),
        ('import', 'ورودی'),
        ('approve', 'تایید'),
        ('reject', 'رد'),
        ('block', 'مسدودسازی'),
        ('unblock', 'رفع مسدودی'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    admin_user = models.ForeignKey(
        AdminUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='actions',
        verbose_name='کاربر ادمین'
    )
    
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name='نوع عملیات'
    )
    
    # جزئیات عملیات
    model_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='نام مدل'
    )
    object_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name='شناسه شیء'
    )
    object_repr = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='نمایش شیء'
    )
    
    # داده‌های قبل و بعد (برای update)
    before_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='داده قبلی'
    )
    after_data = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='داده جدید'
    )
    
    # اطلاعات اضافی
    description = models.TextField(
        blank=True,
        verbose_name='توضیحات'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='متادیتا'
    )
    
    # اطلاعات درخواست
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name='آدرس IP'
    )
    user_agent = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='User Agent'
    )
    
    # تاریخ
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان انجام')
    
    class Meta:
        verbose_name = 'لاگ عملیات ادمین'
        verbose_name_plural = 'لاگ عملیات ادمین‌ها'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
            models.Index(fields=['model_name', 'object_id']),
        ]
    
    def __str__(self):
        return f"{self.admin_user} - {self.get_action_type_display()} - {self.created_at}"


class AdminDashboardWidget(models.Model):
    """ویجت‌های داشبورد ادمین"""
    
    WIDGET_TYPES = [
        ('stats_card', 'کارت آمار'),
        ('chart_line', 'نمودار خطی'),
        ('chart_bar', 'نمودار میله‌ای'),
        ('chart_pie', 'نمودار دایره‌ای'),
        ('table', 'جدول'),
        ('activity_feed', 'فید فعالیت'),
        ('quick_actions', 'دسترسی سریع'),
        ('calendar', 'تقویم'),
        ('todo_list', 'لیست کارها'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(
        max_length=100,
        verbose_name='عنوان'
    )
    widget_type = models.CharField(
        max_length=20,
        choices=WIDGET_TYPES,
        verbose_name='نوع ویجت'
    )
    
    # محتوا و تنظیمات
    config = models.JSONField(
        default=dict,
        verbose_name='تنظیمات',
        help_text='تنظیمات JSON ویجت'
    )
    
    # دسترسی
    required_permission = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='دسترسی مورد نیاز'
    )
    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name='نقش‌های مجاز'
    )
    
    # نمایش
    position_x = models.IntegerField(default=0, verbose_name='موقعیت X')
    position_y = models.IntegerField(default=0, verbose_name='موقعیت Y')
    width = models.IntegerField(default=3, verbose_name='عرض')
    height = models.IntegerField(default=2, verbose_name='ارتفاع')
    
    # وضعیت
    is_active = models.BooleanField(default=True, verbose_name='فعال')
    is_default = models.BooleanField(default=False, verbose_name='پیش‌فرض')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'ویجت داشبورد'
        verbose_name_plural = 'ویجت‌های داشبورد'
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return f"{self.title} ({self.get_widget_type_display()})"


class AdminNotification(models.Model):
    """اعلان‌های ادمین"""
    
    NOTIFICATION_TYPES = [
        ('info', 'اطلاعیه'),
        ('warning', 'هشدار'),
        ('error', 'خطا'),
        ('success', 'موفقیت'),
        ('critical', 'بحرانی'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # گیرنده
    admin_user = models.ForeignKey(
        AdminUser,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='notifications',
        verbose_name='کاربر ادمین'
    )
    roles = models.ManyToManyField(
        Role,
        blank=True,
        verbose_name='نقش‌های گیرنده'
    )
    broadcast = models.BooleanField(
        default=False,
        verbose_name='پخش عمومی'
    )
    
    # محتوا
    title = models.CharField(
        max_length=200,
        verbose_name='عنوان'
    )
    message = models.TextField(
        verbose_name='پیام'
    )
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='info',
        verbose_name='نوع'
    )
    
    # لینک اقدام
    action_url = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='لینک اقدام'
    )
    action_text = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='متن دکمه اقدام'
    )
    
    # وضعیت
    is_read = models.BooleanField(default=False, verbose_name='خوانده شده')
    read_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان خواندن')
    
    # تاریخ‌ها
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='زمان ارسال')
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name='زمان انقضا')
    
    class Meta:
        verbose_name = 'اعلان ادمین'
        verbose_name_plural = 'اعلان‌های ادمین'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['admin_user', 'is_read', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_notification_type_display()}"
    
    def mark_as_read(self):
        """علامت‌گذاری به عنوان خوانده شده"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
