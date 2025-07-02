"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import {
  MessageSquare,
  Shield,
  Zap,
  BookOpen,
  Search,
  FileText,
  Clock,
  Globe,
  CheckCircle,
  Star,
  Target,
  Users,
} from "lucide-react"
import Link from "next/link"

export default function FeaturesPage() {
  const { t } = useLanguage()

  const features = [
    {
      icon: MessageSquare,
      title: t("features.ai.chat.title"),
      description: t("features.ai.chat.description"),
      benefits: [
        t("features.ai.chat.benefit1"),
        t("features.ai.chat.benefit2"),
        t("features.ai.chat.benefit3"),
      ]
    },
    {
      icon: BookOpen,
      title: t("features.legal.database.title"),
      description: t("features.legal.database.description"),
      benefits: [
        t("features.legal.database.benefit1"),
        t("features.legal.database.benefit2"),
        t("features.legal.database.benefit3"),
      ]
    },
    {
      icon: Shield,
      title: t("features.accuracy.title"),
      description: t("features.accuracy.description"),
      benefits: [
        t("features.accuracy.benefit1"),
        t("features.accuracy.benefit2"),
        t("features.accuracy.benefit3"),
      ]
    },
    {
      icon: Zap,
      title: t("features.speed.title"),
      description: t("features.speed.description"),
      benefits: [
        t("features.speed.benefit1"),
        t("features.speed.benefit2"),
        t("features.speed.benefit3"),
      ]
    },
    {
      icon: Globe,
      title: t("features.multilingual.title"),
      description: t("features.multilingual.description"),
      benefits: [
        t("features.multilingual.benefit1"),
        t("features.multilingual.benefit2"),
        t("features.multilingual.benefit3"),
      ]
    },
    {
      icon: Users,
      title: t("features.specialized.title"),
      description: t("features.specialized.description"),
      benefits: [
        t("features.specialized.benefit1"),
        t("features.specialized.benefit2"),
        t("features.specialized.benefit3"),
      ]
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-4 bg-primary/10 text-primary border-primary/20">
            {t("features.badge")}
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            {t("features.title")}
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("features.subtitle")}
          </p>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, index) => (
              <Card key={index} className="border-border bg-card hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mb-4">
                    <feature.icon className="h-6 w-6 text-primary" />
                  </div>
                  <CardTitle className="text-foreground">{feature.title}</CardTitle>
                  <CardDescription className="text-muted-foreground">
                    {feature.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {feature.benefits.map((benefit, benefitIndex) => (
                      <li key={benefitIndex} className="flex items-start space-x-2">
                        <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-muted-foreground">{benefit}</span>
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-6">
            {t("features.cta.title")}
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            {t("features.cta.description")}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="w-full sm:w-auto">
                {t("features.cta.start")}
              </Button>
            </Link>
            <Link href="/pricing">
              <Button variant="outline" size="lg" className="w-full sm:w-auto">
                {t("features.cta.pricing")}
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <SharedFooter />
    </div>
  )
}
