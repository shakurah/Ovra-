"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { ChatWidget } from "@/components/chat-widget"
import {
  CheckCircle,
  MessageSquare,
  Shield,
  Zap,
  Users,
  BookOpen,
  BarChart3,
  Clock,
  Target,
  FileText,
  Lightbulb,
  Star,
} from "lucide-react"
import Link from "next/link"

export default function LandingPage() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-background transition-colors">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="mb-6">
            <Badge className="mb-4 bg-primary/10 text-primary border-primary/20 hover:bg-primary/20">
              {t("hero.badge")}
            </Badge>
          </div>

          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 leading-tight">
            {t("hero.title")}
            <br />
            <span className="text-primary">{t("hero.subtitle")}</span>
          </h1>

          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
            {t("hero.description")}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
            <Link href="/chat">
              <Button size="lg" className="text-lg px-8 py-4 bg-primary hover:bg-primary/90">
                {t("hero.cta.primary")}
              </Button>
            </Link>
            <Button size="lg" variant="ghost" className="text-lg px-8 py-4 text-muted-foreground hover:text-foreground">
              {t("hero.cta.secondary")}
            </Button>
          </div>

          {/* Trust Indicators */}
          <div className="flex flex-wrap justify-center items-center gap-8 text-sm text-muted-foreground">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-4 w-4 text-green-500" />
              <span>{t("trust.verified")}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-blue-500" />
              <span>{t("trust.availability")}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Shield className="h-4 w-4 text-purple-500" />
              <span>{t("trust.updated")}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Users className="h-4 w-4 text-orange-500" />
              <span>{t("trust.specialized")}</span>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <Card className="text-center border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <BookOpen className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <div className="text-3xl font-bold text-foreground mb-1">50</div>
                <div className="text-sm text-muted-foreground">{t("stats.laws")}</div>
              </CardContent>
            </Card>

            <Card className="text-center border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <FileText className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <div className="text-3xl font-bold text-foreground mb-1">0.5K</div>
                <div className="text-sm text-muted-foreground">{t("stats.articles")}</div>
              </CardContent>
            </Card>

            <Card className="text-center border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Target className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <div className="text-3xl font-bold text-foreground mb-1">98%</div>
                <div className="text-sm text-muted-foreground">{t("stats.accuracy")}</div>
              </CardContent>
            </Card>

            <Card className="text-center border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Clock className="h-6 w-6 text-orange-600 dark:text-orange-400" />
                </div>
                <div className="text-3xl font-bold text-foreground mb-1">24/7</div>
                <div className="text-sm text-muted-foreground">{t("stats.availability")}</div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Why Choose Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">{t("why.title")}</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto">{t("why.subtitle")}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-lg flex items-center justify-center mb-6">
                  <Shield className="h-6 w-6 text-blue-600 dark:text-blue-400" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{t("why.legislation.title")}</h3>
                <p className="text-muted-foreground">{t("why.legislation.desc")}</p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-lg flex items-center justify-center mb-6">
                  <Users className="h-6 w-6 text-green-600 dark:text-green-400" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{t("why.specialized.title")}</h3>
                <p className="text-muted-foreground">{t("why.specialized.desc")}</p>
              </CardContent>
            </Card>

            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-8">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-lg flex items-center justify-center mb-6">
                  <Zap className="h-6 w-6 text-purple-600 dark:text-purple-400" />
                </div>
                <h3 className="text-xl font-semibold text-foreground mb-3">{t("why.instant.title")}</h3>
                <p className="text-muted-foreground">{t("why.instant.desc")}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Frequent Questions */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">{t("faq.title")}</h2>
            <p className="text-xl text-muted-foreground">{t("faq.subtitle")}</p>
          </div>

          <div className="grid md:grid-cols-2 gap-6">
            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">V</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-foreground">{t("faq.vat.title")}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {t("badge.popular")}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground text-sm">{t("faq.vat.desc")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-green-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">I</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-foreground">{t("faq.irpf.title")}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {t("badge.essential")}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground text-sm">{t("faq.irpf.desc")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">I</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-foreground">{t("faq.international.title")}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {t("badge.advanced")}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground text-sm">{t("faq.international.desc")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-orange-600 rounded-lg flex items-center justify-center flex-shrink-0">
                    <span className="text-white font-semibold text-sm">O</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-foreground">{t("faq.objective.title")}</h3>
                      <Badge variant="secondary" className="text-xs">
                        {t("badge.recommended")}
                      </Badge>
                    </div>
                    <p className="text-muted-foreground text-sm">{t("faq.objective.desc")}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Testimonials */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-foreground mb-4">{t("testimonials.title")}</h2>
            <p className="text-xl text-muted-foreground">{t("testimonials.subtitle")}</p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            <Card className="border-border bg-card">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4">"{t("testimonials.maria")}"</p>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center">
                    <span className="text-blue-600 dark:text-blue-400 font-semibold text-sm">MG</span>
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">María García</div>
                    <div className="text-sm text-muted-foreground">{t("testimonials.maria.role")}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4">"{t("testimonials.carlos")}"</p>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center">
                    <span className="text-green-600 dark:text-green-400 font-semibold text-sm">CR</span>
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Carlos Rodríguez</div>
                    <div className="text-sm text-muted-foreground">{t("testimonials.carlos.role")}</div>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card className="border-border bg-card">
              <CardContent className="p-6">
                <div className="flex items-center mb-4">
                  {[...Array(5)].map((_, i) => (
                    <Star key={i} className="h-4 w-4 text-yellow-400 fill-current" />
                  ))}
                </div>
                <p className="text-muted-foreground mb-4">"{t("testimonials.ana")}"</p>
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center">
                    <span className="text-purple-600 dark:text-purple-400 font-semibold text-sm">AM</span>
                  </div>
                  <div>
                    <div className="font-semibold text-foreground">Ana Martínez</div>
                    <div className="text-sm text-muted-foreground">{t("testimonials.ana.role")}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-4xl mx-auto text-center">
          <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <Lightbulb className="h-8 w-8 text-blue-600 dark:text-blue-400" />
          </div>

          <h2 className="text-4xl font-bold text-foreground mb-4">{t("cta.title")}</h2>

          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">{t("cta.description")}</p>

          <Link href="/chat">
            <Button size="lg" className="text-lg px-8 py-4 bg-primary hover:bg-primary/90">
              {t("cta.button")}
            </Button>
          </Link>
        </div>
      </section>

      <SharedFooter />
      
      {/* Chat Widget */}
      <ChatWidget />
    </div>
  )
}
