"""
File upload views for chat attachments.
"""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.core.files.uploadedfile import UploadedFile
import logging

from core.storage import s3_service

logger = logging.getLogger(__name__)

# Allowed file types
ALLOWED_CONTENT_TYPES = [
    'image/jpeg',
    'image/jpg', 
    'image/png',
    'image/gif',
    'image/bmp',
    'image/webp',
    'application/pdf',
    'text/plain',
    'text/markdown',
    'text/x-markdown',
    'text/html',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
]

# Maximum file size (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024

# Maximum number of files per upload
MAX_FILES_PER_UPLOAD = 5


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_file(request):
    """
    آپلود یک فایل به MinIO.
    
    Returns:
        {
            'object_key': 'temp_uploads/user123/file.pdf',
            'filename': 'document.pdf',
            'size_bytes': 1024,
            'content_type': 'application/pdf',
            'expires_at': '2024-11-30T12:00:00',
            'bucket_name': 'shared-storage'
        }
    """
    if 'file' not in request.FILES:
        return Response(
            {'error': 'فایلی ارسال نشده است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    file: UploadedFile = request.FILES['file']
    
    # Validate filename
    if not file.name:
        return Response(
            {'error': 'نام فایل الزامی است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate file size
    if file.size > MAX_FILE_SIZE:
        return Response(
            {'error': f'حجم فایل نباید بیشتر از {MAX_FILE_SIZE // (1024*1024)}MB باشد'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Validate content type
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        return Response(
            {'error': f'نوع فایل {file.content_type} پشتیبانی نمی‌شود'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Read file content
        file_content = file.read()
        
        # Upload to S3
        result = s3_service.upload_file(
            file_content=file_content,
            filename=file.name,
            user_id=str(request.user.id),
            content_type=file.content_type
        )
        
        logger.info(f"User {request.user.id} uploaded file: {file.name}")
        
        return Response(result, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"File upload error: {e}")
        return Response(
            {'error': 'خطا در آپلود فایل'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_multiple_files(request):
    """
    آپلود چند فایل همزمان (حداکثر 5).
    
    Returns:
        {
            'files': [
                {
                    'object_key': '...',
                    'filename': '...',
                    'size_bytes': 1024,
                    'content_type': '...',
                    'expires_at': '...',
                    'bucket_name': '...'
                },
                ...
            ]
        }
    """
    files = request.FILES.getlist('files')
    
    if not files:
        return Response(
            {'error': 'هیچ فایلی ارسال نشده است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(files) > MAX_FILES_PER_UPLOAD:
        return Response(
            {'error': f'حداکثر {MAX_FILES_PER_UPLOAD} فایل مجاز است'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    results = []
    
    for file in files:
        # Validate file size
        if file.size > MAX_FILE_SIZE:
            results.append({
                'filename': file.name,
                'error': f'حجم فایل نباید بیشتر از {MAX_FILE_SIZE // (1024*1024)}MB باشد'
            })
            continue
        
        # Validate content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            results.append({
                'filename': file.name,
                'error': f'نوع فایل {file.content_type} پشتیبانی نمی‌شود'
            })
            continue
        
        try:
            # Read file content
            file_content = file.read()
            
            # Upload to MinIO
            result = minio_service.upload_file(
                file_content=file_content,
                filename=file.name,
                user_id=str(request.user.id),
                content_type=file.content_type
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"File upload error for {file.name}: {e}")
            results.append({
                'filename': file.name,
                'error': 'خطا در آپلود فایل'
            })
    
    logger.info(f"User {request.user.id} uploaded {len(results)} files")
    
    return Response({'files': results}, status=status.HTTP_200_OK)
