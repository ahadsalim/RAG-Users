'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import clsx from 'clsx'

interface ChatInputProps {
  onSendMessage: (message: string, files?: File[]) => void
  isLoading: boolean
  disabled?: boolean
}

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  
  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])
  
  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || [])
    
    // فیلتر فایل‌ها: فقط عکس، PDF و متن
    const validFiles = files.filter(file => {
      const isImage = file.type.startsWith('image/')
      const isPDF = file.type === 'application/pdf'
      const isText = file.type === 'text/plain'
      return isImage || isPDF || isText
    })
    
    // حداکثر 5 فایل
    const totalFiles = attachedFiles.length + validFiles.length
    if (totalFiles > 5) {
      alert('حداکثر 5 فایل می‌توانید پیوست کنید')
      return
    }
    
    // حداکثر 10MB برای هر فایل
    const oversizedFiles = validFiles.filter(file => file.size > 10 * 1024 * 1024)
    if (oversizedFiles.length > 0) {
      alert('حجم هر فایل نباید بیشتر از 10MB باشد')
      return
    }
    
    setAttachedFiles([...attachedFiles, ...validFiles])
    
    // Reset input
    if (e.target) {
      e.target.value = ''
    }
  }
  
  const handleRemoveFile = (index: number) => {
    setAttachedFiles(attachedFiles.filter((_, i) => i !== index))
  }
  
  const handleSubmit = () => {
    if ((message.trim() || attachedFiles.length > 0) && !isLoading && !disabled) {
      onSendMessage(message, attachedFiles)
      setMessage('')
      setAttachedFiles([])
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
      {/* Attached Files Preview */}
      {attachedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2">
          {attachedFiles.map((file, index) => (
            <div
              key={index}
              className="flex items-center gap-2 px-3 py-2 bg-gray-100 dark:bg-gray-700 rounded-lg text-sm"
            >
              <span>{getFileIcon(file)}</span>
              <span className="text-gray-700 dark:text-gray-300 max-w-[150px] truncate">
                {file.name}
              </span>
              <span className="text-gray-500 dark:text-gray-400 text-xs">
                ({(file.size / 1024).toFixed(1)} KB)
              </span>
              <button
                onClick={() => handleRemoveFile(index)}
                className="text-red-500 hover:text-red-700 dark:hover:text-red-400 ml-1"
                title="حذف"
              >
                ✕
              </button>
            </div>
          ))}
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
          accept="image/*,.pdf,.txt"
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
            title={attachedFiles.length >= 5 ? 'حداکثر 5 فایل' : 'پیوست فایل (عکس، PDF، متن)'}
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
