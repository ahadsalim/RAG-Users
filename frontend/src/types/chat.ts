export interface User {
  id: string
  email: string
  username: string
  first_name?: string
  last_name?: string
  phone_number?: string
  is_superuser?: boolean
  is_staff?: boolean
  user_type?: 'individual' | 'business' | 'legal'
  company_name?: string
  organization?: Organization
  language: string
  timezone: string
  created_at: string
  updated_at: string
}

export interface Organization {
  id: string
  name: string
  type: 'individual' | 'company'
  economic_code?: string
}

export interface Conversation {
  id: string
  user: string
  organization?: string
  rag_conversation_id?: string
  title: string
  description?: string
  tags: string[]
  default_response_mode: ResponseMode
  folder?: string
  is_pinned: boolean
  is_archived: boolean
  is_shared: boolean
  share_token?: string
  message_count: number
  token_usage: number
  last_message_at?: string
  last_message?: {
    content: string
    role: 'user' | 'assistant'
  }
  messages?: Message[]
  created_at: string
  updated_at: string
}

export interface Message {
  id: string
  conversation: string
  rag_message_id?: string
  role: 'user' | 'assistant' | 'system'
  content: string
  response_mode?: ResponseMode
  sources?: string[]
  chunks?: MessageChunk[]
  status: 'pending' | 'processing' | 'completed' | 'failed'
  error_message?: string
  tokens: number
  processing_time_ms: number
  model_used?: string
  cached: boolean
  rating?: number
  feedback_type?: string
  feedback_text?: string
  attachments?: MessageAttachment[]
  created_at: string
  updated_at: string
}

export interface MessageChunk {
  text: string
  score: number
  source: string
  metadata: {
    document_title: string
    unit_number: string
    unit_type: string
    authority: string
  }
}

export interface MessageAttachment {
  id: string
  file: string
  file_name: string
  file_size: number
  file_type: 'document' | 'image' | 'pdf' | 'spreadsheet'
  mime_type: string
  thumbnail?: string
  extracted_text?: string
  extraction_status: string
  created_at: string
}

export interface ConversationFolder {
  id: string
  name: string
  color: string
  icon: string
  parent?: string
  order: number
  created_at: string
  updated_at: string
}

export interface ChatTemplate {
  id: string
  title: string
  description: string
  category: 'legal' | 'business' | 'tax' | 'insurance' | 'labor' | 'contract'
  prompt_template: string
  variables: string[]
  icon: string
  is_active: boolean
  usage_count: number
  is_public: boolean
  created_by: string
  created_at: string
  updated_at: string
}

export type ResponseMode = 'simple_explanation' | 'legal_reference' | 'action_checklist'

export interface QueryRequest {
  query: string
  conversation_id?: string
  response_mode?: ResponseMode
  max_results?: number
  use_cache?: boolean
  use_reranking?: boolean
  stream?: boolean
  filters?: QueryFilters
  llm_config?: LLMConfig
  context?: Record<string, any>
}

export interface QueryFilters {
  document_type?: string
  jurisdiction?: string
  authority?: string
  date_range?: {
    gte: string
    lte: string
  }
}

export interface LLMConfig {
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface QueryResponse {
  conversation_id: string
  message_id: string
  answer: string
  sources: string[]
  chunks: MessageChunk[]
  tokens_used?: number
  processing_time?: number
  processing_time_ms?: number
  model_used?: string
  context_used?: boolean
  metadata?: {
    tokens: number
    processing_time_ms: number
    model_used: string
    cached: boolean
  }
  user_info?: {
    daily_queries_remaining: number
    total_queries: number
  }
}

export interface WebSocketMessage {
  type: 'connection' | 'query' | 'typing' | 'feedback' | 'chunk' | 'sources' | 'error' | 'ping' | 'pong' | 'processing_started' | 'processing_completed' | 'message_received'
  [key: string]: any
}
