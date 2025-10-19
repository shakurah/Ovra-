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
import { sendStreamingMessage } from '@/lib/services/chat.service'

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

  // rotating loading messages
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

  useEffect(() => {
    if (!isLoading) {
      setLoadingMessage('')
      return
    }
    let index = 0
    setLoadingMessage(loadingMessages[0])
    const interval = setInterval(() => {
      index = (index + 1) % loadingMessages.length
      setLoadingMessage(loadingMessages[index])
    }, 1500)
    return () => clearInterval(interval)
  }, [isLoading])

  // load from localStorage
  useEffect(() => {
    const savedEmail = localStorage.getItem('ovra_widget_email')
    if (savedEmail) {
      setEmail(savedEmail)
      setIsRegistered(true)
      setShowEmailForm(false)
      setPrivacyAccepted(true)
      setTermsAccepted(true)
    }

    const savedSession = localStorage.getItem('ovra_widget_session')
    if (savedSession) setSessionId(savedSession)
  }, [])

  // auto-scroll
  useEffect(() => {
    const smoothScroll = () => {
      if (scrollAreaRef.current) {
        const viewport = scrollAreaRef.current.querySelector('[data-radix-scroll-area-viewport]')
        if (viewport) {
          const target = viewport.scrollHeight - viewport.clientHeight
          viewport.scrollTo({ top: target, behavior: 'smooth' })
        }
      }
    }
    setTimeout(smoothScroll, 50)
  }, [messages])

  // register
  const handleRegister = async () => {
    if (!email || !privacyAccepted || !termsAccepted) return
    setIsLoading(true)
    try {
      const res = await fetch(`${apiUrl}/widget/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          privacy_accepted: privacyAccepted,
          terms_accepted: termsAccepted,
          source_website: sourceWebsite
        })
      })
      const data = await res.json()
      if (data.is_success) {
        setIsRegistered(true)
        setShowEmailForm(false)
        localStorage.setItem('ovra_widget_email', email)
        setMessages([{
          id: uuidv4(),
          role: 'assistant',
          content: '¡Hola! Soy tu asistente fiscal. ¿En qué puedo ayudarte hoy?',
          timestamp: new Date(),
        }])
      } else {
        setMessages([{
          id: uuidv4(),
          role: 'assistant',
          content: 'Error al registrar el email. Por favor, verifica tu email e inténtalo de nuevo.',
          timestamp: new Date(),
        }])
      }
    } catch (err) {
      console.error('Registration error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  // ✅ FIXED STREAM HANDLER

  const handleSendMessage = async () => {
    console.log("📩 handleSubmit triggered")

    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    const assistantId = uuidv4()
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
    }])

    console.log('[chat-widget] handleSendMessage START', { assistantId, sessionId })
    try {
      console.log('[chat-widget] calling sendStreamingMessage (about to await)')
      console.log('[chat-widget] sendStreamingMessage value', sendStreamingMessage)

      // sanity guard: if missing, throw visible error
      if (typeof sendStreamingMessage !== 'function') {
        console.error('[chat-widget] sendStreamingMessage is not a function', sendStreamingMessage)
        throw new Error('sendStreamingMessage missing')
      }
      
      console.log("🚀 Calling sendStreamingMessage")

      await sendStreamingMessage(
        { message: userMessage.content, conversation_id: sessionId ?? undefined },
        // onChunk
        (chunk: string) => {
          console.log('[chat-widget] onChunk', { assistantId, len: chunk.length, preview: chunk.slice(0,100) })
          setMessages(prev =>
            prev.map(m => m.id === assistantId ? { ...m, content: (m.content || '') + chunk } : m)
          )
        },
        // onConversationId
        (convId: string) => {
          console.log('[chat-widget] onConversationId', convId)
          if (!sessionId) {
            setSessionId(convId)
            localStorage.setItem('ovra_widget_session', convId)
          }
        },
        // onError
        (err: string) => {
          console.log('[chat-widget] onError', err)
          console.error('stream error', err)
          setMessages(prev => prev.map(m => m.id === assistantId ? { ...m, content: 'Lo siento, ha ocurrido un error.' } : m))
        }
      )
      console.log('[chat-widget] sendStreamingMessage AWAIT returned')
    } finally {
      console.log('[chat-widget] finally clearing isLoading (was)', isLoading)
      setIsLoading(false)
      console.log('[chat-widget] isLoading cleared (now false)')
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      if (showEmailForm) handleRegister()
      else handleSendMessage()
    }
  }

  return (
    <>
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-4 right-4 rounded-full w-14 h-14 shadow-lg bg-black dark:bg-white hover:bg-black hover:dark:bg-white hover:shadow-xl transition-shadow"
          size="icon"
        >
          <MessageCircle className="!h-6 !w-6 text-white dark:text-black" />
        </Button>
      )}

      {isOpen && (
        <Card className="fixed bottom-4 right-4 w-96 h-[600px] flex flex-col shadow-xl">
          <div className="flex items-center justify-between p-4 border-b">
            <h3 className="font-semibold">Asistente Fiscal OVRA</h3>
            <Button onClick={() => setIsOpen(false)} variant="ghost" size="icon" className="h-8 w-8">
              <X className="h-4 w-4" />
            </Button>
          </div>

          {!isRegistered || showEmailForm ? (
            <div className="flex-1 p-6 flex flex-col justify-center">
              {/* Registration Form */}
              <div className="space-y-4">
                <div className="text-center mb-6">
                  <h4 className="text-lg font-semibold mb-2">¡Bienvenido a OVRA!</h4>
                  <p className="text-sm text-muted-foreground">
                    Ingresa tu email para comenzar a hacer preguntas sobre impuestos y contabilidad.
                  </p>
                </div>
                <Input
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyPress={handleKeyPress}
                  disabled={isLoading}
                />
                <div className="space-y-3">
                  <div className="flex items-start space-x-2">
                    <Checkbox
                      id="privacy"
                      checked={privacyAccepted}
                      onCheckedChange={checked => setPrivacyAccepted(!!checked)}
                      disabled={isLoading}
                    />
                    <label htmlFor="privacy" className="text-xs leading-none">
                      Acepto la{' '}
                      <a href="/privacy" target="_blank" className="underline hover:text-primary">
                        política de privacidad
                      </a>
                    </label>
                  </div>
                  <div className="flex items-start space-x-2">
                    <Checkbox
                      id="terms"
                      checked={termsAccepted}
                      onCheckedChange={checked => setTermsAccepted(!!checked)}
                      disabled={isLoading}
                    />
                    <label htmlFor="terms" className="text-xs leading-none">
                      Acepto los{' '}
                      <a href="/terms" target="_blank" className="underline hover:text-primary">
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
              <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
                <div className="space-y-4">
                  {messages.map(msg => (
                    <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                      <div
                        className={`max-w-[80%] rounded-lg p-3 ${msg.role === 'user'
                          ? 'bg-primary text-primary-foreground'
                          : 'bg-muted'}`}
                      >
                        {msg.role === 'assistant'
                          ? <div className="prose prose-sm dark:prose-invert"><ReactMarkdown>{msg.content}</ReactMarkdown></div>
                          : <p className="text-sm">{msg.content}</p>}
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
                          <span className="text-sm text-muted-foreground italic">{loadingMessage}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </ScrollArea>

              <div className="p-4 border-t">
                <div className="flex space-x-2">
                  <Input
                    placeholder="Haz tu pregunta sobre impuestos..."
                    value={input}
                    onChange={e => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                    disabled={isLoading}
                  />
                  <Button onClick={handleSendMessage} disabled={!input.trim() || isLoading} size="icon">
                    <Send className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-muted-foreground mt-2 text-center">Powered by ARTISTING</p>
              </div>
            </>
          )}
        </Card>
      )}
    </>
  )
}
