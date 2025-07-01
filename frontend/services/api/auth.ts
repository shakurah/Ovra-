/**
 * Authentication API service
 */

import { apiClient } from './base'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  full_name: string
  password: string
  confirm_password: string
  phone_number?: string
  profession?: string
  company_name?: string
  preferred_language?: string
}

export interface User {
  id: number
  email: string
  full_name: string
  preferred_language: string
  created_at: string
  display_name: string
  profile_picture?: string
  phone_number?: string
  profession?: string
  company_name?: string
}

export interface AuthResponse {
  message: string
  user: User
  tokens: {
    access: string
    refresh: string
  }
}

export interface TokenRefreshResponse {
  access: string
}

export class AuthService {
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login/', credentials)
    
    // Store tokens in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))
    }

    return response
  }

  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register/', userData)
    
    // Store tokens in localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.tokens.access)
      localStorage.setItem('refresh_token', response.tokens.refresh)
      localStorage.setItem('user', JSON.stringify(response.user))
    }

    return response
  }

  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout/')
    } catch (error) {
      console.error('Logout API error:', error)
    } finally {
      // Clear local storage regardless of API call success
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
      }
    }
  }

  async refreshToken(): Promise<TokenRefreshResponse> {
    const refreshToken = typeof window !== 'undefined' ? localStorage.getItem('refresh_token') : null
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await apiClient.post<TokenRefreshResponse>('/auth/token/refresh/', {
      refresh: refreshToken
    })

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access)
    }
    
    return response
  }

  async verifyToken(): Promise<void> {
    const accessToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (!accessToken) {
      throw new Error('No access token available')
    }

    await apiClient.post('/auth/token/verify/', {
      token: accessToken
    })
  }

  getStoredUser(): User | null {
    if (typeof window === 'undefined') return null
    
    try {
      const userStr = localStorage.getItem('user')
      return userStr ? JSON.parse(userStr) : null
    } catch {
      return null
    }
  }

  getStoredToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  isAuthenticated(): boolean {
    return !!this.getStoredToken() && !!this.getStoredUser()
  }
}

// Export singleton instance
export const authService = new AuthService()
