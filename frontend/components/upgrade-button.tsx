"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Dialog, DialogContent } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { useRouter } from "next/navigation"
import { useLanguage } from "@/contexts/language-context"
import { Star } from "lucide-react"

export function UpgradeButton() {
  const [isOpen, setIsOpen] = useState(false)
  const router = useRouter()
  const { t } = useLanguage()

  const plans = [
    {
      name: t("pricing.basic.name"),
      price: "9",
      credits: "50",
      popular: false,
      description: t("pricing.basic.description"),
    },
    {
      name: t("pricing.professional.name"),
      price: "29",
      credits: "200",
      popular: true,
      description: t("pricing.professional.description"),
    },
    {
      name: t("pricing.enterprise.name"),
      price: "69",
      credits: "500",
      popular: false,
      description: t("pricing.enterprise.description"),
    },
  ]

  const handlePlanSelect = (plan: string) => {
    router.push(`/payment?plan=${plan.toLowerCase()}`)
    setIsOpen(false)
  }

  return (
    <>
      <Button
        onClick={() => setIsOpen(true)}
        variant="outline"
        className="gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white hover:from-violet-700 hover:to-indigo-700 border-0"
      >
        <Star className="h-4 w-4" />
        {t("pricing.upgrade_button")}
      </Button>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <div className="grid gap-4">
            <div className="text-center mb-4">
              <h2 className="text-2xl font-bold">{t("pricing.dialog.title")}</h2>
              <p className="text-sm text-muted-foreground">
                {t("pricing.dialog.subtitle")}
              </p>
            </div>

            <div className="grid gap-4">
              {plans.map((plan) => (
                <div
                  key={plan.name}
                  className={`p-4 rounded-lg border ${
                    plan.popular
                      ? "ring-2 ring-primary border-primary"
                      : "border-border"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <h3 className="font-semibold">{plan.name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {plan.description}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold">€{plan.price}</div>
                      <Badge variant="secondary" className="bg-muted">
                        {plan.credits} {t("pricing.credits")}
                      </Badge>
                    </div>
                  </div>
                  <Button
                    onClick={() => handlePlanSelect(plan.name)}
                    className="w-full mt-2"
                    variant={plan.popular ? "default" : "outline"}
                  >
                    {t("pricing.select_plan")}
                  </Button>
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  )
}