/**
 * User Service
 * Handles user profile management and user-related operations
 */

import { BaseApiService } from './base.service'
import type { User } from './auth.service'

export interface UserProfileUpdateRequest {
  full_name?: string
  profile_picture?: string | null
  preferred_language?: string
}

export interface UserProfileResponse extends User {
  // Additional profile fields can be added here
}

export interface UserStatsResponse {
  total_queries: number
  queries_this_month: number
  subscription_status: string
  trial_queries_remaining?: number
}

export class UserService extends BaseApiService {
  /**
   * Get current user profile
   */
  async getProfile(): Promise<UserProfileResponse> {
    const response = await this.get<any>('/auth/me', true)
    return response.user || response
  }

  /**
   * Update user profile
   */
  async updateProfile(data: UserProfileUpdateRequest): Promise<UserProfileResponse> {
    const response = await this.patch<UserProfileResponse>('/user/profile/', data, true)
    
    // Update local storage with new user data
    this.setUser(response)
    
    return response
  }

  /**
   * Upload profile picture
   */
  async uploadProfilePicture(file: File): Promise<{ profile_picture: string }> {
    const formData = new FormData()
    formData.append('profile_picture', file)

    const token = this.getAccessToken()
    const response = await fetch(`${this.baseUrl}/user/profile/picture/`, {
      method: 'POST',
      headers: {
        ...(token && { Authorization: `Bearer ${token}` })
      },
      body: formData
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.message || 'Failed to upload profile picture')
    }

    const result = await response.json()
    
    // Update local user data
    const currentUser = this.getUser()
    if (currentUser) {
      currentUser.profile_picture = result.profile_picture
      this.setUser(currentUser)
    }
    
    return result
  }

  /**
   * Delete profile picture
   */
  async deleteProfilePicture(): Promise<{ message: string }> {
    const response = await this.delete<{ message: string }>('/user/profile/picture/', true)
    
    // Update local user data
    const currentUser = this.getUser()
    if (currentUser) {
      currentUser.profile_picture = null
      this.setUser(currentUser)
    }
    
    return response
  }

  /**
   * Get user statistics and usage data
   */
  async getUserStats(): Promise<UserStatsResponse> {
    return this.get<UserStatsResponse>('/user/stats/', true)
  }

  /**
   * Delete user account
   */
  async deleteAccount(password: string): Promise<{ message: string }> {
    const response = await this.delete<{ message: string }>('/user/account/', true)
    
    // Clear local storage after successful deletion
    this.clearTokens()
    
    return response
  }

  /**
   * Get user preferences
   */
  async getPreferences(): Promise<Record<string, any>> {
    return this.get<Record<string, any>>('/user/preferences/', true)
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Record<string, any>): Promise<Record<string, any>> {
    return this.patch<Record<string, any>>('/user/preferences/', preferences, true)
  }

  /**
   * Get user activity history
   */
  async getActivityHistory(page: number = 1, limit: number = 20): Promise<{
    results: Array<{
      id: number
      action: string
      timestamp: string
      details?: Record<string, any>
    }>
    count: number
    next: string | null
    previous: string | null
  }> {
    return this.get<any>(`/user/activity/?page=${page}&limit=${limit}`, true)
  }

  /**
   * Export user data (GDPR compliance)
   */
  async exportUserData(): Promise<{ download_url: string; expires_at: string }> {
    return this.post<{ download_url: string; expires_at: string }>('/user/export/', {}, true)
  }

  /**
   * Update notification settings
   */
  async updateNotificationSettings(settings: {
    email_notifications?: boolean
    push_notifications?: boolean
    marketing_emails?: boolean
  }): Promise<{ message: string }> {
    return this.patch<{ message: string }>('/user/notifications/', settings, true)
  }

  /**
   * Get notification settings
   */
  async getNotificationSettings(): Promise<{
    email_notifications: boolean
    push_notifications: boolean
    marketing_emails: boolean
  }> {
    return this.get<any>('/user/notifications/', true)
  }
}

// Export singleton instance
export const userService = new UserService()
