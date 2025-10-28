"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { FileText } from "lucide-react"
import Link from "next/link"

export default function TermsPage() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <FileText className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold text-foreground">{t("terms.title")}</h1>
          </div>
          <p className="text-muted-foreground">{t("terms.last.updated")}: {t("terms.date")}</p>
        </div>

        <div className="space-y-8">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.acceptance.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.acceptance.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.description.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.description.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.user.obligations.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.user.obligations.intro")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("terms.user.obligations.item1")}</li>
                <li>{t("terms.user.obligations.item2")}</li>
                <li>{t("terms.user.obligations.item3")}</li>
                <li>{t("terms.user.obligations.item4")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.intellectual.property.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.intellectual.property.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.privacy.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.privacy.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.payment.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.payment.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.limitation.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.limitation.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.termination.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.termination.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.changes.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.changes.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("terms.contact.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("terms.contact.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="font-medium artisting-logo">ARTISTING</p>
                <p>Email: legal@ovra-ai.com</p>
                <p>Address: Madrid, Spain</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <Link href="/">
            <Button>
              {t("terms.back.home")}
            </Button>
          </Link>
        </div>
      </div>

      <SharedFooter />
    </div>
  )
}
