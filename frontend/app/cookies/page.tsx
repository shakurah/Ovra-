"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { Cookie } from "lucide-react"
import Link from "next/link"

export default function CookiesPage() {
  const { t } = useLanguage()

  const cookieTypes = [
    {
      name: t("cookies.essential.name"),
      description: t("cookies.essential.description"),
      duration: t("cookies.essential.duration"),
      required: true,
      examples: [
        t("cookies.essential.example1"),
        t("cookies.essential.example2"),
        t("cookies.essential.example3"),
      ]
    },
    {
      name: t("cookies.analytics.name"),
      description: t("cookies.analytics.description"),
      duration: t("cookies.analytics.duration"),
      required: false,
      examples: [
        t("cookies.analytics.example1"),
        t("cookies.analytics.example2"),
        t("cookies.analytics.example3"),
      ]
    },
    {
      name: t("cookies.functional.name"),
      description: t("cookies.functional.description"),
      duration: t("cookies.functional.duration"),
      required: false,
      examples: [
        t("cookies.functional.example1"),
        t("cookies.functional.example2"),
        t("cookies.functional.example3"),
      ]
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <Cookie className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold text-foreground">{t("cookies.title")}</h1>
          </div>
          <p className="text-muted-foreground">{t("cookies.last.updated")}: {t("cookies.date")}</p>
        </div>

        <div className="space-y-8">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.what.are.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.what.are.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.how.we.use.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.how.we.use.content")}</p>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-foreground">{t("cookies.types.title")}</h2>
            
            {cookieTypes.map((cookieType, index) => (
              <Card key={index} className="border-border bg-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                      <span>{cookieType.name}</span>
                      {cookieType.required && (
                        <Badge variant="secondary" className="bg-primary/10 text-primary">
                          {t("cookies.required")}
                        </Badge>
                      )}
                    </CardTitle>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">{cookieType.description}</p>
                  
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">{t("cookies.duration")}</h4>
                    <p className="text-sm text-muted-foreground">{cookieType.duration}</p>
                  </div>
                  
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">{t("cookies.examples")}</h4>
                    <ul className="list-disc pl-6 space-y-1">
                      {cookieType.examples.map((example, exampleIndex) => (
                        <li key={exampleIndex} className="text-sm text-muted-foreground">
                          {example}
                        </li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.third.party.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.third.party.content")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("cookies.third.party.item1")}</li>
                <li>{t("cookies.third.party.item2")}</li>
                <li>{t("cookies.third.party.item3")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.manage.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.manage.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <h4 className="font-semibold text-foreground mb-2">{t("cookies.browser.settings")}</h4>
                <ul className="list-disc pl-6 space-y-1 text-sm">
                  <li>{t("cookies.browser.chrome")}</li>
                  <li>{t("cookies.browser.firefox")}</li>
                  <li>{t("cookies.browser.safari")}</li>
                  <li>{t("cookies.browser.edge")}</li>
                </ul>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.consent.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.consent.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.updates.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.updates.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("cookies.contact.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("cookies.contact.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="font-medium">OVRA AI</p>
                <p>Email: privacy@ovra-ai.com</p>
                <p>Address: Madrid, Spain</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <Link href="/">
            <Button>
              {t("cookies.back.home")}
            </Button>
          </Link>
        </div>
      </div>

      <SharedFooter />
    </div>
  )
}
