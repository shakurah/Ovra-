"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { ProtectedRoute } from "@/components/protected-route"
import { Scale, CreditCard, Zap, Clock, CheckCircle, ArrowLeft, Sparkles } from "lucide-react"
import Link from "next/link"

function CreditsPageContent() {
  const [currentCredits] = useState(47)
  const [totalCredits] = useState(200)
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)

  const creditPackages = [
    {
      id: "basic",
      name: "Paquete Básico",
      credits: 50,
      price: 9,
      popular: false,
      description: "Perfecto para consultas ocasionales",
    },
    {
      id: "professional",
      name: "Paquete Profesional",
      credits: 200,
      price: 29,
      popular: true,
      description: "Ideal para profesionales activos",
    },
    {
      id: "enterprise",
      name: "Paquete Empresa",
      credits: 500,
      price: 69,
      popular: false,
      description: "Para equipos y empresas",
    },
  ]

  const recentUsage = [
    {
      date: "2024-01-15",
      question: "¿Cómo facturar servicios artísticos con IVA?",
      credits: 1,
      time: "14:30",
    },
    {
      date: "2024-01-15",
      question: "Deducciones IRPF para material artístico",
      credits: 1,
      time: "12:15",
    },
    {
      date: "2024-01-14",
      question: "Tributación de derechos de autor",
      credits: 1,
      time: "16:45",
    },
    {
      date: "2024-01-14",
      question: "Obligaciones fiscales autónomo cultural",
      credits: 1,
      time: "10:20",
    },
    {
      date: "2024-01-13",
      question: "Régimen especial del criterio de caja",
      credits: 1,
      time: "15:30",
    },
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <Link href="/chat">
                <Button variant="ghost" size="sm">
                  <ArrowLeft className="h-4 w-4 mr-2" />
                  Volver al Chat
                </Button>
              </Link>
              <div className="flex items-center space-x-2">
                <Scale className="h-8 w-8 text-blue-600" />
                <span className="text-2xl font-bold text-gray-900">Ovra AI</span>
              </div>
            </div>
            <Badge variant="outline" className="text-green-600 border-green-200">
              <Sparkles className="h-3 w-3 mr-1" />
              Plan Profesional
            </Badge>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Gestión de Créditos</h1>
          <p className="text-gray-600">Administra tus créditos y consulta tu historial de uso</p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Current Credits Status */}
          <div className="lg:col-span-2 space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <CreditCard className="h-5 w-5 text-blue-600" />
                  <span>Estado Actual de Créditos</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-2xl font-bold text-gray-900">{currentCredits}</span>
                    <span className="text-sm text-gray-500">de {totalCredits} créditos</span>
                  </div>
                  <Progress value={(currentCredits / totalCredits) * 100} className="h-3" />
                  <div className="flex items-center justify-between text-sm text-gray-600">
                    <span>Créditos utilizados: {totalCredits - currentCredits}</span>
                    <span>Renovación: 15 Feb 2024</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Usage History */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Clock className="h-5 w-5 text-blue-600" />
                  <span>Historial de Uso Reciente</span>
                </CardTitle>
                <CardDescription>Tus últimas consultas legales</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {recentUsage.map((usage, index) => (
                    <div key={index} className="flex items-start justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <p className="font-medium text-gray-900 mb-1">{usage.question}</p>
                        <div className="flex items-center space-x-4 text-sm text-gray-500">
                          <span>{usage.date}</span>
                          <span>{usage.time}</span>
                        </div>
                      </div>
                      <Badge variant="outline" className="ml-4">
                        -{usage.credits} crédito
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Credit Packages */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-blue-600" />
                  <span>Comprar Créditos</span>
                </CardTitle>
                <CardDescription>Elige el paquete que mejor se adapte a tus necesidades</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {creditPackages.map((pkg) => (
                  <div
                    key={pkg.id}
                    className={`relative p-4 border rounded-lg cursor-pointer transition-all ${
                      selectedPlan === pkg.id ? "border-blue-500 bg-blue-50" : "border-gray-200 hover:border-gray-300"
                    } ${pkg.popular ? "ring-2 ring-blue-500" : ""}`}
                    onClick={() => setSelectedPlan(pkg.id)}
                  >
                    {pkg.popular && <Badge className="absolute -top-2 left-4 bg-blue-600">Más Popular</Badge>}
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">{pkg.name}</h3>
                        <span className="text-2xl font-bold text-blue-600">€{pkg.price}</span>
                      </div>
                      <p className="text-sm text-gray-600">{pkg.description}</p>
                      <div className="flex items-center space-x-2">
                        <Badge variant="secondary">{pkg.credits} créditos</Badge>
                        <span className="text-xs text-gray-500">
                          €{(pkg.price / pkg.credits).toFixed(2)} por crédito
                        </span>
                      </div>
                    </div>
                  </div>
                ))}

                <Button className="w-full mt-4" disabled={!selectedPlan} size="lg">
                  <CreditCard className="h-4 w-4 mr-2" />
                  Comprar Créditos
                </Button>
              </CardContent>
            </Card>

            {/* Benefits */}
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Beneficios Incluidos</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3 text-sm">
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Respuestas con referencias legales</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Acceso a legislación actualizada</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Soporte especializado</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Historial de consultas</span>
                  </li>
                  <li className="flex items-center space-x-2">
                    <CheckCircle className="h-4 w-4 text-green-600" />
                    <span>Sin compromisos a largo plazo</span>
                  </li>
                </ul>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function CreditsPage() {
  return (
    <ProtectedRoute>
      <CreditsPageContent />
    </ProtectedRoute>
  )
}
