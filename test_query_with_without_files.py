#!/usr/bin/env python3
"""
تست query با فایل و بدون فایل
"""
import os
import sys
import django

sys.path.insert(0, '/app')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from chat.core_service import CoreAPIService
from core.storage import s3_service
import json
import asyncio

User = get_user_model()

def test_without_files():
    """تست query بدون فایل"""
    print('\n' + '='*80)
    print('🧪 تست 1: Query بدون فایل')
    print('='*80)
    
    try:
        # تولید token
        user = User.objects.first()
        if not user:
            print('❌ کاربری وجود ندارد')
            return False
            
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        print(f'✅ کاربر: {user.username}')
        print(f'✅ Token: {token[:50]}...')
        
        # ارسال query ساده
        core_service = CoreAPIService()
        
        print('\n📤 ارسال query...')
        print('   Query: "قانون کار در مورد مرخصی استعلاجی چه می‌گوید؟"')
        
        response = asyncio.run(core_service.send_query(
            query="قانون کار در مورد مرخصی استعلاجی چه می‌گوید؟",
            token=token,
            language='fa'
        ))
        
        print('\n✅ پاسخ دریافت شد!')
        print(f'   Answer: {response.get("answer", "")[:200]}...')
        print(f'   Conversation ID: {response.get("conversation_id", "N/A")}')
        print(f'   Tokens: {response.get("tokens_used", 0)}')
        print(f'   Processing Time: {response.get("processing_time_ms", 0)} ms')
        print(f'   Context Used: {response.get("context_used", False)}')
        print(f'   Sources: {len(response.get("sources", []))} منبع')
        
        return True
        
    except Exception as e:
        print(f'\n❌ خطا: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        return False


def test_with_files():
    """تست query با فایل"""
    print('\n' + '='*80)
    print('🧪 تست 2: Query با فایل')
    print('='*80)
    
    try:
        # تولید token
        user = User.objects.first()
        if not user:
            print('❌ کاربری وجود ندارد')
            return False
            
        refresh = RefreshToken.for_user(user)
        token = str(refresh.access_token)
        
        print(f'✅ کاربر: {user.username}')
        print(f'✅ User ID: {user.id}')
        
        # آپلود فایل تستی
        print('\n📤 آپلود فایل تستی...')
        
        test_content = '''
        قرارداد خرید و فروش
        
        طرفین قرارداد:
        1. فروشنده: شرکت تجارت الکترونیک
        2. خریدار: آقای احمد محمدی
        
        موضوع: خرید یک دستگاه لپ‌تاپ
        مبلغ: 50,000,000 ریال
        تاریخ تحویل: 1403/09/15
        
        شرایط پرداخت:
        - پیش‌پرداخت 30%
        - باقیمانده هنگام تحویل
        
        امضا طرفین
        '''.encode('utf-8')
        
        upload_result = s3_service.upload_file(
            file_content=test_content,
            filename='contract_test.txt',
            user_id=str(user.id),
            content_type='text/plain'
        )
        
        print(f'✅ فایل آپلود شد')
        print(f'   Object Key: {upload_result["object_key"]}')
        print(f'   Size: {upload_result["size_bytes"]} bytes')
        
        # آماده‌سازی file_attachments
        file_attachments = [
            {
                'filename': 'contract_test.txt',
                'minio_url': upload_result['object_key'],
                'file_type': 'text/plain',
                'size_bytes': upload_result['size_bytes']
            }
        ]
        
        # ارسال query با فایل
        core_service = CoreAPIService()
        
        print('\n📤 ارسال query با فایل...')
        print('   Query: "این قرارداد را بررسی کن و نکات مهم را بگو"')
        print(f'   Files: {len(file_attachments)} فایل')
        
        response = asyncio.run(core_service.send_query(
            query="این قرارداد را بررسی کن و نکات مهم آن را خلاصه کن",
            token=token,
            language='fa',
            file_attachments=file_attachments
        ))
        
        print('\n✅ پاسخ دریافت شد!')
        print(f'   Answer: {response.get("answer", "")[:300]}...')
        print(f'   Conversation ID: {response.get("conversation_id", "N/A")}')
        print(f'   Tokens: {response.get("tokens_used", 0)}')
        print(f'   Processing Time: {response.get("processing_time_ms", 0)} ms')
        print(f'   Context Used: {response.get("context_used", False)}')
        print(f'   Sources: {len(response.get("sources", []))} منبع')
        
        # بررسی file_analysis
        if 'file_analysis' in response:
            print(f'\n📊 File Analysis:')
            file_analysis = response['file_analysis']
            if isinstance(file_analysis, list):
                for i, analysis in enumerate(file_analysis, 1):
                    print(f'   {i}. {analysis.get("filename", "N/A")}')
                    print(f'      Status: {analysis.get("status", "N/A")}')
                    if 'summary' in analysis:
                        print(f'      Summary: {analysis["summary"][:100]}...')
            else:
                print(f'   {json.dumps(file_analysis, indent=2, ensure_ascii=False)[:200]}...')
        else:
            print('\n⚠️  هیچ file_analysis در پاسخ وجود ندارد')
        
        # پاکسازی فایل تستی
        print('\n🗑️  پاکسازی فایل تستی...')
        s3_service.delete_file(upload_result['object_key'])
        print('✅ فایل حذف شد')
        
        return True
        
    except Exception as e:
        print(f'\n❌ خطا: {type(e).__name__}: {e}')
        import traceback
        traceback.print_exc()
        return False


def main():
    print('='*80)
    print('🧪 تست کامل Query با و بدون فایل')
    print('='*80)
    
    # تست 1: بدون فایل
    test1_result = test_without_files()
    
    # تست 2: با فایل
    test2_result = test_with_files()
    
    # خلاصه نتایج
    print('\n' + '='*80)
    print('📊 خلاصه نتایج')
    print('='*80)
    
    print(f'\n1. Query بدون فایل: {"✅ موفق" if test1_result else "❌ ناموفق"}')
    print(f'2. Query با فایل: {"✅ موفق" if test2_result else "❌ ناموفق"}')
    
    if test1_result and test2_result:
        print('\n🎉 همه تست‌ها موفق بود!')
        print('\n✅ سیستم آماده است:')
        print('   - Query ساده کار می‌کند')
        print('   - Query با فایل کار می‌کند')
        print('   - آپلود به MinIO موفق است')
        print('   - ارتباط با سیستم مرکزی برقرار است')
    else:
        print('\n⚠️  برخی تست‌ها ناموفق بودند')
    
    print('\n' + '='*80)


if __name__ == '__main__':
    main()
