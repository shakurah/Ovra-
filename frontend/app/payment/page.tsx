"use client"

import { useSearchParams } from "next/navigation"
import { useEffect, useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { CreditCard, Shield, Lock, CheckCircle } from "lucide-react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { useAuth } from "@/contexts/auth-context" // <-- add (adjust path if different)

// map plan slugs to real Stripe price IDs (set these in frontend/.env)
const PRICE_ID_MAP: Record<string,string> = {
  basic: process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC_ID ?? "",
  professional: process.env.NEXT_PUBLIC_STRIPE_PRICE_PROFESSIONAL_ID ?? "",
  enterprise: process.env.NEXT_PUBLIC_STRIPE_PRICE_ENTERPRISE_ID ?? "",
}

export default function PaymentPage() {
  const { t, language } = useLanguage()
  const auth = useAuth?.() // adjust if your hook is named differently (useAuth / useAuthContext)
  // prefer token from AuthContext, fallback to common localStorage keys
  const ctxToken = auth?.token || auth?.accessToken || null
  const token = typeof window !== "undefined"
    ? (ctxToken || localStorage.getItem("token") || localStorage.getItem("authToken") || localStorage.getItem("access") || localStorage.getItem("access_token"))
    : ctxToken
  const searchParams = useSearchParams()
  const planId = searchParams.get("plan")
  const priceParam = searchParams.get("price")
  const durationParam = searchParams.get("duration")

  // default to Enterprise when landing directly on /payment
  const [selectedPlan, setSelectedPlan] = useState(() => ({
    id: "enterprise",
    name: t("pricing.enterprise.name"),
    credits: 500,
    price: Number(process.env.NEXT_PUBLIC_DEFAULT_ENTERPRISE_PRICE ?? 69),
  }))

  useEffect(() => {
    // Get plan details based on planId
    const plans = {
      basic: {
        id: "basic",
        name: t("pricing.basic.name"),
        credits: 50,
        price: Number(priceParam ?? 9),
      },
      professional: {
        id: "professional",
        name: t("pricing.professional.name"),
        credits: 200,
        price: Number(priceParam ?? 29),
      },
      enterprise: {
        id: "enterprise",
        name: t("pricing.enterprise.name"),
        credits: 500,
        price: Number(priceParam ?? 69),
      },
    }

    if (planId && plans[planId as keyof typeof plans]) {
      const p = plans[planId as keyof typeof plans]
      // override price if explicit query param provided
      if (priceParam) p.price = Number(priceParam)
      setSelectedPlan(p)
    } else if (priceParam) {
      // fallback: create a generic plan when only price provided
      setSelectedPlan({ id: "custom", name: t("pricing.title"), credits: 0, price: Number(priceParam) })
    }
    // else: leave the default enterprise already set in initial state
  }, [planId, t])

  const router = useRouter()
  const [isProcessing, setIsProcessing] = useState(false)
  const [paymentData, setPaymentData] = useState({
    cardNumber: "",
    expiryDate: "",
    cvc: "",
    cardholderName: "",
    country: "Spain",
    postalCode: "",
  })

  const handlePayment = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsProcessing(true)

    try {
      // quick mapping (replace keys with your real Stripe price IDs or fetch from backend)
      const PRICE_DISPLAY_MAP: Record<string, number> = {
        "price_basic_id": 0.0,
        "price_plus_id": 2.99,
        "price_advanced_id": 9.99,
      }

      // resolve the real Stripe price id using map, fallback to any provided priceId field or env
      const candidate = (selectedPlan as any)?.priceId || selectedPlan.id || process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC_ID
      let resolvedPriceId = PRICE_ID_MAP[selectedPlan.id] || candidate

      const displayAmount = selectedPlan?.price ?? 0
      // send numeric amount (cents) to backend — backend will create a Stripe Price if needed
      const amountCents = Math.round((displayAmount || 0) * 100)
      const body: Record<string, any> = {
        amount: amountCents, // integer cents (e.g. 29 -> 2900)
        currency: "eur",
        description: `${selectedPlan.name} plan`,
        success_url: `${window.location.origin}/credits?session_id={CHECKOUT_SESSION_ID}`,
        cancel_url: `${window.location.origin}/pricing`,
      }
      // optional: include an existing price_id if selectedPlan provides one
      if ((selectedPlan as any)?.priceId && String((selectedPlan as any).priceId).startsWith("price_")) {
        body.price_id = (selectedPlan as any).priceId
      }

      // define headers (include Authorization if token available)
      const headers: Record<string,string> = { "Content-Type": "application/json" }
      if (token) {
        const scheme = token.startsWith("eyJ") ? "Bearer" : "Token"
        headers["Authorization"] = `${scheme} ${token}`
      }
      const url = `${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1"}/billing/create-checkout-session/`
       console.log("payment token (raw):", token, "resolvedPriceId:", resolvedPriceId, "backend url:", url)
      console.log("sending Authorization:", headers["Authorization"])
      const res = await fetch(url, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      })

      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'create session failed' }))
        throw new Error(err.error || 'Failed to create checkout session')
      }

      const data = await res.json()
      if (data.url) {
        // redirect to Stripe Checkout
        window.location.href = data.url
        return
      }

      throw new Error('No checkout url returned')
    } catch (err) {
      console.error('Checkout error', err)
      // show an error message in UI (use t(...) keys)
      setIsProcessing(false)
    } finally {
      setIsProcessing(false)
    }
  }

  const formatCardNumber = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")
    const matches = v.match(/\d{4,16}/g)
    const match = (matches && matches[0]) || ""
    const parts = []

    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4))
    }

    if (parts.length) {
      return parts.join(" ")
    } else {
      return v
    }
  }

  const formatExpiryDate = (value: string) => {
    const v = value.replace(/\s+/g, "").replace(/[^0-9]/gi, "")
    if (v.length >= 2) {
      return v.substring(0, 2) + "/" + v.substring(2, 4)
    }
    return v
  }

  return (
    <ProtectedLayout title={t("payment.title")} credits={47}>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("payment.title")}</h1>
          <p className="text-muted-foreground">{t("payment.subtitle")}</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Order Summary */}
          <div className="lg:col-span-1">
            <Card className="border-border bg-card sticky top-8">
              <CardHeader>
                <CardTitle>{t("payment.order.summary")}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="p-4 bg-muted/30 rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-foreground">{selectedPlan.name}</span>
                    {selectedPlan.id !== 'custom' && <Badge className="bg-primary/10 text-primary">{t('pricing.popular')}</Badge>}
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{selectedPlan.credits} {t('pricing.credits')}</p>
                  <div className="flex items-center justify-between text-lg font-bold text-foreground">
                    <span>{t('payment.order.total')}</span>
                    <span>{new Intl.NumberFormat(language === 'es' ? 'es-ES' : 'en-US', { style: 'currency', currency: 'EUR' }).format(selectedPlan.price)}</span>
                  </div>
                </div>

                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t('payment.features.immediate')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t('payment.features.no_commitment')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t('payment.features.support')}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>{t('payment.features.invoice')}</span>
                  </div>
                </div>

                <div className="pt-4 border-t border-border">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Lock className="h-4 w-4" />
                    <span>Pago seguro con cifrado SSL</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Payment Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handlePayment} className="space-y-6">
              <Card className="border-border bg-card">
                <CardHeader>
                  <CardTitle className="flex items-center space-x-2">
                    <CreditCard className="h-5 w-5 text-primary" />
                    <span>{t("payment.payment.method")}</span>
                  </CardTitle>
                  <CardDescription>Enter your payment details securely</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="cardNumber">{t("payment.card.number")}</Label>
                    <Input
                      id="cardNumber"
                      placeholder="1234 5678 9012 3456"
                      value={paymentData.cardNumber}
                      onChange={(e) =>
                        setPaymentData({
                          ...paymentData,
                          cardNumber: formatCardNumber(e.target.value),
                        })
                      }
                      maxLength={19}
                      className="bg-background border-border"
                      required
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="expiryDate">{t("payment.expiry")}</Label>
                      <Input
                        id="expiryDate"
                        placeholder="MM/YY"
                        value={paymentData.expiryDate}
                        onChange={(e) =>
                          setPaymentData({
                            ...paymentData,
                            expiryDate: formatExpiryDate(e.target.value),
                          })
                        }
                        maxLength={5}
                        className="bg-background border-border"
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="cvc">{t("payment.cvc")}</Label>
                      <Input
                        id="cvc"
                        placeholder="123"
                        value={paymentData.cvc}
                        onChange={(e) =>
                          setPaymentData({
                            ...paymentData,
                            cvc: e.target.value.replace(/\D/g, "").substring(0, 4),
                          })
                        }
                        maxLength={4}
                        className="bg-background border-border"
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="cardholderName">{t("payment.cardholder")}</Label>
                    <Input
                      id="cardholderName"
                      placeholder="María García"
                      value={paymentData.cardholderName}
                      onChange={(e) => setPaymentData({ ...paymentData, cardholderName: e.target.value })}
                      className="bg-background border-border"
                      required
                    />
                  </div>
                </CardContent>
              </Card>

              <Card className="border-border bg-card">
                <CardHeader>
                  <CardTitle>{t("payment.billing.address")}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="country">{t("payment.country")}</Label>
                    <Input
                      id="country"
                      value={paymentData.country}
                      onChange={(e) => setPaymentData({ ...paymentData, country: e.target.value })}
                      className="bg-background border-border"
                      required
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="postalCode">{t("payment.postal.code")}</Label>
                    <Input
                      id="postalCode"
                      placeholder="28001"
                      value={paymentData.postalCode}
                      onChange={(e) => setPaymentData({ ...paymentData, postalCode: e.target.value })}
                      className="bg-background border-border"
                      required
                    />
                  </div>
                </CardContent>
              </Card>

              {/* Security Notice */}
              <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                <div className="flex items-start space-x-3">
                  <Shield className="h-5 w-5 text-black-600 dark:text-blue-400 mt-0.5" />
                  <div>
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-1">{t('payment.security.notice.title')}</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">{t('payment.security.notice.desc')}</p>
                  </div>
                </div>
              </div>

              <Button type="submit" size="lg" className="w-full" disabled={isProcessing}>
                {isProcessing ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    {t("payment.processing")}
                  </>
                ) : (
                  <>
                    <Lock className="h-4 w-4 mr-2" />
                    {t("payment.complete.payment")} €{selectedPlan.price}
                  </>
                )}
              </Button>

              <div className="text-center text-sm text-muted-foreground">
                <p>
                  {t('payment.security.notice.desc')}
                </p>
                <p className="mt-2">
                  <Link href="/terms" className="text-primary hover:underline">{t('terms.title')}</Link>{' '}
                  &middot;{' '}
                  <Link href="/privacy" className="text-primary hover:underline">{t('privacy.title')}</Link>
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  )
}
