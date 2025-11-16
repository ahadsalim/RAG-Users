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
    SharedConversationView
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
    
    # Shared conversations
    path('shared/<str:share_token>/', SharedConversationView.as_view(), name='shared-conversation'),
    
    # ViewSets
    path('', include(router.urls)),
    path('', include(conversations_router.urls)),
]
