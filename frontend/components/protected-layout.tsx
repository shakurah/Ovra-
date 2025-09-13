"use client"

import { useState, ReactNode } from "react"
import { ProtectedRoute } from "@/components/protected-route"
import { ProtectedSidebar, SidebarToggle } from "@/components/protected-sidebar"
import { ThemeToggle } from "@/components/theme-toggle"
import { LanguageToggle } from "@/components/language-toggle"
import { useLanguage } from "@/contexts/language-context"

interface ProtectedLayoutProps {
  children: ReactNode
  title?: string
  credits?: number
}

export function ProtectedLayout({ children, title, credits }: ProtectedLayoutProps) {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { t } = useLanguage()

  return (
    <ProtectedRoute>
      <div className="flex h-screen bg-background">
        {/* Sidebar */}
        <ProtectedSidebar 
          sidebarOpen={sidebarOpen} 
          setSidebarOpen={setSidebarOpen} 
          credits={credits}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <header className="bg-card border-b border-border px-4 py-3 flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <SidebarToggle onClick={() => setSidebarOpen(true)} />
              {title && (
                <h1 className="text-xl font-semibold text-foreground">{title}</h1>
              )}
            </div>
            <div className="flex items-center space-x-4">
              <LanguageToggle />
              <ThemeToggle />
            </div>
          </header>

          {/* Page Content */}
          <main className="flex-1 overflow-auto">
            {children}
          </main>
        </div>

        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}
      </div>
    </ProtectedRoute>
  )
}
