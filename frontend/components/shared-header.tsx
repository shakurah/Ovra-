"use client"

import Link from 'next/link'
import { Scale, User } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { LanguageToggle } from '@/components/language-toggle'
import { ThemeToggle } from '@/components/theme-toggle'
import { useAuth } from '@/contexts/auth-context'
import { useLanguage } from '@/contexts/language-context'

export function SharedHeader() {
  const { isAuthenticated, user } = useAuth()
  const { t } = useLanguage()

  return (
    <nav className="bg-card border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <Scale className="h-5 w-5 text-primary-foreground" />
            </div>
            <Link href="/">
              <span className="text-xl font-bold text-foreground hover:text-primary transition-colors">
                OVRA AI
              </span>
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
                <Link href="/chat">
                  <Button size="sm" className="bg-primary hover:bg-primary/90">
                    {t("nav.chat")}
                  </Button>
                </Link>
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
                <Link href="/chat">
                  <Button size="sm" className="bg-primary hover:bg-primary/90">
                    {t("nav.chat")}
                  </Button>
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </nav>
  )
}
