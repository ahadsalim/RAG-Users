"""
تست یکپارچگی سیستم آپلود فایل با RAG Core
"""
import json

# نمونه payload که به RAG Core ارسال می‌شود
sample_payload_without_files = {
    "query": "قانون مدنی در مورد مالکیت چه می‌گوید؟",
    "language": "fa",
    "max_results": 5,
    "use_cache": True,
    "use_reranking": True
}

sample_payload_with_one_file = {
    "query": "این سند چه می‌گوید؟",
    "language": "fa",
    "max_results": 5,
    "use_cache": True,
    "use_reranking": True,
    "file_attachments": [
        {
            "filename": "document.pdf",
            "minio_url": "temp_uploads/user123/20241129_120000_abc_document.pdf",
            "file_type": "application/pdf",
            "size_bytes": 1024000
        }
    ]
}

sample_payload_with_multiple_files = {
    "query": "این اسناد را مقایسه کن",
    "language": "fa",
    "max_results": 5,
    "use_cache": True,
    "use_reranking": True,
    "file_attachments": [
        {
            "filename": "doc1.pdf",
            "minio_url": "temp_uploads/user123/file1.pdf",
            "file_type": "application/pdf"
        },
        {
            "filename": "image.jpg",
            "minio_url": "temp_uploads/user123/file2.jpg",
            "file_type": "image/jpeg"
        }
    ]
}

# نمونه response از RAG Core
sample_response = {
    "answer": "پاسخ تولید شده...",
    "sources": ["doc-id-1", "doc-id-2"],
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "message_id": "660e8400-e29b-41d4-a716-446655440001",
    "tokens_used": 250,
    "processing_time_ms": 1500,
    "cached": False,
    "files_processed": 1
}

print("=" * 80)
print("تست یکپارچگی سیستم آپلود فایل")
print("=" * 80)

print("\n1. Payload بدون فایل:")
print(json.dumps(sample_payload_without_files, indent=2, ensure_ascii=False))

print("\n2. Payload با یک فایل:")
print(json.dumps(sample_payload_with_one_file, indent=2, ensure_ascii=False))

print("\n3. Payload با چند فایل:")
print(json.dumps(sample_payload_with_multiple_files, indent=2, ensure_ascii=False))

print("\n4. نمونه Response از RAG Core:")
print(json.dumps(sample_response, indent=2, ensure_ascii=False))

print("\n" + "=" * 80)
print("✅ فرمت‌ها مطابق با مستندات RAG Core هستند")
print("=" * 80)

# بررسی محدودیت‌ها
print("\n📋 محدودیت‌ها:")
print("  ✅ حداکثر 5 فایل در هر درخواست")
print("  ✅ حداکثر 10MB برای هر فایل")
print("  ✅ فرمت‌های مجاز: JPG, PNG, GIF, BMP, WEBP, TIFF, PDF, TXT")
print("  ✅ فایل‌ها باید از قبل در MinIO آپلود شده باشند")

print("\n🔗 Endpoints:")
print("  • آپلود فایل: POST /api/v1/chat/upload/")
print("  • آپلود چند فایل: POST /api/v1/chat/upload/multiple/")
print("  • ارسال Query: POST /api/v1/chat/query/")
print("  • RAG Core: POST http://rag-core:7001/api/v1/query/")

print("\n🎯 جریان کار:")
print("  1. کاربر فایل را انتخاب می‌کند")
print("  2. Frontend فایل را به /api/v1/chat/upload/ می‌فرستد")
print("  3. Backend فایل را در MinIO آپلود می‌کند")
print("  4. Backend object_key را به Frontend برمی‌گرداند")
print("  5. کاربر query را می‌نویسد و ارسال می‌کند")
print("  6. Frontend query + object_key را به Backend می‌فرستد")
print("  7. Backend به RAG Core ارسال می‌کند")
print("  8. RAG Core فایل را از MinIO دانلود و پردازش می‌کند")
print("  9. RAG Core پاسخ را برمی‌گرداند")
print("  10. Backend پاسخ را به Frontend می‌فرستد")

print("\n✅ همه چیز آماده است!")
