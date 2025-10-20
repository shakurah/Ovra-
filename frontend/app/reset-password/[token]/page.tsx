"use client"

import { useState } from "react"
import { useRouter, useParams } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { toastService } from "@/lib/services"
import { useLanguage } from "@/contexts/language-context"

export default function ResetPasswordWithTokenPage() {
  const { t } = useLanguage()
  const router = useRouter()
  const { token } = useParams() || {}
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  if (!token) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
        <Card className="w-full max-w-md shadow-lg border-0">
          <CardHeader>
            <CardTitle className="text-2xl text-center">{t("auth.reset.invalid_link")}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-center mb-4">{t("auth.reset.invalid_token_message")}</p>
            <div className="flex gap-2">
              <Link href="/forgot-password" className="w-full">
                <Button className="w-full">{t("auth.reset.request_new")}</Button>
              </Link>
              <Link href="/" className="w-full">
                <Button variant="ghost" className="w-full">{t("common.return_home")}</Button>
              </Link>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const validatePasswords = () => {
    if (newPassword.length < 8) return t("auth.password.min_length")
    if (newPassword !== confirmPassword) return t("auth.password.mismatch")
    return ""
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    const validationError = validatePasswords()
    if (validationError) {
      setError(validationError)
      toastService.error(validationError)
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reset-password/${token}/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ new_password: newPassword }),
      })

      const data = await response.json()
      if (!response.ok) throw new Error(data.error || data.message || t("auth.reset.link_expired"))

      toastService.success(t("auth.reset.success"))
      router.push("/login")
    } catch (err: any) {
      setError(err.message || t("auth.reset.error"))
      toastService.error(err.message || t("auth.reset.error"))
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-2xl text-center">{t("auth.reset.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label>{t("auth.password.label")}</Label>
              <div className="relative">
                <Input
                  type={showPassword ? "text" : "password"}
                  placeholder={t("auth.password.placeholder")}
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  required
                  className="h-11 pr-10"
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? <EyeOff className="h-4 w-4 text-gray-400" /> : <Eye className="h-4 w-4 text-gray-400" />}
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-1">{t("auth.password.requirements")}</p>
            </div>

            <div>
              <Label>{t("auth.password.confirm_label")}</Label>
              <Input
                type="password"
                placeholder={t("auth.password.confirm_placeholder")}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="h-11"
              />
            </div>

            <Button type="submit" className="w-full h-11" disabled={isLoading}>
              {isLoading ? t("auth.reset.resetting") : t("auth.reset.submit")}
            </Button>
          </form>

          <p className="text-center text-sm text-gray-600 mt-6">
            {t("auth.reset.remember_password")}{" "}
            <Link href="/login" className="text-blue-600 hover:underline font-medium">
              {t("auth.login.submit")}
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  )
}