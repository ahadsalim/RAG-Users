#!/usr/bin/env python3
"""
حذف تمام مکالمات و پیام‌ها از دیتابیس
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from chat.models import Conversation, Message

print('='*80)
print('🗑️  حذف تمام مکالمات و پیام‌ها')
print('='*80)

# شمارش قبل از حذف
conversations_count = Conversation.objects.count()
messages_count = Message.objects.count()

print(f'\n📊 وضعیت فعلی:')
print(f'   - تعداد مکالمات: {conversations_count}')
print(f'   - تعداد پیام‌ها: {messages_count}')

if conversations_count == 0 and messages_count == 0:
    print('\n✅ دیتابیس خالی است، نیازی به حذف نیست')
else:
    print(f'\n⚠️  در حال حذف {conversations_count} مکالمه و {messages_count} پیام...')
    
    # حذف تمام پیام‌ها
    Message.objects.all().delete()
    print('✅ تمام پیام‌ها حذف شدند')
    
    # حذف تمام مکالمات
    Conversation.objects.all().delete()
    print('✅ تمام مکالمات حذف شدند')
    
    # بررسی نهایی
    print('\n📊 وضعیت بعد از حذف:')
    print(f'   - تعداد مکالمات: {Conversation.objects.count()}')
    print(f'   - تعداد پیام‌ها: {Message.objects.count()}')
    
    print('\n🎉 دیتابیس پاکسازی شد!')
    print('✅ سیستم آماده است برای شروع مجدد با سیستم مرکزی')

print('\n' + '='*80)
