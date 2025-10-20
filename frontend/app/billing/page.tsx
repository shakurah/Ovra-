"use client"

import React, { useState } from "react"
import { createCheckoutSession } from "@/lib/services/billing.service"

const PRICES = {
  basic: process.env.NEXT_PUBLIC_STRIPE_PRICE_BASIC || "",
  plus: process.env.NEXT_PUBLIC_STRIPE_PRICE_PLUS || "",
  advanced: process.env.NEXT_PUBLIC_STRIPE_PRICE_ADVANCED || ""
}

export default function BillingPage() {
  const [loading, setLoading] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleSubscribe = async (priceId: string, tierName: string) => {
    setError(null)
    setLoading(tierName)
    try {
      const json = await createCheckoutSession(priceId)
      if (json?.url) {
        // redirect to Stripe Checkout
        window.location.href = json.url
      } else {
        throw new Error("No checkout URL returned")
      }
    } catch (err: any) {
      console.error("createCheckoutSession error", err)
      setError(err?.message || "Failed to start checkout")
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <h1 className="text-2xl font-semibold mb-6">Planes y Suscripciones</h1>
      {error && <div className="mb-4 text-sm text-red-600">{error}</div>}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-lg font-medium">Basic</h2>
          <p className="text-sm text-muted-foreground mt-2">X consultas / mes</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => handleSubscribe(PRICES.basic, "basic")}
            disabled={!PRICES.basic || loading !== null}
          >
            {loading === "basic" ? "Redirigiendo..." : "Suscribirse Basic"}
          </button>
        </div>

        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-lg font-medium">Plus</h2>
          <p className="text-sm text-muted-foreground mt-2">Y consultas / mes</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => handleSubscribe(PRICES.plus, "plus")}
            disabled={!PRICES.plus || loading !== null}
          >
            {loading === "plus" ? "Redirigiendo..." : "Suscribirse Plus"}
          </button>
        </div>

        <div className="p-6 border rounded-lg shadow-sm">
          <h2 className="text-lg font-medium">Advanced</h2>
          <p className="text-sm text-muted-foreground mt-2">Z consultas / mes</p>
          <button
            className="mt-4 btn btn-primary"
            onClick={() => handleSubscribe(PRICES.advanced, "advanced")}
            disabled={!PRICES.advanced || loading !== null}
          >
            {loading === "advanced" ? "Redirigiendo..." : "Suscribirse Advanced"}
          </button>
        </div>
      </div>
      <p className="text-xs text-muted-foreground mt-6">
        Nota: si no ves un plan activo, revisa las variables NEXT_PUBLIC_STRIPE_PRICE_*
      </p>
    </div>
  )
}