/**
 * Chat Service
 * Handles AI chat interactions, conversation management, and legal queries
 */

import { BaseApiService } from './base.service'
import { generateUUID } from '@/utils/uuid'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  metadata?: {
    legal_references?: Array<{
      article: string
      law: string
      url?: string
    }>
    confidence_score?: number
    processing_time?: number
  }
}

export interface Conversation {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface ChatRequest {
  message: string
  conversation_id?: string
  context?: {
    user_profession?: string
    previous_context?: string
    law_filter?: string
  }
}

export interface ChatResponse {
  message: ChatMessage
  conversation_id: string
  legal_references?: Array<{
    article: string
    law: string
    content: string
    url?: string
    relevance_score: number
  }>
  suggested_questions?: string[]
  usage_info?: {
    queries_used: number
    queries_remaining: number
  }
  usage?: any
}

export interface ConversationListResponse {
  results: Conversation[]
  count: number
  next: string | null
  previous: string | null
}

export class ChatService extends BaseApiService {
  /**
   * Send a message to the AI assistant (non-streaming)
   */
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const payload = {
      message: request.message,
      conversation_id: request.conversation_id,
      context: request.context ? [
        { role: 'system', content: `User profession: ${request.context.user_profession || 'General'}` }
      ] : []
    }

    try {
      const response = await this.post<any>('/chat/message/', payload, true)

      return {
        message: {
          id: generateUUID(),
          role: 'assistant',
          content: response.message || response.data?.message,
          timestamp: new Date().toISOString(),
          metadata: {
            legal_references: response.data?.citations || [],
            confidence_score: 0.9,
            processing_time: response.data?.duration_ms
          }
        },
        conversation_id: response.conversation_id || response.data?.conversation_id || request.conversation_id,
        usage: response.data?.usage
      }
    } catch (error: any) {
      // Handle session not found - automatically create new session
      if (error.status === 404 || (error.response && error.response.code === 404)) {
        // Try again without session_id to create a new session
        const newPayload = {
          ...payload,
          conversation_id: undefined
        }

        const retryResponse = await this.post<any>('/chat/message/', newPayload, true)

        return {
          message: {
            id: generateUUID(),
            role: 'assistant',
            content: retryResponse.message || retryResponse.data?.message,
            timestamp: new Date().toISOString(),
            metadata: {
              legal_references: retryResponse.data?.citations || [],
              confidence_score: 0.9,
              processing_time: retryResponse.data?.duration_ms
            }
          },
          conversation_id: retryResponse.conversation_id || retryResponse.data?.conversation_id,
          usage: retryResponse.data?.usage
        }
      }

      // Re-throw other errors
      throw error
    }
  }

  /**
   * Send a streaming message to the AI assistant
   */
  async sendStreamingMessage(
  payload: { message: string; conversation_id?: string },
  onChunk: (chunk: string) => void,
  onConversationId?: (id: string) => void,
  onError?: (err: string) => void
) {
  const controller = new AbortController()
  let reader: ReadableStreamDefaultReader<Uint8Array> | null = null
  let finished = false
  try {
    const token = localStorage.getItem("accessToken")
    const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/chat/stream/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify(payload),
      signal: controller.signal,
    })

    if (!res.ok) {
      onError?.(await res.text().catch(() => `HTTP ${res.status}`))
      return
    }

    reader = res.body?.getReader() ?? null
    if (!reader) {
      onError?.("No response body")
      return
    }

    const decoder = new TextDecoder()
    let buffer = ""

    while (!finished) {
      const { value, done } = await reader.read()
      if (done) break
      if (value) buffer += decoder.decode(value, { stream: true })

      // process any complete SSE-style events separated by double newline
      const parts = buffer.split("\n\n")
      buffer = parts.pop() || ""

      for (const part of parts) {
        const lines = part.split("\n").map(l => l.trim()).filter(Boolean)
        for (const line of lines) {
          if (!line) continue
          // accept lines that start with "data:" or raw JSON
          const payloadStr = line.startsWith("data:") ? line.slice(5).trim() : line.trim()

          // handle DONE even when combined / split
          if (payloadStr === "[DONE]" || payloadStr.includes("[DONE]")) {
            finished = true
            break
          }

          // try parse JSON payload like {"content": "...}
          try {
            const obj = JSON.parse(payloadStr)
            if (obj.conversation_id) onConversationId?.(obj.conversation_id)
            const content = (obj.content ?? "").toString()
            if (content && content.trim() !== "") onChunk(content)
          } catch {
            // not JSON — forward raw text
            if (payloadStr && payloadStr.trim() !== "") onChunk(payloadStr)
          }
        }
        if (finished) break
      }

      if (finished) break
    }

    // cancel reader so fetch resolves and connection closes
    try { await reader.cancel() } catch {}
    return
  } catch (err: any) {
    if (err?.name === "AbortError") onError?.("stream aborted")
    else onError?.(err?.message || String(err))
    return
  } finally {
    try { if (reader) await reader.releaseLock?.() } catch {}
    try { controller.abort() } catch {}
  }
}

  /**
   * Process streaming response (extracted for reuse)
   */
  private async processStreamingResponse(
  res: Response,
  onChunk: (chunk: string) => void,
  onConversationId?: (id: string) => void,
  onError?: (err: string) => void
) {
  const reader = res.body?.getReader()
  if (!reader) {
    onError?.("No response body")
    return
  }

  const decoder = new TextDecoder()
  let buffer = ""

  try {
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      if (value) buffer += decoder.decode(value, { stream: true })

      const parts = buffer.split("\n\n")
      buffer = parts.pop() || ""

      for (const part of parts) {
        const lines = part.split("\n").map(l => l.trim()).filter(Boolean)
        for (const line of lines) {
          const payloadStr = line.startsWith("data:") ? line.slice(5).trim() : line.trim()
          if (!payloadStr) continue

          // handle DONE even when combined or split
          if (payloadStr === "[DONE]" || payloadStr.includes("[DONE]")) {
            return
          }

          try {
            const obj = JSON.parse(payloadStr)
            if (obj.conversation_id) onConversationId?.(obj.conversation_id)
            const content = (obj.content ?? "").toString()
            if (content && content.trim() !== "") onChunk(content)
          } catch {
            // not JSON — forward raw chunk
            onChunk(payloadStr)
          }
        }
      }
    }

    // flush any leftover buffer
    if (buffer.trim() && buffer.trim() !== "[DONE]") {
      const b = buffer.trim()
      try {
        const obj = JSON.parse(b.startsWith("data:") ? b.slice(5).trim() : b)
        if (obj.conversation_id) onConversationId?.(obj.conversation_id)
        if (obj.content) onChunk(obj.content)
      } catch {
        onChunk(b)
      }
    }
  } catch (err: any) {
    onError?.(err?.message || String(err))
  } finally {
    try { await reader.cancel() } catch {}
    try { reader.releaseLock?.() } catch {}
  }
}

  /**
   * Start a new conversation
   */
  async startConversation(initialMessage: string): Promise<ChatResponse> {
    return this.sendMessage({ message: initialMessage })
  }

  /**
   * Continue an existing conversation
   */
  async continueConversation(
    conversationId: string,
    message: string
  ): Promise<ChatResponse> {
    return this.sendMessage({
      message,
      conversation_id: conversationId
    })
  }

  /**
   * Get conversation history
   */
  async getConversation(conversationId: string): Promise<{
    conversation: Conversation
    messages: ChatMessage[]
  }> {
    if (!conversationId || conversationId === 'undefined') {
      throw new Error('Invalid conversation ID')
    }
    
    try {
      const response = await this.get<any>(`/chat/sessions/${conversationId}/`, true)
      
      // Validate response structure
      if (!response || !response.session) {
        throw new Error('Invalid response structure')
      }
      
      const { session, messages } = response
      
      // Validate messages array
      if (!Array.isArray(messages)) {
        console.warn('Messages is not an array:', messages)
        return {
          conversation: session || { 
            id: conversationId, 
            title: 'Chat Session', 
            created_at: new Date().toISOString(), 
            updated_at: new Date().toISOString(), 
            message_count: 0 
          },
          messages: []
        }
      }
      
      // Convert backend ChatMessage format to frontend format
      const convertedMessages: ChatMessage[] = messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role as 'user' | 'assistant',
        content: msg.content,
        timestamp: msg.created_at || new Date().toISOString(),
        metadata: msg.role === 'assistant' ? {
          legal_references: msg.legal_references || [],
          processing_time: msg.response_time_ms || 0
        } : undefined
      }))
      
      return {
        conversation: {
          id: session.id,
          title: session.title || 'Chat Session',
          created_at: session.created_at,
          updated_at: session.updated_at,
          message_count: session.message_count || convertedMessages.length,
          last_message_preview: convertedMessages.length > 0 ? 
            convertedMessages[convertedMessages.length - 1].content.substring(0, 100) + '...' : 
            undefined
        },
        messages: convertedMessages
      }
    } catch (error) {
      console.error('Error in getConversation:', error)
      throw new Error(`Failed to load conversation: ${error instanceof Error ? error.message : 'Unknown error'}`)
    }
  }

  /**
   * Get chat history (all messages for user)
   */
  async getChatHistory(page: number = 1, pageSize: number = 20): Promise<{
    success: boolean
    data: Array<{
      id: string
      question: string
      answer: string
      citations: string[]
      created_at: string
      duration_ms: number
      model_used: string
      user_rating?: number
      session?: string // UUID string, not object
    }>
    total: number
    page: number
    page_size: number
  }> {
    // TODO: Implement when backend supports chat history
    console.warn('Chat history not yet implemented in backend')
    return {
      success: false,
      data: [],
      total: 0,
      page: 1,
      page_size: pageSize
    }
  }

  /**
   * Get list of user's conversations
   */
  async getConversations(
    page: number = 1, 
    limit: number = 20
  ): Promise<ConversationListResponse> {
    try {
      const response = await this.get<any>(`/chat/sessions/?page=${page}&limit=${limit}`, true)
      
      // Backend returns { sessions } array, not { results }
      const sessions = response.sessions || []
      
      const conversations: Conversation[] = sessions.map((session: any) => ({
        id: session.id,
        title: session.title || 'Chat Session',
        created_at: session.createdAt || session.created_at,
        updated_at: session.updatedAt || session.updated_at,
        message_count: session.message_count || 0,
        last_message_preview: session.last_message_preview
      }))

      return {
        results: conversations,
        count: response.total || conversations.length,
        next: null, // Backend uses page/limit instead of next/previous
        previous: null
      }
    } catch (error) {
      console.error('Error fetching conversations:', error)
      return {
        results: [],
        count: 0,
        next: null,
        previous: null
      }
    }
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/chat/sessions/${conversationId}/`, true)
  }

  /**
   * Update conversation title
   */
  async updateConversationTitle(
    conversationId: string, 
    title: string
  ): Promise<Conversation> {
    return this.patch<Conversation>(
      `/chat/sessions/${conversationId}/`, 
      { title }, 
      true
    )
  }

  /**
   * Search through conversation history
   */
  async searchConversations(
    query: string, 
    page: number = 1, 
    limit: number = 20
  ): Promise<{
    results: Array<{
      conversation: Conversation
      matching_messages: ChatMessage[]
      relevance_score: number
    }>
    count: number
    next: string | null
    previous: string | null
  }> {
    return this.get<any>(
      `/chat/search/?q=${encodeURIComponent(query)}&page=${page}&limit=${limit}`, 
      true
    )
  }

  /**
   * Get suggested questions based on user profile
   */
  async getSuggestedQuestions(): Promise<{
    categories: Array<{
      name: string
      questions: string[]
    }>
  }> {
    return this.get<any>('/chat/suggestions/', true)
  }

  /**
   * Rate a message (thumbs up/down feedback)
   */
  async rateMessage(
    messageId: string, 
    rating: 'positive' | 'negative',
    feedback?: string
  ): Promise<{ message: string }> {
    return this.post<{ message: string }>(
      `/chat/messages/${messageId}/rate/`, 
      { rating, feedback }, 
      true
    )
  }

  /**
   * Report inappropriate content
   */
  async reportMessage(
    messageId: string, 
    reason: string, 
    details?: string
  ): Promise<{ message: string }> {
    return this.post<{ message: string }>(
      `/chat/messages/${messageId}/report/`, 
      { reason, details }, 
      true
    )
  }

  /**
   * Get legal document information
   */
  async getLegalDocument(documentId: string): Promise<{
    id: string
    title: string
    type: string
    content: string
    articles: Array<{
      number: string
      title: string
      content: string
    }>
    last_updated: string
  }> {
    return this.get<any>(`/legal/documents/${documentId}/`, true)
  }

  /**
   * Search legal documents
   */
  async searchLegalDocuments(
    query: string, 
    documentType?: string
  ): Promise<{
    results: Array<{
      document_id: string
      document_title: string
      article_number: string
      article_title: string
      content_snippet: string
      relevance_score: number
    }>
    total_results: number
  }> {
    const params = new URLSearchParams({ q: query })
    if (documentType) params.append('type', documentType)
    
    return this.get<any>(`/legal/search/?${params.toString()}`, true)
  }

  /**
   * Export conversation as PDF or text
   */
  async exportConversation(
    conversationId: string, 
    format: 'pdf' | 'txt' = 'pdf'
  ): Promise<{ download_url: string; expires_at: string }> {
    return this.post<{ download_url: string; expires_at: string }>(
      `/chat/sessions/${conversationId}/export/`, 
      { format }, 
      true
    )
  }

  /**
   * Get chat usage statistics
   */
  async getChatStats(): Promise<{
    total_conversations: number
    total_messages: number
    queries_this_month: number
    most_asked_topics: Array<{
      topic: string
      count: number
    }>
    average_response_time: number
  }> {
    return this.get<any>('/chat/stats/', true)
  }
}

 // Export singleton instance
 export const chatService = new ChatService()

 export const sendStreamingMessage = (
   payload: { message: string; conversation_id?: string },
   onChunk: (chunk: string) => void,
   onConversationId?: (id: string) => void,
   onError?: (err: string) => void
 ) => chatService.sendStreamingMessage(payload, onChunk, onConversationId, onError)
