#!/bin/bash
# Cron job برای پاک‌سازی خودکار توکن‌ها و session های قدیمی
# اجرا: هر روز ساعت 3 صبح
# 0 3 * * * /srv/deployment/cron/cleanup-tokens.sh >> /var/log/cleanup-tokens.log 2>&1

echo "$(date): Starting token cleanup..."
docker exec app_backend python manage.py cleanup_tokens --max-tokens-per-user 3 --session-days 30
echo "$(date): Token cleanup completed"
