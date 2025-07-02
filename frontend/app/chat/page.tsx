"use client"

import { useChat } from "ai/react"
import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ThemeToggle } from "@/components/theme-toggle"
import { LanguageToggle } from "@/components/language-toggle"
import { ProtectedRoute } from "@/components/protected-route"
import { useLanguage } from "@/contexts/language-context"
import { useAuth } from "@/contexts/auth-context"
import { Scale, Send, User, Bot, Menu, CreditCard, LogOut, BookOpen, MessageSquare, Sparkles } from "lucide-react"
import Link from "next/link"

function ChatPageContent() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat()
  const { t } = useLanguage()
  const { logout } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const [credits, setCredits] = useState(47) // Mock credits

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

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
    handleInputChange({ target: { value: question } } as any)
  }

  return (
    <div className="flex h-screen bg-background">
      {/* Sidebar */}
      <div
        className={`${sidebarOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-50 w-64 bg-card shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 border-r border-border`}
      >
        <div className="flex items-center justify-between p-4 border-b border-border">
          <Link href="/" className="flex items-center space-x-2">
            <Scale className="h-8 w-8 text-primary" />
            <span className="text-xl font-bold text-foreground">Ovra AI</span>
          </Link>
          <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(false)}>
            ×
          </Button>
        </div>

        <div className="p-4">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-muted-foreground">{t("chat.credits.remaining")}</span>
              <Badge variant="secondary" className="bg-primary/10 text-primary">
                {credits}
              </Badge>
            </div>
            <div className="w-full bg-muted rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${(credits / 50) * 100}%` }}
              ></div>
            </div>
          </div>

          <nav className="space-y-2">
            <Link href="/chat" className="flex items-center space-x-3 px-3 py-2 rounded-lg bg-primary/10 text-primary">
              <MessageSquare className="h-5 w-5" />
              <span>{t("chat.sidebar.chat")}</span>
            </Link>
            <Link
              href="/credits"
              className="flex items-center space-x-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted"
            >
              <CreditCard className="h-5 w-5" />
              <span>{t("chat.sidebar.credits")}</span>
            </Link>
            <Link
              href="/history"
              className="flex items-center space-x-3 px-3 py-2 rounded-lg text-muted-foreground hover:bg-muted"
            >
              <BookOpen className="h-5 w-5" />
              <span>{t("chat.sidebar.docs")}</span>
            </Link>
          </nav>
        </div>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border">
          <Button
            variant="ghost"
            className="w-full justify-start text-muted-foreground"
            onClick={logout}
          >
            <LogOut className="h-5 w-5 mr-3" />
            {t("chat.sidebar.logout")}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <header className="bg-card border-b border-border px-4 py-3 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(true)}>
              <Menu className="h-5 w-5" />
            </Button>
            <div>
              <h1 className="text-xl font-semibold text-foreground">{t("chat.title")}</h1>
              <p className="text-sm text-muted-foreground">{t("chat.subtitle")}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <LanguageToggle />
            <ThemeToggle />
            <Badge
              variant="outline"
              className="text-green-600 border-green-200 dark:text-green-400 dark:border-green-800"
            >
              <Sparkles className="h-3 w-3 mr-1" />
              GPT-4 Activo
            </Badge>
          </div>
        </header>

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
              {messages.map((message) => (
                <div key={message.id} className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`flex max-w-[80%] ${message.role === "user" ? "flex-row-reverse" : "flex-row"}`}>
                    <Avatar className="flex-shrink-0">
                      <AvatarFallback className={message.role === "user" ? "bg-primary/10" : "bg-muted"}>
                        {message.role === "user" ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                      </AvatarFallback>
                    </Avatar>
                    <Card
                      className={`mx-3 ${message.role === "user" ? "bg-primary text-primary-foreground" : "bg-card"}`}
                    >
                      <CardContent className="p-4">
                        <div className="prose prose-sm max-w-none dark:prose-invert">{message.content}</div>
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
    </div>
  )
}

export default function ChatPage() {
  return (
    <ProtectedRoute>
      <ChatPageContent />
    </ProtectedRoute>
  )
}
