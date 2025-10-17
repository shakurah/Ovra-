"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import Link from "next/link"
import { toastService } from "@/lib/services"

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState("")

  const isValidEmail = (value: string) => {
    return /\S+@\S+\.\S+/.test(value)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!isValidEmail(email)) {
      toastService.error("Por favor ingresa una dirección de correo electrónico válida.")
      return
    }

    setIsLoading(true)
    setMessage("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/forgot-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()
      if (!response.ok) {
        throw new Error(data.error || data.message || "Algo salió mal")
      }

      toastService.success("Si existe una cuenta con ese correo electrónico, se ha enviado un enlace de restablecimiento.")
      setMessage("Si existe una cuenta con ese correo electrónico, revisa tu correo para el enlace de restablecimiento.")
      setEmail("")
    } catch (err: any) {
      toastService.error(err.message || "Error al enviar el enlace de restablecimiento.")
      setMessage(err.message || "Error al enviar el enlace de restablecimiento.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Olvidé mi contraseña</CardTitle>
          <CardDescription className="text-center">
            Ingresa tu correo electrónico para recibir un enlace de restablecimiento de contraseña.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>Email</Label>
              <Input
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                aria-invalid={!isValidEmail(email) && email.length > 0}
              />
            </div>

            <Button type="submit" disabled={isLoading || !isValidEmail(email)} className="w-full">
              {isLoading ? "Enviando..." : "Enviar enlace de restablecimiento"}
            </Button>

            {message && (
              <p className="text-center text-sm mt-3 text-gray-600">{message}</p>
            )}
          </form>

          <p className="text-center text-sm text-gray-600 mt-6">
            ¿Recuerdas tu contraseña?{" "}
            <Link href="/login" className="text-black-600 hover:underline font-medium">
              Iniciar sesión
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
