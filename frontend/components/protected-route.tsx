"use client"

import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/auth-context'
import { useLanguage } from '@/contexts/language-context'
import { Card, CardContent } from '@/components/ui/card'
import { Scale } from 'lucide-react'

interface ProtectedRouteProps {
  children: React.ReactNode
  redirectTo?: string
}

export function ProtectedRoute({ children, redirectTo = '/login' }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const { t } = useLanguage()
  const router = useRouter()

  useEffect(() => {
    // Only redirect if we're done loading AND not authenticated
    if (!isLoading && !isAuthenticated) {
      console.log('ProtectedRoute: Redirecting to login - isLoading:', isLoading, 'isAuthenticated:', isAuthenticated)
      router.push(redirectTo)
    }
  }, [isAuthenticated, isLoading, router, redirectTo])

  // Show loading state while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="flex flex-col items-center justify-center p-8">
            <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mb-4">
              <Scale className="h-6 w-6 text-primary animate-pulse" />
            </div>
            <h2 className="text-lg font-semibold text-foreground mb-2">
              {t('auth.verifying_access', 'Verifying access...')}
            </h2>
            <p className="text-sm text-muted-foreground text-center">
              {t('auth.please_wait_session', 'Please wait while we verify your session')}
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}
