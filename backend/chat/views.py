"""
Views برای ماژول چت
"""
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db.models import Q, Count
from django.http import StreamingHttpResponse, HttpResponse
import asyncio
import json
import uuid
import logging
from typing import AsyncGenerator

from .models import (
    Conversation, Message, ConversationFolder,
    ChatTemplate, SharedConversation, MessageAttachment
)
from .serializers import (
    ConversationSerializer, ConversationDetailSerializer,
    MessageSerializer, ConversationFolderSerializer,
    ChatTemplateSerializer, SharedConversationSerializer,
    QueryRequestSerializer, QueryResponseSerializer,
    MessageFeedbackSerializer, ConversationExportSerializer,
    BulkConversationActionSerializer
)
from .core_service import core_service
from accounts.models import AuditLog
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger('app')


class RAGCoreException(Exception):
    """Exception for RAG Core errors"""
    pass


class RateLimitException(Exception):
    """Exception for rate limit errors"""
    pass


class QueryView(APIView):
    """ارسال سوال به سیستم RAG Core"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """ارسال سوال معمولی (non-streaming)"""
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user = request.user
        
        # بررسی اشتراک کاربر
        if not user.is_superuser:
            from subscriptions.models import Subscription
            active_subscription = user.subscriptions.filter(
                status__in=['active', 'trial'],
                end_date__gt=timezone.now()
            ).first()
            
            if not active_subscription:
                return Response(
                    {
                        'error': 'شما اشتراک فعالی ندارید',
                        'code': 'NO_ACTIVE_SUBSCRIPTION',
                        'plans_url': '/api/v1/plans/'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # بررسی محدودیت روزانه و ماهانه
            can_query, message = active_subscription.can_query()
            if not can_query:
                return Response(
                    {
                        'error': message,
                        'code': 'QUOTA_EXCEEDED',
                        'usage': {
                            'daily_used': active_subscription.queries_used_today,
                            'daily_limit': active_subscription.plan.max_queries_per_day,
                            'monthly_used': active_subscription.queries_used_month,
                            'monthly_limit': active_subscription.plan.max_queries_per_month,
                        }
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
        
        # دریافت یا ایجاد conversation
        conversation_id = data.get('conversation_id')
        conversation = None
        
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=user
            )
        else:
            # ایجاد conversation جدید
            conversation = Conversation.objects.create(
                user=user,
                organization=user.organization,
                title=data['query'][:50] + '...' if len(data['query']) > 50 else data['query'],
                default_response_mode=data.get('response_mode', 'simple_explanation')
            )
        
        # ایجاد پیام کاربر
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=data['query'],
            response_mode=data.get('response_mode', 'simple_explanation'),
            status='completed'
        )
        
        # ایجاد پیام assistant (در حالت processing)
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content='',
            status='processing'
        )
        
        try:
            # Generate JWT token for Core API
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            
            # Get user preferences as object (not just response_style)
            user_preferences = None
            if user.preferences:
                user_preferences = {
                    'response_style': user.preferences.get('response_style', 'formal'),
                    'detail_level': user.preferences.get('detail_level', 'moderate'),
                    'include_examples': user.preferences.get('include_examples', True),
                    'language_style': user.preferences.get('language_style', 'simple'),
                    'format': user.preferences.get('format', 'paragraph')
                }
            
            # آماده‌سازی file_attachments برای ارسال به RAG Core
            file_attachments = None
            if 'file_attachments' in data and data['file_attachments']:
                file_attachments = [
                    {
                        'filename': f['filename'],
                        'minio_url': f['minio_url'],
                        'file_type': f['file_type'],
                        'size_bytes': f.get('size_bytes')
                    }
                    for f in data['file_attachments']
                ]
            
            # ارسال به RAG Core به صورت async
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(
                core_service.send_query(
                    query=data['query'],
                    token=access_token,
                    conversation_id=conversation.rag_conversation_id or None,
                    language='fa',
                    stream=False,
                    filters=data.get('filters'),
                    user_preferences=user_preferences,
                    file_attachments=file_attachments
                )
            )
            
            # به‌روزرسانی conversation با ID از RAG Core
            if not conversation.rag_conversation_id and 'metadata' in response:
                conversation.rag_conversation_id = response['metadata'].get('conversation_id')
                conversation.save(update_fields=['rag_conversation_id'])
            
            # به‌روزرسانی پیام assistant
            assistant_message.content = response.get('answer', '')
            assistant_message.sources = response.get('sources', [])
            assistant_message.chunks = response.get('chunks', [])
            assistant_message.status = 'completed'
            assistant_message.tokens = response.get('metadata', {}).get('total_tokens', 0)
            assistant_message.processing_time_ms = response.get('metadata', {}).get('processing_time_ms', 0)
            assistant_message.model_used = response.get('metadata', {}).get('model_used', '')
            assistant_message.cached = response.get('metadata', {}).get('cached', False)
            assistant_message.rag_message_id = response.get('metadata', {}).get('message_id', '')
            assistant_message.save()
            
            # به‌روزرسانی آمار conversation
            conversation.message_count = conversation.messages.count()
            conversation.token_usage = conversation.messages.aggregate(
                total=Count('tokens')
            )['total'] or 0
            conversation.last_message_at = timezone.now()
            conversation.save()
            
            # ثبت در audit log
            AuditLog.objects.create(
                user=user,
                action='chat_query',
                details={
                    'conversation_id': str(conversation.id),
                    'query_length': len(data['query']),
                    'tokens_used': assistant_message.tokens
                },
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # به‌روزرسانی مصرف اشتراک
            if not user.is_superuser and 'active_subscription' in locals():
                # active_subscription.increment_usage(tokens=assistant_message.tokens)
                
                # TODO: Implement usage logging when UsageLog model is ready
                # from subscriptions.models import UsageLog
                # UsageLog.objects.create(
                #     subscription=active_subscription,
                #     user=user,
                #     action_type='query',
                #     tokens_used=assistant_message.tokens,
                #     metadata={
                #         'conversation_id': str(conversation.id),
                #         'message_id': str(assistant_message.id),
                #         'model': assistant_message.model_used
                #     },
                #     ip_address=request.META.get('REMOTE_ADDR'),
                #     user_agent=request.META.get('HTTP_USER_AGENT', '')
                # )
                pass
            
            # آماده‌سازی پاسخ
            return Response({
                'conversation_id': conversation.id,
                'message_id': assistant_message.id,
                'answer': assistant_message.content,
                'sources': assistant_message.sources,
                'chunks': assistant_message.chunks,
                'metadata': {
                    'tokens': assistant_message.tokens,
                    'processing_time_ms': assistant_message.processing_time_ms,
                    'model_used': assistant_message.model_used,
                    'cached': assistant_message.cached
                },
                'user_info': response.get('user_info', {})
            }, status=status.HTTP_200_OK)
            
        except RateLimitException as e:
            assistant_message.status = 'failed'
            assistant_message.error_message = str(e)
            assistant_message.save()
            return Response(
                {'error': str(e), 'code': 'rate_limit_exceeded'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        except RAGCoreException as e:
            assistant_message.status = 'failed'
            assistant_message.error_message = str(e)
            assistant_message.save()
            return Response(
                {'error': str(e), 'code': 'rag_core_error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in query: {str(e)}")
            assistant_message.status = 'failed'
            assistant_message.error_message = str(e)
            assistant_message.save()
            return Response(
                {'error': 'خطای غیرمنتظره در پردازش سوال'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StreamingQueryView(APIView):
    """ارسال سوال با پاسخ streaming"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """ارسال سوال با streaming response"""
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        user = request.user
        
        # دریافت یا ایجاد conversation
        conversation_id = data.get('conversation_id')
        conversation = None
        
        if conversation_id:
            conversation = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=user
            )
        else:
            conversation = Conversation.objects.create(
                user=user,
                organization=user.organization,
                title=data['query'][:50] + '...' if len(data['query']) > 50 else data['query'],
                default_response_mode=data.get('response_mode', 'simple_explanation')
            )
        
        # ایجاد پیام کاربر
        user_message = Message.objects.create(
            conversation=conversation,
            role='user',
            content=data['query'],
            response_mode=data.get('response_mode', 'simple_explanation'),
            status='completed'
        )
        
        # ایجاد پیام assistant
        assistant_message = Message.objects.create(
            conversation=conversation,
            role='assistant',
            content='',
            status='processing'
        )
        
        async def generate_stream():
            """Generator برای streaming response"""
            try:
                # Generate JWT token for Core API
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                
                # Get user preferences as object
                user_preferences = None
                if user.preferences:
                    user_preferences = {
                        'response_style': user.preferences.get('response_style', 'formal'),
                        'detail_level': user.preferences.get('detail_level', 'moderate'),
                        'include_examples': user.preferences.get('include_examples', True),
                        'language_style': user.preferences.get('language_style', 'simple'),
                        'format': user.preferences.get('format', 'paragraph')
                    }
                
                full_content = ""
                sources = []
                chunks = []
                metadata = {}
                
                # ارسال اطلاعات اولیه
                yield f"data: {json.dumps({'type': 'start', 'conversation_id': str(conversation.id), 'message_id': str(assistant_message.id)})}\n\n"
                
                # دریافت stream از RAG Core
                async for chunk_text in core_service.send_query_stream(
                    query=data['query'],
                    token=access_token,
                    conversation_id=conversation.rag_conversation_id,
                    language='fa',
                    filters=data.get('filters'),
                    user_preferences=user_preferences
                ):
                    # Parse JSON chunk
                    try:
                        chunk_data = json.loads(chunk_text)
                        chunk_type = chunk_data.get('type')
                        
                        if chunk_type == 'chunk':
                            content = chunk_data.get('content', '')
                            full_content += content
                            yield f"data: {json.dumps({'type': 'chunk', 'content': content})}\n\n"
                        
                        elif chunk_type == 'sources':
                            sources = chunk_data.get('sources', [])
                            yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"
                        
                        elif chunk_type == 'end':
                            metadata = chunk_data.get('metadata', {})
                            chunks = chunk_data.get('chunks', [])
                            yield f"data: {json.dumps({'type': 'end', 'metadata': metadata})}\n\n"
                    except json.JSONDecodeError:
                        # اگر JSON نبود، مستقیم به عنوان content ارسال کن
                        full_content += chunk_text
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk_text})}\n\n"
                
                # به‌روزرسانی پیام در دیتابیس
                assistant_message.content = full_content
                assistant_message.sources = sources
                assistant_message.chunks = chunks
                assistant_message.status = 'completed'
                assistant_message.tokens = metadata.get('tokens', 0)
                assistant_message.processing_time_ms = metadata.get('processing_time_ms', 0)
                assistant_message.model_used = metadata.get('model_used', '')
                assistant_message.cached = metadata.get('cached', False)
                await asyncio.get_event_loop().run_in_executor(None, assistant_message.save)
                
                # به‌روزرسانی conversation
                await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: conversation.update_stats()
                )
                
            except Exception as e:
                logger.error(f"Error in streaming: {str(e)}")
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
                
                # به‌روزرسانی وضعیت خطا
                assistant_message.status = 'failed'
                assistant_message.error_message = str(e)
                await asyncio.get_event_loop().run_in_executor(None, assistant_message.save)
        
        # برگرداندن streaming response
        response = StreamingHttpResponse(
            generate_stream(),
            content_type='text/event-stream'
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


class ConversationViewSet(viewsets.ModelViewSet):
    """مدیریت گفتگوها"""
    serializer_class = ConversationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = Conversation.objects.filter(user=user)
        
        # فیلترها
        folder_id = self.request.query_params.get('folder')
        if folder_id:
            queryset = queryset.filter(folder_id=folder_id)
        
        is_pinned = self.request.query_params.get('pinned')
        if is_pinned is not None:
            queryset = queryset.filter(is_pinned=is_pinned == 'true')
        
        is_archived = self.request.query_params.get('archived')
        if is_archived is not None:
            queryset = queryset.filter(is_archived=is_archived == 'true')
        
        # جستجو
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(description__icontains=search) |
                Q(messages__content__icontains=search)
            ).distinct()
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ConversationDetailSerializer
        return ConversationSerializer
    
    @action(detail=True, methods=['post'])
    def pin(self, request, pk=None):
        """پین کردن گفتگو"""
        conversation = self.get_object()
        conversation.is_pinned = True
        conversation.save()
        return Response({'status': 'pinned'})
    
    @action(detail=True, methods=['post'])
    def unpin(self, request, pk=None):
        """برداشتن پین گفتگو"""
        conversation = self.get_object()
        conversation.is_pinned = False
        conversation.save()
        return Response({'status': 'unpinned'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """آرشیو کردن گفتگو"""
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        return Response({'status': 'archived'})
    
    @action(detail=True, methods=['post'])
    def unarchive(self, request, pk=None):
        """خارج کردن از آرشیو"""
        conversation = self.get_object()
        conversation.is_archived = False
        conversation.save()
        return Response({'status': 'unarchived'})
    
    def destroy(self, request, *args, **kwargs):
        """
        حذف گفتگو
        ابتدا از Core حذف می‌شود، سپس از Django
        اگر حذف از Core ناموفق باشد، خطا برمی‌گرداند
        """
        conversation = self.get_object()
        
        try:
            # Signal به طور خودکار حذف از Core را انجام می‌دهد
            # اگر خطا رخ دهد، exception می‌فرستد و حذف متوقف می‌شود
            conversation.delete()
            
            return Response(
                {'message': 'گفتگو با موفقیت حذف شد'},
                status=status.HTTP_204_NO_CONTENT
            )
            
        except Exception as e:
            logger.error(f"Failed to delete conversation {conversation.id}: {e}")
            return Response(
                {
                    'error': 'خطا در حذف گفتگو',
                    'detail': 'امکان حذف از سیستم مرکزی وجود ندارد. لطفا دوباره تلاش کنید.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def share(self, request, pk=None):
        """اشتراک‌گذاری گفتگو"""
        conversation = self.get_object()
        
        # ایجاد توکن اشتراک
        share_token = str(uuid.uuid4())
        
        shared = SharedConversation.objects.create(
            conversation=conversation,
            shared_by=request.user,
            share_token=share_token,
            **request.data
        )
        
        conversation.is_shared = True
        conversation.share_token = share_token
        conversation.save()
        
        serializer = SharedConversationSerializer(shared)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def export(self, request, pk=None):
        """Export گفتگو"""
        conversation = self.get_object()
        serializer = ConversationExportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        format = serializer.validated_data['format']
        
        # TODO: پیاده‌سازی export به فرمت‌های مختلف
        
        return Response({'status': 'export started'})
    
    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        """عملیات گروهی روی گفتگوها"""
        serializer = BulkConversationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        conversation_ids = data['conversation_ids']
        action = data['action']
        
        conversations = Conversation.objects.filter(
            id__in=conversation_ids,
            user=request.user
        )
        
        if action == 'archive':
            conversations.update(is_archived=True)
        elif action == 'unarchive':
            conversations.update(is_archived=False)
        elif action == 'delete':
            conversations.delete()
        elif action == 'move_to_folder':
            folder_id = data.get('folder_id')
            conversations.update(folder_id=folder_id)
        elif action == 'tag':
            tags = data.get('tags', [])
            for conv in conversations:
                conv.tags = list(set(conv.tags + tags))
                conv.save()
        
        return Response({'status': 'success', 'affected': conversations.count()})


class MessageViewSet(viewsets.ModelViewSet):
    """مدیریت پیام‌ها"""
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        conversation_id = self.kwargs.get('conversation_pk')
        return Message.objects.filter(
            conversation_id=conversation_id,
            conversation__user=self.request.user
        )
    
    @action(detail=True, methods=['post'])
    def feedback(self, request, conversation_pk=None, pk=None):
        """ارسال بازخورد برای پیام"""
        message = self.get_object()
        serializer = MessageFeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        
        # به‌روزرسانی پیام
        message.rating = data.get('rating', message.rating)
        message.feedback_type = data.get('feedback_type', message.feedback_type)
        message.feedback_text = data.get('feedback_text', message.feedback_text)
        message.save()
        
        # ارسال به RAG Core
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        success = loop.run_until_complete(
            rag_client.send_feedback(
                user=request.user,
                message_id=message.rag_message_id,
                **data
            )
        )
        
        return Response({
            'status': 'success' if success else 'failed',
            'message': 'بازخورد شما ثبت شد' if success else 'خطا در ثبت بازخورد'
        })


class ConversationFolderViewSet(viewsets.ModelViewSet):
    """مدیریت پوشه‌های گفتگو"""
    serializer_class = ConversationFolderSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return ConversationFolder.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ChatTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """قالب‌های چت"""
    serializer_class = ChatTemplateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = ChatTemplate.objects.filter(
            Q(is_public=True) | Q(created_by=self.request.user),
            is_active=True
        )
        
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        
        return queryset
    
    @action(detail=True, methods=['post'])
    def use(self, request, pk=None):
        """استفاده از قالب"""
        template = self.get_object()
        template.usage_count += 1
        template.save()
        
        return Response({
            'prompt': template.prompt_template,
            'variables': template.variables
        })


class SharedConversationView(APIView):
    """مشاهده گفتگوی اشتراکی"""
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, share_token):
        """دریافت گفتگوی اشتراکی"""
        shared = get_object_or_404(
            SharedConversation,
            share_token=share_token
        )
        
        # بررسی انقضا
        if shared.is_expired():
            return Response(
                {'error': 'این لینک منقضی شده است'},
                status=status.HTTP_410_GONE
            )
        
        # بررسی رمز عبور
        if shared.password_protected:
            password = request.query_params.get('password')
            if not password or not shared.check_password(password):
                return Response(
                    {'error': 'رمز عبور اشتباه است', 'password_required': True},
                    status=status.HTTP_401_UNAUTHORIZED
                )
        
        # به‌روزرسانی آمار
        shared.view_count += 1
        shared.last_viewed_at = timezone.now()
        shared.save()
        
        # برگرداندن داده‌ها
        conversation = shared.conversation
        serializer = ConversationDetailSerializer(conversation)
        
        return Response({
            'conversation': serializer.data,
            'settings': {
                'allow_copy': shared.allow_copy,
                'allow_export': shared.allow_export
            }
        })
