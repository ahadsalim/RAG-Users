'use client'

import { useState, useEffect } from 'react'
import axios from 'axios'
import clsx from 'clsx'

interface SupportPageProps {
  isOpen: boolean
  onClose: () => void
}

interface Ticket {
  id: string
  ticket_number: string
  subject: string
  description: string
  status: string
  status_display: string
  priority: string
  priority_display: string
  category_name?: string
  department_name?: string
  messages_count: number
  user_read: boolean
  created_at: string
  updated_at: string
}

interface TicketMessage {
  id: string
  sender_info: {
    id: string
    full_name: string
    is_staff: boolean
  }
  content: string
  is_staff_reply: boolean
  created_at: string
}

interface Department {
  id: string
  name: string
  description: string
}

interface Category {
  id: string
  name: string
  description: string
  icon: string
  color: string
  default_priority: string
}

export default function SupportPage({ isOpen, onClose }: SupportPageProps) {
  const [view, setView] = useState<'list' | 'create' | 'detail'>('list')
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [ticketMessages, setTicketMessages] = useState<TicketMessage[]>([])
  const [departments, setDepartments] = useState<Department[]>([])
  const [categories, setCategories] = useState<Category[]>([])
  const [loading, setLoading] = useState(false)
  const [sending, setSending] = useState(false)
  
  // Form states
  const [subject, setSubject] = useState('')
  const [description, setDescription] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [departmentId, setDepartmentId] = useState('')
  const [priority, setPriority] = useState('medium')
  const [replyContent, setReplyContent] = useState('')

  useEffect(() => {
    if (isOpen) {
      loadTickets()
      loadDepartments()
      loadCategories()
    }
  }, [isOpen])

  const loadTickets = async () => {
    try {
      setLoading(true)
      const response = await axios.get('/api/v1/support/tickets/my_tickets/')
      setTickets(response.data.results || response.data)
    } catch (error) {
      console.error('Error loading tickets:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadDepartments = async () => {
    try {
      const response = await axios.get('/api/v1/support/departments/')
      setDepartments(response.data.results || response.data)
    } catch (error) {
      console.error('Error loading departments:', error)
    }
  }

  const loadCategories = async () => {
    try {
      const response = await axios.get('/api/v1/support/categories/')
      setCategories(response.data.results || response.data)
    } catch (error) {
      console.error('Error loading categories:', error)
    }
  }

  const loadTicketDetail = async (ticketId: string) => {
    try {
      setLoading(true)
      const response = await axios.get(`/api/v1/support/tickets/${ticketId}/`)
      
      if (response.data) {
        setSelectedTicket(response.data)
        
        // فیلتر کردن پیام‌ها - فقط reply و question برای کاربر قابل رویت است
        if (response.data.messages && Array.isArray(response.data.messages)) {
          const visibleMessages = response.data.messages.filter(
            (msg: any) => msg.message_type === 'reply' || msg.message_type === 'question'
          )
          setTicketMessages(visibleMessages)
        } else {
          setTicketMessages([])
        }
        
        setView('detail')
      }
    } catch (error: any) {
      console.error('Error loading ticket detail:', error)
      const errorMsg = error.response?.data?.detail || error.message || 'خطا در بارگذاری جزئیات تیکت'
      alert(errorMsg)
    } finally {
      setLoading(false)
    }
  }

  const createTicket = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      setSending(true)
      await axios.post('/api/v1/support/tickets/', {
        subject,
        description,
        category: categoryId,
        department: departmentId,
        priority
      })
      
      setSubject('')
      setDescription('')
      setCategoryId('')
      setDepartmentId('')
      setPriority('medium')
      
      await loadTickets()
      setView('list')
    } catch (error) {
      console.error('Error creating ticket:', error)
      alert('خطا در ایجاد تیکت')
    } finally {
      setSending(false)
    }
  }

  const sendReply = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedTicket || !replyContent.trim()) return
    
    try {
      setSending(true)
      await axios.post(`/api/v1/support/tickets/${selectedTicket.id}/reply/`, {
        content: replyContent,
        message_type: 'reply'
      })
      
      setReplyContent('')
      await loadTicketDetail(selectedTicket.id)
    } catch (error) {
      console.error('Error sending reply:', error)
      alert('خطا در ارسال پاسخ')
    } finally {
      setSending(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
      case 'in_progress': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
      case 'waiting': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200'
      case 'answered': return 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
      case 'closed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200'
    }
  }

  const getPriorityColor = (priority: string) => {
    const colors: Record<string, string> = {
      low: 'bg-gray-100 text-gray-700',
      medium: 'bg-blue-100 text-blue-700',
      high: 'bg-orange-100 text-orange-700',
      urgent: 'bg-red-100 text-red-700'
    }
    return colors[priority] || 'bg-gray-100 text-gray-700'
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return new Intl.DateTimeFormat('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-3">
            <span className="text-xl">🎧</span>
            <h2 className="text-xl font-bold text-gray-900 dark:text-white">پشتیبانی</h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-xl"
          >
            ×
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 px-6 pt-4 border-b border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setView('list')}
            className={clsx(
              'px-4 py-2 rounded-t-lg text-xs font-medium transition-colors',
              view === 'list'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            تیکت‌های من
          </button>
          <button
            onClick={() => setView('create')}
            className={clsx(
              'px-4 py-2 rounded-t-lg text-xs font-medium transition-colors',
              view === 'create'
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
            )}
          >
            تیکت جدید
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* List View */}
          {view === 'list' && (
            <div className="space-y-3">
              {loading ? (
                <div className="text-center py-12 text-gray-500 text-xs">در حال بارگذاری...</div>
              ) : tickets.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  <p className="text-4xl mb-4">📭</p>
                  <p className="text-xs">هیچ تیکتی وجود ندارد</p>
                  <button
                    onClick={() => setView('create')}
                    className="mt-4 px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 text-xs"
                  >
                    ایجاد تیکت جدید
                  </button>
                </div>
              ) : (
                tickets.map((ticket) => (
                  <div
                    key={ticket.id}
                    onClick={() => loadTicketDetail(ticket.id)}
                    className={clsx(
                      'p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md',
                      ticket.user_read
                        ? 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800'
                        : 'border-blue-300 dark:border-blue-700 bg-blue-50 dark:bg-blue-900/20'
                    )}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="font-mono text-xs text-gray-500">#{ticket.ticket_number}</span>
                          <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', getStatusColor(ticket.status))}>
                            {ticket.status_display}
                          </span>
                          <span className={clsx('px-2 py-0.5 rounded-full text-xs font-medium', getPriorityColor(ticket.priority))}>
                            {ticket.priority_display}
                          </span>
                          {!ticket.user_read && (
                            <span className="px-2 py-0.5 bg-red-500 text-white rounded-full text-xs font-medium">
                              جدید
                            </span>
                          )}
                        </div>
                        <h3 className="font-semibold text-gray-900 dark:text-white mb-1 text-xs">{ticket.subject}</h3>
                        <p className="text-xs text-gray-600 dark:text-gray-400 line-clamp-2">{ticket.description}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          {ticket.category_name && <span>📁 {ticket.category_name}</span>}
                          {ticket.department_name && <span>🏢 {ticket.department_name}</span>}
                          <span>💬 {ticket.messages_count} پیام</span>
                          <span>🕐 {formatDate(ticket.created_at)}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}

          {/* Create View */}
          {view === 'create' && (
            <form onSubmit={createTicket} className="space-y-4">
              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                  موضوع تیکت *
                </label>
                <input
                  type="text"
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  required
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs"
                  placeholder="موضوع تیکت خود را وارد کنید"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                  توضیحات *
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  required
                  rows={6}
                  className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none text-xs"
                  placeholder="توضیحات کامل مشکل یا سوال خود را بنویسید..."
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    دسته‌بندی *
                  </label>
                  <select
                    value={categoryId}
                    onChange={(e) => setCategoryId(e.target.value)}
                    required
                    className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs appearance-none bg-no-repeat bg-[length:16px] bg-[center_left_0.75rem] cursor-pointer"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236B7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E")`
                    }}
                  >
                    <option value="">انتخاب کنید</option>
                    {categories.map((cat) => (
                      <option key={cat.id} value={cat.id}>{cat.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    دپارتمان *
                  </label>
                  <select
                    value={departmentId}
                    onChange={(e) => setDepartmentId(e.target.value)}
                    required
                    className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs appearance-none bg-no-repeat bg-[length:16px] bg-[center_left_0.75rem] cursor-pointer"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236B7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E")`
                    }}
                  >
                    <option value="">انتخاب کنید</option>
                    {departments.map((dept) => (
                      <option key={dept.id} value={dept.id}>{dept.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    اولویت
                  </label>
                  <select
                    value={priority}
                    onChange={(e) => setPriority(e.target.value)}
                    className="w-full px-4 py-2 pr-10 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white text-xs appearance-none bg-no-repeat bg-[length:16px] bg-[center_left_0.75rem] cursor-pointer"
                    style={{
                      backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 20 20'%3E%3Cpath stroke='%236B7280' stroke-linecap='round' stroke-linejoin='round' stroke-width='1.5' d='M6 8l4 4 4-4'/%3E%3C/svg%3E")`
                    }}
                  >
                    <option value="low">کم</option>
                    <option value="medium">متوسط</option>
                    <option value="high">بالا</option>
                    <option value="urgent">فوری</option>
                  </select>
                </div>
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="submit"
                  disabled={sending || !categoryId || !departmentId}
                  className="flex-1 px-6 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed font-medium text-xs"
                >
                  {sending ? 'در حال ارسال...' : 'ایجاد تیکت'}
                </button>
                <button
                  type="button"
                  onClick={() => setView('list')}
                  className="px-6 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 text-xs"
                >
                  انصراف
                </button>
              </div>
            </form>
          )}

          {/* Detail View */}
          {view === 'detail' && selectedTicket && (
            <div className="space-y-4">
              {/* Ticket Header */}
              <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => { setView('list'); setSelectedTicket(null); }}
                      className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 text-xs"
                    >
                      ← بازگشت
                    </button>
                    <span className="font-mono text-xs text-gray-500">#{selectedTicket.ticket_number}</span>
                  </div>
                  <div className="flex gap-2">
                    <span className={clsx('px-3 py-1 rounded-full text-xs font-medium', getStatusColor(selectedTicket.status))}>
                      {selectedTicket.status_display}
                    </span>
                    <span className={clsx('px-3 py-1 rounded-full text-xs font-medium', getPriorityColor(selectedTicket.priority))}>
                      {selectedTicket.priority_display}
                    </span>
                  </div>
                </div>
                <h2 className="text-sm font-bold text-gray-900 dark:text-white mb-2">{selectedTicket.subject}</h2>
                <p className="text-gray-600 dark:text-gray-400 text-xs">{selectedTicket.description}</p>
              </div>

              {/* Messages */}
              <div className="space-y-3">
                {ticketMessages.map((message) => (
                  <div
                    key={message.id}
                    className={clsx(
                      'p-4 rounded-lg',
                      message.is_staff_reply
                        ? 'bg-blue-50 dark:bg-blue-900/20 border-r-4 border-blue-500'
                        : 'bg-gray-50 dark:bg-gray-700/50'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <span className="font-semibold text-gray-900 dark:text-white text-xs">
                        {message.sender_info.full_name}
                      </span>
                      {message.is_staff_reply && (
                        <span className="px-2 py-0.5 bg-blue-500 text-white rounded-full text-xs">
                          پشتیبانی
                        </span>
                      )}
                      <span className="text-xs text-gray-500 mr-auto">
                        {formatDate(message.created_at)}
                      </span>
                    </div>
                    <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap text-xs">{message.content}</p>
                  </div>
                ))}
              </div>

              {/* Reply Form */}
              {selectedTicket.status !== 'closed' && (
                <form onSubmit={sendReply} className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4">
                  <label className="block text-xs font-medium text-gray-700 dark:text-gray-300 mb-2">
                    پاسخ شما
                  </label>
                  <textarea
                    value={replyContent}
                    onChange={(e) => setReplyContent(e.target.value)}
                    required
                    rows={4}
                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white resize-none mb-3 text-xs"
                    placeholder="پاسخ خود را بنویسید..."
                  />
                  <button
                    type="submit"
                    disabled={sending || !replyContent.trim()}
                    className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 disabled:opacity-50 font-medium text-xs"
                  >
                    {sending ? 'در حال ارسال...' : 'ارسال پاسخ'}
                  </button>
                </form>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
