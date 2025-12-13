'use client'

import { useState } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Message } from '@/types/chat'
import clsx from 'clsx'
import Image from 'next/image'

interface ChatMessagesProps {
  messages: Message[]
  isLoading: boolean
  isTyping: boolean
}

// Parse source string from RAG Core format
interface ParsedSource {
  index: number
  text: string
  documentName: string
  path: string
}

function parseSource(source: string, idx: number): ParsedSource {
  // Format: "📌 منبع X:\n📄 متن: ...\n\n📎 نام سند: ...\n📍 مسیر: ..."
  const result: ParsedSource = {
    index: idx + 1,
    text: '',
    documentName: '',
    path: ''
  }
  
  // Clean broken emoji characters (�) and other unwanted symbols
  const cleanSource = source.replace(/�/g, '').replace(/📌|📄|📎|📍/g, '');
  
  // Extract source number if present
  const indexMatch = cleanSource.match(/منبع\s*(\d+)/);
  if (indexMatch) {
    result.index = parseInt(indexMatch[1]);
  }
  
  // Extract text content - only the actual text, not metadata
  const textMatch = cleanSource.match(/متن:\s*([^]*?)(?=\s*نام سند:|$)/);
  if (textMatch) {
    // Clean the text: remove extra whitespace and newlines
    result.text = textMatch[1].trim().replace(/\n{2,}/g, '\n');
  }
  
  // Extract document name
  const docMatch = cleanSource.match(/نام سند:\s*([^\n]+)/);
  if (docMatch) {
    result.documentName = docMatch[1].trim();
  }
  
  // Extract path
  const pathMatch = cleanSource.match(/مسیر:\s*([^\n]+)/);
  if (pathMatch) {
    result.path = pathMatch[1].trim();
  }
  
  return result;
}

export function ChatMessages({ messages, isLoading, isTyping }: ChatMessagesProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [feedbackSent, setFeedbackSent] = useState<Set<string>>(new Set())
  const [expandedSource, setExpandedSource] = useState<string | null>(null)
  
  const handleCopy = async (text: string, messageId: string) => {
    await navigator.clipboard.writeText(text)
    setCopiedId(messageId)
    setTimeout(() => setCopiedId(null), 2000)
  }
  
  const handleFeedback = async (messageId: string, rating: number) => {
    // Send feedback to API
    setFeedbackSent(prev => new Set(prev).add(messageId))
  }
  
  const renderMessage = (message: Message) => {
    const isUser = message.role === 'user'
    
    return (
      <div
        key={message.id}
        className={clsx(
          'group py-6 px-4 rounded-xl my-2 mx-2',
          isUser 
            ? 'bg-gradient-to-l from-blue-50 to-white dark:from-blue-950/40 dark:to-gray-800/60 border border-blue-100 dark:border-blue-900/50' 
            : 'bg-gradient-to-l from-gray-50 to-white dark:from-gray-800/80 dark:to-gray-850/60 border border-gray-100 dark:border-gray-700/50'
        )}
      >
        <div className="w-full">
          <div className="flex gap-4">
            {/* Avatar */}
            <div className={clsx(
              'flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold shadow-sm',
              isUser 
                ? 'bg-blue-500 text-white dark:bg-blue-600' 
                : 'bg-emerald-500 dark:bg-emerald-600 p-1'
            )}>
              {isUser ? (
                'ش'
              ) : (
                <Image 
                  src="/favicon.ico" 
                  alt="AI" 
                  width={24} 
                  height={24}
                  className="w-full h-full object-contain"
                />
              )}
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
              
              {/* File Attachments */}
              {message.attachments && message.attachments.length > 0 && (
                <div className="mb-2 flex flex-wrap gap-2">
                  {message.attachments.map((attachment, idx) => {
                    // فقط در حالت processing نمایش دهیم اگر assistant message هنوز processing است
                    const isProcessing = message.status === 'processing' && attachment.extraction_status === 'processing'
                    const isImage = attachment.file_type === 'image' || 
                      attachment.mime_type?.startsWith('image/') ||
                      /\.(png|jpg|jpeg|gif|webp)$/i.test(attachment.file_name)
                    
                    // برای تصاویر، پیش‌نمایش نمایش بده
                    if (isImage && attachment.file) {
                      return (
                        <div 
                          key={idx}
                          className={`relative rounded-lg overflow-hidden ${
                            isProcessing ? 'opacity-50' : ''
                          }`}
                        >
                          <img
                            src={attachment.file}
                            alt={attachment.file_name}
                            className="max-w-[200px] max-h-[150px] object-cover rounded-lg border border-gray-200 dark:border-gray-700"
                          />
                          {isProcessing && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                              <span className="text-white animate-pulse">⏳</span>
                            </div>
                          )}
                          <div className="absolute bottom-0 left-0 right-0 bg-black/50 text-white text-xs px-2 py-1 truncate">
                            {attachment.file_name}
                          </div>
                        </div>
                      )
                    }
                    
                    // برای فایل‌های غیر تصویری، آیکون نمایش بده
                    return (
                      <div 
                        key={idx}
                        className={`relative flex items-center gap-1.5 px-2 py-1 rounded text-xs transition-all ${
                          isProcessing 
                            ? 'bg-gray-50 dark:bg-gray-900 border border-dashed border-gray-300 dark:border-gray-700' 
                            : 'bg-gray-100 dark:bg-gray-800'
                        }`}
                      >
                        {/* File Icon */}
                        <span className={`text-base ${isProcessing ? 'opacity-40 animate-pulse' : ''}`}>
                          {attachment.mime_type === 'application/pdf' ? '📄' : 
                           attachment.mime_type === 'text/plain' ? '📝' :
                           attachment.mime_type?.includes('word') ? '📃' :
                           attachment.mime_type === 'text/html' ? '🌐' : '📎'}
                        </span>
                        
                        {/* File Name */}
                        <span className="text-gray-700 dark:text-gray-300 truncate max-w-[120px] font-medium">
                          {attachment.file_name}
                        </span>
                        
                        {/* File Size */}
                        <span className="text-gray-500">
                          ({Math.round(attachment.file_size / 1024)}KB)
                        </span>
                        
                        {/* Processing Indicator */}
                        {isProcessing && (
                          <span className="text-xs text-gray-600 dark:text-gray-400 animate-pulse mr-1">
                            ⏳
                          </span>
                        )}
                      </div>
                    )
                  })}
                </div>
              )}
              
              {/* Message Content */}
              <div className="prose prose-sm dark:prose-invert max-w-none">
                {message.status === 'failed' ? (
                  <div className="text-red-600 dark:text-red-400">
                    خطا: {message.error_message || 'خطای نامشخص'}
                  </div>
                ) : (
                  <>
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
                  {message.status === 'processing' && (
                    <span className="inline-flex items-center gap-1 text-gray-500 text-sm ml-1">
                      <span className="animate-pulse">●</span>
                    </span>
                  )}
                  </>
                )}
              </div>
              
              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <div className="mt-4 p-3 bg-gray-50 dark:bg-gray-800/50 rounded-lg border border-gray-200 dark:border-gray-700">
                  <div className="flex items-center gap-2 mb-3">
                    <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      منابع:
                    </span>
                  </div>
                  <div className="space-y-2">
                    {message.sources.map((source, idx) => {
                      const parsed = parseSource(source, idx);
                      const sourceKey = `${message.id}-${idx}`;
                      const isExpanded = expandedSource === sourceKey;
                      
                      return (
                        <div key={idx} className="text-sm">
                          <button
                            onClick={() => setExpandedSource(isExpanded ? null : sourceKey)}
                            className="flex items-center gap-2 text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 transition-colors text-right w-full"
                          >
                            <span className="flex-shrink-0">📍</span>
                            <span className="hover:underline">
                              منبع {parsed.index}: {parsed.documentName}{parsed.path ? ` - ${parsed.path}` : ''}
                            </span>
                            <span className="mr-auto text-gray-400 text-xs">
                              {isExpanded ? '▲' : '▼'}
                            </span>
                          </button>
                          
                          {/* Expanded content */}
                          {isExpanded && parsed.text && (
                            <div className="mt-2 mr-6 p-3 bg-white dark:bg-gray-900 rounded border border-gray-200 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm leading-relaxed">
                              {parsed.text}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
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
      <div className="flex-1 flex items-center justify-center py-12">
        <div className="text-center w-full px-4">
          <div className="text-6xl mb-6">💬</div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            چت جدید
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-400">
            سوال خود را بپرسید...
          </p>
        </div>
      </div>
    )
  }
  
  // Check if there's already a processing message
  const hasProcessingMessage = messages.some(msg => msg.status === 'processing')
  
  return (
    <div className="w-full">
      {messages.map(renderMessage)}
      
      {/* Loading indicator - only show if no processing message exists */}
      {isLoading && !hasProcessingMessage && (
        <div className="py-6 bg-gray-50 dark:bg-gray-900">
          <div className="w-full">
            <div className="flex gap-4">
              <div className="flex-shrink-0 w-8 h-8 rounded-md bg-green-100 dark:bg-green-900 flex items-center justify-center p-1">
                <Image 
                  src="/favicon.ico" 
                  alt="AI" 
                  width={24} 
                  height={24}
                  className="w-full h-full object-contain"
                />
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
