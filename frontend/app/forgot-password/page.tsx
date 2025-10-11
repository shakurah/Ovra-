"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Eye, EyeOff, Scale, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"
import { toastService } from "@/lib/services"

export default function ForgotAndResetPassword() {
  const router = useRouter()

  // State for step management
  const [step, setStep] = useState(1) // 1 = Email entry, 2 = New password entry

  // Email form states
  const [email, setEmail] = useState("")
  const [emailStatus, setEmailStatus] = useState(null) // loading | success | error
  const [emailMessage, setEmailMessage] = useState("")

  // Password form states
  const [newPassword, setNewPassword] = useState("")
  const [confirmPassword, setConfirmPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")

  // 🔹 Step 1: Handle email submission
  const handleEmailSubmit = async (e) => {
    e.preventDefault()
    setEmailStatus("loading")
    setEmailMessage("")

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/forgot-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (response.ok) {
        setEmailStatus("success")
        setEmailMessage("Email verified! Enter your new password below.")
        toastService.success("Email verified successfully!")
        setStep(2) // Move to password step
      } else {
        setEmailStatus("error")
        setEmailMessage(data.error || "Email not found.")
        toastService.error(data.error || "Email not found.")
      }
    } catch (err) {
      setEmailStatus("error")
      setEmailMessage("Network error. Please try again.")
      toastService.error("Network error. Please try again.")
    }
  }

  // 🔹 Step 2: Handle password reset
  const handlePasswordSubmit = async (e) => {
    e.preventDefault()
    setError("")

    if (newPassword !== confirmPassword) {
      setError("Passwords do not match.")
      toastService.error("Passwords do not match.")
      return
    }

    setIsLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/reset-password/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, new_password: newPassword }),
      })

      const data = await response.json()

      if (!response.ok) throw new Error(data.error || "Failed to reset password.")

      toastService.success("Password reset successfully! You can now log in.")
      router.push("/login")
    } catch (err) {
      setError(err.message)
      toastService.error(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 dark:from-slate-900 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2">
            <Scale className="h-10 w-10 text-black-600" />
            <span className="text-3xl font-bold text-gray-900 dark:text-white">ARTISTING</span>
          </Link>
          <p className="text-gray-600 dark:text-white mt-2">
            {step === 1 ? "Recover your password" : "Reset your password securely"}
          </p>
        </div>

        <Card className="shadow-xl border-0">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl font-bold text-center">
              {step === 1 ? "Forgot Password" : "Reset Password"}
            </CardTitle>
            <CardDescription className="text-center">
              {step === 1
                ? "Enter your email address to verify your account."
                : "Enter and confirm your new password below."}
            </CardDescription>
          </CardHeader>

          <CardContent>
            {/* Step 1: Email Form */}
            {step === 1 && (
              <form onSubmit={handleEmailSubmit} className="space-y-4">
                <div>
                  <Label>Email Address</Label>
                  <Input
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="h-11"
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full h-11"
                  disabled={emailStatus === "loading"}
                >
                  {emailStatus === "loading" ? "Checking..." : "Continue"}
                </Button>

                {emailMessage && (
                  <p
                    className={`text-center text-sm mt-3 ${
                      emailStatus === "error" ? "text-red-600" : "text-green-600"
                    }`}
                  >
                    {emailMessage}
                  </p>
                )}
              </form>
            )}

            {/* Step 2: Password Reset Form */}
            {step === 2 && (
              <>
                {error && (
                  <Alert variant="destructive" className="mb-4">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{error}</AlertDescription>
                  </Alert>
                )}

                <form onSubmit={handlePasswordSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Label htmlFor="newPassword">New Password</Label>
                    <div className="relative">
                      <Input
                        id="newPassword"
                        type={showPassword ? "text" : "password"}
                        placeholder="Enter new password"
                        value={newPassword}
                        onChange={(e) => setNewPassword(e.target.value)}
                        required
                        className="h-11 pr-10"
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
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="confirmPassword">Confirm Password</Label>
                    <Input
                      id="confirmPassword"
                      type="password"
                      placeholder="Re-enter new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      required
                      className="h-11"
                    />
                  </div>

                  <Button type="submit" className="w-full h-11" disabled={isLoading}>
                    {isLoading ? "Resetting..." : "Reset Password"}
                  </Button>
                </form>
              </>
            )}

            <p className="text-center text-sm text-gray-600 mt-6">
              Remember your password?{" "}
              <Link href="/login" className="text-black-600 hover:underline font-medium">
                Go back to login
              </Link>
            </p>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
