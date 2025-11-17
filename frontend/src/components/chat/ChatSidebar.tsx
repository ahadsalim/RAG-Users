'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { useChatStore } from '@/store/chat'
import { useAuthStore } from '@/store/auth'
import { Conversation } from '@/types/chat'
import clsx from 'clsx'
import SettingsModal from '@/components/SettingsModal'

interface ChatSidebarProps {
  isOpen: boolean
  onClose: () => void
  onNewChat: () => void
  currentConversationId?: string
}

export function ChatSidebar({ 
  isOpen, 
  onClose, 
  onNewChat,
  currentConversationId 
}: ChatSidebarProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [showArchived, setShowArchived] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const { conversations, loadConversations, loadConversation, deleteConversation } = useChatStore()
  const { user, logout } = useAuthStore()
  
  useEffect(() => {
    loadConversations()
  }, [loadConversations])
  
  const filteredConversations = conversations.filter(conv => {
    const matchesSearch = conv.title.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesArchived = showArchived ? conv.is_archived : !conv.is_archived
    return matchesSearch && matchesArchived
  })
  
  const handleSelectConversation = (conversationId: string) => {
    loadConversation(conversationId)
    if (window.innerWidth < 768) {
      onClose()
    }
  }
  
  const handleDeleteConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation()
    if (confirm('آیا از حذف این گفتگو اطمینان دارید؟')) {
      await deleteConversation(conversationId)
    }
  }
  
  const handleLogout = () => {
    logout()
  }
  
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black/50 z-40"
          onClick={onClose}
        />
      )}
      
      {/* Sidebar */}
      <aside className={clsx(
        'fixed md:relative z-50 md:z-auto',
        'w-80 h-full',
        'bg-gray-900 text-white',
        'transition-transform duration-300',
        'flex flex-col',
        isOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'
      )}>
        {/* Header */}
        <div className="p-3 border-b border-gray-700">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Image 
                src="/logo-small.png" 
                alt="Logo" 
                width={24} 
                height={24}
                className="rounded"
              />
              <h2 className="text-lg font-bold">گفتگوها</h2>
            </div>
            <button
              onClick={onClose}
              className="md:hidden p-1 hover:bg-gray-800 rounded"
            >
              <span className="text-xl">×</span>
            </button>
          </div>
          
          {/* New Chat Button */}
          <button
            onClick={onNewChat}
            className="w-full flex items-center gap-2 px-3 py-2 bg-gray-800 hover:bg-gray-700 rounded-lg transition-colors text-sm"
          >
            <span>➕</span>
            <span>گفتگوی جدید</span>
          </button>
          
          {/* Search */}
          <div className="mt-3 relative">
            <span className="absolute right-2.5 top-1/2 -translate-y-1/2 text-gray-400 text-sm">🔍</span>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="جستجو..."
              className="w-full pr-9 pl-3 py-1.5 text-sm bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-gray-600"
            />
          </div>
        </div>
        
        {/* Conversations List */}
        <div className="flex-1 overflow-y-auto p-4">
          {/* Toggle Archive */}
          <div className="flex items-center justify-between mb-4">
            <button
              onClick={() => setShowArchived(!showArchived)}
              className="flex items-center gap-2 text-sm text-gray-400 hover:text-white"
            >
              <span>📦</span>
              {showArchived ? 'نمایش فعال' : 'نمایش آرشیو'}
            </button>
          </div>
          
          {/* Conversations */}
          <div className="space-y-2">
            {filteredConversations.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                <div className="text-5xl opacity-50 mb-3">💬</div>
                <p>گفتگویی یافت نشد</p>
              </div>
            ) : (
              filteredConversations.map((conversation) => (
                <div
                  key={conversation.id}
                  onClick={() => handleSelectConversation(conversation.id)}
                  className={clsx(
                    'group flex items-start gap-3 p-3 rounded-lg cursor-pointer transition-colors',
                    currentConversationId === conversation.id
                      ? 'bg-gray-700'
                      : 'hover:bg-gray-800'
                  )}
                >
                  <span className="text-gray-400">💬</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium truncate">{conversation.title}</h4>
                    <p className="text-sm text-gray-400 truncate">
                      {conversation.last_message?.content || 'بدون پیام'}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(conversation.updated_at).toLocaleDateString('fa-IR')}
                    </p>
                  </div>
                  <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => handleDeleteConversation(e, conversation.id)}
                      className="p-1 hover:bg-gray-700 rounded"
                    >
                      <span className="text-gray-400 hover:text-red-400">🗑️</span>
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
        {/* Footer */}
        <div className="p-2 border-t border-gray-700">
          {/* User Info */}
          <div className="flex items-center gap-2 mb-2">
            <div className="w-8 h-8 bg-gray-700 rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-xs font-bold">
                {user?.first_name?.[0] || user?.email?.[0] || '?'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {user?.first_name && user?.last_name 
                  ? `${user.first_name} ${user.last_name}`
                  : user?.email}
              </p>
              <p className="text-xs text-gray-400 truncate">
                {user?.organization?.name || 'کاربر عادی'}
              </p>
            </div>
          </div>
          
          {/* Actions */}
          <div className="space-y-0.5">
            <button 
              onClick={() => setIsSettingsOpen(true)}
              className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-gray-800 rounded transition-colors text-sm"
            >
              <span className="text-gray-400 text-xs">⚙️</span>
              <span>تنظیمات</span>
            </button>
            <button 
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-2 py-1.5 hover:bg-gray-800 rounded transition-colors text-red-400 text-sm"
            >
              <span className="text-xs">🚪</span>
              <span>خروج</span>
            </button>
          </div>
        </div>
      </aside>
      
      {/* Settings Modal */}
      <SettingsModal 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </>
  )
}
