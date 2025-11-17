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
  const { isAuthenticated, user } = useAuthStore()
  const { 
    currentConversation,
    messages,
    isLoading,
    sendMessage,
    createNewConversation,
    loadConversation
  } = useChatStore()
  
  const [isSidebarOpen, setIsSidebarOpen] = useState(false) // Start closed for faster load
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  
  // WebSocket connection (optional - won't block UI)
  const [isConnected, setIsConnected] = useState(true) // Assume connected for better UX
  
  // Disable WebSocket for now to improve performance
  // const { sendMessage: wsSendMessage, isConnected } = useWebSocket({
  //   onMessage: (data) => {
  //     console.log('WebSocket message:', data)
  //   },
  //   onTyping: (userId, isTyping) => {
  //     if (userId !== user?.id) {
  //       setIsTyping(isTyping)
  //     }
  //   }
  // })

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Check authentication
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/auth/login')
    }
  }, [isAuthenticated, router])

  // Handle sending message
  const handleSendMessage = useCallback(async (content: string, mode?: string) => {
    if (!content.trim()) return
    
    try {
      await sendMessage(content, currentConversation?.id, mode)
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

  if (!isAuthenticated) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="h-screen overflow-hidden bg-white dark:bg-gray-900">
      <div className="flex h-full">
        {/* Sidebar */}
        <ChatSidebar 
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          onNewChat={handleNewChat}
          currentConversationId={currentConversation?.id}
        />
        
        {/* Main Chat Area - ChatGPT Style */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <ChatHeader 
            onToggleSidebar={toggleSidebar}
            conversation={currentConversation}
            isConnected={isConnected}
          />
          
          {/* Messages Container */}
          <div className="flex-1 overflow-y-auto bg-white dark:bg-gray-900">
            <div className="max-w-3xl mx-auto px-4">
              <ChatMessages 
                messages={messages}
                isLoading={isLoading}
                isTyping={isTyping}
              />
              <div className="h-32" /> {/* Spacer for bottom */}
              <div ref={messagesEndRef} />
            </div>
          </div>
          
          {/* Input Container - Fixed Bottom */}
          <div className="border-t border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900">
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
    </div>
  )
}
