"use client"

import { Badge } from "@/components/ui/badge"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Switch } from "@/components/ui/switch"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { useTheme } from "next-themes"
import { toastService } from "@/lib/services"
import {
  SettingsIcon,
  Globe,
  Palette,
  Bell,
  Shield,
  Download,
  Trash2,
  AlertTriangle,
} from "lucide-react"

function SettingsPageContent() {
  const { t, language, setLanguage } = useLanguage()
  const { theme, setTheme } = useTheme()
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    pushNotifications: false,
    weeklyReports: true,
    marketingEmails: false,
  })

  const handleDataExport = async () => {
    try {
      // TODO: Replace with actual API call
      // const data = await userService.exportData()
      toastService.success(t("settings.data.export.success"))
    } catch (error) {
      toastService.handleApiError(error, t("settings.data.export.error"))
    }
  }

  const handleDataDelete = async () => {
    if (!confirm(t("settings.data.delete.confirm"))) {
      return
    }

    try {
      // TODO: Replace with actual API call
      // await userService.deleteAllData()
      toastService.success(t("settings.data.delete.success"))
    } catch (error) {
      toastService.handleApiError(error, t("settings.data.delete.error"))
    }
  }

  const handleAccountDelete = async () => {
    if (!confirm(t("settings.account.delete.confirm"))) {
      return
    }

    try {
      // TODO: Replace with actual API call
      // await userService.deleteAccount()
      toastService.success(t("settings.account.delete.success"))
      // Redirect to login or home page
    } catch (error) {
      toastService.handleApiError(error, t("settings.account.delete.error"))
    }
  }

  return (
    <ProtectedLayout title={t("settings.title")} credits={47}>
      <div className="p-6 max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("settings.title")}</h1>
          <p className="text-muted-foreground">Customize your OVRA AI experience</p>
        </div>

        <div className="space-y-6">
          {/* General Settings */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <SettingsIcon className="h-5 w-5 text-primary" />
                <span>{t("settings.general")}</span>
              </CardTitle>
              <CardDescription>Basic application preferences</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Globe className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{t("settings.language")}</p>
                    <p className="text-sm text-muted-foreground">Choose your preferred language</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant={language === "en" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setLanguage("en")}
                  >
                    🇺🇸 English
                  </Button>
                  <Button
                    variant={language === "es" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setLanguage("es")}
                  >
                    🇪🇸 Español
                  </Button>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <Palette className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{t("settings.theme")}</p>
                    <p className="text-sm text-muted-foreground">Choose light or dark mode</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Button
                    variant={theme === "light" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTheme("light")}
                  >
                    ☀️ Light
                  </Button>
                  <Button variant={theme === "dark" ? "default" : "outline"} size="sm" onClick={() => setTheme("dark")}>
                    🌙 Dark
                  </Button>
                  <Button
                    variant={theme === "system" ? "default" : "outline"}
                    size="sm"
                    onClick={() => setTheme("system")}
                  >
                    💻 System
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Notifications */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Bell className="h-5 w-5 text-primary" />
                <span>{t("settings.notifications")}</span>
              </CardTitle>
              <CardDescription>Manage how you receive notifications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Email Notifications</p>
                  <p className="text-sm text-muted-foreground">Receive important updates via email</p>
                </div>
                <Switch
                  checked={notifications.emailNotifications}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, emailNotifications: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Push Notifications</p>
                  <p className="text-sm text-muted-foreground">Get notified in your browser</p>
                </div>
                <Switch
                  checked={notifications.pushNotifications}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, pushNotifications: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Weekly Reports</p>
                  <p className="text-sm text-muted-foreground">Receive weekly usage summaries</p>
                </div>
                <Switch
                  checked={notifications.weeklyReports}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, weeklyReports: checked })}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-foreground">Marketing Emails</p>
                  <p className="text-sm text-muted-foreground">Receive promotional content and offers</p>
                </div>
                <Switch
                  checked={notifications.marketingEmails}
                  onCheckedChange={(checked) => setNotifications({ ...notifications, marketingEmails: checked })}
                />
              </div>
            </CardContent>
          </Card>

          {/* Privacy & Data */}
          <Card className="border-border bg-card">
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Shield className="h-5 w-5 text-primary" />
                <span>{t("settings.privacy")}</span>
              </CardTitle>
              <CardDescription>Control your data and privacy settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Download className="h-5 w-5 text-muted-foreground" />
                  <div>
                    <p className="font-medium text-foreground">{t("settings.data.export")}</p>
                    <p className="text-sm text-muted-foreground">Download all your data in JSON format</p>
                  </div>
                </div>
                <Button variant="outline" size="sm" onClick={handleDataExport}>
                  <Download className="h-4 w-4 mr-2" />
                  Export
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
                <div className="flex items-center space-x-3">
                  <Trash2 className="h-5 w-5 text-destructive" />
                  <div>
                    <p className="font-medium text-foreground">{t("settings.data.delete")}</p>
                    <p className="text-sm text-muted-foreground">Permanently delete all your data</p>
                  </div>
                </div>
                <Button variant="destructive" size="sm" onClick={handleDataDelete}>
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Danger Zone */}
          <Card className="border-destructive/20 bg-card">
            <CardHeader>
              <CardTitle className="text-destructive flex items-center space-x-2">
                <AlertTriangle className="h-5 w-5" />
                <span>Danger Zone</span>
              </CardTitle>
              <CardDescription>Irreversible and destructive actions</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="p-4 bg-destructive/5 border border-destructive/20 rounded-lg">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-foreground">Delete Account</p>
                    <p className="text-sm text-muted-foreground">
                      Permanently delete your account and all associated data
                    </p>
                  </div>
                  <Button variant="destructive" onClick={handleAccountDelete}>
                    <Trash2 className="h-4 w-4 mr-2" />
                    Delete Account
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </ProtectedLayout>
  )
}

export default function SettingsPage() {
  return <SettingsPageContent />
}
