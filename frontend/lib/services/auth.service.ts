/**
 * Authentication Service
 * Handles user authentication, registration, and token management
 */

import { BaseApiService, ApiResponse } from './base.service'

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
  token: string
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

    // Store token and user data
    this.setTokens(response.token, '')
    this.setUser(response.user)

    return response
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<AuthResponse> {
    // Register endpoint returns user and token
    const response = await this.post<AuthResponse>('/auth/register', userData)
    
    // Store token and user data
    this.setTokens(response.token, '')
    this.setUser(response.user)

    return response
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      // Call logout endpoint if token exists
      if (this.getAccessToken()) {
        await this.post('/auth/logout/', {}, true)
      }
    } catch (error) {
      console.error('Logout API error:', error)
      // Continue with local cleanup even if API call fails
    } finally {
      // Always clear local storage
      this.clearTokens()
    }
  }

  /**
   * Refresh access token using refresh token
   */
  async refreshToken(): Promise<TokenRefreshResponse> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) {
      throw new Error('No refresh token available')
    }

    const response = await this.post<TokenRefreshResponse>(
      '/auth/token/refresh/', 
      { refresh_token: refreshToken }
    )
    
    // Update both tokens in localStorage
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
   * Get current user data from localStorage
   */
  getCurrentUser(): User | null {
    return this.getUser()
  }

  /**
   * Get stored access token
   */
  getStoredToken(): string | null {
    return this.getAccessToken()
  }

  /**
   * Get stored refresh token
   */
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
   * Reset password with token
   */
  async resetPassword(
    token: string, 
    newPassword: string, 
    confirmPassword: string
  ): Promise<{ message: string }> {
    return this.post('/auth/password-reset/confirm/', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword
    })
  }

  /**
   * Change password for authenticated user
   */
  async changePassword(
    currentPassword: string,
    newPassword: string,
    confirmPassword: string
  ): Promise<{ message: string }> {
    return this.post('/auth/change-password/', {
      current_password: currentPassword,
      new_password: newPassword,
      confirm_password: confirmPassword
    }, true)
  }

  /**
   * Auto-refresh token if it's about to expire
   * Call this method periodically or before making API calls
   */
  async autoRefreshToken(): Promise<boolean> {
    try {
      const token = this.getAccessToken()
      if (!token) return false

      // Decode JWT to check expiration (basic check)
      const payload = JSON.parse(atob(token.split('.')[1]))
      const currentTime = Math.floor(Date.now() / 1000)
      const timeUntilExpiry = payload.exp - currentTime

      // Refresh if token expires in less than 5 minutes
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
