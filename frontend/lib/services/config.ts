/**
 * Service Configuration
 * Centralized configuration for all API services
 */

export const API_CONFIG = {
  // Base URLs
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
  WEBSOCKET_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws',
  
  // Timeouts (in milliseconds)
  REQUEST_TIMEOUT: 30000, // 30 seconds
  UPLOAD_TIMEOUT: 120000, // 2 minutes
  
  // Retry configuration
  MAX_RETRIES: 3,
  RETRY_DELAY: 1000, // 1 second base delay
  
  // Token management
  TOKEN_REFRESH_THRESHOLD: 300, // 5 minutes before expiry
  AUTO_REFRESH_INTERVAL: 60000, // Check every minute
  
  // File upload limits
  MAX_FILE_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_IMAGE_TYPES: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
  ALLOWED_DOCUMENT_TYPES: ['application/pdf', 'text/plain', 'application/msword'],
  
  // Pagination defaults
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
  
  // Chat configuration
  MAX_MESSAGE_LENGTH: 5000,
  MAX_CONVERSATION_TITLE_LENGTH: 100,
  TYPING_INDICATOR_DELAY: 500,
  
  // Cache configuration
  CACHE_DURATION: 5 * 60 * 1000, // 5 minutes
  MAX_CACHE_SIZE: 100, // Maximum number of cached items
  
  // Feature flags
  FEATURES: {
    REAL_TIME_CHAT: true,
    FILE_UPLOAD: true,
    CONVERSATION_EXPORT: true,
    VOICE_INPUT: false,
    DARK_MODE: true,
    ANALYTICS: true
  },
  
  // API endpoints
  ENDPOINTS: {
    // Authentication
    LOGIN: '/auth/login',
    REGISTER: '/auth/register',
    LOGOUT: '/auth/logout',
    REFRESH_TOKEN: '/auth/token/refresh',
    VERIFY_TOKEN: '/auth/token/verify',
    PASSWORD_RESET: '/auth/password-reset',
    PASSWORD_RESET_CONFIRM: '/auth/password-reset/confirm',
    CHANGE_PASSWORD: '/auth/change-password',
    
    // User management
    USER_PROFILE: '/user/profile/',
    USER_STATS: '/user/stats/',
    USER_PREFERENCES: '/user/preferences/',
    USER_ACTIVITY: '/user/activity/',
    USER_EXPORT: '/user/export/',
    USER_NOTIFICATIONS: '/user/notifications/',
    PROFILE_PICTURE: '/user/profile/picture/',
    
    // Chat and AI
    CHAT_MESSAGE: '/chat/message/',
    CONVERSATIONS: '/chat/conversations/',
    CONVERSATION_SEARCH: '/chat/search/',
    CHAT_SUGGESTIONS: '/chat/suggestions/',
    MESSAGE_RATE: '/chat/messages/{id}/rate/',
    MESSAGE_REPORT: '/chat/messages/{id}/report/',
    CONVERSATION_EXPORT: '/chat/conversations/{id}/export/',
    CHAT_STATS: '/chat/stats/',
    
    // Legal documents
    LEGAL_DOCUMENTS: '/legal/documents/',
    LEGAL_SEARCH: '/legal/search/',
    
    // System
    HEALTH: '/health/',
    VERSION: '/version/'
  }
} as const

// Environment-specific configurations
export const getEnvironmentConfig = () => {
  const env = process.env.NODE_ENV || 'development'
  
  const configs = {
    development: {
      ...API_CONFIG,
      BASE_URL: 'http://localhost:8000/api',
      WEBSOCKET_URL: 'ws://localhost:8000/ws',
      REQUEST_TIMEOUT: 10000, // Shorter timeout for dev
      FEATURES: {
        ...API_CONFIG.FEATURES,
        ANALYTICS: false // Disable analytics in dev
      }
    },
    
    production: {
      ...API_CONFIG,
      BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'https://api.ovra-ai.com/api',
      WEBSOCKET_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://api.ovra-ai.com/ws',
      REQUEST_TIMEOUT: 30000,
      FEATURES: {
        ...API_CONFIG.FEATURES,
        ANALYTICS: true
      }
    },
    
    test: {
      ...API_CONFIG,
      BASE_URL: 'http://localhost:8001/api',
      WEBSOCKET_URL: 'ws://localhost:8001/ws',
      REQUEST_TIMEOUT: 5000,
      MAX_RETRIES: 1,
      FEATURES: {
        ...API_CONFIG.FEATURES,
        ANALYTICS: false,
        REAL_TIME_CHAT: false
      }
    }
  }
  
  return configs[env as keyof typeof configs] || configs.development
}

// Export the current environment config
export const config = getEnvironmentConfig()

// Utility functions for configuration
export const configUtils = {
  /**
   * Get endpoint URL with base URL
   */
  getEndpointUrl: (endpoint: string): string => {
    return `${config.BASE_URL}${endpoint}`
  },
  
  /**
   * Replace placeholders in endpoint URLs
   */
  formatEndpoint: (endpoint: string, params: Record<string, string>): string => {
    let formatted = endpoint
    Object.entries(params).forEach(([key, value]) => {
      formatted = formatted.replace(`{${key}}`, value)
    })
    return formatted
  },
  
  /**
   * Check if a feature is enabled
   */
  isFeatureEnabled: (feature: keyof typeof API_CONFIG.FEATURES): boolean => {
    return config.FEATURES[feature] || false
  },
  
  /**
   * Get file size limit in bytes
   */
  getFileSizeLimit: (): number => {
    return config.MAX_FILE_SIZE
  },
  
  /**
   * Check if file type is allowed
   */
  isFileTypeAllowed: (fileType: string, category: 'image' | 'document'): boolean => {
    const allowedTypes = category === 'image' 
      ? config.ALLOWED_IMAGE_TYPES 
      : config.ALLOWED_DOCUMENT_TYPES
    return allowedTypes.includes(fileType)
  }
} as const
