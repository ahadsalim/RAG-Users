"""
Core RAG System API Service
This service handles all communication with the Core RAG system.
"""
import httpx
import logging
from typing import Optional, Dict, Any, AsyncGenerator
from django.conf import settings
import json

logger = logging.getLogger(__name__)


class CoreAPIService:
    """Service for interacting with Core RAG API."""
    
    def __init__(self):
        # استفاده از RAG_CORE_BASE_URL که در settings تعریف شده
        self.base_url = settings.RAG_CORE_BASE_URL
        self.api_key = settings.RAG_CORE_API_KEY
        self.timeout = 300.0  # 5 minutes for file processing queries
        
    def _get_headers(self, token: str) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
        }
    
    async def send_query(
        self,
        query: str,
        token: str,
        conversation_id: Optional[str] = None,
        language: str = 'fa',
        file_attachments: Optional[list] = None,
    ) -> Dict[str, Any]:
        """
        ارسال سوال به سیستم مرکزی RAG Core.
        
        Args:
            query: سوال کاربر (1-2000 کاراکتر)
            token: JWT token
            conversation_id: شناسه مکالمه برای استفاده از حافظه
            language: زبان (پیش‌فرض: fa)
            file_attachments: لیست فایل‌های ضمیمه (حداکثر 5)
            
        Returns:
            پاسخ شامل answer, file_analysis, conversation_id و غیره
        """
        url = f"{self.base_url}/api/v1/query/"
        
        # ساخت payload مطابق با API سیستم مرکزی
        payload = {
            "query": query,
            "language": language,
        }
        
        # اضافه کردن conversation_id برای استفاده از حافظه
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        # اضافه کردن فایل‌های ضمیمه (حداکثر 5)
        if file_attachments and len(file_attachments) > 0:
            payload["file_attachments"] = file_attachments[:5]
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Core API HTTP error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Core API error: {str(e)}")
            raise
    
    async def get_conversations(
        self,
        token: str,
        limit: int = 20,
        offset: int = 0,
    ) -> list:
        """
        Get user's conversations from Core.
        
        Args:
            token: JWT token
            limit: Number of conversations to fetch
            offset: Offset for pagination
            
        Returns:
            List of conversations
        """
        url = f"{self.base_url}/api/v1/users/conversations"
        params = {"limit": limit, "offset": offset}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching conversations: {str(e)}")
            return []
    
    async def get_conversation_messages(
        self,
        conversation_id: str,
        token: str,
        limit: int = 50,
        offset: int = 0,
    ) -> list:
        """
        Get messages in a conversation.
        
        Args:
            conversation_id: Conversation ID
            token: JWT token
            limit: Number of messages
            offset: Offset for pagination
            
        Returns:
            List of messages
        """
        url = f"{self.base_url}/api/v1/users/conversations/{conversation_id}/messages"
        params = {"limit": limit, "offset": offset}
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url,
                    params=params,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching messages: {str(e)}")
            return []
    
    async def delete_conversation(
        self,
        conversation_id: str,
        token: str,
    ) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation ID
            token: JWT token
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/v1/users/conversations/{conversation_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.delete(
                    url,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Error deleting conversation: {str(e)}")
            return False
    
    async def submit_feedback(
        self,
        message_id: str,
        rating: int,
        token: str,
        feedback_text: Optional[str] = None,
    ) -> bool:
        """
        Submit feedback for a message.
        
        Args:
            message_id: Message ID
            rating: Rating (1-5)
            token: JWT token
            feedback_text: Optional feedback text
            
        Returns:
            True if successful
        """
        url = f"{self.base_url}/api/v1/query/feedback"
        
        payload = {
            "message_id": message_id,
            "rating": rating,
            "feedback_type": "general",
        }
        
        if feedback_text:
            payload["feedback_text"] = feedback_text
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return True
                
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            return False
    
    async def get_user_profile(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile from Core.
        
        Args:
            token: JWT token
            
        Returns:
            User profile data
        """
        url = f"{self.base_url}/api/v1/users/profile"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    url,
                    headers=self._get_headers(token),
                )
                response.raise_for_status()
                return response.json()
                
        except Exception as e:
            logger.error(f"Error fetching user profile: {str(e)}")
            return None
    
    async def delete_conversation(
        self,
        conversation_id: str,
        token: str,
    ) -> bool:
        """
        Delete a conversation from Core RAG system.
        
        Args:
            conversation_id: UUID of the conversation to delete
            token: JWT token for authentication
            
        Returns:
            True if deletion was successful, False otherwise
        """
        url = f"{self.base_url}/api/v1/users/conversations/{conversation_id}"
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.delete(
                    url,
                    headers=self._get_headers(token),
                )
                
                if response.status_code == 200:
                    logger.info(f"✅ Conversation {conversation_id} deleted from Core RAG")
                    return True
                elif response.status_code == 404:
                    logger.warning(f"⚠️ Conversation {conversation_id} not found in Core RAG")
                    return True  # Consider it deleted if not found
                else:
                    logger.error(f"❌ Failed to delete conversation {conversation_id}: {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ Error deleting conversation from Core RAG: {str(e)}")
            return False

    async def health_check(self) -> Dict[str, Any]:
        """
        Check if Core RAG system is available.
        
        Returns:
            Dict with status and details
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health/")
                
                if response.status_code == 200:
                    return {
                        'status': 'connected',
                        'message': 'سیستم مرکزی متصل است'
                    }
                else:
                    return {
                        'status': 'error',
                        'message': f'خطای سیستم مرکزی: {response.status_code}'
                    }
        except httpx.TimeoutException:
            return {
                'status': 'disconnected',
                'message': 'اتصال به سیستم مرکزی قطع است (timeout)'
            }
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return {
                'status': 'disconnected',
                'message': 'اتصال به سیستم مرکزی قطع است'
            }


# Singleton instance
core_service = CoreAPIService()
