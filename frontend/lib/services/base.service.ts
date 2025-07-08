/**
 * Base API Service
 * Provides common functionality for all API services
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'

export interface ApiError {
  message: string
  errors?: Record<string, string[]>
  code?: number
}

export interface ApiResponse<T = any> {
  code: number
  is_success: boolean
  message: string
  data?: T
}

export class BaseApiService {
  protected baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    console.log('baseUrl: ', baseUrl);
    this.baseUrl = baseUrl
  }

  /**
   * Get authentication headers with current token
   */
  protected getAuthHeaders(): Record<string, string> {
    const token = this.getAccessToken()
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    }
  }

  /**
   * Get headers without authentication
   */
  protected getHeaders(): Record<string, string> {
    return {
      'Content-Type': 'application/json'
    }
  }

  /**
   * Handle API response and error cases
   */
  protected async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      const error: ApiError = {
        message: errorData.message || `HTTP error! status: ${response.status}`,
        errors: errorData.errors,
        code: response.status
      }
      throw error
    }
    return response.json()
  }

  /**
   * Make GET request
   */
  protected async get<T>(endpoint: string, requireAuth: boolean = false): Promise<T> {
    const headers = requireAuth ? this.getAuthHeaders() : this.getHeaders()
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'GET',
      headers
    })
    return this.handleResponse<T>(response)
  }

  /**
   * Make POST request
   */
  protected async post<T>(
    endpoint: string, 
    data?: any, 
    requireAuth: boolean = false
  ): Promise<T> {
    const headers = requireAuth ? this.getAuthHeaders() : this.getHeaders()
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'POST',
      headers,
      body: data ? JSON.stringify(data) : undefined
    })
    return this.handleResponse<T>(response)
  }

  /**
   * Make PUT request
   */
  protected async put<T>(
    endpoint: string, 
    data?: any, 
    requireAuth: boolean = true
  ): Promise<T> {
    const headers = requireAuth ? this.getAuthHeaders() : this.getHeaders()
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PUT',
      headers,
      body: data ? JSON.stringify(data) : undefined
    })
    return this.handleResponse<T>(response)
  }

  /**
   * Make PATCH request
   */
  protected async patch<T>(
    endpoint: string, 
    data?: any, 
    requireAuth: boolean = true
  ): Promise<T> {
    const headers = requireAuth ? this.getAuthHeaders() : this.getHeaders()
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'PATCH',
      headers,
      body: data ? JSON.stringify(data) : undefined
    })
    return this.handleResponse<T>(response)
  }

  /**
   * Make DELETE request
   */
  protected async delete<T>(endpoint: string, requireAuth: boolean = true): Promise<T> {
    const headers = requireAuth ? this.getAuthHeaders() : this.getHeaders()
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      method: 'DELETE',
      headers
    })
    return this.handleResponse<T>(response)
  }

  /**
   * Token management utilities
   */
  protected getAccessToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('access_token')
  }

  protected getRefreshToken(): string | null {
    if (typeof window === 'undefined') return null
    return localStorage.getItem('refresh_token')
  }

  protected setTokens(accessToken: string, refreshToken: string): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('access_token', accessToken)
    if (refreshToken) {
      localStorage.setItem('refresh_token', refreshToken)
    }
  }

  protected clearTokens(): void {
    if (typeof window === 'undefined') return
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  protected setUser(user: any): void {
    if (typeof window === 'undefined') return
    localStorage.setItem('user', JSON.stringify(user))
  }

  protected getUser(): any | null {
    if (typeof window === 'undefined') return null
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    return this.get('/health/')
  }
}
