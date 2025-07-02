"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import { toastService } from "@/lib/services"
import {
  User,
  CreditCard,
  Shield,
  Bell,
  Save,
  Eye,
  EyeOff,
  Trash2,
  AlertTriangle,
} from "lucide-react"

function AccountPageContent() {
  const { t } = useLanguage()
  const [activeTab, setActiveTab] = useState("profile")
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)

  const [profileData, setProfileData] = useState({
    firstName: "María",
    lastName: "García",
    email: "maria.garcia@email.com",
    phone: "+34 600 123 456",
    company: "Estudio Creativo MG",
    profession: "Diseñadora Freelance",
  })

  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  })

  const [notifications, setNotifications] = useState({
    emailUpdates: true,
    creditAlerts: true,
    weeklyReports: false,
    marketingEmails: false,
  })

  const tabs = [
    { id: "profile", label: t("account.profile"), icon: User },
    { id: "billing", label: t("account.billing"), icon: CreditCard },
    { id: "security", label: t("account.security"), icon: Shield },
    { id: "notifications", label: t("account.notifications"), icon: Bell },
  ]

  const handleProfileSave = async () => {
    try {
      // TODO: Replace with actual API call
      // await userService.updateProfile(profileData)
      console.log("Profile saved:", profileData)
      toastService.success(t("account.profile.saved"))
    } catch (error) {
      toastService.handleApiError(error, t("account.profile.save.error"))
    }
  }

  const handlePasswordChange = async () => {
    if (passwordData.newPassword !== passwordData.confirmPassword) {
      toastService.error(t("account.password.mismatch"))
      return
    }

    if (passwordData.newPassword.length < 8) {
      toastService.error(t("account.password.too.short"))
      return
    }

    try {
      // TODO: Replace with actual API call
      // await userService.changePassword(passwordData)
      console.log("Password change requested")
      toastService.success(t("account.password.changed"))
      setPasswordData({ currentPassword: "", newPassword: "", confirmPassword: "" })
    } catch (error) {
      toastService.handleApiError(error, t("account.password.change.error"))
    }
  }

  return (
    <ProtectedLayout title={t("account.title")} credits={47}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("account.title")}</h1>
          <p className="text-muted-foreground">{t("account.subtitle")}</p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <nav className="space-y-2">
              {tabs.map((tab) => (
                <Button
                  key={tab.id}
                  variant={activeTab === tab.id ? "default" : "ghost"}
                  className="w-full justify-start"
                  onClick={() => setActiveTab(tab.id)}
                >
                  <tab.icon className="h-4 w-4 mr-2" />
                  {tab.label}
                </Button>
              ))}
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">
            {activeTab === "profile" && (
              <Card className="border-border bg-card">
                <CardHeader>
                  <CardTitle>{t("account.personal.info")}</CardTitle>
                  <CardDescription>Update your personal information and professional details</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">{t("account.first.name")}</Label>
                      <Input
                        id="firstName"
                        value={profileData.firstName}
                        onChange={(e) => setProfileData({ ...profileData, firstName: e.target.value })}
                        className="bg-background border-border"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">{t("account.last.name")}</Label>
                      <Input
                        id="lastName"
                        value={profileData.lastName}
                        onChange={(e) => setProfileData({ ...profileData, lastName: e.target.value })}
                        className="bg-background border-border"
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="email">{t("account.email")}</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileData.email}
                      onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="phone">{t("account.phone")}</Label>
                    <Input
                      id="phone"
                      value={profileData.phone}
                      onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="company">{t("account.company")}</Label>
                    <Input
                      id="company"
                      value={profileData.company}
                      onChange={(e) => setProfileData({ ...profileData, company: e.target.value })}
                      className="bg-background border-border"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="profession">{t("account.profession")}</Label>
                    <Input
                      id="profession"
                      value={profileData.profession}
                      onChange={(e) => setProfileData({ ...profileData, profession: e.target.value })}
                      className="bg-background border-border"
                    />
                  </div>

                  <Button onClick={handleProfileSave} className="w-full md:w-auto">
                    <Save className="h-4 w-4 mr-2" />
                    {t("account.save.changes")}
                  </Button>
                </CardContent>
              </Card>
            )}

            {activeTab === "billing" && (
              <div className="space-y-6">
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle>{t("credits.current.status")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between p-4 bg-muted/30 rounded-lg">
                      <div>
                        <p className="text-2xl font-bold text-foreground">47 créditos</p>
                        <p className="text-sm text-muted-foreground">de 200 créditos totales</p>
                      </div>
                      <Link href="/credits">
                        <Button>
                          <CreditCard className="h-4 w-4 mr-2" />
                          {t("credits.buy.credits")}
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle>{t("credits.billing.history")}</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {[
                        { date: "2024-01-15", amount: "€29.00", credits: "200", status: "Paid" },
                        { date: "2023-12-15", amount: "€29.00", credits: "200", status: "Paid" },
                        { date: "2023-11-15", amount: "€9.00", credits: "50", status: "Paid" },
                      ].map((invoice, index) => (
                        <div
                          key={index}
                          className="flex items-center justify-between p-3 border border-border rounded-lg"
                        >
                          <div>
                            <p className="font-medium text-foreground">{invoice.credits} créditos</p>
                            <p className="text-sm text-muted-foreground">{invoice.date}</p>
                          </div>
                          <div className="flex items-center space-x-3">
                            <span className="font-medium text-foreground">{invoice.amount}</span>
                            <Badge variant="outline" className="text-green-600 border-green-200">
                              {invoice.status}
                            </Badge>
                            <Button variant="outline" size="sm">
                              {t("credits.download")}
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "security" && (
              <div className="space-y-6">
                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle>{t("account.change.password")}</CardTitle>
                    <CardDescription>Update your password to keep your account secure</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="space-y-2">
                      <Label htmlFor="currentPassword">{t("account.current.password")}</Label>
                      <div className="relative">
                        <Input
                          id="currentPassword"
                          type={showCurrentPassword ? "text" : "password"}
                          value={passwordData.currentPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, currentPassword: e.target.value })}
                          className="bg-background border-border pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                        >
                          {showCurrentPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="newPassword">{t("account.new.password")}</Label>
                      <div className="relative">
                        <Input
                          id="newPassword"
                          type={showNewPassword ? "text" : "password"}
                          value={passwordData.newPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                          className="bg-background border-border pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowNewPassword(!showNewPassword)}
                        >
                          {showNewPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <div className="space-y-2">
                      <Label htmlFor="confirmPassword">{t("account.confirm.password")}</Label>
                      <div className="relative">
                        <Input
                          id="confirmPassword"
                          type={showConfirmPassword ? "text" : "password"}
                          value={passwordData.confirmPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                          className="bg-background border-border pr-10"
                        />
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                          onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                        >
                          {showConfirmPassword ? (
                            <EyeOff className="h-4 w-4 text-muted-foreground" />
                          ) : (
                            <Eye className="h-4 w-4 text-muted-foreground" />
                          )}
                        </Button>
                      </div>
                    </div>

                    <Button onClick={handlePasswordChange} className="w-full md:w-auto">
                      <Shield className="h-4 w-4 mr-2" />
                      {t("account.change.password")}
                    </Button>
                  </CardContent>
                </Card>

                <Card className="border-border bg-card">
                  <CardHeader>
                    <CardTitle>{t("account.two.factor")}</CardTitle>
                    <CardDescription>Add an extra layer of security to your account</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium text-foreground">Two-Factor Authentication</p>
                        <p className="text-sm text-muted-foreground">Secure your account with 2FA</p>
                      </div>
                      <Switch />
                    </div>
                  </CardContent>
                </Card>

                <Card className="border-border bg-card border-destructive/20">
                  <CardHeader>
                    <CardTitle className="text-destructive flex items-center">
                      <AlertTriangle className="h-5 w-5 mr-2" />
                      Danger Zone
                    </CardTitle>
                    <CardDescription>Permanently delete your account and all data</CardDescription>
                  </CardHeader>
                  <CardContent>
                    <Button variant="destructive" className="w-full md:w-auto">
                      <Trash2 className="h-4 w-4 mr-2" />
                      {t("account.delete.account")}
                    </Button>
                  </CardContent>
                </Card>
              </div>
            )}

            {activeTab === "notifications" && (
              <Card className="border-border bg-card">
                <CardHeader>
                  <CardTitle>{t("account.notifications")}</CardTitle>
                  <CardDescription>Manage your notification preferences</CardDescription>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">Email Updates</p>
                      <p className="text-sm text-muted-foreground">
                        Receive updates about new features and improvements
                      </p>
                    </div>
                    <Switch
                      checked={notifications.emailUpdates}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, emailUpdates: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">Credit Alerts</p>
                      <p className="text-sm text-muted-foreground">Get notified when your credits are running low</p>
                    </div>
                    <Switch
                      checked={notifications.creditAlerts}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, creditAlerts: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">Weekly Reports</p>
                      <p className="text-sm text-muted-foreground">Receive weekly usage and analytics reports</p>
                    </div>
                    <Switch
                      checked={notifications.weeklyReports}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, weeklyReports: checked })}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-foreground">Marketing Emails</p>
                      <p className="text-sm text-muted-foreground">Receive promotional emails and special offers</p>
                    </div>
                    <Switch
                      checked={notifications.marketingEmails}
                      onCheckedChange={(checked) => setNotifications({ ...notifications, marketingEmails: checked })}
                    />
                  </div>

                  <Button className="w-full md:w-auto">
                    <Save className="h-4 w-4 mr-2" />
                    {t("account.save.changes")}
                  </Button>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </div>
    </ProtectedLayout>
  )
}

export default function AccountPage() {
  return <AccountPageContent />
}
