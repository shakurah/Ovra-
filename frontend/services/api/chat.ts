/**
 * Chat API service
 */

import { apiClient } from './base'

export interface ChatMessage {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: string
  metadata?: {
    legal_references?: string[]
    confidence_score?: number
    processing_time?: number
  }
}

export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

export interface SendMessageRequest {
  message: string
  session_id?: string
}

export interface SendMessageResponse {
  message: ChatMessage
  session_id: string
  legal_references?: Array<{
    article: string
    law: string
    relevance_score: number
    excerpt: string
  }>
}

export interface ChatHistory {
  sessions: ChatSession[]
  total_count: number
  page: number
  page_size: number
}

export class ChatService {
  async sendMessage(data: SendMessageRequest): Promise<SendMessageResponse> {
    return apiClient.post<SendMessageResponse>('/chat/send/', data)
  }

  async getSession(sessionId: string): Promise<{
    session: ChatSession
    messages: ChatMessage[]
  }> {
    return apiClient.get<{
      session: ChatSession
      messages: ChatMessage[]
    }>(`/chat/sessions/${sessionId}/`)
  }

  async getSessions(page = 1, pageSize = 20): Promise<ChatHistory> {
    return apiClient.get<ChatHistory>(`/chat/sessions/?page=${page}&page_size=${pageSize}`)
  }

  async deleteSession(sessionId: string): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>(`/chat/sessions/${sessionId}/`)
  }

  async updateSessionTitle(sessionId: string, title: string): Promise<ChatSession> {
    return apiClient.patch<ChatSession>(`/chat/sessions/${sessionId}/`, { title })
  }

  async exportSession(sessionId: string, format: 'json' | 'pdf' | 'txt' = 'json'): Promise<Blob> {
    const response = await fetch(`${apiClient['baseURL']}/chat/sessions/${sessionId}/export/?format=${format}`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`
      }
    })

    if (!response.ok) {
      throw new Error('Failed to export session')
    }

    return response.blob()
  }

  // WebSocket connection for real-time chat
  connectWebSocket(sessionId: string, onMessage: (message: ChatMessage) => void): WebSocket {
    const wsUrl = `ws://localhost:8000/ws/chat/${sessionId}/`
    const token = localStorage.getItem('access_token')
    
    const ws = new WebSocket(`${wsUrl}?token=${token}`)
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'chat_message') {
          onMessage(data.message)
        }
      } catch (error) {
        console.error('WebSocket message parsing error:', error)
      }
    }

    ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    return ws
  }
}

// Export singleton instance
export const chatService = new ChatService()
