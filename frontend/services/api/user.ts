/**
 * User API service
 */

import { apiClient } from './base'
import type { User } from './auth'

export interface UserProfileUpdateRequest {
  full_name?: string
  profile_picture?: File
  phone_number?: string
  profession?: string
  company_name?: string
  preferred_language?: string
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
  confirm_password: string
}

export interface UserStats {
  total_queries: number
  queries_this_month: number
  trial_queries_used: number
  trial_queries_remaining: number
}

export class UserService {
  async getProfile(): Promise<User> {
    return apiClient.get<User>('/user/profile/')
  }

  async updateProfile(data: UserProfileUpdateRequest): Promise<User> {
    // Handle file upload if profile picture is included
    if (data.profile_picture) {
      const formData = new FormData()
      Object.entries(data).forEach(([key, value]) => {
        if (value !== undefined) {
          formData.append(key, value)
        }
      })

      const response = await fetch(`${apiClient['baseURL']}/user/profile/`, {
        method: 'PATCH',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access_token')}`
        },
        body: formData
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.message || 'Failed to update profile')
      }

      return response.json()
    }

    return apiClient.patch<User>('/user/profile/', data)
  }

  async changePassword(data: ChangePasswordRequest): Promise<{ message: string }> {
    return apiClient.post<{ message: string }>('/user/change-password/', data)
  }

  async getStats(): Promise<UserStats> {
    return apiClient.get<UserStats>('/user/stats/')
  }

  async deleteAccount(): Promise<{ message: string }> {
    return apiClient.delete<{ message: string }>('/user/profile/')
  }
}

// Export singleton instance
export const userService = new UserService()
