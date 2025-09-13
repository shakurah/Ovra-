"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { SharedHeader } from "@/components/shared-header"
import { SharedFooter } from "@/components/shared-footer"
import { useLanguage } from "@/contexts/language-context"
import {
  Users,
  MessageSquare,
  Heart,
  Star,
  Calendar,
  ExternalLink,
  Github,
  Twitter,
  Linkedin,
  BookOpen,
  Award,
  TrendingUp,
} from "lucide-react"
import Link from "next/link"

export default function CommunityPage() {
  const { t } = useLanguage()

  const communityStats = [
    {
      icon: Users,
      label: t("community.stats.members"),
      value: "2,500+",
      description: t("community.stats.members.description")
    },
    {
      icon: MessageSquare,
      label: t("community.stats.discussions"),
      value: "850+",
      description: t("community.stats.discussions.description")
    },
    {
      icon: BookOpen,
      label: t("community.stats.resources"),
      value: "120+",
      description: t("community.stats.resources.description")
    },
    {
      icon: Award,
      label: t("community.stats.experts"),
      value: "45+",
      description: t("community.stats.experts.description")
    },
  ]

  const platforms = [
    {
      name: "Discord",
      description: t("community.discord.description"),
      members: "1,200+",
      icon: MessageSquare,
      link: "#",
      primary: true
    },
    {
      name: "GitHub",
      description: t("community.github.description"),
      members: "800+",
      icon: Github,
      link: "#",
      primary: false
    },
    {
      name: "Twitter",
      description: t("community.twitter.description"),
      members: "3,500+",
      icon: Twitter,
      link: "#",
      primary: false
    },
    {
      name: "LinkedIn",
      description: t("community.linkedin.description"),
      members: "1,800+",
      icon: Linkedin,
      link: "#",
      primary: false
    },
  ]

  const featuredDiscussions = [
    {
      title: t("community.discussion.1.title"),
      author: "María González",
      avatar: "/avatars/maria.jpg",
      replies: 23,
      likes: 45,
      category: t("community.category.tax"),
      time: "2 hours ago"
    },
    {
      title: t("community.discussion.2.title"),
      author: "Carlos Ruiz",
      avatar: "/avatars/carlos.jpg",
      replies: 18,
      likes: 32,
      category: t("community.category.freelance"),
      time: "5 hours ago"
    },
    {
      title: t("community.discussion.3.title"),
      author: "Ana Martín",
      avatar: "/avatars/ana.jpg",
      replies: 31,
      likes: 67,
      category: t("community.category.legal"),
      time: "1 day ago"
    },
  ]

  const upcomingEvents = [
    {
      title: t("community.event.1.title"),
      date: "2024-02-15",
      time: "18:00 CET",
      type: t("community.event.webinar"),
      attendees: 156
    },
    {
      title: t("community.event.2.title"),
      date: "2024-02-22",
      time: "19:00 CET",
      type: t("community.event.workshop"),
      attendees: 89
    },
    {
      title: t("community.event.3.title"),
      date: "2024-03-01",
      time: "17:30 CET",
      type: t("community.event.qa"),
      attendees: 234
    },
  ]

  return (
    <div className="min-h-screen bg-background">
      <SharedHeader />

      {/* Hero Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8 bg-gradient-to-br from-primary/5 to-secondary/5">
        <div className="max-w-4xl mx-auto text-center">
          <div className="flex items-center justify-center space-x-3 mb-6">
            <Users className="h-12 w-12 text-primary" />
            <h1 className="text-4xl md:text-6xl font-bold text-foreground">{t("community.title")}</h1>
          </div>
          <p className="text-xl text-muted-foreground mb-8 max-w-2xl mx-auto">
            {t("community.subtitle")}
          </p>
          <Button size="lg" className="mr-4">
            {t("community.join.button")}
          </Button>
          <Button variant="outline" size="lg">
            {t("community.explore.button")}
          </Button>
        </div>
      </section>

      {/* Community Stats */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {communityStats.map((stat, index) => (
              <Card key={index} className="border-border bg-card text-center">
                <CardContent className="p-6">
                  <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
                    <stat.icon className="h-6 w-6 text-primary" />
                  </div>
                  <h3 className="text-2xl font-bold text-foreground mb-1">{stat.value}</h3>
                  <p className="font-medium text-foreground mb-2">{stat.label}</p>
                  <p className="text-sm text-muted-foreground">{stat.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Community Platforms */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">{t("community.platforms.title")}</h2>
            <p className="text-xl text-muted-foreground">{t("community.platforms.subtitle")}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {platforms.map((platform, index) => (
              <Card key={index} className={`border-border bg-card ${platform.primary ? 'ring-2 ring-primary' : ''}`}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      <div className="w-10 h-10 bg-primary/10 rounded-lg flex items-center justify-center">
                        <platform.icon className="h-5 w-5 text-primary" />
                      </div>
                      <div>
                        <CardTitle className="flex items-center space-x-2">
                          <span>{platform.name}</span>
                          {platform.primary && (
                            <Badge className="bg-primary/10 text-primary">
                              {t("community.primary")}
                            </Badge>
                          )}
                        </CardTitle>
                        <CardDescription>{platform.members} {t("community.members")}</CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="space-y-4">
                  <p className="text-muted-foreground">{platform.description}</p>
                  <Button className="w-full" variant={platform.primary ? "default" : "outline"}>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    {t("community.join")} {platform.name}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Featured Discussions */}
      <section className="py-16 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-2xl font-bold text-foreground mb-2">{t("community.discussions.title")}</h2>
              <p className="text-muted-foreground">{t("community.discussions.subtitle")}</p>
            </div>
            <Button variant="outline">
              <TrendingUp className="h-4 w-4 mr-2" />
              {t("community.view.all")}
            </Button>
          </div>
          
          <div className="space-y-4">
            {featuredDiscussions.map((discussion, index) => (
              <Card key={index} className="border-border bg-card hover:shadow-md transition-shadow cursor-pointer">
                <CardContent className="p-6">
                  <div className="flex items-start space-x-4">
                    <Avatar className="w-10 h-10">
                      <AvatarImage src={discussion.avatar} alt={discussion.author} />
                      <AvatarFallback>{discussion.author.split(' ').map(n => n[0]).join('')}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-2">
                        <Badge variant="secondary" className="text-xs">
                          {discussion.category}
                        </Badge>
                        <span className="text-xs text-muted-foreground">{discussion.time}</span>
                      </div>
                      <h3 className="font-semibold text-foreground mb-2">{discussion.title}</h3>
                      <div className="flex items-center space-x-4 text-sm text-muted-foreground">
                        <span>{t("community.by")} {discussion.author}</span>
                        <div className="flex items-center space-x-1">
                          <MessageSquare className="h-4 w-4" />
                          <span>{discussion.replies}</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <Heart className="h-4 w-4" />
                          <span>{discussion.likes}</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Upcoming Events */}
      <section className="py-16 px-4 sm:px-6 lg:px-8 bg-muted/30">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-foreground mb-4">{t("community.events.title")}</h2>
            <p className="text-xl text-muted-foreground">{t("community.events.subtitle")}</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {upcomingEvents.map((event, index) => (
              <Card key={index} className="border-border bg-card">
                <CardHeader>
                  <div className="flex items-center space-x-2 mb-2">
                    <Calendar className="h-4 w-4 text-primary" />
                    <span className="text-sm text-muted-foreground">{event.date} • {event.time}</span>
                  </div>
                  <Badge variant="outline" className="w-fit mb-2">
                    {event.type}
                  </Badge>
                  <CardTitle className="text-lg">{event.title}</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                    <Users className="h-4 w-4" />
                    <span>{event.attendees} {t("community.registered")}</span>
                  </div>
                  <Button className="w-full">
                    {t("community.register")}
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 sm:px-6 lg:px-8">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-foreground mb-6">
            {t("community.cta.title")}
          </h2>
          <p className="text-xl text-muted-foreground mb-8">
            {t("community.cta.description")}
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button size="lg">
              <Users className="h-4 w-4 mr-2" />
              {t("community.cta.join")}
            </Button>
            <Link href="/signup">
              <Button variant="outline" size="lg">
                {t("community.cta.signup")}
              </Button>
            </Link>
          </div>
        </div>
      </section>

      <SharedFooter />
    </div>
  )
}
