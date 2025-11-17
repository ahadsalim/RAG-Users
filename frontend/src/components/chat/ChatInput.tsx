'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import clsx from 'clsx'

interface ChatInputProps {
  onSendMessage: (message: string, mode?: string) => void
  isLoading: boolean
  disabled?: boolean
}

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`
    }
  }, [message])
  
  const handleSubmit = () => {
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message)
      setMessage('')
    }
  }
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
  
  return (
    <div className="w-full">
      {/* ChatGPT Style Input Container */}
      <div className={clsx(
        'flex items-end gap-2 rounded-2xl border shadow-sm',
        'bg-white dark:bg-gray-800',
        'border-gray-300 dark:border-gray-700',
        'focus-within:border-gray-400 dark:focus-within:border-gray-600',
        'transition-all duration-200'
      )}>
        {/* Attach Button */}
        <button
          disabled={disabled}
          className={clsx(
            'p-3 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300',
            'disabled:opacity-50 disabled:cursor-not-allowed transition-colors'
          )}
          title="پیوست فایل"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
          </svg>
        </button>
        
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
            'px-2 py-3 min-h-[44px]',
            'focus:outline-none',
            'disabled:opacity-50 disabled:cursor-not-allowed',
            'placeholder-gray-400 dark:placeholder-gray-500',
            'text-gray-900 dark:text-gray-100'
          )}
          rows={1}
          style={{ maxHeight: '200px' }}
        />
        
        {/* Send Button - ChatGPT Style */}
        <button
          onClick={handleSubmit}
          disabled={!message.trim() || isLoading || disabled}
          className={clsx(
            'p-2 m-2 rounded-lg transition-all duration-200',
            message.trim() && !isLoading && !disabled
              ? 'bg-black dark:bg-white text-white dark:text-black hover:bg-gray-800 dark:hover:bg-gray-200'
              : 'bg-gray-300 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed'
          )}
          title="ارسال پیام"
        >
          {isLoading ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
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
      
      {/* Helper Text */}
      <div className="mt-2 flex items-center justify-between text-xs text-gray-400 dark:text-gray-500">
        <span>Enter برای ارسال • Shift+Enter برای خط جدید</span>
        {message.length > 0 && (
          <span>{message.length} / 5000</span>
        )}
      </div>
    </div>
  )
}
