"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useLanguage } from "@/contexts/language-context"
import { useAuth } from "@/contexts/auth-context"
import { Scale, Menu, CreditCard, LogOut, MessageSquare, History, Settings, UserCircle, HelpCircle, BarChart3, Receipt, Activity } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"

interface ProtectedSidebarProps {
  sidebarOpen: boolean
  setSidebarOpen: (open: boolean) => void
  credits?: number
}

export function ProtectedSidebar({ sidebarOpen, setSidebarOpen, credits = 47 }: ProtectedSidebarProps) {
  const { t } = useLanguage()
  const { logout } = useAuth()
  const pathname = usePathname()

  const navigationItems = [
    {
      href: "/chat",
      icon: MessageSquare,
      label: t("chat.sidebar.chat"),
      key: "chat"
    },
    {
      href: "/credits",
      icon: CreditCard,
      label: t("chat.sidebar.credits"),
      key: "credits"
    },
    {
      href: "/history",
      icon: History,
      label: t("chat.sidebar.history"),
      key: "history"
    },
    {
      href: "/account",
      icon: UserCircle,
      label: t("chat.sidebar.account"),
      key: "account"
    },
    {
      href: "/settings",
      icon: Settings,
      label: t("chat.sidebar.settings"),
      key: "settings"
    },
    {
      href: "/help",
      icon: HelpCircle,
      label: t("chat.sidebar.help"),
      key: "help"
    },
    {
      href: "/analytics",
      icon: BarChart3,
      label: t("chat.sidebar.analytics"),
      key: "analytics"
    },
    {
      href: "/payment",
      icon: Receipt,
      label: t("chat.sidebar.payment"),
      key: "payment"
    },
    {
      href: "/status",
      icon: Activity,
      label: t("chat.sidebar.status"),
      key: "status"
    }
  ]

  const isActive = (href: string) => pathname === href

  return (
    <div
      className={`${sidebarOpen ? "translate-x-0" : "-translate-x-full"} fixed inset-y-0 left-0 z-50 w-64 bg-card shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 border-r border-border`}
    >
      <div className="flex items-center justify-between p-4 border-b border-border">
        <Link href="/" className="flex items-center space-x-2">
          <Scale className="h-8 w-8 text-primary" />
          <span className="text-xl font-bold text-foreground">Ovra AI</span>
        </Link>
        <Button variant="ghost" size="sm" className="lg:hidden" onClick={() => setSidebarOpen(false)}>
          ×
        </Button>
      </div>

      <div className="p-4">
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-muted-foreground">{t("chat.credits.remaining")}</span>
            <Badge variant="secondary" className="bg-primary/10 text-primary">
              {credits}
            </Badge>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${(credits / 50) * 100}%` }}
            ></div>
          </div>
        </div>

        <nav className="space-y-1">
          {navigationItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.href)
            
            return (
              <Link
                key={item.key}
                href={item.href}
                className={`flex items-center space-x-3 px-3 py-2 rounded-lg transition-colors ${
                  active
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                }`}
              >
                <Icon className="h-5 w-5" />
                <span>{item.label}</span>
              </Link>
            )
          })}
        </nav>
      </div>

      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-border">
        <Button
          variant="ghost"
          className="w-full justify-start text-muted-foreground hover:text-foreground"
          onClick={logout}
        >
          <LogOut className="h-5 w-5 mr-3" />
          {t("chat.sidebar.logout")}
        </Button>
      </div>
    </div>
  )
}

// Mobile sidebar toggle button component
export function SidebarToggle({ onClick }: { onClick: () => void }) {
  return (
    <Button variant="ghost" size="sm" className="lg:hidden" onClick={onClick}>
      <Menu className="h-5 w-5" />
    </Button>
  )
}
