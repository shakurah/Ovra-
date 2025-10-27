"use client"

import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { useAuth } from "@/contexts/auth-context"
import { chatService } from "@/lib/services/chat.service"
import { useRouter } from "next/navigation"
import { Search, Download, Clock, MessageSquare, ArrowRight } from "lucide-react"
import jsPDF from "jspdf"
import "jspdf-autotable"

interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
  message_count: number
  last_message_preview?: string
}

function HistoryPageContent() {
  const { t } = useLanguage()
  const { user } = useAuth()
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState("")
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    fetchChatHistory()
  }, [user])

  const fetchChatHistory = async () => {
    setLoading(true)
    try {
      const response = await chatService.getConversations()
      const items = Array.isArray(response.results) ? response.results : []
      setSessions(items)
    } catch (err) {
      console.error("Error fetching chat history:", err)
      setError("Failed to load chat history.")
    } finally {
      setLoading(false)
    }
  }
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
  const handleContinueChat = (sessionId: string) => {
    router.push(`/chat?session=${sessionId}`)
  }
  const [credits, setCredits] = useState<number | null>(null)
  const fetchCredits = async () => {

    const base = apiUrl
    const endpoint = base ? `${base}/chat/chat_health/` : `chat.artisting.es/api/v1/chat/chat_health/`

    // helper: attempt GET with given headers/credentials
    const tryGet = async (opts: RequestInit) => {
      try {
        const res = await fetch(endpoint, opts)
        if (!res.ok) return null
        return await res.json()
      } catch (e) {
        return null
      }
    }

    // 1) try Authorization header from localStorage
    const access = getStoredToken()
    if (access) {
      const json = await tryGet({ method: 'GET', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${access}` } })
      if (json && typeof json.credits === 'number') {
        setCredits(json.credits)
        return
      }
    }

    // 2) try refresh token flow (if refresh token stored)
    const refresh = localStorage.getItem('refresh') || localStorage.getItem('refresh_token')
    if (refresh) {
      try {
        const refreshBase = base || ''
        const refreshUrl = refreshBase ? `${refreshBase}/auth/token/refresh/` : 'chat.artisting.es/api/v1/auth/token/refresh/'
        const r = await fetch(refreshUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh })
        })
        if (r.ok) {
          const body = await r.json()
          if (body.access) {
            localStorage.setItem('access', body.access)
            // retry with new access token
            const json = await tryGet({ method: 'GET', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${body.access}` } })
            if (json && typeof json.credits === 'number') {
              setCredits(json.credits)
              return
            }
          }
        }
      } catch (e) {
        // ignore and continue to cookie fallback
      }
    }

    // 3) fallback: maybe backend uses cookie/session auth — try including credentials
    const jsonCred = await tryGet({ method: 'GET', credentials: 'include' })
    if (jsonCred && typeof jsonCred.credits === 'number') {
      setCredits(jsonCred.credits)
      return
    }

    // final: debug hint (no token or unauthorized)
    console.debug('fetchCredits: no valid token or cookie session; endpoint:', endpoint)
  }
  useEffect(() => { fetchCredits() }, [])
  const getTopicFromTitle = (title: string): string => {
    const lowercaseTitle = title.toLowerCase()
    if (lowercaseTitle.includes("iva") || lowercaseTitle.includes("vat")) return "IVA"
    if (lowercaseTitle.includes("irpf") || lowercaseTitle.includes("income")) return "IRPF"
    if (lowercaseTitle.includes("autónomo") || lowercaseTitle.includes("freelancer")) return "Autónomos"
    if (lowercaseTitle.includes("factura") || lowercaseTitle.includes("billing")) return "Facturación"
    if (lowercaseTitle.includes("deducción") || lowercaseTitle.includes("deduction")) return "Deducciones"
    return "General"
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString("es-ES"),
      time: date.toLocaleTimeString("es-ES", { hour: "2-digit", minute: "2-digit" }),
    }
  }

  const filteredSessions = sessions.filter(
    (session) =>
      session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (session.last_message_preview &&
        session.last_message_preview.toLowerCase().includes(searchQuery.toLowerCase()))
  )

  /** 🧾 Export chat history to PDF */
  const handleExportPDF = () => {
    const doc = new jsPDF()
    doc.setFontSize(16)
    doc.text("Chat History", 14, 15)
    doc.setFontSize(11)
    doc.text(`User: ${user?.email || "Anonymous"}`, 14, 22)
    doc.text(`Date: ${new Date().toLocaleString()}`, 14, 29)

    const rows = filteredSessions.map((s) => [
      s.title || "Untitled",
      s.message_count,
      new Date(s.updated_at).toLocaleString(),
      getTopicFromTitle(s.title),
    ])

    // Create table
    ;(doc as any).autoTable({
      head: [["Title", "Messages", "Updated", "Topic"]],
      body: rows,
      startY: 35,
      styles: { fontSize: 10, cellPadding: 2 },
    })

    doc.save("chat_history.pdf")
  }

  if (loading) {
    return (
      <ProtectedLayout title={t("history.title")} credits={credits ?? 0}>

        <div className="p-6 flex justify-center items-center h-64">
          <p className="text-muted-foreground">Loading chat history...</p>
        </div>
      </ProtectedLayout>
    )
  }

  if (error) {
    return (
      <ProtectedLayout title={t("history.title")} credits={0}>
        <div className="p-6 flex flex-col items-center justify-center h-64 text-center">
          <p className="text-red-500 mb-4">{error}</p>
          <Button onClick={fetchChatHistory}>Try Again</Button>
        </div>
      </ProtectedLayout>
    )
  }

  return (
    <ProtectedLayout title={t("history.title")} credits={credits ?? 0}>

      <div className="p-4 sm:p-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl sm:text-3xl font-bold mb-1">{t("history.title")}</h1>
          <p className="text-sm text-muted-foreground">{t("history.subtitle")}</p>
        </div>

        {/* Search & Export */}
        <div className="flex flex-col sm:flex-row gap-3 mb-6">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t("history.search.placeholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-background border-border w-full"
            />
          </div>
          <Button
            variant="outline"
            size="sm"
            className="flex items-center justify-center"
            onClick={handleExportPDF}
          >
            <Download className="h-4 w-4 mr-2" />
            {t("history.export") || "Export History"}
          </Button>
        </div>

        {/* Chat List */}
        <div className="space-y-4">
          {filteredSessions.length === 0 ? (
            <Card className="bg-card text-center p-8">
              <CardContent>
                <MessageSquare className="h-10 w-10 text-muted-foreground mx-auto mb-3" />
                <h3 className="font-semibold text-lg mb-1">{t("history.no.results")}</h3>
                <p className="text-sm text-muted-foreground">Try searching with a different term.</p>
              </CardContent>
            </Card>
          ) : (
            filteredSessions.map((session) => {
              const topic = getTopicFromTitle(session.title)
              const { date, time } = formatDate(session.updated_at)

              return (
                <Card
                  key={session.id}
                  className="bg-card border-border hover:shadow-sm transition-all duration-200"
                >
                  <CardContent className="p-4 sm:p-6">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-3 gap-2">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                          <MessageSquare className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <Badge variant="secondary" className="mb-1">{topic}</Badge>
                          <div className="flex items-center space-x-2 text-xs text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{date}</span>
                            <span>{time}</span>
                          </div>
                        </div>
                      </div>
                      <Badge variant="outline" className="text-xs self-start sm:self-auto">
                        {session.message_count} messages
                      </Badge>
                    </div>

                    <div>
                      <h3 className="font-semibold text-foreground mb-2">
                        {session.title || "Chat Session"}
                      </h3>
                      {session.last_message_preview && (
                        <p className="text-sm text-muted-foreground leading-relaxed">
                          {session.last_message_preview.length > 150
                            ? `${session.last_message_preview.substring(0, 150)}...`
                            : session.last_message_preview}
                        </p>
                      )}
                    </div>

                    <div className="flex justify-end mt-4 border-t border-border pt-3">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleContinueChat(session.id)}
                        className="flex items-center gap-2"
                      >
                        Continue Chat
                        <ArrowRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>
      </div>
    </ProtectedLayout>
  )
}

export default function HistoryPage() {
  return <HistoryPageContent />
}
