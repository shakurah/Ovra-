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

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/$/, "")

function getAccessToken() {
  return localStorage.getItem("accessToken") || localStorage.getItem("access_token")
}
function getRefreshToken() {
  return localStorage.getItem("refreshToken") || localStorage.getItem("refresh_token")
}
function setTokens(access?: string | null, refresh?: string | null) {
  if (access) {
    localStorage.setItem("accessToken", access)
    localStorage.setItem("access_token", access)
  }
  if (refresh) {
    localStorage.setItem("refreshToken", refresh)
    localStorage.setItem("refresh_token", refresh)
  }
}
function clearTokens() {
  localStorage.removeItem("accessToken")
  localStorage.removeItem("access_token")
  localStorage.removeItem("refreshToken")
  localStorage.removeItem("refresh_token")
}

let pendingRefresh: Promise<string> | null = null

async function doRefreshOnce(): Promise<string> {
  // If a refresh is already in progress, reuse it
  if (pendingRefresh) return pendingRefresh

  const refresh = getRefreshToken()
  if (!refresh) throw new Error("no refresh token")

  pendingRefresh = (async () => {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh })
    })

    const body = await res.json().catch(() => ({}))
    if (!res.ok || !body.access) {
      clearTokens()
      pendingRefresh = null
      throw new Error("refresh failed")
    }

    setTokens(body.access, body.refresh || refresh)
    const access = body.access
    pendingRefresh = null
    return access
  })()

  return pendingRefresh
}

/**
 * Generic fetch wrapper that attaches Authorization and refreshes token once on 401.
 */
export async function fetchWithAuth(input: RequestInfo, init: RequestInit = {}): Promise<Response> {
  const baseUrl = input.toString().startsWith("http") ? input.toString() : `${API_BASE}${input}`
  const headers = { "Content-Type": "application/json", ...(init.headers || {}) } as Record<string, string>

  let access = getAccessToken()
  if (access) headers.Authorization = `Bearer ${access}`
  const opts = { ...init, headers }

  let res = await fetch(baseUrl, opts)
  if (res.status !== 401) return res

  // try refresh once
  try {
    const newAccess = await doRefreshOnce()
    headers.Authorization = `Bearer ${newAccess}`
    const retryOpts = { ...init, headers }
    const retried = await fetch(baseUrl, retryOpts)
    if (retried.status === 401) {
      // final failure -> clear tokens
      clearTokens()
    }
    return retried
  } catch (err) {
    clearTokens()
    throw err
  }
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
      // also store modern keys used elsewhere
      localStorage.setItem('accessToken', response.access)
      localStorage.setItem('refreshToken', response.refresh)
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
  async refreshToken(): Promise<any> {
    const refreshToken = this.getRefreshToken()
    if (!refreshToken) throw new Error('No refresh token available')

    // send key named "refresh" (SimpleJWT expects this)
    const response = await this.post<any>(
      '/auth/token/refresh/',
      { refresh: refreshToken }
    )

    if (typeof window !== 'undefined') {
      // handle both possible response shapes { access } or { access_token }
      const access = response.access || response.access_token
      const refresh = response.refresh || response.refresh_token

      if (access) {
        localStorage.setItem('access_token', access)
        localStorage.setItem('accessToken', access)
      }
      if (refresh) {
        localStorage.setItem('refresh_token', refresh)
        localStorage.setItem('refreshToken', refresh)
      }
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
