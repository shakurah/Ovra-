"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"

export default function ResetPasswordRootPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-2xl text-center">Reset Password</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center mb-4">
            This page requires a reset token. Use the link you received by email (it should look like <code>/reset-password/&lt;token&gt;</code>).
          </p>
          <div className="flex gap-2">
            <Link href="/forgot-password" className="w-full">
              <Button className="w-full">Request new reset link</Button>
            </Link>
            <Link href="/" className="w-full">
              <Button variant="ghost" className="w-full">Return home</Button>
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
