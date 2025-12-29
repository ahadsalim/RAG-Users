"""
ویوهای سفارشی پنل ادمین امور مالی
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta, datetime
import jdatetime
from .models import Invoice


@staff_member_required
def revenue_report_view(request):
    """گزارش درآمد با نمودارهای هفتگی و ماهانه"""
    
    # دریافت بازه تاریخی از کاربر (اختیاری)
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    
    # محاسبه درآمد هفته جاری (شروع از شنبه)
    today = timezone.now()
    # پیدا کردن شنبه این هفته (weekday: شنبه=5)
    days_since_saturday = (today.weekday() + 2) % 7
    week_start = (today - timedelta(days=days_since_saturday)).replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)
    
    weekly_data = []
    week_labels = ['شنبه', 'یکشنبه', 'دوشنبه', 'سه‌شنبه', 'چهارشنبه', 'پنج‌شنبه', 'جمعه']
    
    for i in range(7):
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        
        daily_revenue = Invoice.objects.filter(
            status='paid',
            paid_at__gte=day_start,
            paid_at__lt=day_end
        ).aggregate(total=Sum('total'))['total'] or 0
        
        weekly_data.append(float(daily_revenue))
    
    # محاسبه درآمد ماه جاری (شمسی)
    now_jalali = jdatetime.datetime.now()
    month_start_jalali = now_jalali.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # تبدیل به میلادی
    month_start_gregorian = month_start_jalali.togregorian()
    month_start = timezone.make_aware(datetime.combine(month_start_gregorian, datetime.min.time()))
    
    # محاسبه تعداد روزهای ماه شمسی
    if now_jalali.month <= 6:
        days_in_month = 31
    elif now_jalali.month <= 11:
        days_in_month = 30
    else:
        # بهمن - بررسی کبیسه
        days_in_month = 30 if jdatetime.j_days_in_month[12](now_jalali.year) == 30 else 29
    
    monthly_data = []
    monthly_labels = []
    
    for day in range(1, days_in_month + 1):
        day_jalali = now_jalali.replace(day=day, hour=0, minute=0, second=0, microsecond=0)
        day_start = timezone.make_aware(datetime.combine(day_jalali.togregorian(), datetime.min.time()))
        day_end = day_start + timedelta(days=1)
        
        daily_revenue = Invoice.objects.filter(
            status='paid',
            paid_at__gte=day_start,
            paid_at__lt=day_end
        ).aggregate(total=Sum('total'))['total'] or 0
        
        monthly_data.append(float(daily_revenue))
        monthly_labels.append(str(day))
    
    # گزارش بازه تاریخی سفارشی
    custom_revenue = None
    custom_invoice_count = None
    custom_date_from = None
    custom_date_to = None
    
    if date_from and date_to:
        try:
            # تبدیل تاریخ شمسی به میلادی
            from_parts = date_from.split('-')
            to_parts = date_to.split('-')
            
            from_jalali = jdatetime.date(int(from_parts[0]), int(from_parts[1]), int(from_parts[2]))
            to_jalali = jdatetime.date(int(to_parts[0]), int(to_parts[1]), int(to_parts[2]))
            
            from_gregorian = from_jalali.togregorian()
            to_gregorian = to_jalali.togregorian()
            
            custom_date_from = timezone.make_aware(datetime.combine(from_gregorian, datetime.min.time()))
            custom_date_to = timezone.make_aware(datetime.combine(to_gregorian, datetime.max.time()))
            
            custom_stats = Invoice.objects.filter(
                status='paid',
                paid_at__gte=custom_date_from,
                paid_at__lte=custom_date_to
            ).aggregate(
                total=Sum('total'),
                count=Count('id')
            )
            
            custom_revenue = custom_stats['total'] or 0
            custom_invoice_count = custom_stats['count'] or 0
        except (ValueError, IndexError):
            pass
    
    # محاسبه مجموع درآمد هفته و ماه
    week_total = sum(weekly_data)
    month_total = sum(monthly_data)
    
    context = {
        'weekly_labels': week_labels,
        'weekly_data': weekly_data,
        'week_total': week_total,
        'monthly_labels': monthly_labels,
        'monthly_data': monthly_data,
        'month_total': month_total,
        'current_month_name': now_jalali.strftime('%B %Y'),
        'custom_revenue': custom_revenue,
        'custom_invoice_count': custom_invoice_count,
        'date_from': date_from,
        'date_to': date_to,
    }
    
    return render(request, 'admin/finance/revenue_report.html', context)
