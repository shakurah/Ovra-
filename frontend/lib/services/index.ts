/**
 * Services Index
 * Central export point for all API services
 */

// Base service and types
export { BaseApiService, API_BASE_URL } from './base.service'
export type { ApiError, ApiResponse } from './base.service'

// Authentication service
export { authService, AuthService } from './auth.service'
export type { 
  LoginRequest, 
  RegisterRequest, 
  User, 
  AuthResponse, 
  TokenRefreshResponse 
} from './auth.service'

// User service
export { userService, UserService } from './user.service'
export type { 
  UserProfileUpdateRequest, 
  UserProfileResponse, 
  UserStatsResponse 
} from './user.service'

// Chat service
export { chatService, ChatService } from './chat.service'
export type { 
  ChatMessage, 
  Conversation, 
  ChatRequest, 
  ChatResponse, 
  ConversationListResponse 
} from './chat.service'

// Toast service
export { toastService } from './toast.service'
export type { ToastConfig, ApiResponse } from './toast.service'

// Service instances for easy access (lazy loading to avoid circular references)
export const services = {
  get auth() { return authService },
  get user() { return userService },
  get chat() { return chatService },
  get toast() { return toastService }
} as const

// Utility functions
export const apiUtils = {
  /**
   * Check if error is authentication related
   */
  isAuthError: (error: any): boolean => {
    return error?.code === 401 || error?.message?.includes('authentication')
  },

  /**
   * Check if error is network related
   */
  isNetworkError: (error: any): boolean => {
    return error?.message?.includes('fetch') || error?.message?.includes('network')
  },

  /**
   * Format API error for display
   */
  formatError: (error: any): string => {
    if (typeof error === 'string') return error
    if (error?.message) return error.message
    if (error?.errors) {
      const firstError = Object.values(error.errors)[0]
      return Array.isArray(firstError) ? firstError[0] : String(firstError)
    }
    return 'An unexpected error occurred'
  },

  /**
   * Auto-retry API calls with exponential backoff
   */
  retryWithBackoff: async <T>(
    apiCall: () => Promise<T>,
    maxRetries: number = 3,
    baseDelay: number = 1000
  ): Promise<T> => {
    let lastError: any
    
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall()
      } catch (error) {
        lastError = error
        
        // Don't retry on authentication errors
        if (error?.code === 401 || error?.message?.includes('authentication')) {
          throw error
        }
        
        // Don't retry on the last attempt
        if (attempt === maxRetries) {
          throw error
        }
        
        // Wait before retrying with exponential backoff
        const delay = baseDelay * Math.pow(2, attempt)
        await new Promise(resolve => setTimeout(resolve, delay))
      }
    }
    
    throw lastError
  }
} as const
