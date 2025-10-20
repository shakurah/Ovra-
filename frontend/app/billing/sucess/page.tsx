"use client"

import React from "react"

export default function BillingSuccessPage() {
  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-2xl font-semibold mb-4">Pago completado</h1>
      <p className="mb-4">Gracias. Su pago fue procesado correctamente. Actualice su perfil o espere unos segundos para que el webhook aplique los créditos.</p>
      <p className="text-sm text-muted-foreground">Si no ve la actualización, abra el panel de administración o contacte soporte.</p>
    </div>
  )
}