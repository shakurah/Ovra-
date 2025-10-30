"use client"

import Link from 'next/link'
import { Scale, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LanguageToggle } from '@/components/language-toggle'
import { ThemeToggle } from '@/components/theme-toggle'
import { useAuth } from '@/contexts/auth-context'
import { useLanguage } from '@/contexts/language-context'
import { UpgradeButton } from '@/components/upgrade-button'

export function SharedHeader() {
  const { isAuthenticated, user } = useAuth()
  const { t } = useLanguage()

  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <Link href="/">
              <img src="/artisting-logo.png" alt="ARTISTING" className="h-20 w-50 artisting-logo" />
            </Link>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden md:flex items-center space-x-3">
              <LanguageToggle />
              <ThemeToggle />
              {!isAuthenticated && (
                <>
                  <Link href="/login">
                    <Button variant="ghost" size="sm" className="text-muted-foreground">
                      <User className="h-4 w-4 mr-1" />
                      {t("nav.signin")}
                    </Button>
                  </Link>
                  <Link href="/signup">
                    <Button size="sm" className="bg-primary hover:bg-primary/90">
                      {t("nav.signup")}
                    </Button>
                  </Link>
                </>
              )}
              {isAuthenticated && (
                <>
                  <Link href="/chat">
                    <Button size="sm" className="bg-primary hover:bg-primary/90">
                      {t("nav.chat")}
                    </Button>
                  </Link>
                  <UpgradeButton />
                </>
              )}
            </div>

            {/* Mobile menu - simplified for authenticated users */}
            <div className="md:hidden flex items-center space-x-2">
              <LanguageToggle />
              <ThemeToggle />
              {!isAuthenticated && (
                <Link href="/signup">
                  <Button size="sm" className="bg-primary hover:bg-primary/90">
                    {t("nav.signup")}
                  </Button>
                </Link>
              )}
              {isAuthenticated && (
                <>
                  <Link href="/chat">
                    <Button size="sm" className="bg-primary hover:bg-primary/90">
                      {t("nav.chat")}
                    </Button>
                  </Link>
                  <UpgradeButton />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
