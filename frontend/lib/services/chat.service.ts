/**
 * Chat Service
 * Handles AI chat interactions, conversation management, and legal queries
 */

import { BaseApiService } from './base.service'

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
      question: request.message,
      session_id: request.conversation_id,
      law_filter: request.context?.law_filter,
      stream: false
    }

    try {
      const response = await this.post<any>('/chat/', payload, true)

      return {
        message: {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: response.data.answer,
          timestamp: new Date().toISOString(),
          metadata: {
            legal_references: response.data.citations || [],
            confidence_score: 0.9,
            processing_time: response.data.duration_ms
          }
        },
        conversation_id: response.data.session_id || request.conversation_id,
        usage: response.data.usage
      }
    } catch (error: any) {
      // Handle session not found - automatically create new session
      if (error.status === 404 || (error.response && error.response.code === 404)) {
        // Try again without session_id to create a new session
        const newPayload = {
          ...payload,
          session_id: undefined
        }

        const retryResponse = await this.post<any>('/chat/', newPayload, true)

        return {
          message: {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: retryResponse.data.answer,
            timestamp: new Date().toISOString(),
            metadata: {
              legal_references: retryResponse.data.citations || [],
              confidence_score: 0.9,
              processing_time: retryResponse.data.duration_ms
            }
          },
          conversation_id: retryResponse.data.session_id,
          usage: retryResponse.data.usage
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
    request: ChatRequest,
    onChunk: (chunk: string) => void,
    onComplete: (conversationId: string) => void,
    onError: (error: string) => void
  ): Promise<void> {
    const payload = {
      question: request.message,
      session_id: request.conversation_id,
      law_filter: request.context?.law_filter,
      stream: true
    }

    try {
      const response = await fetch(`${this.baseUrl}/chat/stream/`, {
        method: 'POST',
        headers: this.getAuthHeaders(),
        body: JSON.stringify(payload)
      })

      // Handle session not found - automatically create new session
      if (response.status === 404) {
        // Try again without session_id to create a new session
        const newPayload = {
          ...payload,
          session_id: undefined
        }

        const retryResponse = await fetch(`${this.baseUrl}/chat/stream/`, {
          method: 'POST',
          headers: this.getAuthHeaders(),
          body: JSON.stringify(newPayload)
        })

        if (!retryResponse.ok) {
          throw new Error(`HTTP error! status: ${retryResponse.status}`)
        }

        // Use the retry response for processing
        return this.processStreamingResponse(retryResponse, onChunk, onComplete, onError, request.conversation_id)
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return this.processStreamingResponse(response, onChunk, onComplete, onError, request.conversation_id)
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error')
    }
  }

  /**
   * Process streaming response (extracted for reuse)
   */
  private async processStreamingResponse(
    response: Response,
    onChunk: (chunk: string) => void,
    onComplete: (conversationId: string) => void,
    onError: (error: string) => void,
    originalConversationId?: string
  ): Promise<void> {

    const reader = response.body?.getReader()
    if (!reader) {
      throw new Error('No response body')
    }

    const decoder = new TextDecoder()
    let conversationId = originalConversationId

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      const chunk = decoder.decode(value)
      const lines = chunk.split('\n')

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6))

            if (data.type === 'session') {
              conversationId = data.session_id
            } else if (data.type === 'content') {
              onChunk(data.content)
            } else if (data.type === 'done') {
              onComplete(conversationId || '')
              return
            } else if (data.type === 'error') {
              onError(data.message)
              return
            }
          } catch (e) {
            // Ignore malformed JSON
          }
        }
      }
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
    return this.get<any>(`/chat/conversations/${conversationId}/`, true)
  }

  /**
   * Get list of user's conversations
   */
  async getConversations(
    page: number = 1, 
    limit: number = 20
  ): Promise<ConversationListResponse> {
    return this.get<ConversationListResponse>(
      `/chat/conversations/?page=${page}&limit=${limit}`, 
      true
    )
  }

  /**
   * Delete a conversation
   */
  async deleteConversation(conversationId: string): Promise<{ message: string }> {
    return this.delete<{ message: string }>(`/chat/conversations/${conversationId}/`, true)
  }

  /**
   * Update conversation title
   */
  async updateConversationTitle(
    conversationId: string, 
    title: string
  ): Promise<Conversation> {
    return this.patch<Conversation>(
      `/chat/conversations/${conversationId}/`, 
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
      `/chat/conversations/${conversationId}/export/`, 
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
