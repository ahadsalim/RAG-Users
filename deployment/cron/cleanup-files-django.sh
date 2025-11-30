#!/bin/bash
# Cron job برای پاک‌سازی خودکار فایل‌های قدیمی از MinIO
# استفاده از Django management command
# اجرا: هر روز ساعت 2 صبح

echo "$(date): Starting MinIO cleanup..."
docker exec app_backend python3 manage.py cleanup_old_files --hours 24
echo "$(date): Cleanup completed"
