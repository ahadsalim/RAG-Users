'use client'

import { useState, useEffect } from 'react'
import { 
  Brain, 
  Plus, 
  Pencil, 
  Trash2, 
  User, 
  Heart, 
  Target, 
  Sparkles, 
  Briefcase, 
  MessageSquare,
  MoreHorizontal,
  Loader2,
  AlertCircle,
  Check,
  X
} from 'lucide-react'
import axiosInstance from '@/lib/axios'

// دسته‌بندی‌های حافظه
const MEMORY_CATEGORIES = {
  personal_info: { label: 'اطلاعات شخصی', icon: User, color: 'text-blue-500' },
  preference: { label: 'ترجیحات', icon: Heart, color: 'text-pink-500' },
  goal: { label: 'اهداف', icon: Target, color: 'text-green-500' },
  interest: { label: 'علاقه‌مندی‌ها', icon: Sparkles, color: 'text-yellow-500' },
  context: { label: 'زمینه کاری', icon: Briefcase, color: 'text-purple-500' },
  behavior: { label: 'سبک رفتار', icon: MessageSquare, color: 'text-orange-500' },
  other: { label: 'سایر', icon: MoreHorizontal, color: 'text-gray-500' },
}

interface MemoryItem {
  id: string
  content: string
  category: keyof typeof MEMORY_CATEGORIES
  confidence: number
  usage_count: number
  created_at: string
  updated_at: string
}

interface MemoryResponse {
  user_id: string
  memories: MemoryItem[]
  total_count: number
}

export default function MemorySection() {
  const [memories, setMemories] = useState<MemoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editContent, setEditContent] = useState('')
  const [editCategory, setEditCategory] = useState<string>('other')
  const [isAdding, setIsAdding] = useState(false)
  const [newContent, setNewContent] = useState('')
  const [newCategory, setNewCategory] = useState<string>('other')
  const [saving, setSaving] = useState(false)
  const [deleting, setDeleting] = useState<string | null>(null)

  // دریافت حافظه‌ها
  const fetchMemories = async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await axiosInstance.get<MemoryResponse>('/api/v1/chat/memory/')
      setMemories(response.data.memories || [])
    } catch (err: any) {
      console.error('Error fetching memories:', err)
      if (err.response?.status === 404) {
        // اگر endpoint وجود نداشت، لیست خالی نشان بده
        setMemories([])
      } else {
        setError('خطا در دریافت حافظه‌ها')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchMemories()
  }, [])

  // افزودن حافظه جدید
  const handleAdd = async () => {
    if (!newContent.trim()) return
    
    try {
      setSaving(true)
      await axiosInstance.post('/api/v1/chat/memory/', {
        content: newContent.trim(),
        category: newCategory
      })
      setNewContent('')
      setNewCategory('other')
      setIsAdding(false)
      await fetchMemories()
    } catch (err) {
      console.error('Error adding memory:', err)
      setError('خطا در افزودن حافظه')
    } finally {
      setSaving(false)
    }
  }

  // ویرایش حافظه
  const handleEdit = async (id: string) => {
    if (!editContent.trim()) return
    
    try {
      setSaving(true)
      await axiosInstance.put(`/api/v1/chat/memory/${id}/`, {
        content: editContent.trim(),
        category: editCategory
      })
      setEditingId(null)
      await fetchMemories()
    } catch (err) {
      console.error('Error updating memory:', err)
      setError('خطا در ویرایش حافظه')
    } finally {
      setSaving(false)
    }
  }

  // حذف یک حافظه
  const handleDelete = async (id: string) => {
    try {
      setDeleting(id)
      await axiosInstance.delete(`/api/v1/chat/memory/${id}/`)
      await fetchMemories()
    } catch (err) {
      console.error('Error deleting memory:', err)
      setError('خطا در حذف حافظه')
    } finally {
      setDeleting(null)
    }
  }

  // پاک کردن همه حافظه‌ها
  const handleClearAll = async () => {
    if (!confirm('آیا مطمئن هستید که می‌خواهید همه حافظه‌ها را پاک کنید؟')) return
    
    try {
      setLoading(true)
      await axiosInstance.delete('/api/v1/chat/memory/')
      setMemories([])
    } catch (err) {
      console.error('Error clearing memories:', err)
      setError('خطا در پاک کردن حافظه‌ها')
    } finally {
      setLoading(false)
    }
  }

  // شروع ویرایش
  const startEdit = (memory: MemoryItem) => {
    setEditingId(memory.id)
    setEditContent(memory.content)
    setEditCategory(memory.category)
  }

  // گروه‌بندی حافظه‌ها بر اساس دسته‌بندی
  const groupedMemories = memories.reduce((acc, memory) => {
    const category = memory.category || 'other'
    if (!acc[category]) acc[category] = []
    acc[category].push(memory)
    return acc
  }, {} as Record<string, MemoryItem[]>)

  if (loading && memories.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
          <span className="mr-2 text-gray-600 dark:text-gray-400">در حال بارگذاری...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-purple-500" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            حافظه من
          </h3>
          <span className="text-sm text-gray-500 dark:text-gray-400">
            ({memories.length} مورد)
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {memories.length > 0 && (
            <button
              onClick={handleClearAll}
              className="text-sm text-red-500 hover:text-red-600 flex items-center gap-1"
            >
              <Trash2 className="w-4 h-4" />
              پاک کردن همه
            </button>
          )}
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg flex items-center gap-2 text-red-600 dark:text-red-400">
          <AlertCircle className="w-4 h-4" />
          <span className="text-sm">{error}</span>
          <button onClick={() => setError(null)} className="mr-auto">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* توضیحات */}
      <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
        اطلاعاتی که دستیار هوشمند درباره شما یاد گرفته است. این اطلاعات در همه گفتگوها استفاده می‌شود.
      </p>

      {/* لیست حافظه‌ها */}
      <div className="space-y-4">
        {Object.entries(groupedMemories).map(([category, items]) => {
          const categoryInfo = MEMORY_CATEGORIES[category as keyof typeof MEMORY_CATEGORIES] || MEMORY_CATEGORIES.other
          const Icon = categoryInfo.icon
          
          return (
            <div key={category} className="border dark:border-gray-700 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Icon className={`w-4 h-4 ${categoryInfo.color}`} />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {categoryInfo.label}
                </span>
              </div>
              
              <div className="space-y-2">
                {items.map((memory) => (
                  <div 
                    key={memory.id}
                    className="flex items-start justify-between gap-2 p-2 bg-gray-50 dark:bg-gray-700/50 rounded-lg"
                  >
                    {editingId === memory.id ? (
                      // حالت ویرایش
                      <div className="flex-1 space-y-2">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full p-2 text-sm border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                          rows={2}
                          dir="rtl"
                        />
                        <div className="flex items-center gap-2">
                          <select
                            value={editCategory}
                            onChange={(e) => setEditCategory(e.target.value)}
                            className="text-sm border dark:border-gray-600 rounded-lg p-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                          >
                            {Object.entries(MEMORY_CATEGORIES).map(([key, val]) => (
                              <option key={key} value={key}>{val.label}</option>
                            ))}
                          </select>
                          <button
                            onClick={() => handleEdit(memory.id)}
                            disabled={saving}
                            className="p-1 text-green-500 hover:bg-green-100 dark:hover:bg-green-900/30 rounded"
                          >
                            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
                          </button>
                          <button
                            onClick={() => setEditingId(null)}
                            className="p-1 text-gray-500 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ) : (
                      // حالت نمایش
                      <>
                        <span className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                          {memory.content}
                        </span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => startEdit(memory)}
                            className="p-1 text-gray-400 hover:text-blue-500 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded"
                          >
                            <Pencil className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleDelete(memory.id)}
                            disabled={deleting === memory.id}
                            className="p-1 text-gray-400 hover:text-red-500 hover:bg-red-100 dark:hover:bg-red-900/30 rounded"
                          >
                            {deleting === memory.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Trash2 className="w-4 h-4" />
                            )}
                          </button>
                        </div>
                      </>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )
        })}

        {/* پیام خالی بودن */}
        {memories.length === 0 && !isAdding && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <Brain className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>هنوز حافظه‌ای ذخیره نشده است</p>
            <p className="text-sm">دستیار هوشمند به مرور زمان اطلاعات مهم را یاد می‌گیرد</p>
          </div>
        )}

        {/* فرم افزودن */}
        {isAdding ? (
          <div className="border dark:border-gray-700 rounded-lg p-3 bg-blue-50 dark:bg-blue-900/20">
            <div className="space-y-2">
              <textarea
                value={newContent}
                onChange={(e) => setNewContent(e.target.value)}
                placeholder="مثال: من مهندس نرم‌افزار هستم"
                className="w-full p-2 text-sm border dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white resize-none"
                rows={2}
                dir="rtl"
                autoFocus
              />
              <div className="flex items-center gap-2">
                <select
                  value={newCategory}
                  onChange={(e) => setNewCategory(e.target.value)}
                  className="text-sm border dark:border-gray-600 rounded-lg p-1 bg-white dark:bg-gray-800 text-gray-900 dark:text-white"
                >
                  {Object.entries(MEMORY_CATEGORIES).map(([key, val]) => (
                    <option key={key} value={key}>{val.label}</option>
                  ))}
                </select>
                <button
                  onClick={handleAdd}
                  disabled={saving || !newContent.trim()}
                  className="px-3 py-1 bg-blue-500 text-white rounded-lg text-sm hover:bg-blue-600 disabled:opacity-50 flex items-center gap-1"
                >
                  {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plus className="w-4 h-4" />}
                  افزودن
                </button>
                <button
                  onClick={() => { setIsAdding(false); setNewContent(''); }}
                  className="px-3 py-1 text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-lg text-sm"
                >
                  انصراف
                </button>
              </div>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setIsAdding(true)}
            className="w-full py-3 border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg text-gray-500 dark:text-gray-400 hover:border-blue-400 hover:text-blue-500 flex items-center justify-center gap-2 transition-colors"
          >
            <Plus className="w-5 h-5" />
            افزودن حافظه جدید
          </button>
        )}
      </div>
    </div>
  )
}
