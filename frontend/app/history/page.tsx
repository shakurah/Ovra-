"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { useAuth } from "@/contexts/auth-context"
import { chatService } from "@/lib/services"
import { useRouter } from "next/navigation"
import {
  Search,
  Filter,
  Download,
  Clock,
  MessageSquare,
  Star,
  ChevronDown,
  Calendar,
  ArrowRight,
} from "lucide-react"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

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
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [sortBy, setSortBy] = useState("newest")
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchChatHistory()
  }, [])

  const fetchChatHistory = async () => {
    try {
      setLoading(true)
      const response = await chatService.getConversations()
      setSessions(response.results || [])
    } catch (error) {
      console.error("Error fetching chat sessions:", error)
      setError("Failed to load chat sessions")
    } finally {
      setLoading(false)
    }
  }

  const handleContinueChat = (sessionId: string) => {
    // Navigate to chat page with session ID to continue the conversation
    router.push(`/chat?session=${sessionId}`)
  }

  const getTopicFromTitle = (title: string): string => {
    // Simple topic extraction based on keywords in title
    const lowercaseTitle = title.toLowerCase()
    if (lowercaseTitle.includes("iva") || lowercaseTitle.includes("vat")) return "IVA"
    if (lowercaseTitle.includes("irpf") || lowercaseTitle.includes("income")) return "IRPF"
    if (lowercaseTitle.includes("autónomo") || lowercaseTitle.includes("freelancer")) return "Autónomos"
    if (lowercaseTitle.includes("factura") || lowercaseTitle.includes("billing")) return "Facturación"
    if (lowercaseTitle.includes("deducción") || lowercaseTitle.includes("deduction")) return "Deducciones"
    if (lowercaseTitle.includes("derecho") || lowercaseTitle.includes("copyright")) return "Derechos de Autor"
    return "General"
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('es-ES'),
      time: date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
    }
  }

  const filteredSessions = sessions.filter((session) => {
    const topic = getTopicFromTitle(session.title)
    const matchesSearch =
      session.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (session.last_message_preview && session.last_message_preview.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesFilter =
      selectedFilter === "all" || topic.toLowerCase().includes(selectedFilter.toLowerCase())
    return matchesSearch && matchesFilter
  })

  const sortedSessions = [...filteredSessions].sort((a, b) => {
    if (sortBy === "newest") {
      return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime()
    } else if (sortBy === "oldest") {
      return new Date(a.updated_at).getTime() - new Date(b.updated_at).getTime()
    }
    return 0
  })

  if (loading) {
    return (
      <ProtectedLayout title={t("history.title")} credits={47}>
        <div className="p-6 max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
              <p className="text-muted-foreground">Loading chat history...</p>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    )
  }

  if (error) {
    return (
      <ProtectedLayout title={t("history.title")} credits={47}>
        <div className="p-6 max-w-7xl mx-auto">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <p className="text-red-500 mb-4">{error}</p>
              <Button onClick={fetchChatHistory}>Try Again</Button>
            </div>
          </div>
        </div>
      </ProtectedLayout>
    )
  }

  return (
    <ProtectedLayout title={t("history.title")} credits={47}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("history.title")}</h1>
          <p className="text-muted-foreground">{t("history.subtitle")}</p>
        </div>

        {/* Search and Filters */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="relative flex-1">
            <Search className="h-4 w-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder={t("history.search.placeholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-background border-border"
            />
          </div>
          <div className="flex items-center space-x-2">
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Filter className="h-4 w-4 mr-2" />
                  {selectedFilter === "all" ? t("history.filter.all") : selectedFilter}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setSelectedFilter("all")}>{t("history.filter.all")}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSelectedFilter("iva")}>{t("history.filter.vat")}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSelectedFilter("irpf")}>
                  {t("history.filter.irpf")}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSelectedFilter("facturación")}>
                  {t("history.filter.billing")}
                </DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSelectedFilter("deducciones")}>
                  {t("history.filter.deductions")}
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="outline" size="sm">
                  <Calendar className="h-4 w-4 mr-2" />
                  {sortBy === "newest" ? t("history.sort.newest") : t("history.sort.oldest")}
                  <ChevronDown className="h-4 w-4 ml-2" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent>
                <DropdownMenuItem onClick={() => setSortBy("newest")}>{t("history.sort.newest")}</DropdownMenuItem>
                <DropdownMenuItem onClick={() => setSortBy("oldest")}>{t("history.sort.oldest")}</DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>

            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              {t("history.export")}
            </Button>
          </div>
        </div>

        {/* Chat Sessions List */}
        <div className="space-y-6">
          {sortedSessions.length === 0 ? (
            <Card className="border-border bg-card">
              <CardContent className="p-12 text-center">
                <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">{t("history.no.results")}</h3>
                <p className="text-muted-foreground">Try adjusting your search or filters</p>
              </CardContent>
            </Card>
          ) : (
            sortedSessions.map((session) => {
              const topic = getTopicFromTitle(session.title)
              const { date, time } = formatDate(session.updated_at)
              
              return (
                <Card key={session.id} className="border-border bg-card hover:shadow-md transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                          <MessageSquare className="h-5 w-5 text-primary" />
                        </div>
                        <div>
                          <Badge variant="secondary" className="mb-1">
                            {topic}
                          </Badge>
                          <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                            <Clock className="h-3 w-3" />
                            <span>{date}</span>
                            <span>{time}</span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">
                          {session.message_count} messages
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h3 className="font-semibold text-foreground mb-2">{session.title || 'Chat Session'}</h3>
                        {session.last_message_preview && (
                          <p className="text-muted-foreground leading-relaxed">
                            {session.last_message_preview.length > 200 
                              ? `${session.last_message_preview.substring(0, 200)}...` 
                              : session.last_message_preview
                            }
                          </p>
                        )}
                      </div>
                      <div className="flex justify-end pt-4 border-t border-border">
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
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>

        {/* Load More Button */}
        {sortedSessions.length > 0 && (
          <div className="text-center mt-8">
            <Button variant="outline">{t("history.load.more")}</Button>
          </div>
        )}
      </div>
    </ProtectedLayout>
  )
}

export default function HistoryPage() {
  return <HistoryPageContent />
}
