'use client'

import React, { useState, useEffect } from 'react'
import axios from 'axios'
import clsx from 'clsx'

interface Notification {
  id: string
  title: string
  body: string
  category: string
  priority: string
  is_read: boolean
  created_at: string
  action_url?: string
  action_text?: string
}

interface NotificationsPanelProps {
  isOpen: boolean
  onClose: () => void
  onUnreadCountChange?: (count: number) => void
}

const categoryLabels: Record<string, string> = {
  system: 'سیستمی',
  payment: 'پرداخت',
  subscription: 'اشتراک',
  chat: 'چت',
  security: 'امنیت',
  marketing: 'بازاریابی',
  support: 'پشتیبانی',
}

const categoryIcons: Record<string, string> = {
  system: '⚙️',
  payment: '💳',
  subscription: '📦',
  chat: '💬',
  security: '🔒',
  marketing: '📢',
  support: '🎧',
}

const priorityColors: Record<string, string> = {
  urgent: 'border-r-red-500',
  high: 'border-r-orange-500',
  normal: 'border-r-blue-500',
  low: 'border-r-gray-400',
}

export default function NotificationsPanel({ isOpen, onClose, onUnreadCountChange }: NotificationsPanelProps) {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'unread'>('all')

  useEffect(() => {
    if (isOpen) {
      loadNotifications()
    }
  }, [isOpen])

  const loadNotifications = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v1/notifications/')
      setNotifications(response.data.results || response.data || [])
      updateUnreadCount(response.data.results || response.data || [])
    } catch (error) {
      console.error('Error loading notifications:', error)
    } finally {
      setLoading(false)
    }
  }

  const updateUnreadCount = (notifs: Notification[]) => {
    const count = notifs.filter(n => !n.is_read).length
    onUnreadCountChange?.(count)
  }

  const markAsRead = async (id: string) => {
    try {
      await axios.get(`/api/v1/notifications/${id}/`)
      setNotifications(prev => {
        const updated = prev.map(n => n.id === id ? { ...n, is_read: true } : n)
        updateUnreadCount(updated)
        return updated
      })
    } catch (error) {
      console.error('Error marking as read:', error)
    }
  }

  const markAllAsRead = async () => {
    try {
      await axios.post('/api/v1/notifications/mark_all_read/')
      setNotifications(prev => {
        const updated = prev.map(n => ({ ...n, is_read: true }))
        updateUnreadCount(updated)
        return updated
      })
    } catch (error) {
      console.error('Error marking all as read:', error)
    }
  }

  const deleteNotification = async (id: string) => {
    try {
      await axios.delete(`/api/v1/notifications/${id}/`)
      setNotifications(prev => {
        const updated = prev.filter(n => n.id !== id)
        updateUnreadCount(updated)
        return updated
      })
    } catch (error) {
      console.error('Error deleting notification:', error)
    }
  }

  const deleteAllRead = async () => {
    try {
      await axios.post('/api/v1/notifications/delete_read/')
      setNotifications(prev => {
        const updated = prev.filter(n => !n.is_read)
        updateUnreadCount(updated)
        return updated
      })
    } catch (error) {
      console.error('Error deleting read notifications:', error)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'همین الان'
    if (minutes < 60) return `${minutes} دقیقه پیش`
    if (hours < 24) return `${hours} ساعت پیش`
    if (days < 7) return `${days} روز پیش`
    return date.toLocaleDateString('fa-IR')
  }

  const filteredNotifications = filter === 'unread' 
    ? notifications.filter(n => !n.is_read)
    : notifications

  const unreadCount = notifications.filter(n => !n.is_read).length

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-start justify-center pt-20" onClick={onClose}>
      <div 
        className="bg-white dark:bg-gray-900 rounded-2xl shadow-2xl w-full max-w-lg max-h-[70vh] flex flex-col overflow-hidden mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xl">🔔</span>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">اعلان‌ها</h2>
            {unreadCount > 0 && (
              <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                {unreadCount}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-xl">
            ×
          </button>
        </div>

        {/* Filters & Actions */}
        <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <div className="flex gap-2">
            <button
              onClick={() => setFilter('all')}
              className={clsx(
                'px-3 py-1 text-xs rounded-full transition-colors',
                filter === 'all' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              )}
            >
              همه
            </button>
            <button
              onClick={() => setFilter('unread')}
              className={clsx(
                'px-3 py-1 text-xs rounded-full transition-colors',
                filter === 'unread' 
                  ? 'bg-blue-500 text-white' 
                  : 'bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700'
              )}
            >
              خوانده نشده
            </button>
          </div>
          
          <div className="flex gap-2">
            {unreadCount > 0 && (
              <button
                onClick={markAllAsRead}
                className="text-xs text-blue-500 hover:text-blue-600"
              >
                خواندن همه
              </button>
            )}
            {notifications.some(n => n.is_read) && (
              <button
                onClick={deleteAllRead}
                className="text-xs text-red-500 hover:text-red-600"
              >
                حذف خوانده‌شده‌ها
              </button>
            )}
          </div>
        </div>

        {/* Notifications List */}
        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : filteredNotifications.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-gray-500">
              <span className="text-5xl mb-3 opacity-50">🔔</span>
              <p>{filter === 'unread' ? 'اعلان خوانده نشده‌ای ندارید' : 'اعلانی وجود ندارد'}</p>
            </div>
          ) : (
            <div className="divide-y divide-gray-100 dark:divide-gray-800">
              {filteredNotifications.map((notification) => (
                <div
                  key={notification.id}
                  className={clsx(
                    'px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors cursor-pointer border-r-4',
                    priorityColors[notification.priority] || 'border-r-gray-300',
                    !notification.is_read && 'bg-blue-50/50 dark:bg-blue-900/10'
                  )}
                  onClick={() => !notification.is_read && markAsRead(notification.id)}
                >
                  <div className="flex items-start gap-3">
                    {/* Icon */}
                    <span className="text-xl flex-shrink-0">
                      {categoryIcons[notification.category] || '📌'}
                    </span>
                    
                    {/* Content */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className={clsx(
                          'text-sm truncate',
                          !notification.is_read ? 'font-bold text-gray-900 dark:text-white' : 'font-medium text-gray-700 dark:text-gray-300'
                        )}>
                          {notification.title}
                        </h3>
                        {!notification.is_read && (
                          <span className="w-2 h-2 bg-blue-500 rounded-full flex-shrink-0"></span>
                        )}
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                        {notification.body}
                      </p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-xs text-gray-400">
                          {formatDate(notification.created_at)}
                        </span>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-gray-400 bg-gray-100 dark:bg-gray-800 px-2 py-0.5 rounded">
                            {categoryLabels[notification.category] || notification.category}
                          </span>
                          <button
                            onClick={(e) => { e.stopPropagation(); deleteNotification(notification.id); }}
                            className="text-gray-400 hover:text-red-500 text-sm"
                            title="حذف"
                          >
                            🗑️
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
