'use client'

import { useState, useRef, useEffect, KeyboardEvent } from 'react'
import clsx from 'clsx'

interface ChatInputProps {
  onSendMessage: (message: string, mode?: string) => void
  isLoading: boolean
  disabled?: boolean
}

const RESPONSE_MODES = [
  { id: 'simple_explanation', label: 'توضیح ساده', icon: '💡' },
  { id: 'legal_reference', label: 'ارجاع قانونی', icon: '⚖️' },
  { id: 'action_checklist', label: 'چک‌لیست اقدام', icon: '✅' },
]

export function ChatInput({ onSendMessage, isLoading, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('')
  const [responseMode, setResponseMode] = useState('simple_explanation')
  const [showModeSelector, setShowModeSelector] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  
  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`
    }
  }, [message])
  
  const handleSubmit = () => {
    if (message.trim() && !isLoading && !disabled) {
      onSendMessage(message, responseMode)
      setMessage('')
    }
  }
  
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }
  
  const handleVoiceToggle = () => {
    setIsRecording(!isRecording)
    // TODO: Implement voice recording
  }
  
  const handleFileUpload = () => {
    // TODO: Implement file upload
  }
  
  const selectedMode = RESPONSE_MODES.find(mode => mode.id === responseMode)
  
  return (
    <div className="border-t border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800">
      <div className="max-w-4xl mx-auto p-4">
        {/* Mode Selector */}
        <div className="mb-3 flex items-center gap-2">
          <span className="text-sm text-gray-600 dark:text-gray-400">
            حالت پاسخ:
          </span>
          <div className="relative">
            <button
              onClick={() => setShowModeSelector(!showModeSelector)}
              className="flex items-center gap-2 px-3 py-1.5 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
            >
              <span>{selectedMode?.icon}</span>
              <span className="text-sm">{selectedMode?.label}</span>
              <span className="text-xs">▼</span>
            </button>
            
            {showModeSelector && (
              <div className="absolute bottom-full mb-2 right-0 w-56 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg shadow-lg z-10">
                {RESPONSE_MODES.map((mode) => (
                  <button
                    key={mode.id}
                    onClick={() => {
                      setResponseMode(mode.id)
                      setShowModeSelector(false)
                    }}
                    className={clsx(
                      'w-full flex items-center gap-3 px-4 py-2 text-right hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors',
                      responseMode === mode.id && 'bg-gray-100 dark:bg-gray-700'
                    )}
                  >
                    <span>{mode.icon}</span>
                    <span className="text-sm">{mode.label}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>
        
        {/* Input Area */}
        <div className="relative flex items-end gap-2">
          {/* File Upload */}
          <button
            onClick={handleFileUpload}
            disabled={disabled}
            className="p-2 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-lg"
            title="پیوست فایل"
          >
            📎
          </button>
          
          {/* Text Input */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="سوال خود را بپرسید..."
              disabled={isLoading || disabled}
              className={clsx(
                'w-full resize-none rounded-lg border px-4 py-3 pr-4 pl-12',
                'bg-white dark:bg-gray-900',
                'border-gray-300 dark:border-gray-600',
                'focus:outline-none focus:ring-2 focus:ring-primary-500 dark:focus:ring-primary-400',
                'disabled:opacity-50 disabled:cursor-not-allowed',
                'placeholder-gray-400 dark:placeholder-gray-500',
                'text-gray-900 dark:text-gray-100',
                'max-h-40'
              )}
              rows={1}
            />
            
            {/* Character Count */}
            {message.length > 0 && (
              <div className="absolute bottom-2 left-2 text-xs text-gray-400">
                {message.length}/5000
              </div>
            )}
          </div>
          
          {/* Voice Input */}
          <button
            onClick={handleVoiceToggle}
            disabled={disabled}
            className={clsx(
              'p-2 rounded-lg transition-colors text-lg',
              isRecording
                ? 'bg-red-500 text-white hover:bg-red-600'
                : 'text-gray-500 hover:text-gray-700 dark:hover:text-gray-300',
              'disabled:opacity-50 disabled:cursor-not-allowed'
            )}
            title={isRecording ? 'توقف ضبط' : 'ضبط صدا'}
          >
            {isRecording ? '⏹' : '🎤'}
          </button>
          
          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={!message.trim() || isLoading || disabled}
            className={clsx(
              'p-2 rounded-lg transition-colors text-lg',
              message.trim() && !isLoading && !disabled
                ? 'bg-primary-600 text-white hover:bg-primary-700'
                : 'bg-gray-200 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
            )}
            title="ارسال"
          >
            ➤
          </button>
        </div>
        
        {/* Hints */}
        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          <span>Shift+Enter برای خط جدید</span>
          <span className="mx-2">•</span>
          <span>حداکثر 5000 کاراکتر</span>
          {disabled && (
            <>
              <span className="mx-2">•</span>
              <span className="text-orange-500">اتصال برقرار نیست</span>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
