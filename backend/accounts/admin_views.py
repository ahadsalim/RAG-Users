"""
Custom Admin Login Views with OTP Support
Moved from admin_panel app
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
from .utils import send_otp_sms

logger = logging.getLogger(__name__)
User = get_user_model()


class AdminLoginView(View):
    """Custom admin login view with password or OTP option - Single Page"""
    template_name = 'admin/custom_login.html'
    
    def normalize_phone(self, phone_number):
        """Normalize phone number to 09xxxxxxxxx format"""
        phone_number = phone_number.strip()
        if phone_number.startswith('+98'):
            phone_number = '0' + phone_number[3:]
        elif phone_number.startswith('98'):
            phone_number = '0' + phone_number[2:]
        elif not phone_number.startswith('0'):
            phone_number = '0' + phone_number
        return phone_number
    
    def get(self, request):
        if request.user.is_authenticated and request.user.is_staff:
            return redirect('/admin/')
        return render(request, self.template_name, {})
    
    def post(self, request):
        step = request.POST.get('step', 'login')
        
        if step == 'login':
            return self.handle_password_login(request)
        elif step == 'send_otp':
            return self.handle_send_otp(request)
        elif step == 'verify_otp':
            return self.handle_verify_otp(request)
        
        return render(request, self.template_name, {
            'error': 'درخواست نامعتبر'
        })
    
    def handle_password_login(self, request):
        """Handle password authentication"""
        phone_number = self.normalize_phone(request.POST.get('phone_number', ''))
        password = request.POST.get('password', '')
        
        if not phone_number or len(phone_number) < 10:
            return render(request, self.template_name, {
                'error': 'لطفاً شماره موبایل معتبر وارد کنید',
                'phone_number': phone_number
            })
        
        if not password:
            return render(request, self.template_name, {
                'error': 'لطفاً رمز عبور را وارد کنید',
                'phone_number': phone_number
            })
        
        # Check if user exists
        try:
            user = User.objects.get(phone_number=phone_number)
            if not user.is_staff:
                return render(request, self.template_name, {
                    'error': 'شما دسترسی به پنل مدیریت ندارید',
                    'phone_number': phone_number
                })
        except User.DoesNotExist:
            return render(request, self.template_name, {
                'error': 'کاربری با این شماره موبایل یافت نشد',
                'phone_number': phone_number
            })
        
        # Authenticate
        user = authenticate(request, username=phone_number, password=password)
        
        if user is not None and user.is_staff:
            login(request, user)
            next_url = request.GET.get('next', '/admin/')
            return redirect(next_url)
        else:
            return render(request, self.template_name, {
                'error': 'رمز عبور اشتباه است',
                'phone_number': phone_number
            })
    
    def handle_send_otp(self, request):
        """Send OTP to user's phone - Returns JSON for AJAX"""
        phone_number = self.normalize_phone(request.POST.get('phone_number', ''))
        
        if not phone_number or len(phone_number) < 10:
            return JsonResponse({
                'success': False,
                'error': 'لطفاً شماره موبایل معتبر وارد کنید'
            })
        
        # Check if user exists and is staff
        try:
            user = User.objects.get(phone_number=phone_number)
            if not user.is_staff:
                return JsonResponse({
                    'success': False,
                    'error': 'شما دسترسی به پنل مدیریت ندارید'
                })
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'کاربری با این شماره موبایل یافت نشد'
            })
        
        # Check rate limit
        rate_key = f'admin_otp_rate_{phone_number}'
        if cache.get(rate_key):
            return JsonResponse({
                'success': False,
                'error': 'لطفاً 2 دقیقه صبر کنید'
            })
        
        # Generate OTP
        otp_code = str(random.randint(10000, 99999))
        
        # Store OTP in cache (5 minutes)
        cache_key = f'admin_otp_{phone_number}'
        cache.set(cache_key, otp_code, 300)
        
        # Set rate limit (2 minutes)
        cache.set(rate_key, True, 120)
        
        # Store phone in session for verify step
        request.session['admin_login_phone'] = phone_number
        
        # Send OTP
        send_otp_sms(phone_number, otp_code)
        logger.info(f"Admin OTP sent to {phone_number}")
        
        return JsonResponse({
            'success': True,
            'message': 'کد تأیید به شماره موبایل شما ارسال شد'
        })
    
    def handle_verify_otp(self, request):
        """Verify OTP and login"""
        phone_number = self.normalize_phone(request.POST.get('phone_number', ''))
        # OTP is now in password field
        otp_code = request.POST.get('password', '').strip()
        
        if not phone_number or len(phone_number) < 10:
            return render(request, self.template_name, {
                'error': 'لطفاً شماره موبایل معتبر وارد کنید'
            })
        
        if not otp_code or len(otp_code) != 5:
            return render(request, self.template_name, {
                'error': 'لطفاً کد 5 رقمی را وارد کنید',
                'phone_number': phone_number,
                'otp_sent': True
            })
        
        # Get stored OTP
        cache_key = f'admin_otp_{phone_number}'
        stored_otp = cache.get(cache_key)
        
        if not stored_otp:
            return render(request, self.template_name, {
                'error': 'کد تأیید منقضی شده است. لطفاً دوباره درخواست دهید',
                'phone_number': phone_number
            })
        
        if otp_code != stored_otp:
            return render(request, self.template_name, {
                'error': 'کد تأیید اشتباه است',
                'phone_number': phone_number,
                'otp_sent': True
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
                    'error': 'شما دسترسی به پنل مدیریت ندارید'
                })
        except User.DoesNotExist:
            return render(request, self.template_name, {
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
