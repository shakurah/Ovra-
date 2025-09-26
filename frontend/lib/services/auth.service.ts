/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */

import { BaseApiService } from './base.service'

export interface LoginRequest {
  email: string
  password: string
}

export interface RegisterRequest {
  email: string
  firstName: string
  lastName: string
  password: string
  confirm_password: string
  company?: string
  phone?: string
  agree_to_terms: boolean
}

export interface User {
  id: string
  email: string
  firstName: string
  lastName: string
}

export interface AuthResponse {
  access: string
  refresh: string
  user: User
}

export interface TokenRefreshResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export class AuthService extends BaseApiService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await this.post<AuthResponse>('/auth/login', credentials)

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access)
      localStorage.setItem('refresh_token', response.refresh)
    }

    this.setUser(response.user)
    return response
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    const response = await this.post<AuthResponse>('/auth/register', userData)

    this.setTokens(response.access, response.refresh || '')
    this.setUser(response.user)

    return response
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      if (this.getAccessToken()) {
        await this.post('/auth/logout/', {}, true)
      }
    } catch (error) {
      console.error('Logout API error:', error)
    } finally {
      this.clearTokens()
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<TokenRefreshResponse> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) throw new Error('No refresh token available')

    const response = await this.post<TokenRefreshResponse>(
      '/auth/token/refresh/',
      { refresh_token: refreshToken }
    )

    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', response.access_token)
      localStorage.setItem('refresh_token', response.refresh_token)
    }

    return response
  }

  /**
   * Verify if current token is valid
   */
  async verifyToken(): Promise<boolean> {
    try {
      const token = this.getAccessToken()
      if (!token) return false

      await this.post('/auth/token/verify/', { token }, false)
      return true
    } catch {
      return false
    }
  }

  /**
   * Check if user is currently authenticated
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken()
  }

  /**
   * Get current user data
   */
  getCurrentUser(): User | null {
    return this.getUser()
  }

  /**
   * Get stored access token
   */
  getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('refresh_token')
  }

  /**
   * Backward compatibility with old naming
   */
  getStoredToken(): string | null {
    return this.getAccessToken()
  }

  getStoredRefreshToken(): string | null {
    return this.getRefreshToken()
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    return this.post('/auth/password-reset/', { email })
  }

  /**
   * Reset password
   */
  async resetPassword(
    token: string,
    newPassword: string,
    confirmPassword: string
  ): Promise<{ message: string }> {
    return this.post('/auth/password-reset/confirm/', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    })
  }

  /**
   * Change password
   */
  async changePassword(
    currentPassword: string,
    newPassword: string,
    confirmPassword: string
  ): Promise<{ message: string }> {
    return this.post(
      '/auth/change-password/',
      {
        current_password: currentPassword,
        new_password: newPassword,
        confirm_password: confirmPassword,
      },
      true
    )
  }

  /**
   * Auto refresh if close to expiry
   */
  async autoRefreshToken(): Promise<boolean> {
    try {
      const token = this.getAccessToken()
      if (!token) return false

      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const timeUntilExpiry = payload.exp - currentTime

      if (timeUntilExpiry < 300) {
        await this.refreshToken()
        return true
      }

      return false
    } catch (error) {
      console.error('Auto refresh token error:', error)
      return false
    }
  }
}

// Export singleton instance
export const authService = new AuthService()
