"use client"

import { useEffect, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ProtectedLayout } from "@/components/protected-layout"
import { toastService } from "@/lib/services"
import { useLanguage } from "@/contexts/language-context"
import { CreditCard, Zap, Clock, CheckCircle, Sparkles } from "lucide-react"

function CreditsPageContent() {
  const { t, language } = useLanguage()
  const router = useRouter()
  const searchParams = useSearchParams()
  const sessionId = searchParams.get("session_id")
  const [currentCredits, setCurrentCredits] = useState(47)
  const [totalCredits] = useState(200)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  const [status, setStatus] = useState<"pending" | "success" | "failed" | "none">("none")

  useEffect(() => {
    if (!sessionId) return
    setStatus("pending")
    fetch(`/api/billing/verify-checkout-session/?session_id=${encodeURIComponent(sessionId)}`, {
      credentials: "include",
    })
      .then(r => {
        if (!r.ok) throw new Error("verify failed")
        return r.json()
      })
      .then(data => {
        if (data && (data.payment_status === "paid" || (data.subscription && data.subscription.status === "active"))) {
          setStatus("success")
          // TODO: Fetch fresh credits from your backend and update state
          // setCurrentCredits(newCredits)
        } else {
          setStatus("failed")
        }
      })
      .catch(() => setStatus("failed"))
  }, [sessionId])

  const handlePurchase = async () => {
    if (!selectedPlan) {
      toastService.error(t("credits.select.plan"))
      return
    }

    const selectedPackage = creditPackages.find(pkg => pkg.id === selectedPlan)
    if (!selectedPackage) return

    try {
      // TODO: Replace with actual payment API call
      // await paymentService.purchaseCredits(selectedPlan)
      toastService.success(t("credits.purchase.success"))
      setSelectedPlan(null)
    } catch (error) {
      toastService.handleApiError(error, t("credits.purchase.error"))
    }
  }

  const creditPackages = [
    {
      id: "basic",
      name: "Paquete Básico",
      credits: 50,
      price: 9,
      popular: false,
      description: "Perfecto para consultas ocasionales",
    },
    {
      id: "professional",
      name: "Paquete Profesional",
      credits: 200,
      price: 29,
      popular: true,
      description: "Ideal para profesionales activos",
    },
    {
      id: "enterprise",
      name: "Paquete Empresa",
      credits: 500,
      price: 69,
      popular: false,
      description: "Para equipos y empresas",
    },
  ]

  const recentUsage = [
    {
      date: "2024-01-15",
      question: "¿Cómo facturar servicios artísticos con IVA?",
      credits: 1,
      time: "14:30",
    },
    {
      date: "2024-01-15",
      question: "Deducciones IRPF para material artístico",
      credits: 1,
      time: "12:15",
    },
    {
      date: "2024-01-14",
      question: "Tributación de derechos de autor",
      credits: 1,
      time: "16:45",
    },
    {
      date: "2024-01-14",
      question: "Obligaciones fiscales autónomo cultural",
      credits: 1,
      time: "10:20",
    },
    {
      date: "2024-01-13",
      question: "Régimen especial del criterio de caja",
      credits: 1,
      time: "15:30",
    },
  ]

  return (
    <ProtectedLayout title={t("credits.title")} credits={currentCredits}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{t("credits.title")}</h1>
          <p className="text-gray-600">{t("credits.subtitle")}</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Current Credits Status */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CreditCard className="h-5 w-5 text-black-600" />
                  <span>{t("credits.current.status")}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold text-gray-900">{currentCredits}</span>
                    <span className="text-sm text-gray-500">de {totalCredits} créditos</span>
                  </div>
                  <Progress value={(currentCredits / totalCredits) * 100} className="h-3" />
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>{t("credits.used")}: {totalCredits - currentCredits}</span>
                    <span>{t("credits.renewal")}: 15 Feb 2024</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Usage History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-black-600" />
                  <span>{t("credits.history.title")}</span>
                </CardTitle>
                <CardDescription>{t("credits.history.subtitle")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentUsage.map((usage, index) => (
                    <div key={index} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 mb-1">{usage.question}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>{usage.date}</span>
                          <span>{usage.time}</span>
                        </div>
                      </div>
                      <Badge variant="outline" className="ml-4">
                        -{usage.credits} crédito
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Credit Packages */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-black-600" />
                  <span>{t("credits.purchase.title")}</span>
                </CardTitle>
                <CardDescription>{t("credits.purchase.subtitle")}</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {creditPackages.map(pkg => (
                  <div
                    key={pkg.id}
                    className={`relative p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedPlan === pkg.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    } ${pkg.popular ? "ring-2 ring-blue-500" : ""}`}
                    onClick={() => setSelectedPlan(pkg.id)}
                  >
                    {pkg.popular && <Badge className="absolute -top-2 left-4 bg-blue-600">{t("badge.popular")}</Badge>}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">{t(`pricing.${pkg.id}.name`)}</h3>
                        <span className="text-2xl font-bold text-black-600">
                          {new Intl.NumberFormat(language === 'es' ? 'es-ES' : 'en-US', { 
                            style: 'currency', 
                            currency: 'EUR' 
                          }).format(pkg.price)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600">{t(`pricing.${pkg.id}.description`)}</p>
                      <div className="flex items-center space-x-2">
                        <Badge variant="secondary">{pkg.credits} {t("pricing.credits")}</Badge>
                        <span className="text-xs text-gray-500">
                          {new Intl.NumberFormat(language === 'es' ? 'es-ES' : 'en-US', { 
                            style: 'currency', 
                            currency: 'EUR' 
                          }).format(pkg.price / pkg.credits)} {t("credits.per.credit")}
                        </span>
                      </div>
                    </div>
                  </div>
                ))}

                <Button 
                  className="w-full mt-4 bg-primary text-primary-foreground hover:bg-primary/90" 
                  disabled={!selectedPlan} 
                  size="lg" 
                  onClick={() => router.push("/pricing")}
                >
                  <Sparkles className="h-4 w-4 mr-2" />
                  {t("credits.upgrade.button")}
                </Button>
              </CardContent>
            </Card>

            {/* Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">{t("credits.benefits.title")}</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t("credits.benefits.legal")}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t("credits.benefits.updated")}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t("credits.benefits.support")}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t("credits.benefits.history")}</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t("credits.benefits.no_commitment")}</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Payment Status Handling */}
        <div className="mt-8">
          {status === "pending" && (
            <div className="flex items-center justify-center py-4">
              <svg className="animate-spin h-5 w-5 mr-3 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4zm16 0a8 8 0 01-8 8v-8h8z"></path>
              </svg>
              <span className="text-gray-700">{t("credits.verifying.payment")}</span>
            </div>
          )}
          {status === "success" && (
            <div className="p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
              <div className="flex items-center">
                <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <path
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m2-2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span className="font-semibold">{t("credits.payment.success.title")}</span>
              </div>
              <div className="mt-2 text-sm">
                <p>{t("credits.payment.success.message")}</p>
                {/* Optionally show updated credits info */}
                {/* <p>{t("credits.current.credits")}: {currentCredits}</p> */}
              </div>
            </div>
          )}
          {status === "failed" && (
            <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
              <div className="flex items-center">
                <svg className="h-5 w-5 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <path
                    stroke="currentColor"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m2-2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span className="font-semibold">{t("credits.payment.failed.title")}</span>
              </div>
              <div className="mt-2 text-sm">
                <p>{t("credits.payment.failed.message")}</p>
                <p>
                  {t("credits.support.contact")}{" "}
                  <a href="mailto:support@example.com" className="text-blue-600 hover:underline">
                    support@example.com
                  </a>
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </ProtectedLayout>
  )
}

export default function CreditsPage() {
  return <CreditsPageContent />
}
