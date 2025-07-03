"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import {
  Activity,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Clock,
  Server,
  Database,
  Zap,
  Globe,
} from "lucide-react"

export default function StatusPage() {
  const { t } = useLanguage()

  const overallStatus = "operational" // operational, degraded, outage

  const services = [
    {
      name: t("status.service.api"),
      status: "operational",
      uptime: 99.9,
      responseTime: "120ms",
      icon: Server,
      description: t("status.service.api.description")
    },
    {
      name: t("status.service.ai"),
      status: "operational",
      uptime: 99.8,
      responseTime: "2.1s",
      icon: Zap,
      description: t("status.service.ai.description")
    },
    {
      name: t("status.service.database"),
      status: "operational",
      uptime: 99.95,
      responseTime: "45ms",
      icon: Database,
      description: t("status.service.database.description")
    },
    {
      name: t("status.service.web"),
      status: "operational",
      uptime: 99.99,
      responseTime: "89ms",
      icon: Globe,
      description: t("status.service.web.description")
    },
  ]

  const incidents = [
    {
      title: t("status.incident.1.title"),
      description: t("status.incident.1.description"),
      status: "resolved",
      date: "2024-01-15",
      time: "14:30 UTC",
      duration: "23 minutes",
      affected: [t("status.service.ai")]
    },
    {
      title: t("status.incident.2.title"),
      description: t("status.incident.2.description"),
      status: "resolved",
      date: "2024-01-10",
      time: "09:15 UTC",
      duration: "12 minutes",
      affected: [t("status.service.database")]
    },
  ]

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "operational":
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case "degraded":
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      case "outage":
        return <XCircle className="h-5 w-5 text-red-500" />
      default:
        return <CheckCircle className="h-5 w-5 text-green-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "operational":
        return <Badge className="bg-green-100 text-green-800 border-green-200">{t("status.operational")}</Badge>
      case "degraded":
        return <Badge className="bg-yellow-100 text-yellow-800 border-yellow-200">{t("status.degraded")}</Badge>
      case "outage":
        return <Badge className="bg-red-100 text-red-800 border-red-200">{t("status.outage")}</Badge>
      case "resolved":
        return <Badge className="bg-blue-100 text-blue-800 border-blue-200">{t("status.resolved")}</Badge>
      default:
        return <Badge className="bg-green-100 text-green-800 border-green-200">{t("status.operational")}</Badge>
    }
  }

  return (
    <ProtectedLayout title={t("status.title")} credits={47}>
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <Activity className="h-12 w-12 text-primary" />
            <h1 className="text-4xl md:text-6xl font-bold text-foreground">{t("status.title")}</h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("status.subtitle")}
          </p>
          
          {/* Overall Status */}
          <Card className="max-w-md mx-auto border-border bg-card">
            <CardContent className="p-6">
              <div className="flex items-center justify-center space-x-3">
                {getStatusIcon(overallStatus)}
                <div>
                  <h3 className="font-semibold text-foreground">{t("status.overall")}</h3>
                  {getStatusBadge(overallStatus)}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Services Status */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground mb-2">{t("status.services.title")}</h2>
            <p className="text-muted-foreground">{t("status.services.subtitle")}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {services.map((service, index) => (
              <Card key={index} className="border-border bg-card">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <service.icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="text-lg">{service.name}</CardTitle>
                        <CardDescription>{service.description}</CardDescription>
                      </div>
                    </div>
                    {getStatusIcon(service.status)}
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">{t("status.uptime")}</span>
                    <span className="font-medium text-foreground">{service.uptime}%</span>
                  </div>
                  <Progress value={service.uptime} className="h-2" />
                  
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-muted-foreground">{t("status.response.time")}</span>
                    <span className="font-medium text-foreground">{service.responseTime}</span>
                  </div>
                  
                  <div className="pt-2">
                    {getStatusBadge(service.status)}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Recent Incidents */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-foreground mb-2">{t("status.incidents.title")}</h2>
            <p className="text-muted-foreground">{t("status.incidents.subtitle")}</p>
          </div>
          
          {incidents.length > 0 ? (
            <div className="space-y-6">
              {incidents.map((incident, index) => (
                <Card key={index} className="border-border bg-card">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          <Clock className="h-4 w-4 text-muted-foreground" />
                          <span className="text-sm text-muted-foreground">
                            {incident.date} at {incident.time}
                          </span>
                          {getStatusBadge(incident.status)}
                        </div>
                        <CardTitle className="text-lg mb-2">{incident.title}</CardTitle>
                        <CardDescription>{incident.description}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="font-medium text-foreground">{t("status.duration")}: </span>
                        <span className="text-muted-foreground">{incident.duration}</span>
                      </div>
                      <div>
                        <span className="font-medium text-foreground">{t("status.affected.services")}: </span>
                        <span className="text-muted-foreground">{incident.affected.join(", ")}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="border-border bg-card">
              <CardContent className="p-8 text-center">
                <CheckCircle className="h-12 w-12 text-green-500 mx-auto mb-4" />
                <h3 className="font-semibold text-foreground mb-2">{t("status.no.incidents.title")}</h3>
                <p className="text-muted-foreground">{t("status.no.incidents.description")}</p>
              </CardContent>
            </Card>
          )}
        </div>
      </section>

      {/* Subscribe to Updates */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto">
          <Card className="border-border bg-card">
            <CardHeader className="text-center">
              <CardTitle className="text-2xl">{t("status.subscribe.title")}</CardTitle>
              <CardDescription className="text-lg">{t("status.subscribe.description")}</CardDescription>
            </CardHeader>
            <CardContent className="text-center">
              <Button size="lg">
                {t("status.subscribe.button")}
              </Button>
            </CardContent>
          </Card>
        </div>
      </section>
    </ProtectedLayout>
  )
}
