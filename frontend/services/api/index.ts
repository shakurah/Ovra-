/**
 * API services index - exports all API services
 */

// Base API client
export { apiClient, ApiClient, API_CONFIG } from './base'
export type { ApiResponse, ApiError } from './base'

// Authentication service
export { authService, AuthService } from './auth'
export type { 
  LoginRequest, 
  RegisterRequest, 
  User, 
  AuthResponse, 
  TokenRefreshResponse 
} from './auth'

// User service
export { userService, UserService } from './user'
export type { 
  UserProfileUpdateRequest, 
  ChangePasswordRequest, 
  UserStats 
} from './user'

// Chat service
export { chatService, ChatService } from './chat'
export type { 
  ChatMessage, 
  ChatSession, 
  SendMessageRequest, 
  SendMessageResponse, 
  ChatHistory 
} from './chat'

// Health check utility
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  return apiClient.get('/health/')
}
