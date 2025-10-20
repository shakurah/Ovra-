/**
 * Cleaned Chat Service
 * Restores sendStreamingMessage export and fixes syntax errors introduced at file end.
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

export class ChatService extends BaseApiService {
  // Non-streaming send
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    const payload = {
      message: request.message,
      conversation_id: request.conversation_id,
      context: request.context ? [
        { role: 'system', content: `User profession: ${request.context.user_profession || 'General'}` }
      ] : []
    }

    const response = await this.post<any>('/chat/message/', payload, true)

    return {
      message: {
        id: generateUUID(),
        role: 'assistant',
        content: response.message || response.data?.message || '',
        timestamp: new Date().toISOString(),
        metadata: {
          legal_references: response.data?.citations || [],
          confidence_score: 0.9,
          processing_time: response.data?.duration_ms
        }
      },
      conversation_id: response.conversation_id || response.data?.conversation_id || request.conversation_id || '',
      usage: response.data?.usage
    }
  }

  // Streaming send
  public async sendStreamingMessage(
    payload: { message: string; conversation_id?: string },
    onChunk: (chunk: string) => void,
    onConversationId?: (id: string) => void,
    onError?: (err: string) => void
  ) {
    const controller = new AbortController()
    const token = typeof window !== 'undefined' ? localStorage.getItem('accessToken') : null

    console.debug('[chat.service] sendStreamingMessage START', { payload, hasToken: !!token })

    try {
      const base = (process.env.NEXT_PUBLIC_API_URL || '').replace(/\/$/, '')
      const res = await fetch(`${base}/chat/stream/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: JSON.stringify(payload),
        signal: controller.signal
      })

      console.debug('[chat.service] fetch returned', { status: res.status, ok: res.ok, headers: Object.fromEntries(res.headers.entries()) })

      if (!res.ok) {
        const text = await res.text().catch(() => `HTTP ${res.status}`)
        console.debug('[chat.service] non-ok response body', text)
        onError?.(text)
        return
      }

      console.debug('[chat.service] delegating to processStreamingResponse')
      await this.processStreamingResponse(res, onChunk, onConversationId, onError)
      console.debug('[chat.service] processStreamingResponse returned')

    } catch (err: any) {
      console.debug('[chat.service] caught error in sendStreamingMessage', err)
      if (err?.name === 'AbortError') onError?.('stream aborted')
      else onError?.(err?.message || String(err))
    } finally {
      try { controller.abort() } catch {}
      console.debug('[chat.service] sendStreamingMessage FINALLY — controller aborted')
      // intentionally no UI state changes here — caller handles loading state
    }
  }

  // Shared streaming parser: detects [DONE], handles chunks, cleans up reader
  private async processStreamingResponse(
    res: Response,
    onChunk: (chunk: string) => void,
    onConversationId?: (id: string) => void,
    onError?: (err: string) => void
  ) {
    const reader = res.body?.getReader()
    if (!reader) {
      console.debug('[chat.service] no reader on response')
      onError?.('No response body')
      return
    }

    const decoder = new TextDecoder()
    let buffer = ''

    try {
      while (true) {
        const { value, done } = await reader.read()
        console.debug('[chat.service] reader.read ->', { done, chunkSize: value?.length ?? 0 })
        if (done) break
        if (value) buffer += decoder.decode(value, { stream: true })

        // Detect [DONE] even if server didn't include trailing double-newline
        if (buffer.includes('[DONE]')) {
          console.debug('[chat.service] buffer includes [DONE]')
          buffer = buffer.replace(/\[DONE\]/g, '')
          // fall through to process remaining data and then return
        }

        const parts = buffer.split('\n\n')
        buffer = parts.pop() || ''

        for (const part of parts) {
          console.debug('[chat.service] parsing part', part.slice(0, 200))
          const lines = part.split('\n').map(l => l.trim()).filter(Boolean)
          for (const line of lines) {
            const payloadStr = line.startsWith('data:') ? line.slice(5).trim() : line.trim()
            if (!payloadStr) continue

            if (payloadStr === '[DONE]' || payloadStr.includes('[DONE]')) {
              console.debug('[chat.service] detected DONE payloadStr')
              // final marker — stop processing
              return
            }

            try {
              const obj = JSON.parse(payloadStr)
              console.debug('[chat.service] parsed JSON chunk', { conversation_id: obj.conversation_id ?? null, contentPreview: (obj.content ?? '').slice?.(0,100) ?? obj.content })
              if (obj.conversation_id) onConversationId?.(obj.conversation_id)
              const content = (obj.content ?? '').toString()
              if (content && content.trim() !== '') onChunk(content)
            } catch (e) {
              console.debug('[chat.service] JSON parse failed for payloadStr, forwarding raw', payloadStr.slice(0,200))
              // not JSON — forward raw chunk
              onChunk(payloadStr)
            }
          }
        }
      }
      console.debug('[chat.service] reader loop ended, flushing buffer', buffer.slice(0,200))

      // flush any leftover buffer
      if (buffer.trim() && buffer.trim() !== '[DONE]') {
        const b = buffer.trim()
        try {
          const obj = JSON.parse(b.startsWith('data:') ? b.slice(5).trim() : b)
          if (obj.conversation_id) onConversationId?.(obj.conversation_id)
          if (obj.content) onChunk(obj.content)
        } catch {
          console.debug('[chat.service] flushing leftover raw buffer', b.slice(0,200))
          onChunk(b)
        }
      }
    } catch (err: any) {
      console.debug('[chat.service] error in processStreamingResponse', err)
      onError?.(err?.message || String(err))
    } finally {
      console.debug('[chat.service] cleaning up reader (cancel/release)')
      try { await reader.cancel() } catch {}
      try { reader.releaseLock?.() } catch {}
    }
  }

  // --- Minimal stubs for other methods to keep module usable ---
  async startConversation(initialMessage: string): Promise<ChatResponse> {
    return this.sendMessage({ message: initialMessage })
  }

  async continueConversation(conversationId: string, message: string): Promise<ChatResponse> {
    return this.sendMessage({ message, conversation_id: conversationId })
  }

  // add/replace getConversation implementation
  async getConversation(conversationId: string): Promise<{ conversation: any; messages: any[] }> {
    console.debug("[chat.service] getConversation START", { conversationId })
    const raw = await this.get<any>(`/chat/sessions/${conversationId}/`, true).catch((err) => {
      console.error("[chat.service] getConversation fetch error", err)
      return null
    })
    console.debug("[chat.service] getConversation raw", raw)

    if (!raw) return { conversation: { id: conversationId, title: "Chat", created_at: new Date().toISOString() }, messages: [] }

    const session = raw.session ?? { id: conversationId }
    const rows = raw.messages ?? []

    // normalize: backend returns rows with user_message + response_text -> turn into two chat messages per row
    const messages: any[] = []
    for (const row of rows) {
      const ts = row.created_at ?? new Date().toISOString()
      if (row.user_message) {
        messages.push({
          id: `u-${row.id}`,
          role: "user",
          content: row.user_message,
          timestamp: ts,
        })
      }
      if (row.response_text) {
        messages.push({
          id: `a-${row.id}`,
          role: "assistant",
          content: row.response_text,
          timestamp: ts,
        })
      }
    }

    return { conversation: session, messages }
  }

  // Other helpers (return safe defaults)
  async getChatHistory(): Promise<any> { return { success: false, data: [], total: 0 } }
  async getConversations(): Promise<{ results: any[]; total?: number }> {
    console.debug('[chat.service] getConversations START')
    const raw = await this.get<any>('/chat/sessions/', true).catch((err) => {
      console.debug('[chat.service] getConversations fetch error', err)
      return null
    })

    console.debug('[chat.service] raw getConversations response', raw)

    if (!raw) return { results: [], total: 0 }

    // Normalize different backend shapes
    if (Array.isArray(raw)) return { results: raw, total: raw.length }
    if (raw.results) return { results: raw.results, total: raw.total ?? raw.count ?? (raw.results.length || 0) }
    if (raw.sessions) return { results: raw.sessions, total: raw.total ?? raw.count ?? (raw.sessions.length || 0) }
    if (raw.data && Array.isArray(raw.data)) return { results: raw.data, total: raw.total ?? raw.count ?? raw.data.length }

    // fallback: wrap raw
    return { results: [], total: 0 }
  }
  async deleteConversation(conversationId: string): Promise<{ message: string }> { return { message: 'not implemented' } }
  async updateConversationTitle(conversationId: string, title: string): Promise<Conversation> { throw new Error('not implemented') }
  async searchConversations(): Promise<any> { return { results: [], count: 0 } }
  async getSuggestedQuestions(): Promise<any> { return { categories: [] } }
  async rateMessage(): Promise<any> { return { message: 'not implemented' } }
  async reportMessage(): Promise<any> { return { message: 'not implemented' } }
  async getLegalDocument(): Promise<any> { throw new Error('not implemented') }
  async searchLegalDocuments(): Promise<any> { return { results: [], total_results: 0 } }
  async exportConversation(): Promise<any> { throw new Error('not implemented') }
  async getChatStats(): Promise<any> { return { total_conversations: 0, total_messages: 0 } }
}

// Export singleton and convenience wrapper
export const chatService = new ChatService()
export const sendStreamingMessage = (
  payload: { message: string; conversation_id?: string },
  onChunk: (chunk: string) => void,
  onConversationId?: (id: string) => void,
  onError?: (err: string) => void
) => chatService.sendStreamingMessage(payload, onChunk, onConversationId, onError)


