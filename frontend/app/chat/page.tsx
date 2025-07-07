"use client"

import { useRef, useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { toastService, chatService } from "@/lib/services"
import { Send, User, Bot, Sparkles, Scale, Trash2 } from "lucide-react"
import Link from "next/link"
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { generateUUID } from "@/utils/uuid"
import { useSearchParams, useRouter } from "next/navigation"

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

function ChatPageContent() {
  const { t } = useLanguage()
  const searchParams = useSearchParams()
  const router = useRouter()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [credits] = useState(47) // Mock credits
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [isInitialized, setIsInitialized] = useState(false)
  const [sessionLoading, setSessionLoading] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Initialize chat session on component mount
  useEffect(() => {
    const initializeChat = async () => {
      try {
        setSessionLoading(true)
        
        // Check if session parameter is provided in URL
        const sessionParam = searchParams.get('session')
        
        if (sessionParam) {
          // Load existing session from backend
          try {
            const sessionData = await chatService.getConversation(sessionParam)
            
            // Validate response structure
            if (sessionData && sessionData.messages && Array.isArray(sessionData.messages)) {
              setConversationId(sessionParam)
              setMessages(sessionData.messages)
              localStorage.setItem('ovra_chat_conversation_id', sessionParam)
              localStorage.setItem(`ovra_chat_messages_${sessionParam}`, JSON.stringify(sessionData.messages))
            } else {
              console.warn('Invalid session data structure:', sessionData)
              throw new Error('Invalid session data structure')
            }
          } catch (error) {
            console.error('Error loading session:', error)
            toastService.error('Failed to load chat session. Starting new conversation.')
            // Fall back to creating new session
            const newConversationId = generateUUID()
            setConversationId(newConversationId)
            localStorage.setItem('ovra_chat_conversation_id', newConversationId)
          }
        } else {
          // Get or create conversation ID from localStorage
          let storedConversationId = localStorage.getItem('ovra_chat_conversation_id')

          if (!storedConversationId) {
            storedConversationId = generateUUID()
            localStorage.setItem('ovra_chat_conversation_id', storedConversationId)
          }

          setConversationId(storedConversationId)

          // Load chat history if exists
          const storedMessages = localStorage.getItem(`ovra_chat_messages_${storedConversationId}`)
          if (storedMessages) {
            try {
              const parsedMessages = JSON.parse(storedMessages)
              if (Array.isArray(parsedMessages)) {
                setMessages(parsedMessages)
              }
            } catch (error) {
              console.error('Error parsing stored messages:', error)
            }
          }
        }

        setIsInitialized(true)
      } catch (error) {
        console.error('Error initializing chat:', error)
        // Fallback: create new session
        const newConversationId = generateUUID()
        setConversationId(newConversationId)
        localStorage.setItem('ovra_chat_conversation_id', newConversationId)
        setIsInitialized(true)
      } finally {
        setSessionLoading(false)
      }
    }

    initializeChat()
  }, [searchParams])

  // Save messages to localStorage whenever messages change
  useEffect(() => {
    if (isInitialized && conversationId && messages.length > 0) {
      try {
        localStorage.setItem(`ovra_chat_messages_${conversationId}`, JSON.stringify(messages))
      } catch (error) {
        console.error('Error saving messages to localStorage:', error)
      }
    }
  }, [messages, conversationId, isInitialized])

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const exampleQuestions = [
    t("chat.examples.freelancer"),
    t("chat.examples.vat"),
    t("chat.examples.deductions"),
    t("chat.examples.copyright"),
    t("chat.examples.obligations"),
  ]

  const handleExampleClick = (question: string) => {
    setInput(question)
  }

  const clearChatHistory = () => {
    // Clear messages from state
    setMessages([])

    // Remove session parameter from URL
    router.replace('/chat')

    // Remove from localStorage if conversationId exists
    if (conversationId) {
      localStorage.removeItem(`ovra_chat_messages_${conversationId}`)
    }

    // Generate new conversation ID
    const newConversationId = generateUUID()
    setConversationId(newConversationId)
    localStorage.setItem('ovra_chat_conversation_id', newConversationId)
    
    // Clear any loaded session state
    setIsInitialized(true)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    const trimmedInput = input.trim()
    if (!trimmedInput || isLoading || credits <= 0) return

    // Validate minimum length
    if (trimmedInput.length < 3) {
      toastService.error(t('chat.error.question_too_short'))
      return
    }

    const userMessage: Message = {
      id: generateUUID(),
      role: 'user',
      content: trimmedInput,
      timestamp: new Date().toISOString()
    }

    const assistantMessage: Message = {
      id: generateUUID(),
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString()
    }

    setMessages(prev => [...prev, userMessage, assistantMessage])
    setInput('')
    setIsLoading(true)

    try {
      await chatService.sendStreamingMessage(
        {
          message: userMessage.content,
          conversation_id: conversationId
        },
        (chunk: string) => {
          setMessages(prev => {
            const newMessages = [...prev]
            const lastMessage = newMessages[newMessages.length - 1]
            if (lastMessage && lastMessage.role === 'assistant') {
              // Ensure we don't duplicate content
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
        (error: string) => {
          toastService.error(t('chat.error.failed'))
          console.error('Chat error:', error)
          setIsLoading(false)
        }
      )
    } catch (error) {
      toastService.error(t('chat.error.failed'))
      console.error('Chat error:', error)
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInput(e.target.value)
  }

  if (sessionLoading) {
    return (
      <ProtectedLayout
        title={t("chat.title")}
        credits={47}
      >
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading chat session...</p>
          </div>
        </div>
      </ProtectedLayout>
    )
  }

  return (
    <ProtectedLayout
      title={t("chat.title")}
      credits={47}
    >
      <div className="flex flex-col h-full">
        {/* GPT-4 Status Badge and Clear Chat in Header Area */}
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
                  Clear Chat
                </Button>
              )}
            </div>
            <Badge
              variant="outline"
              className="text-green-600 border-green-200 dark:text-green-400 dark:border-green-800"
            >
              <Sparkles className="h-3 w-3 mr-1" />
              GPT-4 Activo
            </Badge>
          </div>
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4">
          {messages.length === 0 ? (
            <div className="max-w-3xl mx-auto">
              <div className="text-center mb-8">
                <div className="inline-flex items-center justify-center w-16 h-16 bg-primary/10 rounded-full mb-4">
                  <Scale className="h-8 w-8 text-primary" />
                </div>
                <h2 className="text-2xl font-bold text-foreground mb-2">{t("chat.welcome.title")}</h2>
                <p className="text-muted-foreground mb-6">{t("chat.welcome.description")}</p>
              </div>

              <div className="grid gap-3 mb-6">
                <h3 className="font-medium text-foreground mb-2">{t("chat.welcome.examples")}</h3>
                {exampleQuestions.map((question, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="text-left justify-start h-auto p-4 whitespace-normal bg-transparent border-border hover:bg-muted"
                    onClick={() => handleExampleClick(question)}
                  >
                    {question}
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <div className="max-w-3xl mx-auto space-y-6">
              {messages.map((message, index) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex max-w-[80%] ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                    <Avatar className="flex-shrink-0">
                      <AvatarFallback className={message.role === "user" ? "bg-primary/10" : "bg-muted"}>
                        {message.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                      </AvatarFallback>
                    </Avatar>
                    <Card
                      className={`mx-3 ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-card"} ${
                        message.role === "assistant" && isLoading && index === messages.length - 1
                          ? "streaming-glow"
                          : ""
                      }`}
                    >
                      <CardContent className="p-4">
                        <div className={`${message.role === 'user' ? 'user-message-text' : ''}`}>
                          {message.role === 'assistant' ? (
                            <div className="prose prose-sm max-w-none dark:prose-invert">
                              <ReactMarkdown
                                remarkPlugins={[remarkGfm]}
                                components={{
                                  h1: ({children}) => <h1 className="text-xl font-bold mb-4 mt-6 first:mt-0 text-foreground">{children}</h1>,
                                  h2: ({children}) => <h2 className="text-lg font-semibold mb-3 mt-5 first:mt-0 text-foreground">{children}</h2>,
                                  h3: ({children}) => <h3 className="text-base font-medium mb-2 mt-4 first:mt-0 text-foreground">{children}</h3>,
                                  p: ({children}) => <p className="mb-3 last:mb-0 text-foreground leading-relaxed">{children}</p>,
                                  ul: ({children}) => <ul className="list-disc pl-6 mb-4 space-y-1 text-foreground">{children}</ul>,
                                  ol: ({children}) => <ol className="list-decimal pl-6 mb-4 space-y-1 text-foreground">{children}</ol>,
                                  li: ({children}) => <li className="text-foreground leading-relaxed">{children}</li>,
                                  strong: ({children}) => <strong className="font-semibold text-foreground">{children}</strong>,
                                  em: ({children}) => <em className="italic text-muted-foreground">{children}</em>,
                                  code: ({children}) => <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono text-foreground border">{children}</code>,
                                  pre: ({children}) => <pre className="bg-muted p-4 rounded-md overflow-x-auto mb-4 border">{children}</pre>,
                                  blockquote: ({children}) => <blockquote className="border-l-4 border-primary pl-4 italic mb-4 text-muted-foreground bg-muted/50 py-2 rounded-r">{children}</blockquote>,
                                  table: ({children}) => <table className="w-full border-collapse border border-border mb-4 text-sm">{children}</table>,
                                  thead: ({children}) => <thead className="bg-muted">{children}</thead>,
                                  tbody: ({children}) => <tbody>{children}</tbody>,
                                  tr: ({children}) => <tr className="border-b border-border">{children}</tr>,
                                  th: ({children}) => <th className="border border-border px-3 py-2 font-semibold text-left text-foreground">{children}</th>,
                                  td: ({children}) => <td className="border border-border px-3 py-2 text-foreground">{children}</td>,
                                  a: ({children, href}) => <a href={href} className="text-primary hover:underline hover:text-primary/80 transition-colors" target="_blank" rel="noopener noreferrer">{children}</a>,
                                }}
                              >
                                {message.content}
                              </ReactMarkdown>
                            </div>
                          ) : (
                            <p className="text-primary-foreground">{message.content}</p>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex max-w-[80%]">
                    <Avatar className="flex-shrink-0">
                      <AvatarFallback className="bg-muted">
                        <Bot className="h-4 w-4" />
                      </AvatarFallback>
                    </Avatar>
                    <Card className="mx-3 bg-card">
                      <CardContent className="p-4">
                        <div className="flex items-center space-x-2">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"></div>
                            <div
                              className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                              style={{ animationDelay: "0.1s" }}
                            ></div>
                            <div
                              className="w-2 h-2 bg-muted-foreground rounded-full animate-bounce"
                              style={{ animationDelay: "0.2s" }}
                            ></div>
                          </div>
                          <span className="text-sm text-muted-foreground">{t("chat.input.analyzing")}</span>
                        </div>
                      </CardContent>
                    </Card>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Input Form */}
        <div className="border-t border-border bg-card p-4">
          <div className="max-w-3xl mx-auto">
            <form onSubmit={handleSubmit} className="flex space-x-4">
              <Input
                value={input}
                onChange={handleInputChange}
                placeholder={t("chat.input.placeholder")}
                className="flex-1 h-12 bg-background border-border"
                disabled={isLoading || credits <= 0}
              />
              <Button type="submit" size="lg" disabled={isLoading || !input.trim() || credits <= 0} className="px-6">
                <Send className="h-4 w-4" />
              </Button>
            </form>

            {credits <= 0 && (
              <div className="mt-2 text-center">
                <span className="text-sm text-destructive">
                  {t("chat.input.nocredits")}{" "}
                  <Link href="/credits" className="underline">
                    {t("chat.input.buycredits")}
                  </Link>
                </span>
              </div>
            )}

            <p className="text-xs text-muted-foreground mt-2 text-center">{t("chat.input.disclaimer")}</p>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  )
}

export default function ChatPage() {
  return <ChatPageContent />
}
