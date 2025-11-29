'use client'

import { Conversation } from '@/types/chat'
import clsx from 'clsx'

interface ChatHeaderProps {
  onToggleSidebar: () => void
  conversation?: Conversation | null
  isConnected: boolean
}

export function ChatHeader({ onToggleSidebar, conversation, isConnected }: ChatHeaderProps) {
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
        </div>
      </div>
    </header>
  )
}
