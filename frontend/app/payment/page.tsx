"use client"

import type React from "react"

import { useState } from "react"
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

export default function PaymentPage() {
  const { t } = useLanguage()
  const router = useRouter()
  const [isProcessing, setIsProcessing] = useState(false)
  const [selectedPackage] = useState({
    id: "professional",
    name: "Paquete Profesional",
    credits: 200,
    price: 29,
  })

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

    // Simulate payment processing
    setTimeout(() => {
      setIsProcessing(false)
      // Redirect to success page or credits page
      router.push("/credits?payment=success")
    }, 3000)
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
                    <span className="font-medium text-foreground">{selectedPackage.name}</span>
                    <Badge className="bg-primary/10 text-primary">Popular</Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mb-3">{selectedPackage.credits} créditos</p>
                  <div className="flex items-center justify-between text-lg font-bold text-foreground">
                    <span>Total</span>
                    <span>€{selectedPackage.price}</span>
                  </div>
                </div>

                <div className="space-y-2 text-sm text-muted-foreground">
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Acceso inmediato a créditos</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Sin compromisos a largo plazo</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Soporte especializado</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Factura disponible</span>
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
                    <h4 className="font-medium text-blue-900 dark:text-blue-100 mb-1">Secure Payment</h4>
                    <p className="text-sm text-blue-800 dark:text-blue-200">
                      Your payment information is encrypted and secure. We use industry-standard SSL encryption to
                      protect your data.
                    </p>
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
                    {t("payment.complete.payment")} €{selectedPackage.price}
                  </>
                )}
              </Button>

              <div className="text-center text-sm text-muted-foreground">
                <p>
                  By completing this purchase, you agree to our{" "}
                  <Link href="/terms" className="text-primary hover:underline">
                    Terms of Service
                  </Link>{" "}
                  and{" "}
                  <Link href="/privacy" className="text-primary hover:underline">
                    Privacy Policy
                  </Link>
                  .
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  )
}
