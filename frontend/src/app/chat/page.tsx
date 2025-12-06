'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { ChatSidebar } from '@/components/chat/ChatSidebar'
import { ChatMessages } from '@/components/chat/ChatMessages'
import { ChatInput } from '@/components/chat/ChatInput'
import { ChatHeader } from '@/components/chat/ChatHeader'
import { useAuthStore } from '@/store/auth'
import { useChatStore } from '@/store/chat'
import { useWebSocket } from '@/hooks/useWebSocket'
import { Message, Conversation } from '@/types/chat'

export default function ChatPage() {
  const router = useRouter()
  const { isAuthenticated, user, isLoading: authLoading } = useAuthStore()
  const store = useChatStore()
  
  // Extract with fallback
  const currentConversation = store?.currentConversation ?? null
  const messages = store?.messages ?? []
  const isLoading = store?.isLoading ?? false
  const sendMessage = store?.sendMessage ?? (async () => {})
  const createNewConversation = store?.createNewConversation ?? (() => {})
  const loadConversation = store?.loadConversation ?? (async () => {})
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false) // Start closed for faster load
  const [isTyping, setIsTyping] = useState(false)
  const [isHydrated, setIsHydrated] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // Wait for hydration
  useEffect(() => {
    setIsHydrated(true)
  }, [])
  
  // Core RAG connection status
  const [isConnected, setIsConnected] = useState(true)
  const [connectionMessage, setConnectionMessage] = useState('')
  
  // Check Core RAG health periodically
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const token = localStorage.getItem('access_token')
        if (!token) return
        
        const response = await fetch('/api/v1/chat/health/', {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        
        if (response.ok) {
          const data = await response.json()
          setIsConnected(data.status === 'connected')
          setConnectionMessage(data.message || '')
        } else {
          setIsConnected(false)
          setConnectionMessage('اتصال به سیستم مرکزی قطع است')
        }
      } catch (error) {
        setIsConnected(false)
        setConnectionMessage('اتصال به سیستم مرکزی قطع است')
      }
    }
    
    // Check immediately and then every 30 seconds
    checkHealth()
    const interval = setInterval(checkHealth, 30000)
    
    return () => clearInterval(interval)
  }, [])

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check authentication after hydration
  useEffect(() => {
    if (isHydrated && !authLoading && !isAuthenticated) {
      console.log('Not authenticated, redirecting to login...')
      router.push('/auth/login')
    }
  }, [isHydrated, authLoading, isAuthenticated, router])

  // Handle sending message
  const handleSendMessage = useCallback(async (content: string, fileAttachments?: any[]) => {
    if (!content.trim() && (!fileAttachments || fileAttachments.length === 0)) return
    
    try {
      // ارسال پیام با API عادی (غیر استریم)
      await sendMessage(content, currentConversation?.id, undefined, fileAttachments)
    } catch (error) {
      console.error('Error sending message:', error)
    }
  }, [sendMessage, currentConversation])

  // Handle new conversation
  const handleNewChat = useCallback(() => {
    createNewConversation()
  }, [createNewConversation])

  // Toggle sidebar
  const toggleSidebar = useCallback(() => {
    setIsSidebarOpen(prev => !prev)
  }, [])

  // Show loading while hydrating or checking auth
  if (!isHydrated || authLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }
  
  // Redirect will happen in useEffect, show loading meanwhile
  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden bg-white dark:bg-gray-900 flex flex-col md:flex-row">
      {/* Sidebar */}
      <ChatSidebar 
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
        onNewChat={handleNewChat}
        currentConversationId={currentConversation?.id}
      />
      
      {/* Main Chat Area - ChatGPT Style */}
      <div className="flex-1 flex flex-col h-full overflow-hidden">
        {/* Header */}
        <ChatHeader 
          onToggleSidebar={toggleSidebar}
          conversation={currentConversation}
          isConnected={isConnected}
        />
        
        {/* Messages Container */}
        <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900">
          <div className="max-w-3xl mx-auto px-4 pb-4">
            <ChatMessages 
              messages={messages}
              isLoading={isLoading}
              isTyping={isTyping}
            />
            <div className="h-32 md:h-20" /> {/* Spacer for bottom input */}
            <div ref={messagesEndRef} />
          </div>
        </div>
        
        {/* Input Container - Fixed Bottom */}
        <div className="shrink-0 border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 safe-area-bottom">
          <div className="max-w-3xl mx-auto p-4">
            <ChatInput 
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              disabled={!isConnected}
            />
          </div>
        </div>
      </div>
    </div>
  )
}
