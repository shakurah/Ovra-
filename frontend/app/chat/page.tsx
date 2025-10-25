"use client"

import { useEffect, useState, useRef } from "react"
import Image from "next/image"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { toastService, chatService } from "@/lib/services"
import { Send, Trash2 } from "lucide-react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { generateUUID } from "@/utils/uuid"
import { useSearchParams, useRouter } from "next/navigation"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

function ChatPageContent() {
  const { t } = useLanguage()
  const searchParams = useSearchParams()
  const router = useRouter()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const formRef = useRef<HTMLFormElement | null>(null)
  const textareaRef = useRef<HTMLTextAreaElement | null>(null)
  // credits: null = unknown, number = actual credits
  const [credits, setCredits] = useState<number | null>(null)
  const apiUrl = process.env.NEXT_PUBLIC_API_URL || ''

  const getStoredToken = (): string | null => {
    if (typeof window === "undefined") return null
    const keys = ['access', 'token', 'jwt', 'ovra_token']
    for (const k of keys) {
      const v = localStorage.getItem(k)
      if (v) return v
    }
    return null
  }

  const fetchCredits = async () => {
    try {
      const token = getStoredToken()
      const headers: Record<string, string> = { 'Content-Type': 'application/json' }
      if (token) headers['Authorization'] = `Bearer ${token}`

      // normalize apiUrl to avoid double "/api/v1" when NEXT_PUBLIC_API_URL already contains it
      const normalizeApiBase = (base: string) => {
        if (!base) return ''
        let b = base.trim().replace(/\/+$/, '') // remove trailing slashes
        b = b.replace(/\/api\/v1$/i, '') // strip trailing /api/v1 if present
        return b
      }
      const base = normalizeApiBase(apiUrl)
      const endpoint = base ? `${base}/api/v1/chat/chat_health` : `/api/v1/chat/_chat_health`
      const res = await fetch(endpoint, { method: 'GET', headers })
      if (!res.ok) return
      const j = await res.json()
      if (typeof j.credits === 'number') setCredits(j.credits)
    } catch (err) {
      console.error('fetchCredits error', err)
    }
  }
  useEffect(() => { fetchCredits() }, [])

  const [input, setInput] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState("")
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [isInitialized, setIsInitialized] = useState(false)
  const [sessionLoading, setSessionLoading] = useState(false)
  const [showBanner, setShowBanner] = useState(false)
  const bannerRef = useRef<HTMLDivElement | null>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    if (credits !== null && credits <= 0) setShowBanner(true)
  }, [credits])

  useEffect(() => {
    const ta = textareaRef.current
    if (!ta) return
    ta.style.height = "auto"
    ta.style.height = `${ta.scrollHeight}px`
  }, [input])

  useEffect(() => {
    const initializeChat = async () => {
      try {
        const sessionParam = searchParams.get("session")
        if (sessionParam && sessionParam !== "undefined") {
          try {
            const sessionData = await chatService.getConversation(sessionParam)
            if (sessionData && sessionData.messages && Array.isArray(sessionData.messages)) {
              setConversationId(sessionParam)
              setMessages(sessionData.messages)
            } else {
              console.warn("Invalid session data structure:", sessionData)
              throw new Error("Invalid session data structure")
            }
          } catch (error) {
            console.error("Error loading session:", error)
            toastService.error("Failed to load chat session. Starting new conversation.")
            setConversationId(null)
          }
        } else {
          setConversationId(null)
        }
        setIsInitialized(true)
      } catch (error) {
        console.error("Error initializing chat:", error)
        setConversationId(null)
        setIsInitialized(true)
      } finally {
        setSessionLoading(false)
      }
    }
    initializeChat()
  }, [searchParams])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleOutsideClick = (e: MouseEvent) => {
    if (bannerRef.current && !bannerRef.current.contains(e.target as Node)) {
      setShowBanner(false)
    }
  }

  useEffect(() => {
    if (showBanner) {
      document.addEventListener("mousedown", handleOutsideClick)
      return () => document.removeEventListener("mousedown", handleOutsideClick)
    }
  }, [showBanner])

  const handleExampleClick = (question: string) => setInput(question)

  const clearChatHistory = () => {
    setMessages([])
    router.replace("/chat")
    setConversationId(null)
    setIsInitialized(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedInput = input.trim()
    if (!trimmedInput || isLoading) return

    if (credits === null || credits <= 0) {
      const assistantMessage: Message = {
        id: generateUUID(),
        role: "assistant",
        content:
          t("chat.input.nocredits") ||
          "Has agotado tus créditos gratuitos. Por favor adquiere más créditos en la página de créditos: /credits",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMessage])
      setInput("")
      setIsLoading(false)
      return
    }

    if (trimmedInput.length < 3) {
      toastService.error(t("chat.error.question_too_short"))
      return
    }

    const userMessage: Message = {
      id: generateUUID(),
      role: "user",
      content: trimmedInput,
      timestamp: new Date().toISOString(),
    }
    const assistantMessage: Message = {
      id: generateUUID(),
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setInput("")
    setIsLoading(true)

    try {
      await chatService.sendStreamingMessage(
        { message: userMessage.content, conversation_id: conversationId },
        (chunk: string) => {
          setMessages((prev) => {
            const newMessages = [...prev]
            const lastMessage = newMessages[newMessages.length - 1]
            if (lastMessage && lastMessage.role === "assistant") {
              if (!lastMessage.content.endsWith(chunk)) {
                lastMessage.content += chunk
              }
            }
            return newMessages
          })
        },
        (newConversationId: string) => {
          setConversationId(newConversationId)
          setIsLoading(false)
        },
        (error: any) => {
          const errMsg =
            (typeof error === "string" && error) ||
            (error && (error.message || JSON.stringify(error))) ||
            t("chat.error.failed")
          const isCreditIssue =
            errMsg.toLowerCase().includes("credit") ||
            errMsg.toLowerCase().includes("crédit") ||
            errMsg.includes("402") ||
            errMsg.toLowerCase().includes("no credits") ||
            errMsg.toLowerCase().includes("agotado")
          if (isCreditIssue) {
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastIndex = newMessages.length - 1
              if (lastIndex >= 0 && newMessages[lastIndex].role === "assistant") {
                newMessages[lastIndex].content =
                  t("chat.input.nocredits") ||
                  "Has agotado tus créditos. Visita /credits para adquirir más."
              } else {
                newMessages.push({
                  id: generateUUID(),
                  role: "assistant",
                  content:
                    t("chat.input.nocredits") ||
                    "Has agotado tus créditos. Visita /credits para adquirir más.",
                  timestamp: new Date().toISOString(),
                })
              }
              return newMessages
            })
          } else {
            toastService.error(t("chat.error.failed"))
            setMessages((prev) => {
              const newMessages = [...prev]
              const lastIndex = newMessages.length - 1
              if (lastIndex >= 0 && newMessages[lastIndex].role === "assistant") {
                newMessages[lastIndex].content = t("chat.error.failed")
              }
              return newMessages
            })
          }
          setIsLoading(false)
        }
      )
    } catch (error) {
      toastService.error(t("chat.error.failed"))
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => setInput(e.target.value)

  if (sessionLoading) {
    return (
      <ProtectedLayout title={t("chat.title")} credits={credits ?? 0}>
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          </div>
        </div>
      </ProtectedLayout>
    )
  }

  return (
    <ProtectedLayout title={t("chat.title")} credits={credits ?? 0}>
      <div className="flex flex-col h-full">
        <div className="px-4 py-2 border-b border-border bg-card/50">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              {messages.length > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={clearChatHistory}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  {t("chat.header.new_chat")}
                </Button>
              )}
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4">
          <div ref={messagesEndRef} />
        </div>

        <div className="border-t border-border bg-card p-4">
          <div className="max-w-3xl mx-auto">
            <form ref={formRef} onSubmit={handleSubmit} className="flex space-x-4">
              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleInputChange}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault()
                    formRef.current?.requestSubmit()
                  }
                }}
                placeholder={t("chat.input.placeholder")}
                rows={1}
                className="flex-1 min-h-[48px] max-h-[280px] resize-none bg-background border-border p-3 rounded-md focus:outline-none"
                disabled={isLoading || (credits ?? 0) <= 0}
              />
              <Button
                type="submit"
                size="lg"
                disabled={isLoading || !input.trim() || (credits ?? 0) <= 0}
                className="px-6"
              >
                <Send className="h-4 w-4" />
              </Button>
            </form>

            <p className="text-xs text-muted-foreground mt-2 text-center">
              {t("chat.input.disclaimer")}
            </p>
          </div>
        </div>
      </div>

      {showBanner && (
        <div className="fixed inset-0 flex items-center justify-center bg-black/50 z-50">
          <div
            ref={bannerRef}
            className="bg-background border rounded-2xl shadow-lg max-w-md w-full p-6 relative"
          >
            <button
              className="absolute top-3 right-3 text-xl font-bold"
              onClick={() => setShowBanner(false)}
              aria-label={t("chat.credits.dismiss")}
            >
              ×
            </button>
            <h2 className="text-xl font-semibold mb-2">
              {t("chat.credits.title")}
            </h2>
            <p className="text-sm mb-4">{t("chat.credits.message")}</p>
            <Button onClick={() => router.push("/pricing")} className="w-full">
              {t("chat.credits.subscribe")}
            </Button>
          </div>
        </div>
      )}
    </ProtectedLayout>
  )
}

export default function ChatPage() {
  return <ChatPageContent />
}
