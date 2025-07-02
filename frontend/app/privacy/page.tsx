"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { Shield } from "lucide-react"
import Link from "next/link"

export default function PrivacyPage() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold text-foreground">{t("privacy.title")}</h1>
          </div>
          <p className="text-muted-foreground">{t("privacy.last.updated")}: {t("privacy.date")}</p>
        </div>

        <div className="space-y-8">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.introduction.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.introduction.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.data.collection.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.data.collection.intro")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("privacy.data.collection.item1")}</li>
                <li>{t("privacy.data.collection.item2")}</li>
                <li>{t("privacy.data.collection.item3")}</li>
                <li>{t("privacy.data.collection.item4")}</li>
                <li>{t("privacy.data.collection.item5")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.data.usage.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.data.usage.intro")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("privacy.data.usage.item1")}</li>
                <li>{t("privacy.data.usage.item2")}</li>
                <li>{t("privacy.data.usage.item3")}</li>
                <li>{t("privacy.data.usage.item4")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.data.sharing.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.data.sharing.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.data.security.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.data.security.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.cookies.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.cookies.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.user.rights.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.user.rights.intro")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("privacy.user.rights.item1")}</li>
                <li>{t("privacy.user.rights.item2")}</li>
                <li>{t("privacy.user.rights.item3")}</li>
                <li>{t("privacy.user.rights.item4")}</li>
                <li>{t("privacy.user.rights.item5")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.data.retention.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.data.retention.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.international.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.international.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.changes.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.changes.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("privacy.contact.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("privacy.contact.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="font-medium">OVRA AI - Data Protection Officer</p>
                <p>Email: privacy@ovra-ai.com</p>
                <p>Address: Madrid, Spain</p>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <Link href="/">
            <Button>
              {t("privacy.back.home")}
            </Button>
          </Link>
        </div>
      </div>

      <SharedFooter />
    </div>
  )
}
