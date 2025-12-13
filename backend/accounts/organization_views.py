"""
Views for Organization Management
کاربران حقوقی می‌توانند اعضای سازمان خود را مدیریت کنند
"""
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Sum, Count
from django.db.models.functions import TruncDate
from datetime import timedelta
import uuid
import logging

from .models import User, Organization
from subscriptions.models import Subscription
from chat.models import Message

logger = logging.getLogger(__name__)


class IsBusinessUser(permissions.BasePermission):
    """فقط کاربران حقوقی دسترسی دارند"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'business'


class IsOrganizationAdmin(permissions.BasePermission):
    """فقط مدیران سازمان دسترسی دارند"""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Owner of organization
        if request.user.owned_organizations.exists():
            return True
        
        # Admin role in organization
        if request.user.organization and request.user.organization_role == 'admin':
            return True
        
        return False


class OrganizationInfoView(APIView):
    """اطلاعات سازمان کاربر"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Check if user is business type
        if user.user_type != 'business':
            return Response({
                'has_organization': False,
                'message': 'این قابلیت فقط برای کاربران حقوقی است'
            })
        
        # Get or create organization for business user
        organization = user.owned_organizations.first()
        if not organization and user.organization:
            organization = user.organization
        
        if not organization:
            # Create organization for business user
            organization = Organization.objects.create(
                name=user.company_name or f"سازمان {user.email}",
                slug=str(uuid.uuid4())[:8],
                owner=user,
                company_name=user.company_name or '',
                phone=user.phone_number or ''
            )
            user.organization = organization
            user.organization_role = 'admin'
            user.save()
        
        # Get subscription info
        subscription = Subscription.objects.filter(
            user=user,
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        max_members = 1
        if subscription and subscription.plan:
            max_members = subscription.plan.max_organization_members
        
        # Get current members count
        members_count = organization.members.count()
        
        # Check if user is admin
        is_admin = (organization.owner == user) or (user.organization_role == 'admin')
        
        return Response({
            'has_organization': True,
            'is_admin': is_admin,
            'organization': {
                'id': str(organization.id),
                'name': organization.name,
                'company_name': organization.company_name,
                'phone': organization.phone,
                'logo': organization.logo.url if organization.logo else None,
            },
            'members_count': members_count,
            'max_members': max_members,
            'can_add_members': members_count < max_members
        })


class OrganizationMembersView(APIView):
    """لیست و مدیریت اعضای سازمان"""
    permission_classes = [IsOrganizationAdmin]
    
    def get(self, request):
        """لیست اعضای سازمان"""
        user = request.user
        organization = user.owned_organizations.first() or user.organization
        
        if not organization:
            return Response({'error': 'سازمان یافت نشد'}, status=404)
        
        members = organization.members.all().values(
            'id', 'email', 'first_name', 'last_name', 
            'organization_role', 'is_active', 'created_at'
        )
        
        # Add usage stats for each member
        members_list = []
        for member in members:
            # Get member's message count this month
            month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            message_count = Message.objects.filter(
                conversation__user_id=member['id'],
                role='user',
                created_at__gte=month_start
            ).count()
            
            member_data = dict(member)
            member_data['id'] = str(member['id'])
            member_data['monthly_usage'] = message_count
            member_data['is_owner'] = organization.owner_id == member['id']
            members_list.append(member_data)
        
        return Response({
            'members': members_list,
            'total': len(members_list)
        })
    
    def post(self, request):
        """اضافه کردن عضو جدید"""
        user = request.user
        organization = user.owned_organizations.first() or user.organization
        
        if not organization:
            return Response({'error': 'سازمان یافت نشد'}, status=404)
        
        # Check member limit
        subscription = Subscription.objects.filter(
            user=organization.owner or user,
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        max_members = 1
        if subscription and subscription.plan:
            max_members = subscription.plan.max_organization_members
        
        current_count = organization.members.count()
        if current_count >= max_members:
            return Response({
                'error': f'حداکثر تعداد اعضا ({max_members} نفر) برای پلن شما پر شده است'
            }, status=400)
        
        # Validate input
        email = request.data.get('email', '').strip().lower()
        phone_number = request.data.get('phone_number', '').strip()
        role = request.data.get('role', 'member')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')
        
        if not email:
            return Response({'error': 'ایمیل الزامی است'}, status=400)
        
        if not phone_number:
            return Response({'error': 'شماره تلفن الزامی است'}, status=400)
        
        # Validate phone format
        import re
        if not re.match(r'^09\d{9}$', phone_number):
            return Response({'error': 'شماره موبایل باید با 09 شروع شود و 11 رقم باشد'}, status=400)
        
        if role not in ['admin', 'member']:
            role = 'member'
        
        # Check if email already exists in organization
        if organization.members.filter(email=email).exists():
            return Response({'error': 'این ایمیل قبلاً در سازمان ثبت شده است'}, status=400)
        
        # Check if email exists as independent user
        existing_user = User.objects.filter(email=email).first()
        if existing_user and existing_user.user_type == 'individual':
            return Response({
                'error': 'این ایمیل متعلق به یک کاربر حقیقی مستقل است'
            }, status=400)
        
        # Check if phone exists as individual user (they cannot login as individual with this phone)
        existing_individual = User.objects.filter(phone_number=phone_number, user_type='individual').first()
        if existing_individual:
            return Response({
                'error': 'این شماره تلفن متعلق به یک کاربر حقیقی مستقل است. کاربر باید ابتدا حساب حقیقی خود را حذف کند.'
            }, status=400)
        
        # Create new member user
        new_member = User.objects.create(
            email=email,
            phone_number=phone_number,
            user_type='business',
            organization=organization,
            organization_role=role,
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            email_verified=False  # Will need to verify email
        )
        new_member.set_unusable_password()  # Will set password on first login
        new_member.save()
        
        logger.info(f"New organization member created: {email} in {organization.name}")
        
        # ارسال ایمیل دعوت با لینک تنظیم رمز عبور
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            from django.contrib.auth.tokens import default_token_generator
            from django.utils.http import urlsafe_base64_encode
            from django.utils.encoding import force_bytes
            
            token = default_token_generator.make_token(new_member)
            uid = urlsafe_base64_encode(force_bytes(new_member.pk))
            reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}&user={uid}"
            
            send_mail(
                subject=f'دعوت به سازمان {organization.name}',
                message=f'''سلام {first_name}،

شما به عنوان عضو جدید به سازمان {organization.name} دعوت شده‌اید.

برای تنظیم رمز عبور و ورود به سیستم، روی لینک زیر کلیک کنید:
{reset_url}

این لینک تا 24 ساعت معتبر است.

با تشکر،
تیم پشتیبانی''',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=True,
            )
            logger.info(f"Invitation email sent to {email}")
        except Exception as e:
            logger.warning(f"Failed to send invitation email to {email}: {e}")
        
        return Response({
            'message': 'عضو جدید با موفقیت اضافه شد',
            'member': {
                'id': str(new_member.id),
                'email': new_member.email,
                'role': new_member.organization_role,
                'first_name': new_member.first_name,
                'last_name': new_member.last_name
            }
        }, status=201)


class OrganizationMemberDetailView(APIView):
    """مدیریت یک عضو خاص"""
    permission_classes = [IsOrganizationAdmin]
    
    def patch(self, request, member_id):
        """تغییر نقش عضو"""
        user = request.user
        organization = user.owned_organizations.first() or user.organization
        
        if not organization:
            return Response({'error': 'سازمان یافت نشد'}, status=404)
        
        try:
            member = organization.members.get(id=member_id)
        except User.DoesNotExist:
            return Response({'error': 'عضو یافت نشد'}, status=404)
        
        # Cannot change owner's role
        if organization.owner == member:
            return Response({'error': 'نمی‌توان نقش مالک سازمان را تغییر داد'}, status=400)
        
        new_role = request.data.get('role')
        if new_role and new_role in ['admin', 'member']:
            member.organization_role = new_role
            member.save()
            
            return Response({
                'message': 'نقش عضو با موفقیت تغییر کرد',
                'member': {
                    'id': str(member.id),
                    'email': member.email,
                    'role': member.organization_role
                }
            })
        
        return Response({'error': 'نقش نامعتبر است'}, status=400)
    
    def delete(self, request, member_id):
        """حذف عضو از سازمان"""
        user = request.user
        organization = user.owned_organizations.first() or user.organization
        
        if not organization:
            return Response({'error': 'سازمان یافت نشد'}, status=404)
        
        try:
            member = organization.members.get(id=member_id)
        except User.DoesNotExist:
            return Response({'error': 'عضو یافت نشد'}, status=404)
        
        # Cannot delete owner
        if organization.owner == member:
            return Response({'error': 'نمی‌توان مالک سازمان را حذف کرد'}, status=400)
        
        # Cannot delete yourself
        if member == user:
            return Response({'error': 'نمی‌توانید خودتان را حذف کنید'}, status=400)
        
        email = member.email
        member.delete()  # This will also delete their conversations
        
        logger.info(f"Organization member deleted: {email} from {organization.name}")
        
        return Response({
            'message': 'عضو با موفقیت حذف شد'
        })


class OrganizationUsageView(APIView):
    """نمودار مصرف سازمان"""
    permission_classes = [IsOrganizationAdmin]
    
    def get(self, request):
        """آمار مصرف کل سازمان"""
        user = request.user
        organization = user.owned_organizations.first() or user.organization
        
        if not organization:
            return Response({'error': 'سازمان یافت نشد'}, status=404)
        
        # Get all member IDs
        member_ids = list(organization.members.values_list('id', flat=True))
        
        # Get subscription
        subscription = Subscription.objects.filter(
            user=organization.owner or user,
            status='active',
            end_date__gt=timezone.now()
        ).first()
        
        daily_limit = 10
        monthly_limit = 300
        if subscription and subscription.plan:
            daily_limit = subscription.plan.max_queries_per_day
            monthly_limit = subscription.plan.max_queries_per_month
        
        # Today's usage
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        daily_usage = Message.objects.filter(
            conversation__user_id__in=member_ids,
            role='user',
            created_at__gte=today_start
        ).count()
        
        # This month's usage
        month_start = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_usage = Message.objects.filter(
            conversation__user_id__in=member_ids,
            role='user',
            created_at__gte=month_start
        ).count()
        
        # Usage by member
        member_usage = Message.objects.filter(
            conversation__user_id__in=member_ids,
            role='user',
            created_at__gte=month_start
        ).values('conversation__user__email').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Daily trend (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_trend = Message.objects.filter(
            conversation__user_id__in=member_ids,
            role='user',
            created_at__gte=thirty_days_ago
        ).annotate(
            date=TruncDate('created_at')
        ).values('date').annotate(
            count=Count('id')
        ).order_by('date')
        
        return Response({
            'daily': {
                'used': daily_usage,
                'limit': daily_limit,
                'percentage': round((daily_usage / daily_limit) * 100, 1) if daily_limit > 0 else 0
            },
            'monthly': {
                'used': monthly_usage,
                'limit': monthly_limit,
                'percentage': round((monthly_usage / monthly_limit) * 100, 1) if monthly_limit > 0 else 0
            },
            'by_member': [
                {'email': item['conversation__user__email'], 'count': item['count']}
                for item in member_usage
            ],
            'daily_trend': [
                {'date': item['date'].isoformat(), 'count': item['count']}
                for item in daily_trend
            ]
        })
