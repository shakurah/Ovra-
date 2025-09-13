"use client"

import React, { useState, useRef, useEffect } from 'react'
import { Send, X, MessageCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card } from '@/components/ui/card'
import { Checkbox } from '@/components/ui/checkbox'
import { ScrollArea } from '@/components/ui/scroll-area'
import { v4 as uuidv4 } from 'uuid'
import ReactMarkdown from 'react-markdown'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  citations?: any[]
  timestamp: Date
}

interface ChatWidgetProps {
  apiUrl?: string
  sourceWebsite?: string
}

export function ChatWidget({
  apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  sourceWebsite = typeof window !== 'undefined' ? window.location.origin : ''
}: ChatWidgetProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [email, setEmail] = useState('')
  const [isRegistered, setIsRegistered] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState('')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [privacyAccepted, setPrivacyAccepted] = useState(false)
  const [termsAccepted, setTermsAccepted] = useState(false)
  const [showEmailForm, setShowEmailForm] = useState(true)
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  // BOE-related loading messages
  const loadingMessages = [
    'Consultando Boletín Oficial del Estado...',
    'Analizando normativa fiscal vigente...',
    'Revisando últimas actualizaciones del BOE...',
    'Procesando legislación tributaria...',
    'Verificando disposiciones administrativas...',
    'Accediendo a jurisprudencia fiscal...',
    'Consultando reglamentos específicos...',
    'Analizando circular normativa...',
    'Revisando ordenanzas municipales...',
    'Procesando Real Decreto vigente...',
    'Verificando Ley General Tributaria...',
    'Consultando instrucciones AEAT...',
    'Analizando resoluciones DGT...',
    'Revisando normativa autonómica...',
    'Procesando documentación oficial...'
  ]

  // Loading message rotation effect
  useEffect(() => {
    if (!isLoading) {
      setLoadingMessage('')
      return
    }

    let messageIndex = 0
    setLoadingMessage(loadingMessages[0])

    const interval = setInterval(() => {
      messageIndex = (messageIndex + 1) % loadingMessages.length
      setLoadingMessage(loadingMessages[messageIndex])
    }, 1500) // Change every 1.5 seconds

    return () => clearInterval(interval)
  }, [isLoading])

  // Load email from localStorage on mount
  useEffect(() => {
    const savedEmail = localStorage.getItem('ovra_widget_email')
    if (savedEmail) {
      setEmail(savedEmail)
      setIsRegistered(true)
      setShowEmailForm(false)
      setPrivacyAccepted(true)
      setTermsAccepted(true)
    } else {
      setIsRegistered(false)
      setShowEmailForm(true)
    }

    // Load session if exists
    const savedSession = localStorage.getItem('ovra_widget_session')
    if (savedSession) {
      setSessionId(savedSession)
    }
  }, [])

  // Auto-scroll to bottom when new messages arrive
 useEffect(() => {
  const smoothScrollToBottom = () => {
    if (scrollAreaRef.current) {
      const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        const startY = viewport.scrollTop;
        const targetY = viewport.scrollHeight - viewport.clientHeight;
        const distance = targetY - startY;
        const duration = 300; // milliseconds
        
        if (distance === 0) return;
        
        const startTime = performance.now();
        
        const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);
        
        const animateScroll = (currentTime: number) => {
          const elapsed = currentTime - startTime;
          const progress = Math.min(elapsed / duration, 1);
          const easedProgress = easeOutCubic(progress);
          
          viewport.scrollTop = startY + distance * easedProgress;
          
          if (progress < 1) {
            requestAnimationFrame(animateScroll);
          }
        };
        
        requestAnimationFrame(animateScroll);
      }
    }
  };
  
  setTimeout(smoothScrollToBottom, 0);
}, [messages])


  const handleRegister = async () => {
    if (!email || !privacyAccepted || !termsAccepted) {
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${apiUrl}/widget/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          privacy_accepted: privacyAccepted,
          terms_accepted: termsAccepted,
          source_website: sourceWebsite,
        }),
      })

      const data = await response.json()

      if (data.is_success) {
        setIsRegistered(true)
        setShowEmailForm(false)
        localStorage.setItem('ovra_widget_email', email)

        // Add welcome message
        setMessages([{
          id: uuidv4(),
          role: 'assistant',
          content: '¡Hola! Soy tu asistente fiscal. ¿En qué puedo ayudarte hoy?',
          timestamp: new Date(),
        }])
      } else {
        console.error('Registration failed:', data.message)
        // Show error message
        setMessages([{
          id: uuidv4(),
          role: 'assistant',
          content: 'Error al registrar el email. Por favor, verifica tu email e inténtalo de nuevo.',
          timestamp: new Date(),
        }])
      }
    } catch (error) {
      console.error('Registration error:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      // Check if user is registered, if not, show email form
      if (!isRegistered || !email) {
        setMessages(prev => [...prev, {
          id: uuidv4(),
          role: 'assistant',
          content: 'Por favor, registra tu email primero para poder ayudarte.',
          timestamp: new Date(),
        }])
        setShowEmailForm(true)
        setIsLoading(false)
        return
      }

      // Use the same endpoint as the login area
      const response = await fetch(`${apiUrl}/chat/message/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          conversation_id: sessionId,
          email: email, // Include email for widget context
          source_website: sourceWebsite,
        }),
      })

      const data = await response.json()

      if (data.message) {
        const assistantMessage: Message = {
          id: data.message.id || uuidv4(),
          role: 'assistant',
          content: data.message.content,
          citations: data.message.metadata?.legal_references || [],
          timestamp: new Date(),
        }

        setMessages(prev => [...prev, assistantMessage])

        // Save session ID
        if (data.conversation_id && !sessionId) {
          setSessionId(data.conversation_id)
          localStorage.setItem('ovra_widget_session', data.conversation_id)
        }
      } else {
        // Check if it's an email registration error
        if (data.error === 'Email not registered') {
          setMessages(prev => [...prev, {
            id: uuidv4(),
            role: 'assistant',
            content: 'Tu email no está registrado. Por favor, regístrate primero.',
            timestamp: new Date(),
          }])
          setIsRegistered(false)
          setShowEmailForm(true)
        } else {
          // Show generic error message
          setMessages(prev => [...prev, {
            id: uuidv4(),
            role: 'assistant',
            content: data.message || 'Lo siento, ha ocurrido un error. Por favor, inténtalo de nuevo.',
            timestamp: new Date(),
          }])
        }
      }
    } catch (error) {
      console.error('Chat error:', error)
      setMessages(prev => [...prev, {
        id: uuidv4(),
        role: 'assistant',
        content: 'Lo siento, ha ocurrido un error de conexión. Por favor, inténtalo de nuevo.',
        timestamp: new Date(),
      }])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (showEmailForm) {
        handleRegister()
      } else {
        handleSendMessage()
      }
    }
  }

  return (
    <>
      {/* Floating button */}
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 rounded-full w-14 h-14 shadow-lg bg-black dark:bg-white hover:bg-black hover:dark:bg-white hover:shadow-xl transition-shadow"
          size="icon"
        >
          <MessageCircle className="!h-6 !w-6 text-white dark:text-black" />
        </Button>
      )}

      {/* Chat widget */}
      {isOpen && (
        <Card className="fixed bottom-4 right-4 w-96 h-[600px] flex flex-col shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-semibold">Asistente Fiscal OVRA</h3>
            <Button
              onClick={() => setIsOpen(false)}
              variant="ghost"
              size="icon"
              className="h-8 w-8"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>

          {/* Messages or Email Form */}
          {!isRegistered || showEmailForm ? (
            <div className="flex-1 p-6 flex flex-col justify-center">
              <div className="space-y-4">
                <div className="text-center mb-6">
                  <h4 className="text-lg font-semibold mb-2">
                    ¡Bienvenido a OVRA!
                  </h4>
                  <p className="text-sm text-muted-foreground">
                    Ingresa tu email para comenzar a hacer preguntas sobre impuestos y contabilidad.
                  </p>
                </div>

                <Input
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />

                <div className="space-y-3">
                  <div className="flex items-start space-x-2">
                    <Checkbox
                      id="privacy"
                      checked={privacyAccepted}
                      onCheckedChange={(checked) => setPrivacyAccepted(!!checked)}
                      disabled={isLoading}
                    />
                    <label
                      htmlFor="privacy"
                      className="text-xs leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      Acepto la{' '}
                      <a
                        href="/privacy"
                        target="_blank"
                        className="underline hover:text-primary"
                      >
                        política de privacidad
                      </a>
                    </label>
                  </div>

                  <div className="flex items-start space-x-2">
                    <Checkbox
                      id="terms"
                      checked={termsAccepted}
                      onCheckedChange={(checked) => setTermsAccepted(!!checked)}
                      disabled={isLoading}
                    />
                    <label
                      htmlFor="terms"
                      className="text-xs leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                    >
                      Acepto los{' '}
                      <a
                        href="/terms"
                        target="_blank"
                        className="underline hover:text-primary"
                      >
                        términos y condiciones
                      </a>
                    </label>
                  </div>
                </div>

                <Button
                  onClick={handleRegister}
                  disabled={!email || !privacyAccepted || !termsAccepted || isLoading}
                  className="w-full"
                >
                  {isLoading ? 'Registrando...' : 'Continuar'}
                </Button>
              </div>
            </div>
          ) : (
            <>
              {/* Messages */}
              <ScrollArea className="flex-1 p-4 " ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.map((message) => (
                    <div
                      key={message.id}
                      className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'
                        }`}
                    >
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${message.role === 'user'
                            ? 'bg-primary text-primary-foreground'
                            : 'bg-muted'
                          }`}
                      >
                        {message.role === 'assistant' ? (
                          <div className="prose prose-sm dark:prose-invert">
                            <ReactMarkdown>
                              {message.content}
                            </ReactMarkdown>
                          </div>
                        ) : (
                          <p className="text-sm">{message.content}</p>
                        )}

                        {message.citations && message.citations.length > 0 && (
                          <div className="mt-2 pt-2 border-t">
                            <p className="text-xs font-semibold mb-1">Referencias:</p>
                            {message.citations.map((citation, idx) => (
                              <p key={idx} className="text-xs opacity-80">
                                • {citation.article} - {citation.law}
                              </p>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}

                  {isLoading && (
                    <div className="flex justify-start">
                      <div className="bg-muted rounded-lg p-3">
                        <div className="flex items-center space-x-3">
                          <div className="flex space-x-1">
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" />
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-100" />
                            <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce delay-200" />
                          </div>
                          <span className="text-sm text-muted-foreground italic">
                            {loadingMessage}
                          </span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              {/* Input */}
              <div className="p-4 border-t">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Haz tu pregunta sobre impuestos..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  <Button
                    onClick={handleSendMessage}
                    disabled={!input.trim() || isLoading}
                    size="icon"
                  >
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  Powered by OVRA AI
                </p>
              </div>
            </>
          )}
        </Card>
      )}
    </>
  )
}