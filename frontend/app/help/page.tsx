"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import {
  HelpCircle,
  MessageSquare,
  CreditCard,
  Shield,
  Settings,
  BookOpen,
  ChevronRight,
} from "lucide-react"
import Link from "next/link"

export default function HelpPage() {
  const { t } = useLanguage()

  const categories = [
    {
      icon: MessageSquare,
      title: t("help.getting.started.title"),
      description: t("help.getting.started.description"),
      articles: [
        t("help.getting.started.article1"),
        t("help.getting.started.article2"),
        t("help.getting.started.article3"),
        t("help.getting.started.article4"),
      ]
    },
    {
      icon: CreditCard,
      title: t("help.billing.title"),
      description: t("help.billing.description"),
      articles: [
        t("help.billing.article1"),
        t("help.billing.article2"),
        t("help.billing.article3"),
        t("help.billing.article4"),
      ]
    },
    {
      icon: Shield,
      title: t("help.privacy.title"),
      description: t("help.privacy.description"),
      articles: [
        t("help.privacy.article1"),
        t("help.privacy.article2"),
        t("help.privacy.article3"),
        t("help.privacy.article4"),
      ]
    },
    {
      icon: Settings,
      title: t("help.account.title"),
      description: t("help.account.description"),
      articles: [
        t("help.account.article1"),
        t("help.account.article2"),
        t("help.account.article3"),
        t("help.account.article4"),
      ]
    },
  ]

  const popularArticles = [
    t("help.popular.article1"),
    t("help.popular.article2"),
    t("help.popular.article3"),
    t("help.popular.article4"),
    t("help.popular.article5"),
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <HelpCircle className="h-12 w-12 text-primary" />
            <h1 className="text-4xl md:text-6xl font-bold text-foreground">{t("help.title")}</h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("help.subtitle")}
          </p>
          
          {/* Search Bar */}
          <div className="max-w-2xl mx-auto">
            <div className="relative">
              <Search className="h-5 w-5 absolute left-4 top-1/2 transform -translate-y-1/2 text-muted-foreground" />
              <Input 
                placeholder={t("help.search.placeholder")} 
                className="pl-12 h-14 text-lg bg-card border-border"
              />
              <Button className="absolute right-2 top-2 h-10">
                {t("help.search")}
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Popular Articles */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground mb-2">{t("help.popular.title")}</h2>
            <p className="text-muted-foreground">{t("help.popular.subtitle")}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {popularArticles.map((article, index) => (
              <Card key={index} className="border-border bg-card hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <BookOpen className="h-5 w-5 text-primary" />
                      <span className="text-sm font-medium text-foreground">{article}</span>
                    </div>
                    <ChevronRight className="h-4 w-4 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Help Categories */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold text-foreground mb-4">{t("help.categories.title")}</h2>
            <p className="text-xl text-muted-foreground">{t("help.categories.subtitle")}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {categories.map((category, index) => (
              <Card key={index} className="border-border bg-card">
                <CardHeader>
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                      <category.icon className="h-5 w-5 text-primary" />
                    </div>
                    <div>
                      <CardTitle>{category.title}</CardTitle>
                      <CardDescription>{category.description}</CardDescription>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3">
                    {category.articles.map((article, articleIndex) => (
                      <li key={articleIndex}>
                        <div className="flex items-center justify-between p-2 rounded-lg hover:bg-muted/50 cursor-pointer transition-colors">
                          <span className="text-sm text-muted-foreground">{article}</span>
                          <ChevronRight className="h-4 w-4 text-muted-foreground" />
                        </div>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Contact Support */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Card className="border-border bg-card">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">{t("help.contact.title")}</CardTitle>
              <CardDescription className="text-lg">{t("help.contact.subtitle")}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card className="border-border bg-muted/30">
                  <CardContent className="p-4 text-center">
                    <MessageSquare className="h-8 w-8 text-primary mx-auto mb-2" />
                    <h3 className="font-semibold text-foreground mb-1">{t("help.contact.chat")}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{t("help.contact.chat.description")}</p>
                    <Button size="sm" className="w-full">
                      {t("help.contact.chat.button")}
                    </Button>
                  </CardContent>
                </Card>
                
                <Card className="border-border bg-muted/30">
                  <CardContent className="p-4 text-center">
                    <HelpCircle className="h-8 w-8 text-primary mx-auto mb-2" />
                    <h3 className="font-semibold text-foreground mb-1">{t("help.contact.email")}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{t("help.contact.email.description")}</p>
                    <Link href="/contact">
                      <Button variant="outline" size="sm" className="w-full">
                        {t("help.contact.email.button")}
                      </Button>
                    </Link>
                  </CardContent>
                </Card>
                
                <Card className="border-border bg-muted/30">
                  <CardContent className="p-4 text-center">
                    <BookOpen className="h-8 w-8 text-primary mx-auto mb-2" />
                    <h3 className="font-semibold text-foreground mb-1">{t("help.contact.guides")}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{t("help.contact.guides.description")}</p>
                    <Button variant="outline" size="sm" className="w-full">
                      {t("help.contact.guides.button")}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      <SharedFooter />
    </div>
  )
}
