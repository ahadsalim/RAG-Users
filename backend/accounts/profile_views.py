"""
Profile management views
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_profile_image(request):
    """
    آپلود تصویر پروفایل کاربر با محدودیت‌ها:
    - فرمت‌های مجاز: jpg, jpeg, png, webp
    - حداکثر حجم: 150KB
    """
    if 'avatar' not in request.FILES:
        return Response(
            {'error': 'فایل تصویر ارسال نشده است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    avatar_file = request.FILES['avatar']
    
    # بررسی فرمت فایل
    allowed_formats = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    if avatar_file.content_type not in allowed_formats:
        return Response(
            {'error': 'فرمت فایل نامعتبر است. فقط jpg, jpeg, png, webp مجاز است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # بررسی حجم فایل (150KB = 153600 bytes)
    max_size = 150 * 1024  # 150KB
    if avatar_file.size > max_size:
        return Response(
            {'error': f'حجم فایل بیش از حد مجاز است. حداکثر: 150KB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # باز کردن تصویر با PIL برای اعتبارسنجی
        img = Image.open(avatar_file)
        img.verify()
        
        # بازگشایی مجدد برای پردازش (verify() فایل را می‌بندد)
        avatar_file.seek(0)
        img = Image.open(avatar_file)
        
        # تبدیل به RGB اگر RGBA است
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # ذخیره تصویر در حافظه
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # ایجاد فایل جدید
        new_avatar = InMemoryUploadedFile(
            output,
            'ImageField',
            f"{request.user.id}_avatar.jpg",
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
        # حذف تصویر قبلی اگر وجود دارد
        if request.user.avatar:
            request.user.avatar.delete(save=False)
        
        # ذخیره تصویر جدید
        request.user.avatar = new_avatar
        request.user.save(update_fields=['avatar'])
        
        return Response({
            'message': 'تصویر پروفایل با موفقیت آپلود شد',
            'avatar_url': request.user.avatar.url
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': f'خطا در پردازش تصویر: {str(e)}'},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_profile_image(request):
    """حذف تصویر پروفایل کاربر"""
    if request.user.avatar:
        request.user.avatar.delete(save=True)
        return Response(
            {'message': 'تصویر پروفایل با موفقیت حذف شد'},
            status=status.HTTP_200_OK
        )
    
    return Response(
        {'error': 'تصویر پروفایلی وجود ندارد'},
        status=status.HTTP_404_NOT_FOUND
    )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    به‌روزرسانی اطلاعات پروفایل کاربر
    فیلدهای قابل ویرایش: first_name, last_name, national_id, bio, preferred_currency
    """
    user = request.user
    
    # فیلدهای قابل ویرایش
    editable_fields = ['first_name', 'last_name', 'national_id', 'bio', 'preferred_currency_id']
    
    updated_fields = []
    for field in editable_fields:
        if field in request.data:
            setattr(user, field, request.data[field])
            updated_fields.append(field)
    
    if updated_fields:
        user.save(update_fields=updated_fields)
        
        from .serializers import UserProfileSerializer
        serializer = UserProfileSerializer(user)
        
        return Response({
            'message': 'اطلاعات پروفایل با موفقیت به‌روزرسانی شد',
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(
        {'error': 'هیچ فیلدی برای به‌روزرسانی ارسال نشده است'},
        status=status.HTTP_400_BAD_REQUEST
    )
