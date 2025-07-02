"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { ThemeToggle } from "@/components/theme-toggle"
import { LanguageToggle } from "@/components/language-toggle"
import { ProtectedRoute } from "@/components/protected-route"
import { useLanguage } from "@/contexts/language-context"
import {
  Scale,
  ArrowLeft,
  Search,
  Filter,
  Download,
  Clock,
  MessageSquare,
  Star,
  ChevronDown,
  Calendar,
} from "lucide-react"
import Link from "next/link"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"

function HistoryPageContent() {
  const { t } = useLanguage()
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedFilter, setSelectedFilter] = useState("all")
  const [sortBy, setSortBy] = useState("newest")

  const consultations = [
    {
      id: 1,
      date: "2024-01-15",
      time: "14:30",
      topic: "IVA",
      question: t("chat.examples.vat"),
      answer:
        "Para servicios artísticos, generalmente se aplica el IVA del 21%. Sin embargo, algunos servicios culturales pueden beneficiarse de tipos reducidos del 10% según el artículo 91 de la Ley del IVA...",
      satisfaction: 5,
      credits: 1,
    },
    {
      id: 2,
      date: "2024-01-15",
      time: "12:15",
      topic: "IRPF",
      question: t("chat.examples.deductions"),
      answer:
        "Sí, puedes deducir los gastos de material artístico como gasto deducible en tu actividad económica según el artículo 30 de la Ley del IRPF. Esto incluye lienzos, pinturas, instrumentos musicales...",
      satisfaction: 5,
      credits: 1,
    },
    {
      id: 3,
      date: "2024-01-14",
      time: "16:45",
      topic: "Derechos de Autor",
      question: t("chat.examples.copyright"),
      answer:
        "Los derechos de autor tributan como rendimientos del trabajo en el IRPF cuando se perciben de forma habitual, aplicándose una reducción del 40% según el artículo 17.2 de la Ley del IRPF...",
      satisfaction: 4,
      credits: 1,
    },
    {
      id: 4,
      date: "2024-01-14",
      time: "10:20",
      topic: "Autónomos",
      question: t("chat.examples.obligations"),
      answer:
        "Como autónomo cultural debes: 1) Darte de alta en el RETA, 2) Presentar declaraciones trimestrales de IVA e IRPF, 3) Llevar libros de registro según el artículo 68 del Reglamento del IRPF...",
      satisfaction: 5,
      credits: 1,
    },
    {
      id: 5,
      date: "2024-01-13",
      time: "15:30",
      topic: "Facturación",
      question: t("chat.examples.freelancer"),
      answer:
        "Como freelancer cultural debes emitir facturas que cumplan los requisitos del Reglamento de Facturación (RD 1619/2012). Incluye: datos identificativos, descripción del servicio, base imponible, IVA...",
      satisfaction: 5,
      credits: 1,
    },
  ]

  const filteredConsultations = consultations.filter((consultation) => {
    const matchesSearch =
      consultation.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      consultation.answer.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesFilter =
      selectedFilter === "all" || consultation.topic.toLowerCase().includes(selectedFilter.toLowerCase())
    return matchesSearch && matchesFilter
  })

  const sortedConsultations = [...filteredConsultations].sort((a, b) => {
    if (sortBy === "newest") {
      return new Date(b.date + " " + b.time).getTime() - new Date(a.date + " " + a.time).getTime()
    } else if (sortBy === "oldest") {
      return new Date(a.date + " " + a.time).getTime() - new Date(b.date + " " + b.time).getTime()
    }
    return 0
  })

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="bg-card border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/chat">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  {t("nav.chat")}
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <Scale className="h-8 w-8 text-primary" />
                <span className="text-2xl font-bold text-foreground">Ovra AI</span>
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <LanguageToggle />
              <ThemeToggle />
              <Badge
                variant="outline"
                className="text-blue-600 border-blue-200 dark:text-blue-400 dark:border-blue-800"
              >
                <Clock className="h-3 w-3 mr-1" />
                {t("history.title")}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
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
            sortedConsultations.map((consultation) => (
              <Card key={consultation.id} className="border-border bg-card hover:shadow-md transition-shadow">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center">
                        <MessageSquare className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <Badge variant="secondary" className="mb-1">
                          {consultation.topic}
                        </Badge>
                        <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                          <Clock className="h-3 w-3" />
                          <span>{consultation.date}</span>
                          <span>{consultation.time}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="flex items-center space-x-1">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            className={`h-4 w-4 ${
                              i < consultation.satisfaction ? "text-yellow-400 fill-current" : "text-muted-foreground"
                            }`}
                          />
                        ))}
                      </div>
                      <Badge variant="outline" className="text-xs">
                        -{consultation.credits} crédito
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
                      <p className="text-muted-foreground leading-relaxed">{consultation.answer}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Load More Button */}
        {sortedConsultations.length > 0 && (
          <div className="text-center mt-8">
            <Button variant="outline">{t("history.load.more")}</Button>
          </div>
        )}
      </div>
    </div>
  )
}

export default function HistoryPage() {
  return (
    <ProtectedRoute>
      <HistoryPageContent />
    </ProtectedRoute>
  )
}
