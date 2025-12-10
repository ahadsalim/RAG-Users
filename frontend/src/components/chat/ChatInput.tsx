'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import clsx from 'clsx'
import { useAuthStore } from '@/store/auth'

// فرمت‌های مجاز فایل
const ALLOWED_IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.webp']
const ALLOWED_DOCUMENT_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx', '.html', '.htm']
const ALLOWED_EXTENSIONS = [...ALLOWED_IMAGE_EXTENSIONS, ...ALLOWED_DOCUMENT_EXTENSIONS]

// MIME types مجاز
const ALLOWED_IMAGE_TYPES = ['image/png', 'image/jpeg', 'image/gif', 'image/webp']
const ALLOWED_DOCUMENT_TYPES = [
  'application/pdf',
  'text/plain',
  'application/msword',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  'text/html'
]
const ALLOWED_MIME_TYPES = [...ALLOWED_IMAGE_TYPES, ...ALLOWED_DOCUMENT_TYPES]

interface FileUploadProgress {
  file: File
  progress: number
  uploaded: boolean
  error?: string
  objectKey?: string
  previewUrl?: string  // URL پیش‌نمایش برای تصاویر
}

interface ChatInputProps {
  onSendMessage: (message: string, fileAttachments?: any[]) => void
  isLoading: boolean
  disabled?: boolean
}

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [uploadProgress, setUploadProgress] = useState<Map<string, FileUploadProgress>>(new Map())
  const [isUploading, setIsUploading] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const { accessToken } = useAuthStore()
  
  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])
  
  const uploadFileToServer = async (file: File): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    
    const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
    const token = accessToken
    
    // بررسی وجود token
    if (!token) {
      console.error('No access token found!')
      const error = 'لطفاً ابتدا وارد شوید'
      setUploadProgress(prev => {
        const newMap = new Map(prev)
        newMap.set(file.name, {
          file,
          progress: 0,
          uploaded: false,
          error
        })
        return newMap
      })
      return Promise.reject(new Error(error))
    }
    
    console.log('Uploading file with token:', token.substring(0, 20) + '...')
    
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest()
      
      // Track upload progress
      xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
          const progress = Math.round((e.loaded / e.total) * 100)
          setUploadProgress(prev => {
            const newMap = new Map(prev)
            const existing = newMap.get(file.name)
            if (existing) {
              newMap.set(file.name, { ...existing, progress })
            }
            return newMap
          })
        }
      })
      
      xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
          const response = JSON.parse(xhr.responseText)
          setUploadProgress(prev => {
            const newMap = new Map(prev)
            newMap.set(file.name, {
              file,
              progress: 100,
              uploaded: true,
              objectKey: response.object_key
            })
            return newMap
          })
          resolve(response)
        } else {
          const error = 'خطا در آپلود فایل'
          setUploadProgress(prev => {
            const newMap = new Map(prev)
            const existing = newMap.get(file.name)
            if (existing) {
              newMap.set(file.name, { ...existing, error })
            }
            return newMap
          })
          reject(new Error(error))
        }
      })
      
      xhr.addEventListener('error', () => {
        const error = 'خطا در اتصال به سرور'
        setUploadProgress(prev => {
          const newMap = new Map(prev)
          const existing = newMap.get(file.name)
          if (existing) {
            newMap.set(file.name, { ...existing, error })
          }
          return newMap
        })
        reject(new Error(error))
      })
      
      xhr.open('POST', `${API_URL}/api/v1/chat/upload/`)
      xhr.setRequestHeader('Authorization', `Bearer ${token}`)
      xhr.send(formData)
    })
  }
  
  // بررسی معتبر بودن فایل
  const isValidFile = (file: File): boolean => {
    // بررسی MIME type
    if (ALLOWED_MIME_TYPES.includes(file.type)) return true
    
    // بررسی پسوند فایل (برای فایل‌هایی که MIME type نادرست دارند)
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return ALLOWED_EXTENSIONS.includes(extension)
  }
  
  // بررسی تصویر بودن فایل
  const isImageFile = (file: File): boolean => {
    if (ALLOWED_IMAGE_TYPES.includes(file.type)) return true
    const extension = '.' + file.name.split('.').pop()?.toLowerCase()
    return ALLOWED_IMAGE_EXTENSIONS.includes(extension)
  }
  
  // ایجاد URL پیش‌نمایش برای تصاویر
  const createPreviewUrl = (file: File): string | undefined => {
    if (isImageFile(file)) {
      return URL.createObjectURL(file)
    }
    return undefined
  }
  
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    
    // فیلتر فایل‌ها بر اساس فرمت‌های مجاز
    const validFiles = files.filter((file: File) => isValidFile(file))
    
    // نمایش خطا برای فایل‌های نامعتبر
    const invalidFiles = files.filter((file: File) => !isValidFile(file))
    if (invalidFiles.length > 0) {
      const invalidNames = invalidFiles.map(f => f.name).join(', ')
      alert(`فرمت فایل‌های زیر مجاز نیست: ${invalidNames}\n\nفرمت‌های مجاز: ${ALLOWED_EXTENSIONS.join(', ')}`)
    }
    
    if (validFiles.length === 0) return
    
    // حداکثر 5 فایل
    const totalFiles = attachedFiles.length + validFiles.length
    if (totalFiles > 5) {
      alert('حداکثر 5 فایل می‌توانید پیوست کنید')
      return
    }
    
    // حداکثر 10MB برای هر فایل
    const oversizedFiles = validFiles.filter((file: File) => file.size > 10 * 1024 * 1024)
    if (oversizedFiles.length > 0) {
      alert('حجم هر فایل نباید بیشتر از 10MB باشد')
      return
    }
    
    setAttachedFiles([...attachedFiles, ...validFiles])
    
    // شروع آپلود فوری
    setIsUploading(true)
    
    // Initialize progress for each file with preview URL for images
    validFiles.forEach((file: File) => {
      const previewUrl = createPreviewUrl(file)
      setUploadProgress(prev => {
        const newMap = new Map(prev)
        newMap.set(file.name, {
          file,
          progress: 0,
          uploaded: false,
          previewUrl
        })
        return newMap
      })
    })
    
    // آپلود همه فایل‌ها به صورت موازی
    try {
      await Promise.all(validFiles.map((file: File) => uploadFileToServer(file)))
    } catch (error) {
      console.error('Error uploading files:', error)
    } finally {
      setIsUploading(false)
    }
    
    // Reset input
    if (e.target) {
      e.target.value = ''
    }
  }
  
  const handleRemoveFile = (index: number) => {
    const fileToRemove = attachedFiles[index]
    const progress = uploadProgress.get(fileToRemove.name)
    
    // آزاد کردن URL پیش‌نمایش
    if (progress?.previewUrl) {
      URL.revokeObjectURL(progress.previewUrl)
    }
    
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index))
    setUploadProgress(prev => {
      const newMap = new Map(prev)
      newMap.delete(fileToRemove.name)
      return newMap
    })
  }
  
  const handleSubmit = () => {
    if ((message.trim() || attachedFiles.length > 0) && !isLoading && !disabled && !isUploading) {
      // جمع‌آوری اطلاعات فایل‌های آپلود شده از uploadProgress
      const fileAttachments = attachedFiles
        .map(file => {
          const progress = uploadProgress.get(file.name)
          if (progress && progress.uploaded && progress.objectKey) {
            return {
              filename: file.name,
              minio_url: progress.objectKey,
              file_type: file.type,
              size_bytes: file.size
            }
          }
          return null
        })
        .filter(f => f !== null)
      
      console.log('Sending message with files:', fileAttachments)
      
      onSendMessage(message, fileAttachments.length > 0 ? fileAttachments : undefined)
      setMessage('')
      setAttachedFiles([])
      setUploadProgress(new Map())
    }
  }
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
  
  const getFileIcon = (file: File) => {
    if (file.type.startsWith('image/')) return '🖼️'
    if (file.type === 'application/pdf') return '📄'
    if (file.type === 'text/plain') return '📝'
    return '📎'
  }
  
  return (
    <div className="w-full">
      {/* Attached Files Preview with Progress */}
      {attachedFiles.length > 0 && (
        <div className="mb-2 flex flex-col gap-2">
          {attachedFiles.map((file, index) => {
            const progress = uploadProgress.get(file.name)
            const isImage = isImageFile(file)
            return (
              <div
                key={index}
                className="flex flex-col gap-1 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm"
              >
                <div className="flex items-center gap-2">
                  {/* پیش‌نمایش تصویر یا آیکون فایل */}
                  {isImage && progress?.previewUrl ? (
                    <div className="relative w-12 h-12 rounded overflow-hidden flex-shrink-0">
                      <img
                        src={progress.previewUrl}
                        alt={file.name}
                        className="w-full h-full object-cover"
                      />
                    </div>
                  ) : (
                    <span className="text-2xl">{getFileIcon(file)}</span>
                  )}
                  
                  <div className="flex flex-col flex-1 min-w-0">
                    <span className="text-gray-700 dark:text-gray-300 max-w-[150px] truncate">
                      {file.name}
                    </span>
                    <span className="text-gray-500 dark:text-gray-400 text-xs">
                      {(file.size / 1024).toFixed(1)} KB
                    </span>
                  </div>
                  
                  {/* Status Icons */}
                  {progress?.uploaded && (
                    <span className="text-green-500" title="آپلود شد">✓</span>
                  )}
                  {progress?.error && (
                    <span className="text-red-500" title={progress.error}>✗</span>
                  )}
                  
                  <button
                    onClick={() => handleRemoveFile(index)}
                    className="text-red-500 hover:text-red-700 dark:hover:text-red-400 ml-1"
                    title="حذف"
                    disabled={isUploading}
                  >
                    ✕
                  </button>
                </div>
                
                {/* Progress Bar */}
                {progress && !progress.uploaded && !progress.error && (
                  <div className="w-full bg-gray-300 dark:bg-gray-600 rounded-full h-1.5">
                    <div
                      className="bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                      style={{ width: `${progress.progress}%` }}
                    />
                  </div>
                )}
                
                {/* Error Message */}
                {progress?.error && (
                  <span className="text-red-500 text-xs">{progress.error}</span>
                )}
              </div>
            )
          })}
        </div>
      )}
      
      {/* ChatGPT Style Input Container */}
      <div className={clsx(
        'flex items-end gap-1 md:gap-2 rounded-2xl border shadow-sm',
        'bg-white dark:bg-gray-800',
        'border-gray-300 dark:border-gray-700',
        'focus-within:border-gray-400 dark:focus-within:border-gray-600',
        'transition-all duration-200'
      )}>
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".png,.jpg,.jpeg,.gif,.webp,.pdf,.txt,.doc,.docx,.html,.htm"
          onChange={handleFileSelect}
          className="hidden"
        />
        
        {/* Attach Button */}
        <div className="relative shrink-0">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled || attachedFiles.length >= 5}
            className={clsx(
              'p-2 md:p-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300',
              'disabled:opacity-50 disabled:cursor-not-allowed transition-colors',
              attachedFiles.length > 0 && 'text-blue-500 dark:text-blue-400'
            )}
            title={attachedFiles.length >= 5 ? 'حداکثر 5 فایل' : 'پیوست فایل (تصویر، PDF، Word، HTML، متن)'}
          >
            <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
            </svg>
          </button>
          {attachedFiles.length > 0 && (
            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-xs rounded-full w-5 h-5 flex items-center justify-center font-semibold">
              {attachedFiles.length}
            </span>
          )}
        </div>
        
        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="پیام خود را بنویسید..."
          disabled={isLoading || disabled}
          className={clsx(
            'flex-1 resize-none bg-transparent',
            'px-1 md:px-2 py-3 min-h-[48px] md:min-h-[44px]',
            'focus:outline-none',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'placeholder-gray-400 dark:placeholder-gray-500',
            'text-gray-900 dark:text-gray-100',
            'text-base'
          )}
          rows={1}
          style={{ maxHeight: '200px' }}
        />
        
        {/* Send Button - ChatGPT Style */}
        <button
          onClick={handleSubmit}
          disabled={(!message.trim() && attachedFiles.length === 0) || isLoading || disabled}
          className={clsx(
            'p-2 m-1 md:m-2 rounded-lg transition-all duration-200',
            'shrink-0',
            (message.trim() || attachedFiles.length > 0) && !isLoading && !disabled
              ? 'bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          )}
          title="ارسال پیام"
        >
          {isLoading ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ) : (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
            </svg>
          )}
        </button>
      </div>
      
      {/* Helper Text - Hidden on mobile */}
      <div className="mt-2 hidden md:flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
        <span>Enter برای ارسال • Shift+Enter برای خط جدید</span>
        {message.length > 0 && (
          <span>{message.length} / 5000</span>
        )}
      </div>
    </div>
  )
}
