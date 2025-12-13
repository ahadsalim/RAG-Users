"""
WebSocket Consumers برای چت real-time
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
import logging

from .models import Conversation, Message
from .core_service import core_service
from accounts.models import AuditLog
from accounts.tokens import CustomAccessToken

logger = logging.getLogger('app')


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket Consumer برای چت real-time"""
    
    async def connect(self):
        """اتصال WebSocket"""
        self.user = self.scope["user"]
        
        # بررسی احراز هویت
        if not self.user.is_authenticated:
            await self.close(code=4001)
            return
        
        # دریافت JWT token برای Core API
        self.jwt_token = await self.get_jwt_token()
        if not self.jwt_token:
            await self.close(code=4002)
            return
        
        # دریافت conversation_id از URL
        self.conversation_id = self.scope['url_route']['kwargs'].get('conversation_id')
        
        # بررسی دسترسی به conversation
        if self.conversation_id:
            has_access = await self.check_conversation_access()
            if not has_access:
                await self.close(code=4003)
                return
            
            # اضافه کردن به گروه conversation
            self.conversation_group_name = f'chat_{self.conversation_id}'
            await self.channel_layer.group_add(
                self.conversation_group_name,
                self.channel_name
            )
        
        # اضافه کردن به گروه کاربر (برای اعلان‌ها)
        self.user_group_name = f'user_{self.user.id}'
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # ارسال پیام خوش‌آمدگویی
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Connected to chat'
        }))
    
    async def disconnect(self, close_code):
        """قطع اتصال WebSocket"""
        # خروج از گروه‌ها
        if hasattr(self, 'conversation_group_name'):
            await self.channel_layer.group_discard(
                self.conversation_group_name,
                self.channel_name
            )
        
        if hasattr(self, 'user_group_name'):
            await self.channel_layer.group_discard(
                self.user_group_name,
                self.channel_name
            )
    
    async def receive(self, text_data):
        """دریافت پیام از WebSocket"""
        try:
            data = json.loads(text_data)
            message_type = data.get('type')
            
            if message_type == 'query':
                await self.handle_query(data)
            elif message_type == 'typing':
                await self.handle_typing(data)
            elif message_type == 'feedback':
                await self.handle_feedback(data)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({'type': 'pong'}))
            else:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': f'Unknown message type: {message_type}'
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
        except Exception as e:
            logger.error(f"Error in WebSocket receive: {str(e)}")
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Internal server error'
            }))
    
    async def handle_query(self, data):
        """پردازش سوال کاربر"""
        query = data.get('query', '').strip()
        conversation_id = data.get('conversation_id')
        response_mode = data.get('response_mode', 'simple_explanation')
        
        if not query:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Query cannot be empty'
            }))
            return
        
        # دریافت یا ایجاد conversation
        conversation = await self.get_or_create_conversation(conversation_id)
        
        # ایجاد پیام کاربر
        user_message = await self.create_message(
            conversation=conversation,
            role='user',
            content=query,
            response_mode=response_mode
        )
        
        # ارسال تایید دریافت پیام
        await self.send(text_data=json.dumps({
            'type': 'message_received',
            'message_id': str(user_message.id),
            'conversation_id': str(conversation.id)
        }))
        
        # ایجاد پیام assistant
        assistant_message = await self.create_message(
            conversation=conversation,
            role='assistant',
            content='',
            status='processing'
        )
        
        # ارسال شروع پردازش
        await self.send(text_data=json.dumps({
            'type': 'processing_started',
            'message_id': str(assistant_message.id)
        }))
        
        try:
            # دریافت تنظیم enable_web_search از preferences کاربر
            enable_web_search = None
            if self.user.preferences:
                enable_web_search = self.user.preferences.get('enable_web_search')
            
            # ارسال به Core RAG (non-streaming)
            response = await core_service.send_query(
                query=query,
                token=self.jwt_token,
                conversation_id=conversation.rag_conversation_id,
                language='fa',
                enable_web_search=enable_web_search
            )
            
            full_content = response.get('answer', response.get('response', ''))
            sources = response.get('sources', [])
            metadata = response.get('metadata', {})
            
            # ارسال پاسخ کامل به کاربر
            await self.send(text_data=json.dumps({
                'type': 'message',
                'content': full_content,
                'message_id': str(assistant_message.id)
            }))
            
            if sources:
                await self.send(text_data=json.dumps({
                    'type': 'sources',
                    'sources': sources,
                    'message_id': str(assistant_message.id)
                }))
            
            # به‌روزرسانی پیام assistant
            await self.update_assistant_message(
                assistant_message,
                full_content,
                sources,
                [],  # chunks - Core API returns sources directly
                metadata
            )
            
            # ارسال پایان پردازش
            await self.send(text_data=json.dumps({
                'type': 'processing_completed',
                'message_id': str(assistant_message.id),
                'metadata': metadata
            }))
            
            # به‌روزرسانی conversation
            if not conversation.rag_conversation_id and metadata.get('conversation_id'):
                await self.update_conversation_rag_id(
                    conversation,
                    metadata['conversation_id']
                )
            
            # ثبت در audit log
            await self.create_audit_log(
                action='chat_query_ws',
                details={
                    'conversation_id': str(conversation.id),
                    'query_length': len(query),
                    'tokens_used': metadata.get('total_tokens', 0)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in query processing: {str(e)}")
            
            # به‌روزرسانی وضعیت خطا
            await self.update_message_status(
                assistant_message,
                'failed',
                str(e)
            )
            
            # ارسال خطا به کاربر
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'خطا در پردازش سوال',
                'error': str(e),
                'message_id': str(assistant_message.id)
            }))
    
    async def handle_typing(self, data):
        """مدیریت وضعیت تایپ کردن"""
        is_typing = data.get('is_typing', False)
        
        # ارسال به سایر کاربران در conversation
        if hasattr(self, 'conversation_group_name'):
            await self.channel_layer.group_send(
                self.conversation_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': str(self.user.id),
                    'user_name': self.user.get_full_name() or self.user.username,
                    'is_typing': is_typing
                }
            )
    
    async def handle_feedback(self, data):
        """پردازش بازخورد کاربر"""
        message_id = data.get('message_id')
        rating = data.get('rating')
        feedback_type = data.get('feedback_type')
        feedback_text = data.get('feedback_text')
        
        if not message_id:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message ID is required'
            }))
            return
        
        # به‌روزرسانی پیام
        success = await self.update_message_feedback(
            message_id,
            rating,
            feedback_type,
            feedback_text
        )
        
        # ارسال به Core API
        if success:
            message = await self.get_message(message_id)
            if message and message.rag_message_id:
                await core_service.submit_feedback(
                    message_id=message.rag_message_id,
                    rating=rating if rating else 3,
                    token=self.jwt_token,
                    feedback_text=feedback_text
                )
        
        await self.send(text_data=json.dumps({
            'type': 'feedback_received',
            'success': success
        }))
    
    # Handler methods for channel layer
    async def typing_indicator(self, event):
        """ارسال نشانگر تایپ به کاربر"""
        # فقط برای کاربران دیگر ارسال شود
        if str(self.user.id) != event['user_id']:
            await self.send(text_data=json.dumps({
                'type': 'typing',
                'user_id': event['user_id'],
                'user_name': event['user_name'],
                'is_typing': event['is_typing']
            }))
    
    async def chat_message(self, event):
        """ارسال پیام چت به کاربر"""
        await self.send(text_data=json.dumps(event['message']))
    
    # Database helper methods
    @database_sync_to_async
    def check_conversation_access(self):
        """بررسی دسترسی کاربر به conversation"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                user=self.user
            )
            return True
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_or_create_conversation(self, conversation_id):
        """دریافت یا ایجاد conversation"""
        if conversation_id:
            try:
                return Conversation.objects.get(
                    id=conversation_id,
                    user=self.user
                )
            except Conversation.DoesNotExist:
                pass
        
        # ایجاد conversation جدید
        return Conversation.objects.create(
            user=self.user,
            organization=self.user.organization,
            title='گفتگوی جدید',
            default_response_mode='simple_explanation'
        )
    
    @database_sync_to_async
    def create_message(self, conversation, role, content, response_mode=None, status='completed'):
        """ایجاد پیام جدید"""
        return Message.objects.create(
            conversation=conversation,
            role=role,
            content=content,
            response_mode=response_mode,
            status=status
        )
    
    @database_sync_to_async
    def update_assistant_message(self, message, content, sources, chunks, metadata):
        """به‌روزرسانی پیام assistant"""
        message.content = content
        message.sources = sources
        message.chunks = chunks
        message.status = 'completed'
        message.tokens = metadata.get('total_tokens', 0)
        message.processing_time_ms = metadata.get('processing_time_ms', 0)
        message.model_used = metadata.get('model_used', '')
        message.cached = metadata.get('cached', False)
        message.rag_message_id = metadata.get('message_id', '')
        message.save()
        return message
    
    @database_sync_to_async
    def update_message_status(self, message, status, error_message=''):
        """به‌روزرسانی وضعیت پیام"""
        message.status = status
        message.error_message = error_message
        message.save()
    
    @database_sync_to_async
    def update_message_feedback(self, message_id, rating, feedback_type, feedback_text):
        """به‌روزرسانی بازخورد پیام"""
        try:
            message = Message.objects.get(
                id=message_id,
                conversation__user=self.user
            )
            if rating:
                message.rating = rating
            if feedback_type:
                message.feedback_type = feedback_type
            if feedback_text:
                message.feedback_text = feedback_text
            message.save()
            return True
        except Message.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_message(self, message_id):
        """دریافت پیام"""
        try:
            return Message.objects.get(
                id=message_id,
                conversation__user=self.user
            )
        except Message.DoesNotExist:
            return None
    
    @database_sync_to_async
    def update_conversation_rag_id(self, conversation, rag_conversation_id):
        """به‌روزرسانی RAG conversation ID"""
        conversation.rag_conversation_id = rag_conversation_id
        conversation.save()
    
    @database_sync_to_async
    def create_audit_log(self, action, details):
        """ایجاد audit log"""
        AuditLog.objects.create(
            user=self.user,
            action=action,
            details=details,
            ip_address=self.scope.get('client', ['', ''])[0],
            user_agent=dict(self.scope.get('headers', {})).get(b'user-agent', b'').decode()
        )
    
    @database_sync_to_async
    def get_jwt_token(self):
        """دریافت JWT token برای کاربر"""
        try:
            token = CustomAccessToken.for_user(self.user)
            return str(token)
        except Exception as e:
            logger.error(f"Error generating JWT token: {str(e)}")
            return None
