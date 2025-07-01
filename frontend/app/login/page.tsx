"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Scale, Eye, EyeOff, TrendingUp, Clock, Users, CheckCircle, ArrowRight, Mail, Lock } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion } from "framer-motion"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState({ email: "", password: "" })
  const router = useRouter()

  const validateForm = () => {
    const newErrors = { email: "", password: "" }
    
    if (!email) {
      newErrors.email = "El correo electrónico es requerido"
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      newErrors.email = "El correo electrónico no es válido"
    }
    
    if (!password) {
      newErrors.password = "La contraseña es requerida"
    } else if (password.length < 6) {
      newErrors.password = "La contraseña debe tener al menos 6 caracteres"
    }
    
    setErrors(newErrors)
    return !newErrors.email && !newErrors.password
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }
    
    setIsLoading(true)

    // Simulate login process
    setTimeout(() => {
      setIsLoading(false)
      // Redirect to chat page after successful login
      router.push("/chat")
    }, 1500)
  }

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-background">
        <motion.div 
          className="w-full max-w-md"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          {/* Logo */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Link href="/" className="inline-flex items-center space-x-2 group">
              <motion.div
                whileHover={{ rotate: 15 }}
                transition={{ type: "spring", stiffness: 300 }}
              >
                <Scale className="h-8 w-8 text-primary transition-colors group-hover:text-primary/80" />
              </motion.div>
              <span className="text-2xl font-bold text-foreground">Ovra AI</span>
            </Link>
          </motion.div>

          {/* Form Header */}
          <motion.div 
            className="mb-8"
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <h1 className="text-3xl font-bold text-foreground mb-2 bg-gradient-to-r from-foreground to-foreground/70 bg-clip-text text-transparent">
              Bienvenido de vuelta
            </h1>
            <p className="text-muted-foreground">Accede a tu cuenta para continuar con tus consultas legales</p>
          </motion.div>

          {/* Form */}
          <motion.form 
            onSubmit={handleSubmit} 
            className="space-y-6"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <motion.div 
              className="space-y-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.4 }}
            >
              <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                Correo Electrónico
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  placeholder="tu@email.com"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value)
                    if (errors.email) setErrors({ ...errors, email: "" })
                  }}
                  className={`h-12 pl-4 pr-4 transition-all duration-200 border-2 hover:border-primary/50 focus:border-primary ${
                    errors.email ? "border-destructive" : ""
                  }`}
                />
                {errors.email && (
                  <motion.p 
                    className="text-sm text-destructive mt-1"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {errors.email}
                  </motion.p>
                )}
              </div>
            </motion.div>

            <motion.div 
              className="space-y-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.5 }}
            >
              <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Tu contraseña"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value)
                    if (errors.password) setErrors({ ...errors, password: "" })
                  }}
                  className={`h-12 pl-4 pr-12 transition-all duration-200 border-2 hover:border-primary/50 focus:border-primary ${
                    errors.password ? "border-destructive" : ""
                  }`}
                />
                <motion.button
                  type="button"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setShowPassword(!showPassword)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </motion.button>
                {errors.password && (
                  <motion.p 
                    className="text-sm text-destructive mt-1"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {errors.password}
                  </motion.p>
                )}
              </div>
            </motion.div>

            <motion.div 
              className="flex items-center justify-between"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              <Link 
                href="/forgot-password" 
                className="text-sm text-primary hover:text-primary/80 transition-colors relative group"
              >
                <span className="relative z-10">¿Olvidaste tu contraseña?</span>
                <motion.div
                  className="absolute -bottom-1 left-0 h-0.5 bg-primary/50"
                  initial={{ width: 0 }}
                  whileHover={{ width: "100%" }}
                  transition={{ duration: 0.3 }}
                />
              </Link>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <Button 
                type="submit" 
                className="w-full h-12 text-base font-medium relative overflow-hidden group"
                disabled={isLoading}
              >
                <motion.div
                  className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/20 to-primary/0"
                  initial={{ x: "-100%" }}
                  animate={isLoading ? { x: "100%" } : {}}
                  transition={{ duration: 1, repeat: isLoading ? Infinity : 0 }}
                />
                <span className="relative z-10 flex items-center justify-center gap-2">
                  {isLoading ? (
                    <>
                      <motion.div
                        className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full"
                        animate={{ rotate: 360 }}
                        transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      />
                      Iniciando sesión...
                    </>
                  ) : (
                    <>
                      Iniciar Sesión
                      <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
                    </>
                  )}
                </span>
              </Button>
            </motion.div>
          </motion.form>



          <motion.p 
            className="text-center text-sm text-muted-foreground mt-8"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.8 }}
          >
            ¿No tienes una cuenta?{" "}
            <Link 
              href="/signup" 
              className="text-primary hover:text-primary/80 font-medium transition-colors relative group inline-block"
            >
              <span className="relative z-10">Regístrate aquí</span>
              <motion.div
                className="absolute -bottom-1 left-0 h-0.5 bg-primary/50"
                initial={{ width: 0 }}
                whileHover={{ width: "100%" }}
                transition={{ duration: 0.3 }}
              />
            </Link>
          </motion.p>
        </motion.div>
      </div>

      {/* Right Side - Gradient with Content */}
      <div className="flex-1 bg-gradient-to-br from-primary via-primary/90 to-primary/80 p-8 flex items-center justify-center relative overflow-hidden">
        {/* Animated Background Pattern */}
        <div className="absolute inset-0">
          <motion.div 
            className="absolute top-20 left-20 w-32 h-32 border border-white/20 rounded-full"
            animate={{ 
              scale: [1, 1.2, 1],
              rotate: [0, 180, 360],
            }}
            transition={{ 
              duration: 20,
              repeat: Infinity,
              ease: "linear"
            }}
          />
          <motion.div 
            className="absolute top-40 right-32 w-24 h-24 border border-white/20 rounded-full"
            animate={{ 
              scale: [1.2, 1, 1.2],
              rotate: [360, 180, 0],
            }}
            transition={{ 
              duration: 15,
              repeat: Infinity,
              ease: "linear"
            }}
          />
          <motion.div 
            className="absolute bottom-32 left-32 w-40 h-40 border border-white/20 rounded-full"
            animate={{ 
              scale: [1, 1.3, 1],
              rotate: [0, -180, -360],
            }}
            transition={{ 
              duration: 25,
              repeat: Infinity,
              ease: "linear"
            }}
          />
          <motion.div 
            className="absolute bottom-20 right-20 w-28 h-28 border border-white/20 rounded-full"
            animate={{ 
              scale: [1.3, 1, 1.3],
              rotate: [-360, -180, 0],
            }}
            transition={{ 
              duration: 18,
              repeat: Infinity,
              ease: "linear"
            }}
          />
        </div>

        <motion.div 
          className="relative z-10 max-w-lg text-white"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          {/* Main Content */}
          <motion.div 
            className="mb-12"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
          >
            <h2 className="text-4xl font-bold mb-6 leading-tight">
              Continúa donde lo dejaste
            </h2>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              Accede a tu historial de consultas, configuraciones personalizadas y
              continúa aprovechando al máximo tu asistente legal inteligente.
            </p>
          </motion.div>

          {/* Recent Activity */}
          <motion.div 
            className="space-y-6 mb-12"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.4 }}
          >
            <motion.div 
              className="flex items-start space-x-4 group cursor-pointer"
              whileHover={{ x: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <motion.div 
                className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center group-hover:bg-white/30 transition-colors"
                whileHover={{ scale: 1.05 }}
              >
                <Clock className="h-6 w-6 text-white" />
              </motion.div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Historial Completo</h3>
                <p className="text-white/80">Accede a todas tus consultas anteriores y respuestas</p>
              </div>
            </motion.div>

            <motion.div 
              className="flex items-start space-x-4 group cursor-pointer"
              whileHover={{ x: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <motion.div 
                className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center group-hover:bg-white/30 transition-colors"
                whileHover={{ scale: 1.05 }}
              >
                <TrendingUp className="h-6 w-6 text-white" />
              </motion.div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Análisis Personalizado</h3>
                <p className="text-white/80">Recomendaciones basadas en tu actividad y consultas</p>
              </div>
            </motion.div>

            <motion.div 
              className="flex items-start space-x-4 group cursor-pointer"
              whileHover={{ x: 5 }}
              transition={{ type: "spring", stiffness: 300 }}
            >
              <motion.div 
                className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center group-hover:bg-white/30 transition-colors"
                whileHover={{ scale: 1.05 }}
              >
                <Users className="h-6 w-6 text-white" />
              </motion.div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Soporte Prioritario</h3>
                <p className="text-white/80">Acceso directo a nuestro equipo de expertos legales</p>
              </div>
            </motion.div>
          </motion.div>

          {/* Trust Indicators */}
          <motion.div 
            className="bg-white/10 rounded-lg p-6 backdrop-blur-sm"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            whileHover={{ scale: 1.02 }}
          >
            <div className="flex items-center space-x-2 mb-4">
              <CheckCircle className="h-5 w-5 text-white" />
              <span className="font-semibold">Datos Seguros y Privados</span>
            </div>
            <p className="text-white/80 text-sm">
              Tu información está protegida con encriptación de nivel bancario.
              Cumplimos con RGPD y todas las normativas de privacidad españolas.
            </p>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}
