"use client"

import { Button } from "@/components/ui/button"
import { useRouter } from "next/navigation"
import { useLanguage } from "@/contexts/language-context"
import { Star } from "lucide-react"

export function UpgradeButton() {
  const router = useRouter()
  const { t } = useLanguage()

  return (
    <Button
      onClick={() => router.push("/pricing")}
      variant="ghost"
      className="gap-2 bg-gradient-to-r from-[#D4AF37] to-[#b8922a] text-white hover:from-[#c99f2f] hover:to-[#9a7a20] border-0 btn-hover"
    >
      <Star className="h-4 w-4" />
      {t("pricing.upgrade.button")}
    </Button>
  )
}