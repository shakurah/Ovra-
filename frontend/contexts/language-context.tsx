"use client"

import type React from "react"
import { createContext, useContext, useState, useEffect } from "react"

type Language = "en" | "es"

interface LanguageContextType {
  language: Language
  setLanguage: (lang: Language) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

const translations = {
  en: {
    // Navigation
    "nav.chat": "Chat",
    "nav.analytics": "Analytics",
    "nav.history": "History",
    "nav.search": "Search",
    "nav.signin": "Sign in",
    "nav.signup": "Sign up",

    // Hero Section
    "hero.badge": "🤖 AI-Powered Tax Assistant for Cultural Professionals",
    "hero.title": "Smart Tax Advice",
    "hero.subtitle": "for Creative Minds",
    "hero.description":
      "Intelligent tax advice for Spanish cultural professionals. Accurate answers based on current Spanish legislation.",
    "hero.cta.primary": "Start Consultation",
    "hero.cta.secondary": "Learn More →",

    // Trust Indicators
    "trust.verified": "Verified legal opinions from BOE",
    "trust.availability": "24/7 availability",
    "trust.updated": "Updated with latest regulations",
    "trust.specialized": "Specialized for freelancers",

    // Stats
    "stats.laws": "Laws analyzed",
    "stats.articles": "Articles indexed",
    "stats.accuracy": "Accuracy",
    "stats.availability": "Availability",

    // Why Choose Section
    "why.title": "Why Choose OVRA AI?",
    "why.subtitle": "Built specifically for Spanish cultural professionals with accurate, legally-backed answers",
    "why.legislation.title": "Answers based on current legislation",
    "why.legislation.desc": "Information updated from BOE",
    "why.specialized.title": "Specialized in cultural professionals",
    "why.specialized.desc": "Specific knowledge of the sector",
    "why.instant.title": "Instant answers with AI",
    "why.instant.desc": "Fast and accurate analysis",

    // Frequent Questions
    "faq.title": "Frequent Questions",
    "faq.subtitle": "Get instant answers to common tax questions",
    "faq.vat.title": "VAT for freelancers",
    "faq.vat.desc": "Consulting on billing and VAT declarations",
    "faq.irpf.title": "IRPF deductions",
    "faq.irpf.desc": "Deductible expenses for cultural professionals",
    "faq.international.title": "International billing",
    "faq.international.desc": "Regulations for services abroad",
    "faq.objective.title": "Objective estimation",
    "faq.objective.desc": "Modules vs direct estimation",

    // Badges
    "badge.popular": "Popular",
    "badge.essential": "Essential",
    "badge.advanced": "Advanced",
    "badge.recommended": "Recommended",

    // Testimonials
    "testimonials.title": "Trusted by Professionals",
    "testimonials.subtitle": "See what cultural professionals say about OVRA AI",
    "testimonials.maria":
      "OVRA AI helped me understand VAT requirements for international clients. Saved me hours of research.",
    "testimonials.carlos":
      "Finally, tax advice that understands the cultural sector. The citations are always accurate.",
    "testimonials.ana": "The instant answers with legal references give me confidence in my tax decisions.",
    "testimonials.maria.role": "Freelance Designer",
    "testimonials.carlos.role": "Independent Musician",
    "testimonials.ana.role": "Content Creator",

    // Final CTA
    "cta.title": "Ready to solve your tax questions?",
    "cta.description":
      "Our AI assistant is specifically trained for the Spanish cultural sector and will provide you with accurate answers based on current legislation.",
    "cta.button": "Start Now →",

    // Footer
    "footer.description": "AI legal assistant specialized in Spanish tax legislation for cultural professionals.",
    "footer.product": "Product",
    "footer.features": "Features",
    "footer.pricing": "Pricing",
    "footer.api": "API",
    "footer.documentation": "Documentation",
    "footer.legal": "Legal",
    "footer.terms": "Terms of Service",
    "footer.privacy": "Privacy Policy",
    "footer.cookies": "Cookies",
    "footer.gdpr": "GDPR",
    "footer.support": "Support",
    "footer.help": "Help Center",
    "footer.contact": "Contact",
    "footer.status": "Service Status",
    "footer.community": "Community",
    "footer.rights": "All rights reserved.",

    // Chat Page
    "chat.title": "Legal AI Consultation",
    "chat.subtitle": "Specialized in Spanish tax legislation",
    "chat.credits.remaining": "Credits remaining",
    "chat.sidebar.chat": "Legal Chat",
    "chat.sidebar.credits": "My Credits",
    "chat.sidebar.docs": "Legal Documents",
    "chat.sidebar.logout": "Sign Out",
    "chat.welcome.title": "Hello! I'm your AI legal assistant",
    "chat.welcome.description":
      "Specialized in Spanish tax legislation for cultural professionals. I can help you with VAT, IRPF, billing and more.",
    "chat.welcome.examples": "Frequent questions:",
    "chat.input.placeholder": "Write your legal question here...",
    "chat.input.analyzing": "Analyzing legislation...",
    "chat.input.nocredits": "No credits remaining.",
    "chat.input.buycredits": "Buy more credits",
    "chat.input.disclaimer": "Each consultation consumes 1 credit. Answers based on official Spanish legislation.",
    "chat.examples.freelancer": "How should I invoice as a cultural freelancer?",
    "chat.examples.vat": "What VAT do I apply to my artistic services?",
    "chat.examples.deductions": "Can I deduct art material expenses in IRPF?",
    "chat.examples.copyright": "How are copyright royalties taxed?",
    "chat.examples.obligations": "What obligations do I have as a cultural freelancer?",

    // Analytics Page
    "analytics.title": "Analytics Dashboard",
    "analytics.subtitle": "Track your legal consultation patterns and insights",
    "analytics.overview": "Overview",
    "analytics.consultations": "Consultations",
    "analytics.topics": "Topics",
    "analytics.trends": "Trends",
    "analytics.total.consultations": "Total Consultations",
    "analytics.this.month": "This Month",
    "analytics.avg.response": "Avg Response Time",
    "analytics.satisfaction": "Satisfaction Rate",
    "analytics.popular.topics": "Most Popular Topics",
    "analytics.recent.activity": "Recent Activity",
    "analytics.consultation.trends": "Consultation Trends",
    "analytics.topic.distribution": "Topic Distribution",
    "analytics.monthly.usage": "Monthly Usage",

    // History Page
    "history.title": "Consultation History",
    "history.subtitle": "Review your past legal consultations and answers",
    "history.search.placeholder": "Search consultations...",
    "history.filter.all": "All Topics",
    "history.filter.vat": "VAT",
    "history.filter.irpf": "IRPF",
    "history.filter.billing": "Billing",
    "history.filter.deductions": "Deductions",
    "history.sort.newest": "Newest First",
    "history.sort.oldest": "Oldest First",
    "history.sort.relevant": "Most Relevant",
    "history.no.results": "No consultations found",
    "history.load.more": "Load More",
    "history.export": "Export History",

    // Account/Profile Page
    "account.title": "Account Settings",
    "account.subtitle": "Manage your profile and preferences",
    "account.profile": "Profile",
    "account.billing": "Billing",
    "account.security": "Security",
    "account.notifications": "Notifications",
    "account.personal.info": "Personal Information",
    "account.first.name": "First Name",
    "account.last.name": "Last Name",
    "account.email": "Email Address",
    "account.phone": "Phone Number",
    "account.company": "Company",
    "account.profession": "Profession",
    "account.save.changes": "Save Changes",
    "account.change.password": "Change Password",
    "account.current.password": "Current Password",
    "account.new.password": "New Password",
    "account.confirm.password": "Confirm New Password",
    "account.two.factor": "Two-Factor Authentication",
    "account.delete.account": "Delete Account",

    // Credits & Payment
    "credits.title": "Credits Management",
    "credits.subtitle": "Manage your credits and billing",
    "credits.current.status": "Current Credit Status",
    "credits.usage.history": "Recent Usage History",
    "credits.buy.credits": "Buy Credits",
    "credits.auto.refill": "Auto-refill",
    "credits.payment.method": "Payment Method",
    "credits.billing.history": "Billing History",
    "credits.invoice": "Invoice",
    "credits.download": "Download",

    // Payment Page
    "payment.title": "Payment",
    "payment.subtitle": "Complete your credit purchase",
    "payment.order.summary": "Order Summary",
    "payment.payment.method": "Payment Method",
    "payment.card.number": "Card Number",
    "payment.expiry": "MM/YY",
    "payment.cvc": "CVC",
    "payment.cardholder": "Cardholder Name",
    "payment.billing.address": "Billing Address",
    "payment.country": "Country",
    "payment.postal.code": "Postal Code",
    "payment.complete.payment": "Complete Payment",
    "payment.secure": "Secure Payment",
    "payment.processing": "Processing...",

    // Settings
    "settings.title": "Settings",
    "settings.general": "General",
    "settings.language": "Language",
    "settings.theme": "Theme",
    "settings.notifications": "Notifications",
    "settings.privacy": "Privacy",
    "settings.data.export": "Export Data",
    "settings.data.delete": "Delete Data",
  },
  es: {
    // Navigation
    "nav.chat": "Chat",
    "nav.analytics": "Analíticas",
    "nav.history": "Historial",
    "nav.search": "Buscar",
    "nav.signin": "Iniciar Sesión",
    "nav.signup": "Registrarse",

    // Hero Section
    "hero.badge": "🤖 Asistente Fiscal IA para Profesionales Culturales",
    "hero.title": "Asesoramiento Fiscal Inteligente",
    "hero.subtitle": "para Mentes Creativas",
    "hero.description":
      "Asesoramiento fiscal inteligente para profesionales culturales españoles. Respuestas precisas basadas en la legislación española actual.",
    "hero.cta.primary": "Comenzar Consulta",
    "hero.cta.secondary": "Saber Más →",

    // Trust Indicators
    "trust.verified": "Opiniones legales verificadas del BOE",
    "trust.availability": "Disponibilidad 24/7",
    "trust.updated": "Actualizado con las últimas regulaciones",
    "trust.specialized": "Especializado para autónomos",

    // Stats
    "stats.laws": "Leyes analizadas",
    "stats.articles": "Artículos indexados",
    "stats.accuracy": "Precisión",
    "stats.availability": "Disponibilidad",

    // Why Choose Section
    "why.title": "¿Por qué elegir OVRA AI?",
    "why.subtitle":
      "Construido específicamente para profesionales culturales españoles con respuestas precisas y respaldadas legalmente",
    "why.legislation.title": "Respuestas basadas en legislación actual",
    "why.legislation.desc": "Información actualizada del BOE",
    "why.specialized.title": "Especializado en profesionales culturales",
    "why.specialized.desc": "Conocimiento específico del sector",
    "why.instant.title": "Respuestas instantáneas con IA",
    "why.instant.desc": "Análisis rápido y preciso",

    // Frequent Questions
    "faq.title": "Preguntas Frecuentes",
    "faq.subtitle": "Obtén respuestas instantáneas a preguntas fiscales comunes",
    "faq.vat.title": "IVA para autónomos",
    "faq.vat.desc": "Consultoría sobre facturación y declaraciones de IVA",
    "faq.irpf.title": "Deducciones IRPF",
    "faq.irpf.desc": "Gastos deducibles para profesionales culturales",
    "faq.international.title": "Facturación internacional",
    "faq.international.desc": "Regulaciones para servicios en el extranjero",
    "faq.objective.title": "Estimación objetiva",
    "faq.objective.desc": "Módulos vs estimación directa",

    // Badges
    "badge.popular": "Popular",
    "badge.essential": "Esencial",
    "badge.advanced": "Avanzado",
    "badge.recommended": "Recomendado",

    // Testimonials
    "testimonials.title": "Confiado por Profesionales",
    "testimonials.subtitle": "Ve lo que dicen los profesionales culturales sobre OVRA AI",
    "testimonials.maria":
      "OVRA AI me ayudó a entender los requisitos de IVA para clientes internacionales. Me ahorró horas de investigación.",
    "testimonials.carlos":
      "Finalmente, asesoramiento fiscal que entiende el sector cultural. Las citas siempre son precisas.",
    "testimonials.ana":
      "Las respuestas instantáneas con referencias legales me dan confianza en mis decisiones fiscales.",
    "testimonials.maria.role": "Diseñadora Freelance",
    "testimonials.carlos.role": "Músico Independiente",
    "testimonials.ana.role": "Creadora de Contenido",

    // Final CTA
    "cta.title": "¿Listo para resolver tus preguntas fiscales?",
    "cta.description":
      "Nuestro asistente IA está específicamente entrenado para el sector cultural español y te proporcionará respuestas precisas basadas en la legislación actual.",
    "cta.button": "Comenzar Ahora →",

    // Footer
    "footer.description":
      "Asistente legal IA especializado en legislación fiscal española para profesionales culturales.",
    "footer.product": "Producto",
    "footer.features": "Características",
    "footer.pricing": "Precios",
    "footer.api": "API",
    "footer.documentation": "Documentación",
    "footer.legal": "Legal",
    "footer.terms": "Términos de Servicio",
    "footer.privacy": "Política de Privacidad",
    "footer.cookies": "Cookies",
    "footer.gdpr": "GDPR",
    "footer.support": "Soporte",
    "footer.help": "Centro de Ayuda",
    "footer.contact": "Contacto",
    "footer.status": "Estado del Servicio",
    "footer.community": "Comunidad",
    "footer.rights": "Todos los derechos reservados.",

    // Chat Page
    "chat.title": "Consulta Legal IA",
    "chat.subtitle": "Especializado en legislación fiscal española",
    "chat.credits.remaining": "Créditos restantes",
    "chat.sidebar.chat": "Chat Legal",
    "chat.sidebar.credits": "Mis Créditos",
    "chat.sidebar.docs": "Documentos Legales",
    "chat.sidebar.logout": "Cerrar Sesión",
    "chat.welcome.title": "¡Hola! Soy tu asistente legal IA",
    "chat.welcome.description":
      "Especializado en legislación fiscal española para profesionales culturales. Puedo ayudarte con IVA, IRPF, facturación y más.",
    "chat.welcome.examples": "Preguntas frecuentes:",
    "chat.input.placeholder": "Escribe tu consulta legal aquí...",
    "chat.input.analyzing": "Analizando legislación...",
    "chat.input.nocredits": "Sin créditos restantes.",
    "chat.input.buycredits": "Comprar más créditos",
    "chat.input.disclaimer": "Cada consulta consume 1 crédito. Respuestas basadas en legislación oficial española.",
    "chat.examples.freelancer": "¿Cómo debo facturar como freelancer cultural?",
    "chat.examples.vat": "¿Qué IVA aplico a mis servicios artísticos?",
    "chat.examples.deductions": "¿Puedo deducir gastos de material artístico en IRPF?",
    "chat.examples.copyright": "¿Cómo tributan los derechos de autor?",
    "chat.examples.obligations": "¿Qué obligaciones tengo como autónomo cultural?",

    // Analytics Page
    "analytics.title": "Panel de Analíticas",
    "analytics.subtitle": "Rastrea tus patrones de consulta legal y obtén insights",
    "analytics.overview": "Resumen",
    "analytics.consultations": "Consultas",
    "analytics.topics": "Temas",
    "analytics.trends": "Tendencias",
    "analytics.total.consultations": "Total de Consultas",
    "analytics.this.month": "Este Mes",
    "analytics.avg.response": "Tiempo Promedio de Respuesta",
    "analytics.satisfaction": "Tasa de Satisfacción",
    "analytics.popular.topics": "Temas Más Populares",
    "analytics.recent.activity": "Actividad Reciente",
    "analytics.consultation.trends": "Tendencias de Consultas",
    "analytics.topic.distribution": "Distribución de Temas",
    "analytics.monthly.usage": "Uso Mensual",

    // History Page
    "history.title": "Historial de Consultas",
    "history.subtitle": "Revisa tus consultas legales pasadas y respuestas",
    "history.search.placeholder": "Buscar consultas...",
    "history.filter.all": "Todos los Temas",
    "history.filter.vat": "IVA",
    "history.filter.irpf": "IRPF",
    "history.filter.billing": "Facturación",
    "history.filter.deductions": "Deducciones",
    "history.sort.newest": "Más Recientes",
    "history.sort.oldest": "Más Antiguos",
    "history.sort.relevant": "Más Relevantes",
    "history.no.results": "No se encontraron consultas",
    "history.load.more": "Cargar Más",
    "history.export": "Exportar Historial",

    // Account/Profile Page
    "account.title": "Configuración de Cuenta",
    "account.subtitle": "Gestiona tu perfil y preferencias",
    "account.profile": "Perfil",
    "account.billing": "Facturación",
    "account.security": "Seguridad",
    "account.notifications": "Notificaciones",
    "account.personal.info": "Información Personal",
    "account.first.name": "Nombre",
    "account.last.name": "Apellidos",
    "account.email": "Correo Electrónico",
    "account.phone": "Teléfono",
    "account.company": "Empresa",
    "account.profession": "Profesión",
    "account.save.changes": "Guardar Cambios",
    "account.change.password": "Cambiar Contraseña",
    "account.current.password": "Contraseña Actual",
    "account.new.password": "Nueva Contraseña",
    "account.confirm.password": "Confirmar Nueva Contraseña",
    "account.two.factor": "Autenticación de Dos Factores",
    "account.delete.account": "Eliminar Cuenta",

    // Credits & Payment
    "credits.title": "Gestión de Créditos",
    "credits.subtitle": "Gestiona tus créditos y facturación",
    "credits.current.status": "Estado Actual de Créditos",
    "credits.usage.history": "Historial de Uso Reciente",
    "credits.buy.credits": "Comprar Créditos",
    "credits.auto.refill": "Recarga automática",
    "credits.payment.method": "Método de Pago",
    "credits.billing.history": "Historial de Facturación",
    "credits.invoice": "Factura",
    "credits.download": "Descargar",

    // Payment Page
    "payment.title": "Pago",
    "payment.subtitle": "Completa tu compra de créditos",
    "payment.order.summary": "Resumen del Pedido",
    "payment.payment.method": "Método de Pago",
    "payment.card.number": "Número de Tarjeta",
    "payment.expiry": "MM/AA",
    "payment.cvc": "CVC",
    "payment.cardholder": "Nombre del Titular",
    "payment.billing.address": "Dirección de Facturación",
    "payment.country": "País",
    "payment.postal.code": "Código Postal",
    "payment.complete.payment": "Completar Pago",
    "payment.secure": "Pago Seguro",
    "payment.processing": "Procesando...",

    // Settings
    "settings.title": "Configuración",
    "settings.general": "General",
    "settings.language": "Idioma",
    "settings.theme": "Tema",
    "settings.notifications": "Notificaciones",
    "settings.privacy": "Privacidad",
    "settings.data.export": "Exportar Datos",
    "settings.data.delete": "Eliminar Datos",
  },
}

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguage] = useState<Language>("en")

  useEffect(() => {
    const savedLanguage = localStorage.getItem("language") as Language
    if (savedLanguage && (savedLanguage === "en" || savedLanguage === "es")) {
      setLanguage(savedLanguage)
    }
  }, [])

  const handleSetLanguage = (lang: Language) => {
    setLanguage(lang)
    localStorage.setItem("language", lang)
  }

  const t = (key: string): string => {
    return translations[language][key as keyof (typeof translations)[typeof language]] || key
  }

  return (
    <LanguageContext.Provider value={{ language, setLanguage: handleSetLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage() {
  const context = useContext(LanguageContext)
  if (context === undefined) {
    throw new Error("useLanguage must be used within a LanguageProvider")
  }
  return context
}
