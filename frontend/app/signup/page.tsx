"use client"

import React, { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Eye, EyeOff, CheckCircle, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { useAuth } from "@/contexts/auth-context"
import { useLanguage } from "@/contexts/language-context"
import { toastService } from "@/lib/services"
import { getValidationErrors } from "@/utils/api"

export default function SignupPage() {
  const router = useRouter()
  const [firstName, setFirstName] = useState("")
  const [lastName, setLastName] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [confirm, setConfirm] = useState("")
  const [accepted, setAccepted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const { register, isLoading } = useAuth()
  const { t } = useLanguage()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    if (!accepted) {
      setError("Debes aceptar los términos y condiciones.")
      return
    }
    if (password.length < 8) {
      setError("La contraseña debe tener al menos 8 caracteres.")
      return
    }
    if (password !== confirm) {
      setError("Las contraseñas no coinciden.")
      return
    }

    setLoading(true)
    try {
      await register({
        email,
        first_name: firstName,
        last_name: lastName,
        password,
        confirm_password: confirm,
        agree_to_terms: accepted
      })
      toastService.success(t("auth.signup.success"))
      router.push('/login')
    } catch (err) {
      const validationErrors = getValidationErrors(err)
      if (Object.keys(validationErrors).length > 0) {
        setError(validationErrors)
      } else {
        const errorMessage = err instanceof Error ? err.message : t("auth.error.create.account")
        setError(errorMessage)
        toastService.error(errorMessage)
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 dark:from-slate-900 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <img src="/ARTISTING.png" alt="ARTISTING" className="h-12 w-auto artisting-logo" />
          </Link>
          <p className="text-gray-600 dark:text-white mt-2">{t("auth.signup.subtitle")}</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">{t("auth.signup.title")}</CardTitle>
            <CardDescription className="text-center">{t("auth.signup.subtitle")}</CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="firstName">{t("auth.signup.first.name")}</Label>
                  <Input
                    id="firstName"
                    name="firstName"
                    placeholder="Juan"
                    value={firstName}
                    onChange={(e) => setFirstName(e.target.value)}
                    required
                    className="h-11 pr-10"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lastName">{t("auth.signup.last.name")}</Label>
                  <Input
                    id="lastName"
                    name="lastName"
                    placeholder="García"
                    value={lastName}
                    onChange={(e) => setLastName(e.target.value)}
                    required
                    className="h-11 pr-10"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">{t("auth.signup.email")}</Label>
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="h-11 pr-10"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.signup.password")}</Label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  placeholder="Mínimo 8 caracteres"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  className="h-11 pr-10"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="confirmPassword">{t("auth.signup.confirm.password")}</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  placeholder="Repite tu contraseña"
                  value={confirm}
                  onChange={(e) => setConfirm(e.target.value)}
                  required
                  className="h-11 pr-10"
                />
              </div>

              <div className="flex items-center space-x-2">
                <Checkbox
                  id="terms"
                  checked={accepted}
                  onCheckedChange={(checked) => setAccepted(checked as boolean)}
                />
                <Label htmlFor="terms" className="text-sm text-gray-600">
                  <a
                    href="https://artisting.es/condiciones"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline"
                  >
                    {t("auth.signup.terms")}
                  </a>
                </Label>
              </div>


              <Button 
                type="submit" 
                className="w-full h-11 bg-black text-white hover:bg-[#D4AF37] hover:text-black transition-colors" 
                disabled={loading}
              >
                {loading ? "Creando..." : t("auth.signup.submit")}
              </Button>
            </form>

            
            <p className="text-center text-sm text-gray-600 mt-6">
              {t("auth.signup.have.account")}{" "}
              <Link href="/login" className="text-black-600 hover:underline font-medium">
                {t("auth.signup.login.link")}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}