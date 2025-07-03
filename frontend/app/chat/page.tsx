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

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  timestamp: string
}

function ChatPageContent() {
  const { t } = useLanguage()
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [credits] = useState(47) // Mock credits
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | undefined>()
  const [isInitialized, setIsInitialized] = useState(false)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  // Generate UUID for chat session
  const generateUUID = () => {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = Math.random() * 16 | 0
      const v = c == 'x' ? r : (r & 0x3 | 0x8)
      return v.toString(16)
    })
  }

  // Initialize chat session on component mount
  useEffect(() => {
    const initializeChat = () => {
      try {
        // Get or create conversation ID
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

        setIsInitialized(true)
      } catch (error) {
        console.error('Error initializing chat:', error)
        // Fallback: create new session
        const newConversationId = generateUUID()
        setConversationId(newConversationId)
        localStorage.setItem('ovra_chat_conversation_id', newConversationId)
        setIsInitialized(true)
      }
    }

    initializeChat()
  }, [])

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
    if (conversationId) {
      // Clear messages from state
      setMessages([])

      // Remove from localStorage
      localStorage.removeItem(`ovra_chat_messages_${conversationId}`)

      // Generate new conversation ID
      const newConversationId = generateUUID()
      setConversationId(newConversationId)
      localStorage.setItem('ovra_chat_conversation_id', newConversationId)
    }
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
      id: crypto.randomUUID(),
      role: 'user',
      content: trimmedInput,
      timestamp: new Date().toISOString()
    }

    const assistantMessage: Message = {
      id: crypto.randomUUID(),
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
                        <div className="prose prose-sm max-w-none dark:prose-invert">
                          {message.role === 'assistant' ? (
                            <ReactMarkdown
                              remarkPlugins={[remarkGfm]}
                              components={{
                                h1: ({children}) => <h1 className="text-xl font-bold mb-3">{children}</h1>,
                                h2: ({children}) => <h2 className="text-lg font-semibold mb-2">{children}</h2>,
                                h3: ({children}) => <h3 className="text-base font-medium mb-2">{children}</h3>,
                                p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                                ul: ({children}) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                                ol: ({children}) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                                li: ({children}) => <li className="mb-1">{children}</li>,
                                strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                                em: ({children}) => <em className="italic">{children}</em>,
                                code: ({children}) => <code className="bg-muted px-1 py-0.5 rounded text-sm font-mono">{children}</code>,
                                pre: ({children}) => <pre className="bg-muted p-3 rounded-md overflow-x-auto mb-2">{children}</pre>,
                                blockquote: ({children}) => <blockquote className="border-l-4 border-primary pl-4 italic mb-2">{children}</blockquote>,
                              }}
                            >
                              {message.content}
                            </ReactMarkdown>
                          ) : (
                            message.content
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
