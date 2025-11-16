import { create } from 'zustand'
import axios from 'axios'
import { Conversation, Message, QueryResponse } from '@/types/chat'

interface ChatState {
  conversations: Conversation[]
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
  
  sendMessage: (content: string, conversationId?: string, mode?: string) => Promise<void>
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
      await axios.post(`${API_URL}/api/v1/chat/conversations/${conversationId}/archive/`)
      
      // Update local state
      set(state => ({
        conversations: state.conversations.map(c =>
          c.id === conversationId ? { ...c, is_archived: true } : c
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
  
  sendMessage: async (content: string, conversationId?: string, mode = 'simple_explanation') => {
    set({ isLoading: true, error: null })
    
    try {
      // Create user message locally
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
      
      // Send to API
      const response = await axios.post<QueryResponse>(`${API_URL}/api/v1/chat/query/`, {
        query: content,
        conversation_id: conversationId || get().currentConversation?.id,
        response_mode: mode,
      })
      
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
                tokens: response.data.metadata.tokens,
                processing_time_ms: response.data.metadata.processing_time_ms,
                model_used: response.data.metadata.model_used,
                cached: response.data.metadata.cached,
              }
            : msg
        ),
        isLoading: false,
      }))
      
      // Reload conversations to update sidebar
      get().loadConversations()
    } catch (error: any) {
      // Update assistant message with error
      set(state => ({
        messages: state.messages.map((msg, idx, arr) =>
          idx === arr.length - 1 && msg.role === 'assistant'
            ? {
                ...msg,
                status: 'failed',
                error_message: error.response?.data?.detail || 'خطا در ارسال پیام',
              }
            : msg
        ),
        isLoading: false,
        error: error.response?.data?.detail || 'خطا در ارسال پیام',
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
