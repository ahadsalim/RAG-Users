'use client'

import { Conversation } from '@/types/chat'
import clsx from 'clsx'
import { useState } from 'react'

interface ChatHeaderProps {
  onToggleSidebar: () => void
  conversation?: Conversation | null
  isConnected: boolean
}

export function ChatHeader({ onToggleSidebar, conversation, isConnected }: ChatHeaderProps) {
  const [showMenu, setShowMenu] = useState(false)
  
  const handleShare = () => {
    // TODO: Implement share functionality
    console.log('Share conversation')
    setShowMenu(false)
  }
  
  const handleArchive = () => {
    // TODO: Implement archive functionality
    console.log('Archive conversation')
    setShowMenu(false)
  }
  
  const handleDelete = () => {
    // TODO: Implement delete functionality
    if (confirm('آیا از حذف این گفتگو اطمینان دارید؟')) {
      console.log('Delete conversation')
    }
    setShowMenu(false)
  }
  
  return (
    <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
      <div className="px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          {/* Sidebar Toggle */}
          <button
            onClick={onToggleSidebar}
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors md:hidden text-xl"
          >
            ☰
          </button>
          
          {/* Conversation Title */}
          <div className="flex-1">
            <h1 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              {conversation?.title || 'گفتگوی جدید'}
            </h1>
            {conversation && (
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {conversation.message_count || 0} پیام
              </p>
            )}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-2">
          {/* Connection Status */}
          <div className={clsx(
            'flex items-center gap-1 px-2 py-1 rounded-lg text-xs',
            isConnected
              ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-400'
              : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-400'
          )}>
            <span>{isConnected ? '🟢' : '🔴'}</span>
            <span>{isConnected ? 'متصل' : 'قطع'}</span>
          </div>
          
          {/* More Options */}
          <div className="relative">
            <button
              onClick={() => setShowMenu(!showMenu)}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors text-lg"
            >
              ⋮
            </button>
            
            {showMenu && (
              <>
                {/* Backdrop */}
                <div 
                  className="fixed inset-0 z-10"
                  onClick={() => setShowMenu(false)}
                />
                
                {/* Menu */}
                <div className="absolute left-0 top-full mt-2 w-48 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-20">
                  <button
                    onClick={handleShare}
                    className="w-full flex items-center gap-3 px-4 py-2 text-right hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <span>🔗</span>
                    <span className="text-sm">اشتراک‌گذاری</span>
                  </button>
                  <button
                    onClick={handleArchive}
                    className="w-full flex items-center gap-3 px-4 py-2 text-right hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
                  >
                    <span>📦</span>
                    <span className="text-sm">آرشیو گفتگو</span>
                  </button>
                  <button
                    onClick={handleDelete}
                    className="w-full flex items-center gap-3 px-4 py-2 text-right hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-red-600 dark:text-red-400"
                  >
                    <span>🗑️</span>
                    <span className="text-sm">حذف گفتگو</span>
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
