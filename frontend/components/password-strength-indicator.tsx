import { motion } from "framer-motion"

interface PasswordStrengthIndicatorProps {
  strength: number
  password: string
}

export function PasswordStrengthIndicator({ strength, password }: PasswordStrengthIndicatorProps) {
  const strengthColors = ["", "bg-red-500", "bg-orange-500", "bg-yellow-500", "bg-green-500"]
  const strengthTexts = ["", "Débil", "Regular", "Buena", "Excelente"]
  
  if (!password) return null

  return (
    <motion.div 
      className="mt-2"
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <div className="flex gap-1 mb-1">
        {[1, 2, 3, 4].map((level) => (
          <motion.div
            key={level}
            className={`h-1 flex-1 rounded-full transition-all duration-300 ${
              level <= strength ? strengthColors[strength] : "bg-muted"
            }`}
            initial={{ scaleX: 0 }}
            animate={{ scaleX: level <= strength ? 1 : 0.3 }}
            transition={{ duration: 0.3, delay: level * 0.05 }}
          />
        ))}
      </div>
      {strength > 0 && (
        <motion.p 
          className={`text-xs ${strength <= 2 ? "text-destructive" : "text-muted-foreground"}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.2 }}
        >
          Seguridad: {strengthTexts[strength]}
        </motion.p>
      )}
    </motion.div>
  )
} 