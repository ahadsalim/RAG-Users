import { create } from 'zustand'
import axiosInstance from '@/lib/axios'
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
  loadMessages: (conversationId: string) => Promise<void>
  sendFeedback: (messageId: string, rating: number, feedback?: string) => Promise<void>
  
  clearError: () => void
  setCurrentConversation: (conversation: Conversation | null) => void
  addMessage: (message: Message) => void
  updateMessage: (messageId: string, updates: Partial<Message>) => void
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || ''

export const useChatStore = create<ChatState>((set, get) => ({
  conversations: [],
  currentConversation: null,
  messages: [],
  isLoading: false,
  error: null,
  
  loadConversations: async () => {
    set({ isLoading: true, error: null })
    try {
      const response = await axiosInstance.get(`${API_URL}/api/v1/chat/conversations/`)
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
      const response = await axiosInstance.get(`${API_URL}/api/v1/chat/conversations/${conversationId}/`)
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
      await axiosInstance.delete(`${API_URL}/api/v1/chat/conversations/${conversationId}/`)
      
      // Remove from local state
      set(state => ({
        conversations: (state.conversations || []).filter(c => c.id !== conversationId),
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
      const conversation = (state.conversations || []).find(c => c.id === conversationId)
      const isArchived = conversation?.is_archived || false
      
      // Toggle archive status
      await axiosInstance.post(`${API_URL}/api/v1/chat/conversations/${conversationId}/archive/`)
      
      // Update local state - toggle the archive status
      set(state => ({
        conversations: (state.conversations || []).map(c =>
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
      await axiosInstance.post(`${API_URL}/api/v1/chat/conversations/${conversationId}/${endpoint}/`)
      
      // Update local state
      set(state => ({
        conversations: (state.conversations || []).map(c =>
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
      
      // Send to API with 5 minute timeout
      const response = await axiosInstance.post<QueryResponse>(
        `${API_URL}/api/v1/chat/query/`, 
        payload,
        {
          timeout: 300000  // 5 minutes (300 seconds)
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
      
      // Update conversation in sidebar locally (avoid full reload)
      set(state => {
        const convId = response.data.conversation_id
        const existingIndex = state.conversations.findIndex(c => c.id === convId)
        if (existingIndex >= 0) {
          const updated = [...state.conversations]
          updated[existingIndex] = {
            ...updated[existingIndex],
            last_message_at: new Date().toISOString(),
          }
          return { conversations: updated }
        } else {
          // New conversation — add to top
          const newConv: Conversation = {
            id: convId,
            title: content.slice(0, 50) + (content.length > 50 ? '...' : ''),
            message_count: 1,
            last_message_at: new Date().toISOString(),
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
          } as Conversation
          return { conversations: [newConv, ...state.conversations] }
        }
      })
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
  
  loadMessages: async (conversationId: string) => {
    set({ isLoading: true, error: null })
    try {
      const response = await axiosInstance.get(`${API_URL}/api/v1/chat/conversations/${conversationId}/messages/`)
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
      
      await axiosInstance.post(
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
