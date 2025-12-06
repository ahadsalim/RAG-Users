'use client'

import { useState, useEffect } from 'react'
import Image from 'next/image'
import { useChatStore } from '@/store/chat'
import { useAuthStore } from '@/store/auth'
import { Conversation } from '@/types/chat'
import clsx from 'clsx'
import SettingsPage from '@/components/SettingsPage'

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
  const [openMenuId, setOpenMenuId] = useState<string | null>(null)
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [editingTitleId, setEditingTitleId] = useState<string | null>(null)
  const [editingTitle, setEditingTitle] = useState('')
  const store = useChatStore()
  const { user, logout } = useAuthStore()
  
  // Extract with fallback
  const conversations = store?.conversations ?? []
  const loadConversations = store?.loadConversations ?? (() => {})
  const loadConversation = store?.loadConversation ?? (() => {})
  const deleteConversation = store?.deleteConversation ?? (async () => {})
  const archiveConversation = store?.archiveConversation ?? (async () => {})
  
  useEffect(() => {
    if (loadConversations) {
      loadConversations()
    }
  }, [loadConversations])
  
  // Safe guard against undefined conversations
  const safeConversations = Array.isArray(conversations) ? conversations : []
  
  const filteredConversations = safeConversations.filter(conv => {
    const matchesSearch = conv.title?.toLowerCase().includes(searchQuery.toLowerCase())
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
      setOpenMenuId(null)
    }
  }
  
  const handleArchiveConversation = async (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation()
    await archiveConversation(conversationId)
    setOpenMenuId(null)
  }
  
  const handleShareConversation = async (e: React.MouseEvent, conversation: Conversation) => {
    e.stopPropagation()
    
    // ساخت متن گفتگو
    let shareText = `گفتگو: ${conversation.title}\n\n`
    
    if (conversation.messages && conversation.messages.length > 0) {
      conversation.messages.forEach((msg, index) => {
        const role = msg.role === 'user' ? '👤 کاربر' : '🤖 دستیار'
        shareText += `${role}:\n${msg.content}\n\n`
      })
    } else {
      shareText += 'این گفتگو هنوز پیامی ندارد.\n'
    }
    
    shareText += `\n---\nتاریخ: ${new Date(conversation.updated_at).toLocaleDateString('fa-IR')}`
    
    // استفاده از Web Share API
    if (navigator.share) {
      try {
        await navigator.share({
          title: conversation.title,
          text: shareText,
        })
      } catch (err) {
        console.log('اشتراک‌گذاری لغو شد')
      }
    } else {
      // Fallback: کپی به کلیپبورد
      try {
        await navigator.clipboard.writeText(shareText)
        alert('متن گفتگو در کلیپبورد کپی شد')
      } catch (err) {
        alert('خطا در کپی متن')
      }
    }
    
    setOpenMenuId(null)
  }
  
  const toggleMenu = (e: React.MouseEvent, conversationId: string) => {
    e.stopPropagation()
    setOpenMenuId(openMenuId === conversationId ? null : conversationId)
  }
  
  const handleLogout = () => {
    logout()
  }
  
  const handleEditTitle = (e: React.MouseEvent, conversation: Conversation) => {
    e.stopPropagation()
    setEditingTitleId(conversation.id)
    setEditingTitle(conversation.title)
    setOpenMenuId(null)
  }
  
  const handleSaveTitle = async (e: React.MouseEvent | React.KeyboardEvent, conversationId: string) => {
    e.stopPropagation()
    if (editingTitle.trim()) {
      // Call API to update title
      try {
        const token = useAuthStore.getState().accessToken
        const API_URL = process.env.NEXT_PUBLIC_API_URL || ''
        await fetch(`${API_URL}/api/v1/chat/conversations/${conversationId}/`, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ title: editingTitle.trim() })
        })
        // Reload conversations
        loadConversations()
      } catch (err) {
        console.error('Error updating title:', err)
      }
    }
    setEditingTitleId(null)
  }
  
  const handleCancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingTitleId(null)
  }
  
  // Get user display name
  const getUserDisplayName = () => {
    const savedSettings = typeof window !== 'undefined' ? localStorage.getItem('userSettings') : null
    if (savedSettings) {
      try {
        const settings = JSON.parse(savedSettings)
        if (settings.full_name) return settings.full_name
      } catch (e) {}
    }
    if (user?.first_name && user?.last_name) return `${user.first_name} ${user.last_name}`
    return user?.email || 'کاربر'
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
        'fixed top-0 right-0 md:relative z-50 md:z-auto',
        'w-80 h-screen md:h-full',
        'bg-gray-900 text-white',
        'transition-transform duration-300',
        'flex flex-col',
        'overflow-hidden',
        isOpen ? 'translate-x-0' : 'translate-x-full md:translate-x-0'
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
                style={{ width: 'auto', height: 'auto' }}
              />
              <h2 className="text-lg font-bold">گفتگوها</h2>
            </div>
            
            {/* User Avatar with Menu */}
            <div className="relative">
              <button
                onClick={() => setShowUserMenu(!showUserMenu)}
                className="w-8 h-8 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center hover:ring-2 hover:ring-blue-400 transition-all"
                title={getUserDisplayName()}
              >
                <span className="text-sm font-bold text-white">
                  {getUserDisplayName().charAt(0).toUpperCase()}
                </span>
              </button>
              
              {/* User Dropdown Menu */}
              {showUserMenu && (
                <>
                  <div 
                    className="fixed inset-0 z-10" 
                    onClick={() => setShowUserMenu(false)}
                  />
                  <div className="absolute left-0 top-10 bg-gray-800 border border-gray-700 rounded-xl shadow-xl py-2 z-20 min-w-[200px]">
                    {/* User Info */}
                    <div className="px-4 py-3 border-b border-gray-700">
                      <p className="font-medium text-white truncate">{getUserDisplayName()}</p>
                      <p className="text-xs text-gray-400 truncate">{user?.email || user?.phone_number}</p>
                      <p className="text-xs mt-1">
                        {user?.is_superuser ? (
                          <span className="text-red-400 font-semibold">مدیر ارشد</span>
                        ) : user?.is_staff ? (
                          <span className="text-yellow-400">کارمند</span>
                        ) : user?.user_type === 'business' ? (
                          <span className="text-purple-400">کاربر حقوقی</span>
                        ) : (
                          <span className="text-blue-400">کاربر عادی</span>
                        )}
                      </p>
                    </div>
                    
                    {/* Menu Items */}
                    <div className="py-1">
                      <button 
                        onClick={() => { setIsSettingsOpen(true); setShowUserMenu(false); }}
                        className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-right text-sm"
                      >
                        <span>⚙️</span>
                        <span>تنظیمات</span>
                      </button>
                      <button 
                        onClick={() => { handleLogout(); setShowUserMenu(false); }}
                        className="w-full flex items-center gap-3 px-4 py-2 hover:bg-gray-700 text-red-400 text-right text-sm"
                      >
                        <span>🚪</span>
                        <span>خروج</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
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
                  onClick={() => editingTitleId !== conversation.id && handleSelectConversation(conversation.id)}
                  className={clsx(
                    'group flex items-center gap-2 p-2 rounded-lg cursor-pointer transition-colors',
                    currentConversationId === conversation.id
                      ? 'bg-gray-700'
                      : 'hover:bg-gray-800'
                  )}
                >
                  <span className="text-gray-400 text-sm">💬</span>
                  <div className="flex-1 min-w-0">
                    {editingTitleId === conversation.id ? (
                      <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                        <input
                          type="text"
                          value={editingTitle}
                          onChange={(e) => setEditingTitle(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter') handleSaveTitle(e, conversation.id)
                            if (e.key === 'Escape') setEditingTitleId(null)
                          }}
                          className="flex-1 bg-gray-600 text-white text-sm px-2 py-1 rounded border border-gray-500 focus:outline-none focus:border-blue-500"
                          autoFocus
                        />
                        <button
                          onClick={(e) => handleSaveTitle(e, conversation.id)}
                          className="p-1 text-green-400 hover:bg-gray-600 rounded"
                        >
                          ✓
                        </button>
                        <button
                          onClick={handleCancelEdit}
                          className="p-1 text-gray-400 hover:bg-gray-600 rounded"
                        >
                          ✕
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2">
                        <h4 className="font-medium truncate text-sm flex-1">{conversation.title}</h4>
                        <span className="text-[10px] text-gray-500 flex-shrink-0">
                          {new Date(conversation.updated_at).toLocaleDateString('fa-IR')}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* 3-dot Menu */}
                  <div className="relative flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      onClick={(e) => toggleMenu(e, conversation.id)}
                      className="p-1 hover:bg-gray-600 rounded"
                      title="منو"
                    >
                      <span className="text-gray-400">⋮</span>
                    </button>
                    
                    {/* Dropdown Menu */}
                    {openMenuId === conversation.id && (
                      <div className="absolute left-0 top-8 bg-gray-800 border border-gray-700 rounded-lg shadow-lg py-1 z-10 min-w-[160px]">
                        <button
                          onClick={(e) => handleEditTitle(e, conversation)}
                          className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-700 text-right text-sm"
                        >
                          <span>✏️</span>
                          <span>ویرایش عنوان</span>
                        </button>
                        <button
                          onClick={(e) => handleShareConversation(e, conversation)}
                          className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-700 text-right text-sm"
                        >
                          <span>🔗</span>
                          <span>اشتراک‌گذاری</span>
                        </button>
                        <button
                          onClick={(e) => handleArchiveConversation(e, conversation.id)}
                          className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-700 text-right text-sm"
                        >
                          <span>📦</span>
                          <span>{conversation.is_archived ? 'خروج از آرشیو' : 'آرشیو'}</span>
                        </button>
                        <button
                          onClick={(e) => handleDeleteConversation(e, conversation.id)}
                          className="w-full flex items-center gap-2 px-3 py-2 hover:bg-gray-700 text-red-400 text-right text-sm"
                        >
                          <span>🗑️</span>
                          <span>حذف</span>
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
        
      </aside>
      
      {/* Settings Page */}
      <SettingsPage 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </>
  )
}
