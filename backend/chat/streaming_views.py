"""
View برای streaming پاسخ‌های دستیار هوشمند.
فعلاً غیرفعال - منتظر پشتیبانی از سیستم مرکزی.
"""
from django.http import StreamingHttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
import json
import asyncio
import httpx


class StreamingQueryView(APIView):
    """
    View برای دریافت پاسخ به صورت streaming.
    
    زمانی که سیستم مرکزی streaming را پشتیبانی کند،
    این view را فعال کنید.
    """
    permission_classes = [IsAuthenticated]
    
    async def stream_response(self, query, token, conversation_id=None, file_attachments=None):
        """
        دریافت پاسخ به صورت streaming از سیستم مرکزی.
        
        Yields:
            رشته‌های JSON برای ارسال به frontend
        """
        url = "https://core.tejarat.chat/api/v1/query/stream/"  # فرضی
        
        payload = {
            "query": query,
            "language": "fa",
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        if file_attachments:
            payload["file_attachments"] = file_attachments
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        async with httpx.AsyncClient(timeout=300.0) as client:
            async with client.stream('POST', url, json=payload, headers=headers) as response:
                # ارسال شروع پاسخ
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                # خواندن و ارسال chunks
                async for chunk in response.aiter_text():
                    if chunk.strip():
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                
                # ارسال پایان پاسخ
                yield f"data: {json.dumps({'type': 'end'})}\n\n"
    
    def post(self, request):
        """
        دریافت درخواست و شروع streaming.
        
        Response format: Server-Sent Events (SSE)
        """
        query = request.data.get('query')
        conversation_id = request.data.get('conversation_id')
        file_attachments = request.data.get('file_attachments')
        
        # تولید JWT token
        from chat.utils import generate_jwt_token
        user = request.user
        token = generate_jwt_token(user)
        
        # ایجاد generator برای streaming
        async def event_stream():
            async for event in self.stream_response(
                query=query,
                token=token,
                conversation_id=conversation_id,
                file_attachments=file_attachments
            ):
                yield event
        
        # تبدیل async generator به sync generator
        def sync_stream():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                async_gen = event_stream()
                while True:
                    try:
                        chunk = loop.run_until_complete(async_gen.__anext__())
                        yield chunk
                    except StopAsyncIteration:
                        break
            finally:
                loop.close()
        
        # برگرداندن StreamingHttpResponse
        response = StreamingHttpResponse(
            sync_stream(),
            content_type='text/event-stream',
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        
        return response


# نمونه استفاده در frontend:
"""
// Frontend code (React/TypeScript)

const sendStreamingMessage = async (query: string) => {
  const response = await fetch('/api/v1/chat/query/stream/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query }),
  })
  
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    
    const chunk = decoder.decode(value)
    const lines = chunk.split('\\n')
    
    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6))
        
        if (data.type === 'chunk') {
          // نمایش کاراکتر به کاراکتر
          setMessage(prev => prev + data.content)
        }
      }
    }
  }
}
"""
