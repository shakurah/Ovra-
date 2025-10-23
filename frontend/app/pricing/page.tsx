"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import {
  CheckCircle,
  X,
  Zap,
  Star,
  CreditCard,
  Users,
  Shield,
} from "lucide-react"
import Link from "next/link"

export default function PricingPage() {
  const { t } = useLanguage()

  const plans = [
    {
      name: t("pricing.basic.name"),
      price: "9",
      credits: "50",
      popular: false,
      description: t("pricing.basic.description"),
      features: [
        t("pricing.basic.feature1"),
        t("pricing.basic.feature2"),
        t("pricing.basic.feature3"),
        t("pricing.basic.feature4"),
      ],
      limitations: [
        t("pricing.basic.limitation1"),
        t("pricing.basic.limitation2"),
      ]
    },
    {
      name: t("pricing.professional.name"),
      price: "29",
      credits: "200",
      popular: true,
      description: t("pricing.professional.description"),
      features: [
        t("pricing.professional.feature1"),
        t("pricing.professional.feature2"),
        t("pricing.professional.feature3"),
        t("pricing.professional.feature4"),
        t("pricing.professional.feature5"),
        t("pricing.professional.feature6"),
      ],
      limitations: []
    },
    {
      name: t("pricing.enterprise.name"),
      price: "69",
      credits: "500",
      popular: false,
      description: t("pricing.enterprise.description"),
      features: [
        t("pricing.enterprise.feature1"),
        t("pricing.enterprise.feature2"),
        t("pricing.enterprise.feature3"),
        t("pricing.enterprise.feature4"),
        t("pricing.enterprise.feature5"),
        t("pricing.enterprise.feature6"),
        t("pricing.enterprise.feature7"),
      ],
      limitations: []
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="mb-4 bg-primary/10 text-primary border-primary/20">
            {t("pricing.badge")}
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            {t("pricing.title")}
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("pricing.subtitle")}
          </p>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, index) => (
              <Card 
                key={index} 
                className={`border-border bg-card relative ${
                  plan.popular ? 'ring-2 ring-primary shadow-lg scale-105' : ''
                }`}
              >
                {plan.popular && (
                  <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-primary">
                    <Star className="h-3 w-3 mr-1" />
                    {t("pricing.popular")}
                  </Badge>
                )}
                
                <CardHeader className="text-center pb-8">
                  <CardTitle className="text-2xl font-bold text-foreground">{plan.name}</CardTitle>
                  <CardDescription className="text-muted-foreground mb-4">
                    {plan.description}
                  </CardDescription>
                  <div className="text-center">
                    <span className="text-4xl font-bold text-foreground">€{plan.price}</span>
                    <span className="text-muted-foreground">/{t("pricing.month")}</span>
                  </div>
                  <div className="text-center mt-2">
                    <Badge variant="secondary" className="bg-muted">
                      {plan.credits} {t("pricing.credits")}
                    </Badge>
                  </div>
                </CardHeader>
                
                <CardContent className="space-y-6">
                  <div>
                    <h4 className="font-semibold text-foreground mb-3">{t("pricing.included")}</h4>
                    <ul className="space-y-2">
                      {plan.features.map((feature, featureIndex) => (
                        <li key={featureIndex} className="flex items-start space-x-2">
                          <CheckCircle className="h-4 w-4 text-primary mt-0.5 flex-shrink-0" />
                          <span className="text-sm text-muted-foreground">{feature}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  {plan.limitations.length > 0 && (
                    <div>
                      <h4 className="font-semibold text-muted-foreground mb-3">{t("pricing.limitations")}</h4>
                      <ul className="space-y-2">
                        {plan.limitations.map((limitation, limitationIndex) => (
                          <li key={limitationIndex} className="flex items-start space-x-2">
                            <X className="h-4 w-4 text-muted-foreground mt-0.5 flex-shrink-0" />
                            <span className="text-sm text-muted-foreground">{limitation}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                  
                  <Link href={`/payment?plan=${encodeURIComponent(plan.name === t("pricing.basic.name") ? 'basic' : plan.name === t("pricing.professional.name") ? 'professional' : 'enterprise')}&price=${plan.price}&duration=monthly`} className="block">
                    <Button 
                      className="w-full bg-primary text-primary-foreground hover:bg-primary/90"
                      size="lg"
                    >
                      <CreditCard className="h-4 w-4 mr-2" />
                      {t("pricing.upgrade.button")}
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-4xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">
              {t("pricing.faq.title")}
            </h2>
            <p className="text-xl text-muted-foreground">
              {t("pricing.faq.subtitle")}
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-lg">{t("pricing.faq.q1")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{t("pricing.faq.a1")}</p>
              </CardContent>
            </Card>
            
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-lg">{t("pricing.faq.q2")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{t("pricing.faq.a2")}</p>
              </CardContent>
            </Card>
            
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-lg">{t("pricing.faq.q3")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{t("pricing.faq.a3")}</p>
              </CardContent>
            </Card>
            
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="text-lg">{t("pricing.faq.q4")}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-muted-foreground">{t("pricing.faq.a4")}</p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      <SharedFooter />
    </div>
  )
}
