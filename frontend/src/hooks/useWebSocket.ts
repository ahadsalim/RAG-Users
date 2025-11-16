import { useEffect, useRef, useState, useCallback } from 'react'
import { useAuthStore } from '@/store/auth'
import { useChatStore } from '@/store/chat'
import { WebSocketMessage } from '@/types/chat'

interface UseWebSocketOptions {
  onMessage?: (data: WebSocketMessage) => void
  onTyping?: (userId: string, isTyping: boolean) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: Event) => void
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const [isConnected, setIsConnected] = useState(false)
  const [reconnectCount, setReconnectCount] = useState(0)
  
  const { accessToken, isAuthenticated } = useAuthStore()
  const { updateMessage, addMessage } = useChatStore()
  
  const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'
  
  const connect = useCallback(() => {
    if (!isAuthenticated || !accessToken) {
      console.log('Not authenticated, skipping WebSocket connection')
      return
    }
    
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      console.log('WebSocket already connected')
      return
    }
    
    console.log('Connecting to WebSocket...')
    
    // Close existing connection if any
    if (wsRef.current) {
      wsRef.current.close()
    }
    
    // Create new WebSocket connection
    const conversationId = useChatStore.getState().currentConversation?.id
    const wsUrl = conversationId 
      ? `${WS_URL}/ws/chat/${conversationId}/?token=${accessToken}`
      : `${WS_URL}/ws/chat/?token=${accessToken}`
    
    const ws = new WebSocket(wsUrl)
    wsRef.current = ws
    
    ws.onopen = () => {
      console.log('WebSocket connected')
      setIsConnected(true)
      setReconnectCount(0)
      options.onConnect?.()
    }
    
    ws.onmessage = (event) => {
      try {
        const data: WebSocketMessage = JSON.parse(event.data)
        console.log('WebSocket message:', data)
        
        // Handle different message types
        switch (data.type) {
          case 'connection':
            console.log('Connection established:', data.message)
            break
            
          case 'chunk':
            // Update message content incrementally
            if (data.message_id) {
              updateMessage(data.message_id, {
                content: (prev: string) => prev + data.content,
              } as any)
            }
            break
            
          case 'sources':
            // Update message sources
            if (data.message_id) {
              updateMessage(data.message_id, {
                sources: data.sources,
              })
            }
            break
            
          case 'processing_started':
            console.log('Processing started for message:', data.message_id)
            break
            
          case 'processing_completed':
            // Update message status
            if (data.message_id) {
              updateMessage(data.message_id, {
                status: 'completed',
                ...data.metadata,
              })
            }
            break
            
          case 'error':
            console.error('WebSocket error:', data.error)
            if (data.message_id) {
              updateMessage(data.message_id, {
                status: 'failed',
                error_message: data.error,
              })
            }
            break
            
          case 'typing':
            options.onTyping?.(data.user_id, data.is_typing)
            break
            
          case 'pong':
            console.log('Pong received')
            break
            
          default:
            options.onMessage?.(data)
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error)
      }
    }
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
      options.onError?.(error)
    }
    
    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason)
      setIsConnected(false)
      wsRef.current = null
      options.onDisconnect?.()
      
      // Attempt to reconnect if not intentionally closed
      if (event.code !== 1000 && isAuthenticated) {
        const delay = Math.min(1000 * Math.pow(2, reconnectCount), 30000)
        console.log(`Reconnecting in ${delay}ms... (attempt ${reconnectCount + 1})`)
        
        reconnectTimeoutRef.current = setTimeout(() => {
          setReconnectCount(prev => prev + 1)
          connect()
        }, delay)
      }
    }
  }, [isAuthenticated, accessToken, WS_URL, options, updateMessage])
  
  const disconnect = useCallback(() => {
    console.log('Disconnecting WebSocket...')
    
    // Clear reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }
    
    // Close WebSocket connection
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect')
      wsRef.current = null
    }
    
    setIsConnected(false)
    setReconnectCount(0)
  }, [])
  
  const sendMessage = useCallback((data: WebSocketMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data))
      return true
    } else {
      console.error('WebSocket is not connected')
      return false
    }
  }, [])
  
  // Ping to keep connection alive
  useEffect(() => {
    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        sendMessage({ type: 'ping' })
      }
    }, 30000) // Ping every 30 seconds
    
    return () => clearInterval(pingInterval)
  }, [sendMessage])
  
  // Connect on mount and when authentication changes
  useEffect(() => {
    if (isAuthenticated) {
      connect()
    } else {
      disconnect()
    }
    
    return () => {
      disconnect()
    }
  }, [isAuthenticated, connect, disconnect])
  
  return {
    isConnected,
    sendMessage,
    connect,
    disconnect,
    reconnectCount,
  }
}
