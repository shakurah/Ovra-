"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ProtectedLayout } from "@/components/protected-layout"
import { useLanguage } from "@/contexts/language-context"
import {
  BarChart3,
  TrendingUp,
  Clock,
  MessageSquare,
  Users,
  Target,
  Calendar,
  Download,
  Filter,
} from "lucide-react"

export default function AnalyticsPage() {
  const { t } = useLanguage()
  const [timeRange, setTimeRange] = useState("30d")

  const stats = [
    {
      title: t("analytics.total.consultations"),
      value: "156",
      change: "+12%",
      icon: MessageSquare,
      color: "text-blue-600 dark:text-blue-400",
      bgColor: "bg-blue-100 dark:bg-blue-900/20",
    },
    {
      title: t("analytics.this.month"),
      value: "23",
      change: "+8%",
      icon: Calendar,
      color: "text-green-600 dark:text-green-400",
      bgColor: "bg-green-100 dark:bg-green-900/20",
    },
    {
      title: t("analytics.avg.response"),
      value: "2.3s",
      change: "-15%",
      icon: Clock,
      color: "text-purple-600 dark:text-purple-400",
      bgColor: "bg-purple-100 dark:bg-purple-900/20",
    },
    {
      title: t("analytics.satisfaction"),
      value: "98%",
      change: "+2%",
      icon: Target,
      color: "text-orange-600 dark:text-orange-400",
      bgColor: "bg-orange-100 dark:bg-orange-900/20",
    },
  ]

  const popularTopics = [
    { topic: "IVA", count: 45, percentage: 65 },
    { topic: "IRPF", count: 32, percentage: 46 },
    { topic: t("history.filter.billing"), count: 28, percentage: 40 },
    { topic: t("history.filter.deductions"), count: 21, percentage: 30 },
    { topic: "Autónomos", count: 18, percentage: 26 },
  ]

  const recentActivity = [
    {
      date: "2024-01-15",
      time: "14:30",
      topic: "IVA",
      question: t("chat.examples.vat"),
      satisfaction: 5,
    },
    {
      date: "2024-01-15",
      time: "12:15",
      topic: "IRPF",
      question: t("chat.examples.deductions"),
      satisfaction: 5,
    },
    {
      date: "2024-01-14",
      time: "16:45",
      topic: "Derechos de Autor",
      question: t("chat.examples.copyright"),
      satisfaction: 4,
    },
    {
      date: "2024-01-14",
      time: "10:20",
      topic: "Autónomos",
      question: t("chat.examples.obligations"),
      satisfaction: 5,
    },
  ]

  return (
    <ProtectedLayout title={t("analytics.title")} credits={47}>
      <div className="p-6 max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-foreground mb-2">{t("analytics.title")}</h1>
          <p className="text-muted-foreground">{t("analytics.subtitle")}</p>
        </div>

        {/* Time Range Selector */}
        <div className="flex items-center justify-between mb-8">
          <div className="flex items-center space-x-2">
            <Button variant={timeRange === "7d" ? "default" : "outline"} size="sm" onClick={() => setTimeRange("7d")}>
              7d
            </Button>
            <Button variant={timeRange === "30d" ? "default" : "outline"} size="sm" onClick={() => setTimeRange("30d")}>
              30d
            </Button>
            <Button variant={timeRange === "90d" ? "default" : "outline"} size="sm" onClick={() => setTimeRange("90d")}>
              90d
            </Button>
          </div>
          <div className="flex items-center space-x-2">
            <Button variant="outline" size="sm">
              <Filter className="h-4 w-4 mr-2" />
              Filter
            </Button>
            <Button variant="outline" size="sm">
              <Download className="h-4 w-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {stats.map((stat, index) => (
            <Card key={index} className="border-border bg-card">
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                    <p className="text-2xl font-bold text-foreground">{stat.value}</p>
                    <p className="text-xs text-green-600 dark:text-green-400 flex items-center mt-1">
                      <TrendingUp className="h-3 w-3 mr-1" />
                      {stat.change}
                    </p>
                  </div>
                  <div className={`w-12 h-12 ${stat.bgColor} rounded-lg flex items-center justify-center`}>
                    <stat.icon className={`h-6 w-6 ${stat.color}`} />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Popular Topics */}
          <div className="lg:col-span-2 space-y-6">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-primary" />
                  <span>{t("analytics.popular.topics")}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {popularTopics.map((topic, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="w-8 h-8 bg-primary/10 rounded-lg flex items-center justify-center">
                          <span className="text-primary font-semibold text-sm">{index + 1}</span>
                        </div>
                        <div>
                          <p className="font-medium text-foreground">{topic.topic}</p>
                          <p className="text-sm text-muted-foreground">{topic.count} consultas</p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-3">
                        <Progress value={topic.percentage} className="w-20 h-2" />
                        <span className="text-sm font-medium text-muted-foreground w-10">{topic.percentage}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Consultation Trends Chart Placeholder */}
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle>{t("analytics.consultation.trends")}</CardTitle>
                <CardDescription>{t("analytics.monthly.usage")}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64 bg-muted/30 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <BarChart3 className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">Chart visualization would go here</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <div className="space-y-6">
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-primary" />
                  <span>{t("analytics.recent.activity")}</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentActivity.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 bg-muted/30 rounded-lg">
                      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center flex-shrink-0">
                        <MessageSquare className="h-4 w-4 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-1">
                          <Badge variant="secondary" className="text-xs">
                            {activity.topic}
                          </Badge>
                          <span className="text-xs text-muted-foreground">
                            {activity.date} {activity.time}
                          </span>
                        </div>
                        <p className="text-sm text-foreground line-clamp-2">{activity.question}</p>
                        <div className="flex items-center mt-2">
                          <div className="flex space-x-1">
                            {[...Array(5)].map((_, i) => (
                              <div
                                key={i}
                                className={`w-3 h-3 rounded-full ${
                                  i < activity.satisfaction ? "bg-yellow-400" : "bg-muted"
                                }`}
                              />
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Topic Distribution */}
            <Card className="border-border bg-card">
              <CardHeader>
                <CardTitle>{t("analytics.topic.distribution")}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="h-48 bg-muted/30 rounded-lg flex items-center justify-center">
                  <div className="text-center">
                    <Users className="h-12 w-12 text-muted-foreground mx-auto mb-2" />
                    <p className="text-muted-foreground">Pie chart would go here</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </ProtectedLayout>
  )
}
