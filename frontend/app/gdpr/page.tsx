"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { Shield, CheckCircle } from "lucide-react"
import Link from "next/link"

export default function GDPRPage() {
  const { t } = useLanguage()

  const rights = [
    {
      title: t("gdpr.right.access.title"),
      description: t("gdpr.right.access.description"),
      action: t("gdpr.right.access.action")
    },
    {
      title: t("gdpr.right.rectification.title"),
      description: t("gdpr.right.rectification.description"),
      action: t("gdpr.right.rectification.action")
    },
    {
      title: t("gdpr.right.erasure.title"),
      description: t("gdpr.right.erasure.description"),
      action: t("gdpr.right.erasure.action")
    },
    {
      title: t("gdpr.right.portability.title"),
      description: t("gdpr.right.portability.description"),
      action: t("gdpr.right.portability.action")
    },
    {
      title: t("gdpr.right.restriction.title"),
      description: t("gdpr.right.restriction.description"),
      action: t("gdpr.right.restriction.action")
    },
    {
      title: t("gdpr.right.objection.title"),
      description: t("gdpr.right.objection.description"),
      action: t("gdpr.right.objection.action")
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Content */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="mb-8">
          <div className="flex items-center space-x-3 mb-4">
            <Shield className="h-8 w-8 text-primary" />
            <h1 className="text-3xl font-bold text-foreground">{t("gdpr.title")}</h1>
          </div>
          <p className="text-muted-foreground">{t("gdpr.subtitle")}</p>
        </div>

        <div className="space-y-8">
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.what.is.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.what.is.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.our.commitment.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.our.commitment.content")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("gdpr.commitment.item1")}</li>
                <li>{t("gdpr.commitment.item2")}</li>
                <li>{t("gdpr.commitment.item3")}</li>
                <li>{t("gdpr.commitment.item4")}</li>
              </ul>
            </CardContent>
          </Card>

          <div className="space-y-6">
            <h2 className="text-2xl font-bold text-foreground">{t("gdpr.your.rights.title")}</h2>
            <p className="text-muted-foreground">{t("gdpr.your.rights.subtitle")}</p>
            
            {rights.map((right, index) => (
              <Card key={index} className="border-border bg-card">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CheckCircle className="h-5 w-5 text-primary" />
                    <span>{right.title}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <p className="text-muted-foreground">{right.description}</p>
                  <div className="p-3 bg-muted rounded-lg">
                    <p className="text-sm font-medium text-foreground">{t("gdpr.how.to.exercise")}</p>
                    <p className="text-sm text-muted-foreground mt-1">{right.action}</p>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.legal.basis.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.legal.basis.content")}</p>
              <ul className="list-disc pl-6 space-y-2 mt-4">
                <li>{t("gdpr.legal.basis.item1")}</li>
                <li>{t("gdpr.legal.basis.item2")}</li>
                <li>{t("gdpr.legal.basis.item3")}</li>
                <li>{t("gdpr.legal.basis.item4")}</li>
              </ul>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.data.transfers.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.data.transfers.content")}</p>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.complaints.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.complaints.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="font-medium">{t("gdpr.supervisory.authority")}</p>
                <p className="text-sm mt-2">Agencia Española de Protección de Datos (AEPD)</p>
                <p className="text-sm">Website: www.aepd.es</p>
                <p className="text-sm">Phone: +34 901 100 099</p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle>{t("gdpr.contact.dpo.title")}</CardTitle>
            </CardHeader>
            <CardContent className="prose prose-sm max-w-none text-muted-foreground">
              <p>{t("gdpr.contact.dpo.content")}</p>
              <div className="mt-4 p-4 bg-muted rounded-lg">
                <p className="font-medium">OVRA AI - Data Protection Officer</p>
                <p>Email: dpo@ovra-ai.com</p>
                <p>Address: Madrid, Spain</p>
                <p className="text-sm mt-2 text-muted-foreground">
                  {t("gdpr.response.time")}
                </p>
              </div>
            </CardContent>
          </Card>

          <Card className="border-border bg-card bg-primary/5 border-primary/20">
            <CardHeader>
              <CardTitle className="text-primary">{t("gdpr.exercise.rights.title")}</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-muted-foreground">{t("gdpr.exercise.rights.content")}</p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Button className="flex-1">
                  {t("gdpr.contact.us")}
                </Button>
                <Link href="/privacy" className="flex-1">
                  <Button variant="outline" className="w-full">
                    {t("gdpr.privacy.policy")}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="mt-12 text-center">
          <Link href="/">
            <Button>
              {t("gdpr.back.home")}
            </Button>
          </Link>
        </div>
      </div>

      <SharedFooter />
    </div>
  )
}
