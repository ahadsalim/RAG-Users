"""
Django management command برای پاک‌سازی فایل‌های قدیمی از MinIO.

استفاده:
    python manage.py cleanup_old_files --hours 24
    python manage.py cleanup_old_files --all
"""
from django.core.management.base import BaseCommand
from core.storage import S3Service
from datetime import datetime, timedelta


class Command(BaseCommand):
    help = 'پاک‌سازی فایل‌های قدیمی از MinIO'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='حذف فایل‌های قدیمی‌تر از X ساعت (پیش‌فرض: 24)'
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='حذف تمام فایل‌ها (خطرناک!)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='فقط نمایش فایل‌ها بدون حذف'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        delete_all = options['all']
        dry_run = options['dry_run']
        
        s3 = S3Service()
        bucket = 'temp-userfile'
        
        if delete_all:
            self.stdout.write(self.style.WARNING('⚠️  حذف تمام فایل‌ها...'))
            self.cleanup_all(s3, bucket, dry_run)
        else:
            self.stdout.write(self.style.SUCCESS(f'🔍 جستجوی فایل‌های قدیمی‌تر از {hours} ساعت...'))
            self.cleanup_old(s3, bucket, hours, dry_run)

    def cleanup_old(self, s3, bucket, hours, dry_run=False):
        """حذف فایل‌های قدیمی‌تر از X ساعت."""
        try:
            response = s3.s3_client.list_objects_v2(Bucket=bucket)
            
            if 'Contents' not in response:
                self.stdout.write(self.style.SUCCESS('✅ هیچ فایلی در MinIO وجود ندارد.'))
                return
            
            files = response['Contents']
            now = datetime.utcnow()
            cutoff_time = now - timedelta(hours=hours)
            
            deleted_count = 0
            deleted_size = 0
            kept_count = 0
            
            for file in files:
                file_time = file['LastModified'].replace(tzinfo=None)
                age_hours = (now - file_time).total_seconds() / 3600
                
                if file_time < cutoff_time:
                    if dry_run:
                        self.stdout.write(
                            f"  🔍 خواهد حذف شد: {file['Key']} "
                            f"({file['Size']/1024:.1f} KB, {age_hours:.1f} ساعت قدیمی)"
                        )
                    else:
                        try:
                            s3.s3_client.delete_object(Bucket=bucket, Key=file['Key'])
                            deleted_count += 1
                            deleted_size += file['Size']
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"  ❌ حذف شد: {file['Key']} ({file['Size']/1024:.1f} KB)"
                                )
                            )
                        except Exception as e:
                            self.stdout.write(
                                self.style.ERROR(f"  ⚠️  خطا در حذف {file['Key']}: {e}")
                            )
                else:
                    kept_count += 1
            
            self.stdout.write('\n📊 نتیجه:')
            if dry_run:
                self.stdout.write(f"  🔍 فایل‌های قابل حذف: {deleted_count}")
            else:
                self.stdout.write(self.style.SUCCESS(f"  ✅ فایل‌های حذف شده: {deleted_count}"))
                self.stdout.write(f"  💾 حجم آزاد شده: {deleted_size / (1024*1024):.2f} MB")
            self.stdout.write(f"  📁 فایل‌های باقی‌مانده: {kept_count}")
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا: {e}'))

    def cleanup_all(self, s3, bucket, dry_run=False):
        """حذف تمام فایل‌ها."""
        try:
            response = s3.s3_client.list_objects_v2(Bucket=bucket)
            
            if 'Contents' not in response:
                self.stdout.write(self.style.SUCCESS('✅ هیچ فایلی در MinIO وجود ندارد.'))
                return
            
            files = response['Contents']
            total_size = sum(f['Size'] for f in files)
            
            if dry_run:
                self.stdout.write(
                    f"🔍 {len(files)} فایل خواهد حذف شد ({total_size / (1024*1024):.2f} MB)"
                )
            else:
                for file in files:
                    s3.s3_client.delete_object(Bucket=bucket, Key=file['Key'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ {len(files)} فایل حذف شد ({total_size / (1024*1024):.2f} MB)"
                    )
                )
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ خطا: {e}'))
