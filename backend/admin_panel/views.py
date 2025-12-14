"""
Custom Admin Login Views with OTP Support
"""
import random
import logging
from django.contrib.admin.sites import AdminSite
from django.contrib.auth import login, authenticate
from django.contrib.auth import get_user_model
from django.shortcuts import render, redirect
from django.views import View
from django.core.cache import cache
from django.contrib import messages
from django.http import JsonResponse
from accounts.utils import send_otp_sms

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminLoginView(View):
    """Custom admin login view with password or OTP option"""
    template_name = 'admin/custom_login.html'
    
    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('/admin/')
        return render(request, self.template_name, {
            'step': 'phone',
            'title': 'ورود به پنل مدیریت'
        })
    
    def post(self, request):
        step = request.POST.get('step', 'phone')
        
        if step == 'phone':
            return self.handle_phone_step(request)
        elif step == 'password':
            return self.handle_password_step(request)
        elif step == 'send_otp':
            return self.handle_send_otp(request)
        elif step == 'verify_otp':
            return self.handle_verify_otp(request)
        
        return render(request, self.template_name, {
            'step': 'phone',
            'error': 'درخواست نامعتبر'
        })
    
    def handle_phone_step(self, request):
        """Handle phone number submission"""
        phone_number = request.POST.get('phone_number', '').strip()
        
        # Normalize phone number
        if phone_number.startswith('+98'):
            phone_number = '0' + phone_number[3:]
        elif phone_number.startswith('98'):
            phone_number = '0' + phone_number[2:]
        elif not phone_number.startswith('0'):
            phone_number = '0' + phone_number
        
        # Check if user exists and is staff
        try:
            user = User.objects.get(phone_number=phone_number)
            if not user.is_staff:
                return render(request, self.template_name, {
                    'step': 'phone',
                    'error': 'شما دسترسی به پنل مدیریت ندارید'
                })
            
            # Store phone in session
            request.session['admin_login_phone'] = phone_number
            
            return render(request, self.template_name, {
                'step': 'auth_choice',
                'phone_number': phone_number,
                'title': 'انتخاب روش ورود'
            })
            
        except User.DoesNotExist:
            return render(request, self.template_name, {
                'step': 'phone',
                'error': 'کاربری با این شماره موبایل یافت نشد'
            })
    
    def handle_password_step(self, request):
        """Handle password authentication"""
        phone_number = request.session.get('admin_login_phone')
        password = request.POST.get('password', '')
        
        if not phone_number:
            return render(request, self.template_name, {
                'step': 'phone',
                'error': 'لطفاً ابتدا شماره موبایل را وارد کنید'
            })
        
        user = authenticate(request, username=phone_number, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            # Clean up session
            if 'admin_login_phone' in request.session:
                del request.session['admin_login_phone']
            
            next_url = request.GET.get('next', '/admin/')
            return redirect(next_url)
        else:
            return render(request, self.template_name, {
                'step': 'password',
                'phone_number': phone_number,
                'error': 'رمز عبور اشتباه است',
                'title': 'ورود با رمز عبور'
            })
    
    def handle_send_otp(self, request):
        """Send OTP to user's phone"""
        phone_number = request.session.get('admin_login_phone')
        
        if not phone_number:
            return render(request, self.template_name, {
                'step': 'phone',
                'error': 'لطفاً ابتدا شماره موبایل را وارد کنید'
            })
        
        # Check rate limit
        rate_key = f'admin_otp_rate_{phone_number}'
        if cache.get(rate_key):
            return render(request, self.template_name, {
                'step': 'otp',
                'phone_number': phone_number,
                'error': 'لطفاً 2 دقیقه صبر کنید',
                'title': 'تأیید کد یکبار مصرف'
            })
        
        # Generate OTP
        otp_code = str(random.randint(10000, 99999))
        
        # Store OTP in cache (5 minutes)
        cache_key = f'admin_otp_{phone_number}'
        cache.set(cache_key, otp_code, 300)
        
        # Set rate limit (2 minutes)
        cache.set(rate_key, True, 120)
        
        # Send OTP
        send_otp_sms(phone_number, otp_code)
        logger.info(f"Admin OTP sent to {phone_number}")
        
        return render(request, self.template_name, {
            'step': 'otp',
            'phone_number': phone_number,
            'message': 'کد تأیید ارسال شد',
            'title': 'تأیید کد یکبار مصرف'
        })
    
    def handle_verify_otp(self, request):
        """Verify OTP and login"""
        phone_number = request.session.get('admin_login_phone')
        otp_code = request.POST.get('otp_code', '').strip()
        
        if not phone_number:
            return render(request, self.template_name, {
                'step': 'phone',
                'error': 'لطفاً ابتدا شماره موبایل را وارد کنید'
            })
        
        # Get stored OTP
        cache_key = f'admin_otp_{phone_number}'
        stored_otp = cache.get(cache_key)
        
        if not stored_otp:
            return render(request, self.template_name, {
                'step': 'otp',
                'phone_number': phone_number,
                'error': 'کد تأیید منقضی شده است. لطفاً دوباره درخواست دهید',
                'title': 'تأیید کد یکبار مصرف'
            })
        
        if otp_code != stored_otp:
            return render(request, self.template_name, {
                'step': 'otp',
                'phone_number': phone_number,
                'error': 'کد تأیید اشتباه است',
                'title': 'تأیید کد یکبار مصرف'
            })
        
        # OTP is correct, login user
        try:
            user = User.objects.get(phone_number=phone_number)
            if user.is_staff:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                
                # Clean up
                cache.delete(cache_key)
                if 'admin_login_phone' in request.session:
                    del request.session['admin_login_phone']
                
                next_url = request.GET.get('next', '/admin/')
                return redirect(next_url)
            else:
                return render(request, self.template_name, {
                    'step': 'phone',
                    'error': 'شما دسترسی به پنل مدیریت ندارید'
                })
        except User.DoesNotExist:
            return render(request, self.template_name, {
                'step': 'phone',
                'error': 'کاربری یافت نشد'
            })


# Custom AdminSite with OTP login
class OTPAdminSite(AdminSite):
    """Custom AdminSite that uses OTP login"""
    
    def login(self, request, extra_context=None):
        """Override login to use custom view"""
        from django.urls import reverse
        return redirect(reverse('admin_otp_login'))


# Create custom admin site instance
otp_admin_site = OTPAdminSite(name='otp_admin')
