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
        self.base_url = getattr(settings, 'CORE_API_URL', 'https://core.tejarat.chat')
        self.api_key = getattr(settings, 'CORE_API_KEY', '')
        self.timeout = 120.0  # 2 minutes for long queries
        
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
        stream: bool = False,
        filters: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send a query to Core API.
        
        Args:
            query: User's question
            token: JWT token
            conversation_id: Optional conversation ID for context
            language: Query language (fa, en, ar)
            stream: Whether to stream the response
            filters: Optional filters (jurisdiction, category, date_range, etc.)
            user_preferences: User's custom preferences for response style
            
        Returns:
            Query response with answer and sources
        """
        url = f"{self.base_url}/api/v1/query/stream" if stream else f"{self.base_url}/api/v1/query/"
        
        payload = {
            "query": query,
            "conversation_id": conversation_id,
            "language": language,
            "stream": stream,
        }
        
        # Add filters if provided
        if filters:
            payload["filters"] = filters
        
        # Add user preferences if provided
        if user_preferences:
            payload["user_preferences"] = user_preferences
        
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
    
    async def send_query_stream(
        self,
        query: str,
        token: str,
        conversation_id: Optional[str] = None,
        language: str = 'fa',
        filters: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Send a query and stream the response.
        
        Args:
            query: User's question
            token: JWT token
            conversation_id: Optional conversation ID
            language: Query language
            filters: Optional filters
            user_preferences: User's custom preferences for response style
            
        Yields:
            Streamed response chunks
        """
        url = f"{self.base_url}/api/v1/query/stream"
        
        payload = {
            "query": query,
            "conversation_id": conversation_id,
            "language": language,
            "stream": True,
        }
        
        # Add filters if provided
        if filters:
            payload["filters"] = filters
        
        # Add user preferences if provided
        if user_preferences:
            payload["user_preferences"] = user_preferences
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    'POST',
                    url,
                    json=payload,
                    headers=self._get_headers(token),
                ) as response:
                    response.raise_for_status()
                    async for chunk in response.aiter_text():
                        if chunk.strip():
                            yield chunk
                            
        except httpx.HTTPStatusError as e:
            logger.error(f"Core API stream error: {e.response.status_code}")
            yield json.dumps({"error": f"خطا در دریافت پاسخ: {e.response.status_code}"})
        except Exception as e:
            logger.error(f"Core API stream error: {str(e)}")
            yield json.dumps({"error": f"خطا در ارتباط با سیستم: {str(e)}"})
    
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


# Singleton instance
core_service = CoreAPIService()
