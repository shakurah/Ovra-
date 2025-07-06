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

interface ChatMessage {
  id: string
  question: string
  answer: string
  citations: string[]
  created_at: string
  duration_ms: number
  model_used: string
  user_rating?: number
  session?: string // This is a UUID string, not an object
}

function HistoryPageContent() {
  const { t } = useLanguage()
  const { user } = useAuth()
  const router = useRouter()
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [sortBy, setSortBy] = useState("newest")
  const [consultations, setConsultations] = useState<ChatMessage[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchChatHistory()
  }, [])

  const fetchChatHistory = async () => {
    try {
      setLoading(true)
      const response = await chatService.getChatHistory()
      if (response.success) {
        setConsultations(response.data)
      } else {
        setError("Failed to load chat history")
      }
    } catch (error) {
      console.error("Error fetching chat history:", error)
      setError("Failed to load chat history")
    } finally {
      setLoading(false)
    }
  }

  const handleContinueChat = (sessionId: string) => {
    // Navigate to chat page with session ID to continue the conversation
    router.push(`/chat?session=${sessionId}`)
  }

  const getTopicFromQuestion = (question: string): string => {
    // Simple topic extraction based on keywords
    const lowercaseQuestion = question.toLowerCase()
    if (lowercaseQuestion.includes("iva") || lowercaseQuestion.includes("vat")) return "IVA"
    if (lowercaseQuestion.includes("irpf") || lowercaseQuestion.includes("income")) return "IRPF"
    if (lowercaseQuestion.includes("autónomo") || lowercaseQuestion.includes("freelancer")) return "Autónomos"
    if (lowercaseQuestion.includes("factura") || lowercaseQuestion.includes("billing")) return "Facturación"
    if (lowercaseQuestion.includes("deducción") || lowercaseQuestion.includes("deduction")) return "Deducciones"
    if (lowercaseQuestion.includes("derecho") || lowercaseQuestion.includes("copyright")) return "Derechos de Autor"
    return "General"
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return {
      date: date.toLocaleDateString('es-ES'),
      time: date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })
    }
  }

  const filteredConsultations = consultations.filter((consultation) => {
    const topic = getTopicFromQuestion(consultation.question)
    const matchesSearch =
      consultation.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      consultation.answer.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter =
      selectedFilter === "all" || topic.toLowerCase().includes(selectedFilter.toLowerCase())
    return matchesSearch && matchesFilter
  })

  const sortedConsultations = [...filteredConsultations].sort((a, b) => {
    if (sortBy === "newest") {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    } else if (sortBy === "oldest") {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
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

        {/* Consultations List */}
        <div className="space-y-6">
          {sortedConsultations.length === 0 ? (
            <Card className="border-border bg-card">
              <CardContent className="p-12 text-center">
                <MessageSquare className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-foreground mb-2">{t("history.no.results")}</h3>
                <p className="text-muted-foreground">Try adjusting your search or filters</p>
              </CardContent>
            </Card>
          ) : (
            sortedConsultations.map((consultation) => {
              const topic = getTopicFromQuestion(consultation.question)
              const { date, time } = formatDate(consultation.created_at)
              
              return (
                <Card key={consultation.id} className="border-border bg-card hover:shadow-md transition-shadow">
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
                        {consultation.user_rating && (
                          <div className="flex items-center space-x-1">
                            {[...Array(5)].map((_, i) => (
                              <Star
                                key={i}
                                className={`h-4 w-4 ${
                                  i < consultation.user_rating! ? "text-yellow-400 fill-current" : "text-muted-foreground"
                                }`}
                              />
                            ))}
                          </div>
                        )}
                        <Badge variant="outline" className="text-xs">
                          {consultation.duration_ms}ms
                        </Badge>
                      </div>
                    </div>

                    <div className="space-y-4">
                      <div>
                        <h3 className="font-semibold text-foreground mb-2">Pregunta:</h3>
                        <p className="text-muted-foreground">{consultation.question}</p>
                      </div>
                      <div>
                        <h3 className="font-semibold text-foreground mb-2">Respuesta:</h3>
                        <p className="text-muted-foreground leading-relaxed">
                          {consultation.answer.length > 300 
                            ? `${consultation.answer.substring(0, 300)}...` 
                            : consultation.answer
                          }
                        </p>
                      </div>
                      {consultation.citations && consultation.citations.length > 0 && (
                        <div>
                          <h3 className="font-semibold text-foreground mb-2">Citas legales:</h3>
                          <div className="flex flex-wrap gap-2">
                            {consultation.citations.map((citation, index) => (
                              <Badge key={index} variant="outline" className="text-xs">
                                {citation}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                      {consultation.session && (
                        <div className="flex justify-end pt-4 border-t border-border">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => handleContinueChat(consultation.session!)}
                            className="flex items-center gap-2"
                          >
                            Continue Chat
                            <ArrowRight className="h-4 w-4" />
                          </Button>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )
            })
          )}
        </div>

        {/* Load More Button */}
        {sortedConsultations.length > 0 && (
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
