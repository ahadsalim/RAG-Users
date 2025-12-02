import { create } from 'zustand'
import axios from 'axios'
import { Conversation, Message, QueryResponse } from '@/types/chat'
import { useAuthStore } from './auth'

interface ChatState {
  conversations: Conversation[] | undefined
  currentConversation: Conversation | null
  messages: Message[]
  isLoading: boolean
  error: string | null
  
  // Actions
  loadConversations: () => Promise<void>
  loadConversation: (conversationId: string) => Promise<void>
  createNewConversation: () => void
  deleteConversation: (conversationId: string) => Promise<void>
  archiveConversation: (conversationId: string) => Promise<void>
  pinConversation: (conversationId: string, pin: boolean) => Promise<void>
  
  sendMessage: (content: string, conversationId?: string, mode?: string, fileAttachments?: any[]) => Promise<void>
  sendMessageStreaming: (content: string, conversationId?: string, mode?: string, fileAttachments?: any[]) => Promise<void>
  loadMessages: (conversationId: string) => Promise<void>
  sendFeedback: (messageId: string, rating: number, feedback?: string) => Promise<void>
  
  clearError: () => void
  setCurrentConversation: (conversation: Conversation | null) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, updates: Partial<Message>) => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  error: null,
  
  loadConversations: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/api/v1/chat/conversations/`)
      set({
        conversations: response.data.results || response.data,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'خطا در دریافت گفتگوها',
      })
    }
  },
  
  loadConversation: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/api/v1/chat/conversations/${conversationId}/`)
      const conversation = response.data
      
      set({
        currentConversation: conversation,
        messages: conversation.messages || [],
        isLoading: false,
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'خطا در دریافت گفتگو',
      })
    }
  },
  
  createNewConversation: () => {
    set({
      currentConversation: null,
      messages: [],
    })
  },
  
  deleteConversation: async (conversationId: string) => {
    try {
      await axios.delete(`${API_URL}/api/v1/chat/conversations/${conversationId}/`)
      
      // Remove from local state
      set(state => ({
        conversations: state.conversations.filter(c => c.id !== conversationId),
        currentConversation: state.currentConversation?.id === conversationId 
          ? null 
          : state.currentConversation,
        messages: state.currentConversation?.id === conversationId 
          ? [] 
          : state.messages,
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'خطا در حذف گفتگو',
      })
    }
  },
  
  archiveConversation: async (conversationId: string) => {
    try {
      const state = get()
      const conversation = state.conversations.find(c => c.id === conversationId)
      const isArchived = conversation?.is_archived || false
      
      // Toggle archive status
      await axios.post(`${API_URL}/api/v1/chat/conversations/${conversationId}/archive/`)
      
      // Update local state - toggle the archive status
      set(state => ({
        conversations: state.conversations.map(c =>
          c.id === conversationId ? { ...c, is_archived: !isArchived } : c
        ),
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'خطا در آرشیو گفتگو',
      })
    }
  },
  
  pinConversation: async (conversationId: string, pin: boolean) => {
    try {
      const endpoint = pin ? 'pin' : 'unpin'
      await axios.post(`${API_URL}/api/v1/chat/conversations/${conversationId}/${endpoint}/`)
      
      // Update local state
      set(state => ({
        conversations: state.conversations.map(c =>
          c.id === conversationId ? { ...c, is_pinned: pin } : c
        ),
      }))
    } catch (error: any) {
      set({
        error: error.response?.data?.detail || 'خطا در پین کردن گفتگو',
      })
    }
  },
  
  sendMessage: async (content: string, conversationId?: string, mode = 'simple_explanation', fileAttachments?: any[]) => {
    set({ isLoading: true, error: null })
    
    try {
      // Create user message locally with attachments
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation: conversationId || '',
        role: 'user',
        content,
        response_mode: mode as any,
        status: 'completed',
        tokens: 0,
        processing_time_ms: 0,
        cached: false,
        attachments: fileAttachments ? fileAttachments.map((f: any) => ({
          id: `temp-${Date.now()}-${Math.random()}`,
          file: f.minio_url,
          file_name: f.filename,
          file_size: f.size_bytes,
          file_type: f.file_type.startsWith('image/') ? 'image' : 'document',
          mime_type: f.file_type,
          extraction_status: 'processing',
          created_at: new Date().toISOString(),
        })) : undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      set(state => ({
        messages: [...state.messages, userMessage],
      }))
      
      // Create assistant message placeholder
      const assistantMessage: Message = {
        id: `temp-${Date.now() + 1}`,
        conversation: conversationId || '',
        role: 'assistant',
        content: '',
        status: 'processing',
        tokens: 0,
        processing_time_ms: 0,
        cached: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      set(state => ({
        messages: [...state.messages, assistantMessage],
      }))
      
      // Prepare request payload
      const payload: any = {
        query: content,
        conversation_id: conversationId || get().currentConversation?.id,
        response_mode: mode,
      }
      
      // Add file attachments if provided
      if (fileAttachments && fileAttachments.length > 0) {
        payload.file_attachments = fileAttachments
      }
      
      // Send to API with 2 minute timeout
      const response = await axios.post<QueryResponse>(
        `${API_URL}/api/v1/chat/query/`, 
        payload,
        {
          timeout: 120000  // 2 minutes (120 seconds)
        }
      )
      
      // Update conversation ID if new
      if (!conversationId && response.data.conversation_id) {
        set(state => ({
          currentConversation: {
            ...state.currentConversation,
            id: response.data.conversation_id,
          } as Conversation,
        }))
      }
      
      // Update assistant message with response
      set(state => ({
        messages: state.messages.map(msg =>
          msg.id === assistantMessage.id
            ? {
                ...msg,
                id: response.data.message_id,
                content: response.data.answer,
                sources: response.data.sources,
                chunks: response.data.chunks,
                status: 'completed',
                tokens: response.data.tokens_used || 0,
                processing_time_ms: response.data.processing_time_ms || 0,
                model_used: response.data.model_used || '',
                cached: response.data.context_used || false,
              }
            : msg
        ),
        isLoading: false,
      }))
      
      // Reload conversations to update sidebar
      try {
        const response = await axios.get(`${API_URL}/api/v1/chat/conversations/`)
        set({ conversations: response.data.results || response.data })
      } catch (err) {
        console.error('Failed to reload conversations:', err)
      }
    } catch (error: any) {
      // تشخیص نوع خطا
      let errorMessage = 'خطا در ارسال پیام'
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorMessage = 'زمان پردازش تمام شد. لطفاً دوباره تلاش کنید.'
      } else if (error.response?.status === 504) {
        errorMessage = 'زمان پردازش تمام شد. سرور پاسخ نداد.'
      } else if (error.response?.status === 503) {
        errorMessage = 'سرور پردازش در دسترس نیست'
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      // Update assistant message with error
      set(state => ({
        messages: state.messages.map((msg, idx, arr) =>
          idx === arr.length - 1 && msg.role === 'assistant'
            ? {
                ...msg,
                status: 'failed',
                error_message: errorMessage,
              }
            : msg
        ),
        isLoading: false,
        error: errorMessage,
      }))
    }
  },
  
  sendMessageStreaming: async (content: string, conversationId?: string, mode = 'simple_explanation', fileAttachments?: any[]) => {
    set({ isLoading: true, error: null })
    
    try {
      // Create user message locally with attachments
      const userMessage: Message = {
        id: `temp-${Date.now()}`,
        conversation: conversationId || '',
        role: 'user',
        content,
        response_mode: mode as any,
        status: 'completed',
        tokens: 0,
        processing_time_ms: 0,
        cached: false,
        attachments: fileAttachments ? fileAttachments.map((f: any) => ({
          id: `temp-${Date.now()}-${Math.random()}`,
          file: f.minio_url,
          file_name: f.filename,
          file_size: f.size_bytes,
          file_type: f.file_type.startsWith('image/') ? 'image' : 'document',
          mime_type: f.file_type,
          extraction_status: 'processing',
          created_at: new Date().toISOString(),
        })) : undefined,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      set(state => ({
        messages: [...state.messages, userMessage],
      }))
      
      // Create assistant message placeholder
      const assistantMessage: Message = {
        id: `temp-${Date.now() + 1}`,
        conversation: conversationId || '',
        role: 'assistant',
        content: '',
        status: 'processing',
        tokens: 0,
        processing_time_ms: 0,
        cached: false,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      set(state => ({
        messages: [...state.messages, assistantMessage],
      }))
      
      // Prepare request payload
      const payload: any = {
        query: content,
        conversation_id: conversationId || get().currentConversation?.id,
        response_mode: mode,
      }
      
      // Add file attachments if provided
      if (fileAttachments && fileAttachments.length > 0) {
        payload.file_attachments = fileAttachments
      }
      
      // Get token from axios default headers (set by auth store)
      const token = axios.defaults.headers.common['Authorization']?.toString().replace('Bearer ', '')
      
      if (!token) {
        throw new Error('No authentication token found')
      }
      
      // Use fetch for streaming
      console.log('🚀 Starting streaming request...')
      const response = await fetch(`${API_URL}/api/v1/chat/query/stream/`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })
      console.log('📡 Response received:', response.status, response.ok)
      
      // اگر streaming موجود نیست (404) یا مشکل authentication (401)، fallback به حالت عادی
      if (response.status === 404 || response.status === 401) {
        console.warn(`Streaming not available (${response.status}), falling back to normal mode`)
        // استفاده از sendMessage عادی که از axios استفاده می‌کند
        set({ isLoading: false })
        await get().sendMessage(content, conversationId, mode, fileAttachments)
        return
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const reader = response.body?.getReader()
      const decoder = new TextDecoder()
      
      let fullContent = ''
      let messageId = assistantMessage.id
      let conversationIdFromServer = conversationId
      let buffer = '' // Buffer for incomplete SSE chunks
      
      if (!reader) {
        throw new Error('Response body is not readable')
      }
      
      console.log('📖 Starting to read stream...')
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          console.log('🏁 Stream finished')
          break
        }
        
        const chunk = decoder.decode(value, { stream: true })
        buffer += chunk
        
        // Split by double newline (SSE event separator)
        const events = buffer.split('\n\n')
        
        // Keep the last incomplete event in buffer
        buffer = events.pop() || ''
        
        for (const event of events) {
          const lines = event.split('\n')
          
          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6))
                
                if (data.type === 'start') {
                  console.log('🎬 Stream started:', data)
                  // Update conversation and message IDs
                  messageId = data.message_id
                  conversationIdFromServer = data.conversation_id
                } else if (data.type === 'chunk') {
                  // Just accumulate content, don't update UI yet
                  fullContent += data.content
                  console.log('📝 Chunk:', data.content.length, 'chars, total:', fullContent.length)
                } else if (data.type === 'sources') {
                  // Update sources
                  set(state => ({
                    messages: state.messages.map(msg =>
                      msg.id === assistantMessage.id
                        ? { ...msg, sources: data.sources }
                        : msg
                    ),
                  }))
                } else if (data.type === 'end') {
                  console.log('✅ Stream ended, showing complete message')
                  // Show complete message at once
                  set(state => ({
                    messages: state.messages.map(msg =>
                      msg.id === assistantMessage.id
                        ? {
                            ...msg,
                            id: messageId,
                            content: fullContent,
                            status: 'completed',
                            tokens: data.metadata?.tokens || 0,
                            processing_time_ms: data.metadata?.processing_time_ms || 0,
                            model_used: data.metadata?.model_used || '',
                            cached: data.metadata?.cached || false,
                          }
                        : msg
                    ),
                    isLoading: false,
                  }))
                } else if (data.type === 'error') {
                  console.error('❌ Stream error:', data.error)
                  // Handle error
                  set(state => ({
                    messages: state.messages.map(msg =>
                      msg.id === assistantMessage.id
                        ? {
                            ...msg,
                            status: 'failed',
                            error_message: data.error,
                          }
                        : msg
                    ),
                    isLoading: false,
                    error: data.error,
                  }))
                }
              } catch (e) {
                console.error('Error parsing SSE data:', e)
              }
            }
          }
        }
      }
      
      // Update conversation ID if new
      if (!conversationId && conversationIdFromServer) {
        set(state => ({
          currentConversation: {
            ...state.currentConversation,
            id: conversationIdFromServer,
          } as Conversation,
        }))
      }
      
      // Reload conversations to update list
      try {
        const response = await axios.get(`${API_URL}/api/v1/chat/conversations/`)
        set({ conversations: response.data.results || response.data })
      } catch (err) {
        console.error('Failed to reload conversations:', err)
      }
      
    } catch (error: any) {
      console.error('Streaming error:', error)
      
      let errorMessage = 'خطا در ارسال پیام'
      const errorText = error.message || error.toString()
      
      if (errorText.includes('429')) {
        errorMessage = 'محدودیت تعداد درخواست. لطفاً کمی صبر کنید.'
      } else if (errorText.includes('403')) {
        errorMessage = 'شما اشتراک فعالی ندارید'
      } else if (errorText.includes('401') || errorText.includes('token not valid') || errorText.includes('authentication')) {
        errorMessage = 'نشست شما منقضی شده است. لطفاً دوباره وارد شوید.'
        const authStore = useAuthStore.getState()
        authStore.logout()
      } else if (errorText.includes('502') || errorText.includes('Bad Gateway')) {
        errorMessage = 'سرور موقتاً در دسترس نیست. لطفاً دوباره تلاش کنید.'
      } else if (errorText.includes('504') || errorText.includes('timeout')) {
        errorMessage = 'زمان انتظار تمام شد. لطفاً دوباره تلاش کنید.'
      }
      
      // Update assistant message with error
      set(state => ({
        messages: state.messages.map((msg, idx, arr) =>
          idx === arr.length - 1 && msg.role === 'assistant'
            ? {
                ...msg,
                status: 'failed',
                error_message: errorMessage,
              }
            : msg
        ),
        isLoading: false,
        error: errorMessage,
      }))
    }
  },
  
  loadMessages: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axios.get(`${API_URL}/api/v1/chat/conversations/${conversationId}/messages/`)
      set({
        messages: response.data.results || response.data,
        isLoading: false,
      })
    } catch (error: any) {
      set({
        isLoading: false,
        error: error.response?.data?.detail || 'خطا در دریافت پیام‌ها',
      })
    }
  },
  
  sendFeedback: async (messageId: string, rating: number, feedback?: string) => {
    try {
      const conversationId = get().currentConversation?.id
      if (!conversationId) return
      
      await axios.post(
        `${API_URL}/api/v1/chat/conversations/${conversationId}/messages/${messageId}/feedback/`,
        {
          rating,
          feedback_text: feedback,
          feedback_type: rating >= 4 ? 'helpful' : 'unhelpful',
        }
      )
      
      // Update local message
      set(state => ({
        messages: state.messages.map(msg =>
          msg.id === messageId
            ? { ...msg, rating, feedback_text: feedback }
            : msg
        ),
      }))
    } catch (error: any) {
      console.error('Error sending feedback:', error)
    }
  },
  
  clearError: () => set({ error: null }),
  
  setCurrentConversation: (conversation: Conversation | null) => {
    set({ currentConversation: conversation })
  },
  
  addMessage: (message: Message) => {
    set(state => ({
      messages: [...state.messages, message],
    }))
  },
  
  updateMessage: (messageId: string, updates: Partial<Message>) => {
    set(state => ({
      messages: state.messages.map(msg =>
        msg.id === messageId ? { ...msg, ...updates } : msg
      ),
    }))
  },
}))
