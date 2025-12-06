"""
URL Configuration برای ماژول چت
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from .views import (
    QueryView,
    StreamingQueryView,
    ConversationViewSet,
    MessageViewSet,
    ConversationFolderViewSet,
    ChatTemplateViewSet,
    SharedConversationView,
    HealthCheckView
)
from .upload_views import upload_file, upload_multiple_files
from .memory_views import (
    MemoryListView,
    MemoryDetailView,
    MemorySummarizeView,
    MemoryContextView
)

# Router اصلی
router = DefaultRouter()
router.register(r'conversations', ConversationViewSet, basename='conversation')
router.register(r'folders', ConversationFolderViewSet, basename='folder')
router.register(r'templates', ChatTemplateViewSet, basename='template')

# Nested router برای پیام‌های هر گفتگو
conversations_router = routers.NestedDefaultRouter(router, r'conversations', lookup='conversation')
conversations_router.register(r'messages', MessageViewSet, basename='conversation-messages')

app_name = 'chat'

urlpatterns = [
    # Query endpoints
    path('query/', QueryView.as_view(), name='query'),
    path('query/stream/', StreamingQueryView.as_view(), name='query-stream'),
    
    # Health check
    path('health/', HealthCheckView.as_view(), name='health-check'),
    
    # File upload endpoints
    path('upload/', upload_file, name='upload-file'),
    path('upload/multiple/', upload_multiple_files, name='upload-multiple-files'),
    
    # Shared conversations
    path('shared/<str:share_token>/', SharedConversationView.as_view(), name='shared-conversation'),
    
    # Memory endpoints (حافظه بلندمدت کاربر)
    path('memory/', MemoryListView.as_view(), name='memory-list'),
    path('memory/<str:memory_id>/', MemoryDetailView.as_view(), name='memory-detail'),
    path('memory/summarize/', MemorySummarizeView.as_view(), name='memory-summarize'),
    path('memory/context/', MemoryContextView.as_view(), name='memory-context'),
    
    # ViewSets
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]
