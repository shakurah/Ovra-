"use client"

import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useLanguage } from "@/contexts/language-context"

export default function ResetPasswordRootPage() {
  const { t } = useLanguage()

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md shadow-lg border-0">
        <CardHeader>
          <CardTitle className="text-2xl text-center">{t("auth.reset.title")}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-center mb-4">
            {t("auth.reset.token_required")} <code>/reset-password/&lt;token&gt;</code>
          </p>
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
