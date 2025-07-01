"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Checkbox } from "@/components/ui/checkbox"
import { Scale, Eye, EyeOff, Shield, Zap, BookOpen, User, Mail, Lock, ArrowRight, CheckCircle2, Sparkles } from "lucide-react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { motion, AnimatePresence } from "framer-motion"
import { PasswordStrengthIndicator } from "@/components/password-strength-indicator"

export default function SignupPage() {
  const [formData, setFormData] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [acceptTerms, setAcceptTerms] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [errors, setErrors] = useState({
    fullName: "",
    email: "",
    password: "",
    confirmPassword: "",
    terms: ""
  })
  const [passwordStrength, setPasswordStrength] = useState(0)
  const router = useRouter()

  const checkPasswordStrength = (password: string) => {
    let strength = 0
    if (password.length >= 8) strength++
    if (password.match(/[a-z]/) && password.match(/[A-Z]/)) strength++
    if (password.match(/[0-9]/)) strength++
    if (password.match(/[^a-zA-Z0-9]/)) strength++
    setPasswordStrength(strength)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData({
      ...formData,
      [name]: value,
    })
    
    // Clear errors when user types
    if (errors[name as keyof typeof errors]) {
      setErrors({
        ...errors,
        [name]: ""
      })
    }
    
    // Check password strength
    if (name === "password") {
      checkPasswordStrength(value)
    }
  }

  const validateForm = () => {
    const newErrors = {
      fullName: "",
      email: "",
      password: "",
      confirmPassword: "",
      terms: ""
    }
    
    if (!formData.fullName.trim()) {
      newErrors.fullName = "El nombre completo es requerido"
    }
    
    if (!formData.email) {
      newErrors.email = "El correo electrónico es requerido"
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "El correo electrónico no es válido"
    }
    
    if (!formData.password) {
      newErrors.password = "La contraseña es requerida"
    } else if (formData.password.length < 8) {
      newErrors.password = "La contraseña debe tener al menos 8 caracteres"
    }
    
    if (!formData.confirmPassword) {
      newErrors.confirmPassword = "Debes confirmar tu contraseña"
    } else if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = "Las contraseñas no coinciden"
    }
    
    if (!acceptTerms) {
      newErrors.terms = "Debes aceptar los términos y condiciones"
    }
    
    setErrors(newErrors)
    return Object.values(newErrors).every(error => !error)
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)

    // Simulate signup process
    setTimeout(() => {
      setIsLoading(false)
      // Redirect to chat page after successful signup
      router.push("/chat")
    }, 2000)
  }

  const passwordStrengthColors = ["", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"]
  const passwordStrengthTexts = ["", "Débil", "Regular", "Buena", "Excelente"]

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
              Crear Cuenta
            </h1>
            <p className="text-muted-foreground flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-primary" />
              Comienza tu prueba gratuita de 7 días
            </p>
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
              <Label htmlFor="fullName" className="text-sm font-medium flex items-center gap-2">
                <User className="h-4 w-4 text-muted-foreground" />
                Nombre Completo
              </Label>
              <div className="relative">
                <Input
                  id="fullName"
                  name="fullName"
                  placeholder="Juan García López"
                  value={formData.fullName}
                  onChange={handleInputChange}
                  className={`h-12 pl-4 pr-4 transition-all duration-200 border-2 hover:border-primary/50 focus:border-primary ${
                    errors.fullName ? "border-destructive" : ""
                  }`}
                />
                {errors.fullName && (
                  <motion.p 
                    className="text-sm text-destructive mt-1"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {errors.fullName}
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
              <Label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                <Mail className="h-4 w-4 text-muted-foreground" />
                Correo Electrónico
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="tu@email.com"
                  value={formData.email}
                  onChange={handleInputChange}
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
              transition={{ duration: 0.5, delay: 0.6 }}
            >
              <Label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                <Lock className="h-4 w-4 text-muted-foreground" />
                Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="Mínimo 8 caracteres"
                  value={formData.password}
                  onChange={handleInputChange}
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
                <PasswordStrengthIndicator strength={passwordStrength} password={formData.password} />
              </div>
            </motion.div>

            <motion.div 
              className="space-y-2"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.5, delay: 0.7 }}
            >
              <Label htmlFor="confirmPassword" className="text-sm font-medium flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-muted-foreground" />
                Confirmar Contraseña
              </Label>
              <div className="relative">
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? "text" : "password"}
                  placeholder="Repite tu contraseña"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  className={`h-12 pl-4 pr-12 transition-all duration-200 border-2 hover:border-primary/50 focus:border-primary ${
                    errors.confirmPassword ? "border-destructive" : ""
                  }`}
                />
                <motion.button
                  type="button"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent text-muted-foreground hover:text-foreground transition-colors"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  whileHover={{ scale: 1.1 }}
                  whileTap={{ scale: 0.95 }}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </motion.button>
                {errors.confirmPassword && (
                  <motion.p 
                    className="text-sm text-destructive mt-1"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {errors.confirmPassword}
                  </motion.p>
                )}
              </div>
            </motion.div>

            <motion.div 
              className="flex items-start space-x-2"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.8 }}
            >
              <Checkbox
                id="terms"
                checked={acceptTerms}
                onCheckedChange={(checked) => {
                  setAcceptTerms(checked as boolean)
                  if (checked && errors.terms) {
                    setErrors({ ...errors, terms: "" })
                  }
                }}
                className="mt-1"
              />
              <div>
                <Label htmlFor="terms" className="text-sm text-muted-foreground leading-relaxed cursor-pointer">
                  Acepto los{" "}
                  <Link href="/terms" className="text-primary hover:text-primary/80 underline underline-offset-2">
                    términos y condiciones
                  </Link>{" "}
                  y la{" "}
                  <Link href="/privacy" className="text-primary hover:text-primary/80 underline underline-offset-2">
                    política de privacidad
                  </Link>
                </Label>
                {errors.terms && (
                  <motion.p 
                    className="text-sm text-destructive mt-1"
                    initial={{ opacity: 0, y: -10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.2 }}
                  >
                    {errors.terms}
                  </motion.p>
                )}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.9 }}
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
                      Creando cuenta...
                    </>
                  ) : (
                    <>
                      Crear Cuenta Gratuita
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
            transition={{ duration: 0.5, delay: 1 }}
          >
            ¿Ya tienes una cuenta?{" "}
            <Link 
              href="/login" 
              className="text-primary hover:text-primary/80 font-medium transition-colors relative group inline-block"
            >
              <span className="relative z-10">Inicia sesión aquí</span>
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

        <div className="relative z-10 max-w-lg text-white">
          {/* Main Content */}
          <div className="mb-12">
            <div className="flex items-center space-x-2 mb-6">
              <Scale className="h-10 w-10 text-white" />
              <span className="text-3xl font-bold">Ovra AI</span>
            </div>
            <h2 className="text-4xl font-bold mb-6 leading-tight">
              Tu Asistente Legal Inteligente para España
            </h2>
            <p className="text-xl text-white/90 mb-8 leading-relaxed">
              Especializado en legislación fiscal española para profesionales del arte y la cultura.
              Respuestas precisas basadas en normativas oficiales.
            </p>
          </div>

          {/* Features */}
          <div className="space-y-6 mb-12">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <BookOpen className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Legislación Actualizada</h3>
                <p className="text-white/80">Acceso a IVA, IRPF, Sociedades y más normativas fiscales</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Respuestas Instantáneas</h3>
                <p className="text-white/80">Consultas legales resueltas en segundos con referencias oficiales</p>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                <Shield className="h-6 w-6 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-lg mb-1">Información Confiable</h3>
                <p className="text-white/80">Basado en fuentes oficiales del BOE y normativas vigentes</p>
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-2 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">5,000+</div>
              <div className="text-white/80 text-sm">Profesionales Registrados</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-1">50,000+</div>
              <div className="text-white/80 text-sm">Consultas Resueltas</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
