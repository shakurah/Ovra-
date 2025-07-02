"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import { toastService } from "@/lib/services"
import {
  Mail,
  Phone,
  MapPin,
  Clock,
  Send,
  MessageSquare,
  HelpCircle,
  Bug,
  Lightbulb,
} from "lucide-react"
import Link from "next/link"

export default function ContactPage() {
  const { t } = useLanguage()
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    category: "",
    message: "",
  })

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Basic validation
    if (!formData.name || !formData.email || !formData.message) {
      toastService.error(t("contact.form.validation.required"))
      return
    }

    if (!formData.email.includes("@")) {
      toastService.error(t("contact.form.validation.email"))
      return
    }

    try {
      // TODO: Replace with actual API call
      // await contactService.submitForm(formData)
      toastService.success(t("contact.form.success"))
      setFormData({
        name: "",
        email: "",
        subject: "",
        category: "",
        message: "",
      })
    } catch (error) {
      toastService.handleApiError(error, t("contact.form.error"))
    }
  }

  const contactMethods = [
    {
      icon: Mail,
      title: t("contact.email.title"),
      description: t("contact.email.description"),
      value: "support@ovra-ai.com",
      action: t("contact.email.action")
    },
    {
      icon: Phone,
      title: t("contact.phone.title"),
      description: t("contact.phone.description"),
      value: "+34 900 123 456",
      action: t("contact.phone.action")
    },
    {
      icon: MapPin,
      title: t("contact.address.title"),
      description: t("contact.address.description"),
      value: "Madrid, Spain",
      action: t("contact.address.action")
    },
    {
      icon: Clock,
      title: t("contact.hours.title"),
      description: t("contact.hours.description"),
      value: t("contact.hours.value"),
      action: ""
    },
  ]

  const categories = [
    { value: "general", label: t("contact.category.general"), icon: MessageSquare },
    { value: "support", label: t("contact.category.support"), icon: HelpCircle },
    { value: "bug", label: t("contact.category.bug"), icon: Bug },
    { value: "feature", label: t("contact.category.feature"), icon: Lightbulb },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-foreground mb-6">
            {t("contact.title")}
          </h1>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("contact.subtitle")}
          </p>
        </div>
      </section>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
          {/* Contact Form */}
          <div>
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Send className="h-5 w-5 text-primary" />
                  <span>{t("contact.form.title")}</span>
                </CardTitle>
                <CardDescription>{t("contact.form.description")}</CardDescription>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label htmlFor="name">{t("contact.form.name")}</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange("name", e.target.value)}
                        placeholder={t("contact.form.name.placeholder")}
                        required
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="email">{t("contact.form.email")}</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange("email", e.target.value)}
                        placeholder={t("contact.form.email.placeholder")}
                        required
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="category">{t("contact.form.category")}</Label>
                    <Select value={formData.category} onValueChange={(value) => handleInputChange("category", value)}>
                      <SelectTrigger>
                        <SelectValue placeholder={t("contact.form.category.placeholder")} />
                      </SelectTrigger>
                      <SelectContent>
                        {categories.map((category) => (
                          <SelectItem key={category.value} value={category.value}>
                            <div className="flex items-center space-x-2">
                              <category.icon className="h-4 w-4" />
                              <span>{category.label}</span>
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="subject">{t("contact.form.subject")}</Label>
                    <Input
                      id="subject"
                      value={formData.subject}
                      onChange={(e) => handleInputChange("subject", e.target.value)}
                      placeholder={t("contact.form.subject.placeholder")}
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="message">{t("contact.form.message")}</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleInputChange("message", e.target.value)}
                      placeholder={t("contact.form.message.placeholder")}
                      rows={6}
                      required
                    />
                  </div>

                  <Button type="submit" className="w-full" size="lg">
                    <Send className="h-4 w-4 mr-2" />
                    {t("contact.form.submit")}
                  </Button>
                </form>
              </CardContent>
            </Card>
          </div>

          {/* Contact Information */}
          <div className="space-y-8">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-6">{t("contact.info.title")}</h2>
              <div className="space-y-6">
                {contactMethods.map((method, index) => (
                  <Card key={index} className="border-border bg-card">
                    <CardContent className="p-6">
                      <div className="flex items-start space-x-4">
                        <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center flex-shrink-0">
                          <method.icon className="h-6 w-6 text-primary" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground mb-1">{method.title}</h3>
                          <p className="text-sm text-muted-foreground mb-2">{method.description}</p>
                          <p className="font-medium text-foreground">{method.value}</p>
                          {method.action && (
                            <p className="text-xs text-muted-foreground mt-1">{method.action}</p>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>

            {/* FAQ Link */}
            <Card className="border-border bg-primary/5 border-primary/20">
              <CardContent className="p-6">
                <h3 className="font-semibold text-foreground mb-2">{t("contact.faq.title")}</h3>
                <p className="text-sm text-muted-foreground mb-4">{t("contact.faq.description")}</p>
                <Link href="/help">
                  <Button variant="outline" className="w-full">
                    <HelpCircle className="h-4 w-4 mr-2" />
                    {t("contact.faq.button")}
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <SharedFooter />
    </div>
  )
}
