#!/bin/bash
# Cron job برای پاک‌سازی خودکار فایل‌های قدیمی از MinIO
# اجرا: هر روز ساعت 2 صبح

echo "$(date): Starting MinIO cleanup..."
docker exec app_backend python3 /srv/cleanup_old_files.py --hours 24
echo "$(date): Cleanup completed"
