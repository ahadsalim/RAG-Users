'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '@/types/chat'
import clsx from 'clsx'

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  isTyping: boolean
}

export function ChatMessages({ messages, isLoading, isTyping }: ChatMessagesProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [feedbackSent, setFeedbackSent] = useState<Set<string>>(new Set())
  
  const handleCopy = async (text: string, messageId: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(messageId)
    setTimeout(() => setCopiedId(null), 2000)
  }
  
  const handleFeedback = async (messageId: string, rating: number) => {
    // Send feedback to API
    console.log('Feedback:', messageId, rating)
    setFeedbackSent(prev => new Set(prev).add(messageId))
  }
  
  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'
    
    return (
      <div
        key={message.id}
        className={clsx(
          'group py-8 px-4 md:px-8',
          isUser ? 'bg-white dark:bg-gray-800' : 'bg-gray-50 dark:bg-gray-900'
        )}
      >
        <div className="max-w-4xl mx-auto">
          <div className="flex gap-4">
            {/* Avatar - Simple Text Based */}
            <div className={clsx(
              'flex-shrink-0 w-8 h-8 rounded-md flex items-center justify-center text-sm font-bold',
              isUser 
                ? 'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200' 
                : 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200'
            )}>
              {isUser ? 'ش' : 'AI'}
            </div>
            
            {/* Content */}
            <div className="flex-1 space-y-2">
              {/* Name and Time */}
              <div className="flex items-center gap-2">
                <span className="font-medium text-gray-900 dark:text-gray-100">
                  {isUser ? 'شما' : 'دستیار هوشمند'}
                </span>
                <span className="text-xs text-gray-500">
                  {new Date(message.created_at).toLocaleTimeString('fa-IR', { hour: '2-digit', minute: '2-digit' })}
                </span>
                {message.cached && (
                  <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-400 px-2 py-0.5 rounded">
                    از کش
                  </span>
                )}
              </div>
              
              {/* Message Content */}
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {message.status === 'processing' ? (
                  <div className="flex items-center gap-2 text-gray-500">
                    <span>⏳ در حال پردازش...</span>
                  </div>
                ) : message.status === 'failed' ? (
                  <div className="text-red-600 dark:text-red-400">
                    خطا: {message.error_message || 'خطای نامشخص'}
                  </div>
                ) : (
                  <ReactMarkdown 
                    remarkPlugins={[remarkGfm]}
                    components={{
                      // Custom rendering for code blocks
                      code: ({ node, inline, className, children, ...props }: any) => {
                        const match = /language-(\w+)/.exec(className || '')
                        return !inline && match ? (
                          <div className="relative group/code">
                            <pre className="bg-gray-900 text-gray-100 rounded-lg p-4 overflow-x-auto">
                              <code className={className} {...props}>
                                {children}
                              </code>
                            </pre>
                            <button
                              onClick={() => handleCopy(String(children), message.id)}
                              className="absolute top-2 left-2 p-1.5 bg-gray-700 hover:bg-gray-600 rounded opacity-0 group-hover/code:opacity-100 transition-opacity"
                            >
                              <span className="text-xs text-gray-300">
                                {copiedId === message.id ? '✓' : '📋'}
                              </span>
                            </button>
                          </div>
                        ) : (
                          <code className="bg-gray-200 dark:bg-gray-700 px-1.5 py-0.5 rounded text-sm" {...props}>
                            {children}
                          </code>
                        )
                      },
                      // Custom rendering for links
                      a: ({ node, ...props }: any) => (
                        <a 
                          className="text-blue-600 dark:text-blue-400 hover:underline"
                          target="_blank"
                          rel="noopener noreferrer"
                          {...props}
                        />
                      ),
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                )}
              </div>
              
              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/30 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-sm font-medium text-blue-900 dark:text-blue-200">
                      📚 منابع:
                    </span>
                  </div>
                  <ul className="space-y-1">
                    {message.sources.map((source, idx) => (
                      <li key={idx} className="text-sm text-blue-800 dark:text-blue-300">
                        • {source}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              
              {/* Actions */}
              {!isUser && message.status === 'completed' && (
                <div className="flex items-center gap-2 mt-3 opacity-0 group-hover:opacity-100 transition-opacity">
                  {/* Copy */}
                  <button
                    onClick={() => handleCopy(message.content, message.id)}
                    className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                    title="کپی"
                  >
                    <span className="text-sm">
                      {copiedId === message.id ? '✓' : '📋'}
                    </span>
                  </button>
                  
                  {/* Feedback */}
                  {!feedbackSent.has(message.id) ? (
                    <>
                      <button
                        onClick={() => handleFeedback(message.id, 5)}
                        className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                        title="مفید بود"
                      >
                        <span>👍</span>
                      </button>
                      <button
                        onClick={() => handleFeedback(message.id, 1)}
                        className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
                        title="مفید نبود"
                      >
                        <span>👎</span>
                      </button>
                    </>
                  ) : (
                    <span className="text-xs text-gray-500">بازخورد ثبت شد</span>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    )
  }
  
  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-2xl mx-auto p-8">
          <div className="text-6xl mb-4">✨</div>
          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
            دستیار هوشمند حقوقی مشاور
          </h2>
          <p className="text-gray-600 dark:text-gray-400 mb-8">
            سوالات حقوقی خود را بپرسید و پاسخ‌های دقیق و مستند دریافت کنید
          </p>
          
          {/* Suggestions */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <button className="text-right p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                قوانین کار
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "حقوق و مزایای کارگران در قرارداد موقت چیست؟"
              </p>
            </button>
            <button className="text-right p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                ثبت شرکت
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "مراحل ثبت شرکت با مسئولیت محدود را توضیح بده"
              </p>
            </button>
            <button className="text-right p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                قراردادها
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "نکات مهم در تنظیم قرارداد اجاره تجاری"
              </p>
            </button>
            <button className="text-right p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                مالیات
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                "معافیت‌های مالیاتی شرکت‌های دانش‌بنیان"
              </p>
            </button>
          </div>
        </div>
      </div>
    )
  }
  
  return (
    <div className="flex-1">
      {messages.map(renderMessage)}
      
      {/* Loading indicator */}
      {isLoading && (
        <div className="py-8 px-4 md:px-8 bg-gray-50 dark:bg-gray-900">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 dark:bg-green-900 flex items-center justify-center">
                <span className="text-sm">✨</span>
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-medium text-gray-900 dark:text-gray-100">
                    دستیار هوشمند
                  </span>
                </div>
                <div className="mt-2 flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {/* Typing indicator */}
      {isTyping && !isLoading && (
        <div className="py-4 px-4 md:px-8">
          <div className="max-w-4xl mx-auto">
            <div className="text-sm text-gray-500 italic">
              کاربر دیگر در حال تایپ است...
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
