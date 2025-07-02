/**
 * API Services - Modular Architecture
 *
 * This file provides a centralized access point to all API services.
 * Each service is responsible for a specific domain of functionality.
 *
 * Services:
 * - AuthService: Authentication, registration, token management
 * - UserService: User profile, preferences, account management
 * - ChatService: AI chat, conversations, legal queries
 * - BaseService: Common HTTP methods and utilities
 *
 * Usage:
 * import { authService, userService, chatService } from '@/lib/api'
 *
 * // Authentication
 * await authService.login({ email, password })
 *
 * // User management
 * await userService.getProfile()
 *
 * // Chat with AI
 * await chatService.sendMessage({ message: "What is VAT?" })
 */

// Export all services and types
export * from './services'

// Legacy compatibility - keep for existing code
export { authService as apiService } from './services'
