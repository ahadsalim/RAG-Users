'use client'

import { useState, useEffect } from 'react'
import { Conversation } from '@/types/chat'
import clsx from 'clsx'
import axios from 'axios'

interface ChatHeaderProps {
  onToggleSidebar: () => void
  conversation?: Conversation | null
  isConnected: boolean
}

interface UsageInfo {
  daily_used: number
  daily_limit: number
  monthly_used: number
  monthly_limit: number
}

export function ChatHeader({ onToggleSidebar, conversation, isConnected }: ChatHeaderProps) {
  const [showUsageTooltip, setShowUsageTooltip] = useState(false)
  const [usage, setUsage] = useState<UsageInfo | null>(null)
  const [loadingUsage, setLoadingUsage] = useState(false)

  // بارگذاری اطلاعات مصرف هنگام hover
  const loadUsage = async () => {
    if (usage) return // اگر قبلاً بارگذاری شده، دوباره نخوان
    
    try {
      setLoadingUsage(true)
      const response = await axios.get('/api/v1/subscriptions/usage/')
      if (response.data?.usage) {
        setUsage(response.data.usage)
      } else {
        // اگر داده‌ای نبود، مقادیر پیش‌فرض
        setUsage({
          daily_used: 0,
          daily_limit: 0,
          monthly_used: 0,
          monthly_limit: 0
        })
      }
    } catch (error) {
      console.error('Error loading usage:', error)
      // در صورت خطا هم مقادیر پیش‌فرض
      setUsage({
        daily_used: 0,
        daily_limit: 0,
        monthly_used: 0,
        monthly_limit: 0
      })
    } finally {
      setLoadingUsage(false)
    }
  }

  const handleMouseEnter = () => {
    setShowUsageTooltip(true)
    loadUsage()
  }

  const handleMouseLeave = () => {
    setShowUsageTooltip(false)
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
          {/* Connection Status with Usage Tooltip */}
          <div 
            className="relative"
            onMouseEnter={handleMouseEnter}
            onMouseLeave={handleMouseLeave}
          >
            <div className={clsx(
              'flex items-center gap-1 px-2 py-1 rounded-lg text-xs cursor-pointer',
              isConnected
                ? 'bg-green-100 dark:bg-green-900 text-green-700 dark:text-green-400'
                : 'bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-400'
            )}>
              <span>{isConnected ? '🟢' : '🔴'}</span>
              <span>{isConnected ? 'متصل' : 'قطع'}</span>
            </div>
            
            {/* Usage Tooltip */}
            {showUsageTooltip && isConnected && (
              <div className="absolute top-full left-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-700 p-3 z-50">
                <div className="text-sm font-semibold text-gray-900 dark:text-white mb-3 border-b border-gray-200 dark:border-gray-700 pb-2">
                  میزان مصرف
                </div>
                
                {loadingUsage ? (
                  <div className="text-center py-2 text-gray-500 text-xs">
                    در حال بارگذاری...
                  </div>
                ) : usage ? (
                  <div className="space-y-3">
                    {/* Daily Usage */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600 dark:text-gray-400">امروز</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {usage.daily_used} / {usage.daily_limit}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div 
                          className={clsx(
                            'h-1.5 rounded-full transition-all',
                            (usage.daily_used / usage.daily_limit) > 0.8 ? 'bg-red-500' : 'bg-blue-500'
                          )}
                          style={{ width: `${Math.min(100, (usage.daily_used / usage.daily_limit) * 100)}%` }}
                        />
                      </div>
                    </div>
                    
                    {/* Monthly Usage */}
                    <div>
                      <div className="flex justify-between text-xs mb-1">
                        <span className="text-gray-600 dark:text-gray-400">این ماه</span>
                        <span className="font-medium text-gray-900 dark:text-white">
                          {usage.monthly_used} / {usage.monthly_limit}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div 
                          className={clsx(
                            'h-1.5 rounded-full transition-all',
                            (usage.monthly_used / usage.monthly_limit) > 0.8 ? 'bg-red-500' : 'bg-purple-500'
                          )}
                          style={{ width: `${Math.min(100, (usage.monthly_used / usage.monthly_limit) * 100)}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-2 text-gray-500 text-xs">
                    اطلاعات مصرف در دسترس نیست
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  )
}
