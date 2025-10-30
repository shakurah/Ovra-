"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { useAuth } from "@/contexts/auth-context"
import { useLanguage } from "@/contexts/language-context"
import { toastService } from "@/lib/services"
import { getValidationErrors } from "@/utils/api"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const { login, isLoading } = useAuth()
  const { t } = useLanguage()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setFieldErrors({})

    try {
      await login({ email, password })
      toastService.success(t("auth.login.success"))
    } catch (err) {
      const validationErrors = getValidationErrors(err)
      if (Object.keys(validationErrors).length > 0) {
        setFieldErrors(validationErrors)
      } else {
        const errorMessage = err instanceof Error ? err.message : t("auth.error.login.failed")
        setError(errorMessage)
        toastService.error(errorMessage)
      }
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 dark:from-slate-900  to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <img src="/artisting-logo.png" alt="ARTISTING" className="h-12 w-auto artisting-logo" />
          </Link>
          <p className="text-gray-600 dark:text-white mt-2">{t("auth.tagline")}</p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">{t("auth.login.title")}</CardTitle>
            <CardDescription className="text-center">
              {t("auth.login.subtitle")}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {error && (
              <Alert variant="destructive" className="mb-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">{t("auth.login.email")}</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className={`h-11 ${fieldErrors.email ? 'border-red-500' : ''} focus:ring-white focus:border-black`}
                />
                {fieldErrors.email && (
                  <p className="text-sm text-red-500">{fieldErrors.email}</p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">{t("auth.login.password")}</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Tu contraseña"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className={`h-11 pr-10 ${fieldErrors.password ? 'border-red-500' : ''} focus:ring-white focus:border-black`}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </Button>
                </div>
                {fieldErrors.password && (
                  <p className="text-sm text-red-500">{fieldErrors.password}</p>
                )}
              </div>

              <div className="flex items-center justify-between">
                <Link href="/forgot-password" className="text-sm text-black-600 hover:underline">
                  {t("auth.login.forgot.password")}
                </Link>
              </div>

              <Button 
                type="submit" 
                className="w-full h-11 bg-black text-white hover:bg-[#D4AF37] hover:text-black transition-colors" 
                disabled={isLoading}
              >
                {isLoading ? `${t("auth.login.submit")}...` : t("auth.login.submit")}
              </Button>
            </form>

            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
              </div>
            </div>

            <p className="text-center text-sm text-gray-600 mt-6">
              {t("auth.login.no.account")}{" "}
              <Link href="/signup" className="text-black-600 hover:underline font-medium">
                {t("auth.login.signup.link")}
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
