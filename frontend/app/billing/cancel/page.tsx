"use client"

import React from "react"

export default function BillingCancelPage() {
  return (
    <div className="p-6 max-w-3xl mx-auto text-center">
      <h1 className="text-2xl font-semibold mb-4">Pago cancelado</h1>
      <p className="mb-6">No se ha procesado ningún pago. Puedes intentar de nuevo.</p>
      <a href="/billing" className="btn">Volver a Billing</a>
    </div>
  )
}