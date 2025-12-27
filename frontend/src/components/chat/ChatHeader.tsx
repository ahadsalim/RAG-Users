'use client'

import { useState, useEffect } from 'react'
import { Conversation } from '@/types/chat'
import { useAuthStore } from '@/store/auth'
import clsx from 'clsx'
import axios from 'axios'
import SettingsPage from '@/components/SettingsPage'
import NotificationsPanel from '@/components/NotificationsPanel'
import SupportPage from '@/components/SupportPage'

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
  const [showUserMenu, setShowUserMenu] = useState(false)
  const [isSettingsOpen, setIsSettingsOpen] = useState(false)
  const [isNotificationsOpen, setIsNotificationsOpen] = useState(false)
  const [isSupportOpen, setIsSupportOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)
  const { user, logout } = useAuthStore()
  
  // Load unread count on mount
  useEffect(() => {
    const loadUnreadCount = async () => {
      try {
        const response = await axios.get('/api/v1/notifications/unread_count/')
        setUnreadCount(response.data.count || 0)
      } catch (error) {
        console.error('Error loading unread count:', error)
      }
    }
    loadUnreadCount()
    // Refresh every 60 seconds
    const interval = setInterval(loadUnreadCount, 60000)
    return () => clearInterval(interval)
  }, [])
  
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

  // بارگذاری اطلاعات مصرف هنگام hover
  const loadUsage = async () => {
    // فقط برای کاربران حقیقی آمار نمایش داده می‌شود
    if (user?.user_type !== 'individual') {
      return
    }
    
    try {
      setLoadingUsage(true)
      const response = await axios.get('/api/v1/subscriptions/usage/', {
        headers: { 'Cache-Control': 'no-cache' }
      })
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
    // فقط برای کاربران حقیقی tooltip نمایش داده می‌شود
    if (user?.user_type === 'individual') {
      setShowUsageTooltip(true)
      loadUsage()
    }
  }

  const handleMouseLeave = () => {
    setShowUsageTooltip(false)
  }

  return (
    <>
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
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex items-center gap-3">
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
          
          {/* User Avatar with Menu */}
          <div className="relative">
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="relative w-9 h-9 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center hover:ring-2 hover:ring-blue-400 transition-all shadow-md"
              title={getUserDisplayName()}
            >
              <span className="text-sm font-bold text-white">
                {getUserDisplayName().charAt(0).toUpperCase()}
              </span>
              {/* Notification Badge */}
              {unreadCount > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center font-bold shadow-lg">
                  {unreadCount > 9 ? '9+' : unreadCount}
                </span>
              )}
            </button>
            
            {/* User Dropdown Menu */}
            {showUserMenu && (
              <>
                <div 
                  className="fixed inset-0 z-40" 
                  onClick={() => setShowUserMenu(false)}
                />
                <div className="absolute left-0 top-12 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-xl shadow-xl py-2 z-50 min-w-[220px]">
                  {/* User Info */}
                  <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700">
                    <p className="font-medium text-gray-900 dark:text-white truncate">{getUserDisplayName()}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{user?.email || user?.phone_number}</p>
                    {(user?.is_superuser || user?.is_staff || user?.user_type === 'business') && (
                      <p className="text-xs mt-1">
                        {user?.is_superuser ? (
                          <span className="text-red-500 font-semibold">مدیر ارشد</span>
                        ) : user?.is_staff ? (
                          <span className="text-yellow-500">کارمند</span>
                        ) : user?.user_type === 'business' ? (
                          <span className="text-purple-500">حقوقی</span>
                        ) : null}
                      </p>
                    )}
                  </div>
                  
                  {/* Menu Items */}
                  <div className="py-1">
                    <button 
                      onClick={() => { setIsNotificationsOpen(true); setShowUserMenu(false); }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 text-right text-sm text-gray-700 dark:text-gray-300"
                    >
                      <span>🔔</span>
                      <span>اعلان‌ها</span>
                      {unreadCount > 0 && (
                        <span className="mr-auto bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                          {unreadCount}
                        </span>
                      )}
                    </button>
                    <button 
                      onClick={() => { setIsSettingsOpen(true); setShowUserMenu(false); }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 text-right text-sm text-gray-700 dark:text-gray-300"
                    >
                      <span>⚙️</span>
                      <span>اطلاعات کاربری</span>
                    </button>
                    <button 
                      onClick={() => { setIsSupportOpen(true); setShowUserMenu(false); }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 text-right text-sm text-gray-700 dark:text-gray-300"
                    >
                      <span>🎧</span>
                      <span>پشتیبانی</span>
                    </button>
                    <button 
                      onClick={() => { logout(); setShowUserMenu(false); }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 hover:bg-gray-100 dark:hover:bg-gray-700 text-red-500 text-right text-sm"
                    >
                      <span>🚪</span>
                      <span>خروج</span>
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
    
    {/* Settings Page */}
    <SettingsPage 
      isOpen={isSettingsOpen} 
      onClose={() => setIsSettingsOpen(false)} 
    />
    
    {/* Notifications Panel */}
    <NotificationsPanel 
      isOpen={isNotificationsOpen} 
      onClose={() => setIsNotificationsOpen(false)}
      onUnreadCountChange={setUnreadCount}
    />
    
    {/* Support Page */}
    <SupportPage 
      isOpen={isSupportOpen} 
      onClose={() => setIsSupportOpen(false)} 
    />
    </>
  )
}
