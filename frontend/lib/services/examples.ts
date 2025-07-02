/**
 * Service Usage Examples
 * 
 * This file demonstrates how to use the modular API services
 * in your React components and pages.
 */

import { authService, userService, chatService, apiUtils } from './index'

// ============================================================================
// AUTHENTICATION EXAMPLES
// ============================================================================

export const authExamples = {
  /**
   * Login user
   */
  async loginUser(email: string, password: string) {
    try {
      const response = await authService.login({ email, password })
      console.log('Login successful:', response.user)
      return response
    } catch (error) {
      console.error('Login failed:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Register new user
   */
  async registerUser(userData: {
    email: string
    full_name: string
    password: string
    confirm_password: string
    preferred_language?: string
  }) {
    try {
      const response = await authService.register(userData)
      console.log('Registration successful:', response.user)
      return response
    } catch (error) {
      console.error('Registration failed:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Check if user is authenticated
   */
  checkAuthStatus() {
    const isAuthenticated = authService.isAuthenticated()
    const currentUser = authService.getCurrentUser()
    
    return {
      isAuthenticated,
      user: currentUser
    }
  },

  /**
   * Logout user
   */
  async logoutUser() {
    try {
      await authService.logout()
      console.log('Logout successful')
    } catch (error) {
      console.error('Logout error:', error)
    }
  }
}

// ============================================================================
// USER MANAGEMENT EXAMPLES
// ============================================================================

export const userExamples = {
  /**
   * Get user profile
   */
  async getUserProfile() {
    try {
      const profile = await userService.getProfile()
      console.log('User profile:', profile)
      return profile
    } catch (error) {
      console.error('Failed to get profile:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Update user profile
   */
  async updateUserProfile(updates: {
    full_name?: string
    preferred_language?: string
  }) {
    try {
      const updatedProfile = await userService.updateProfile(updates)
      console.log('Profile updated:', updatedProfile)
      return updatedProfile
    } catch (error) {
      console.error('Failed to update profile:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Upload profile picture
   */
  async uploadProfilePicture(file: File) {
    try {
      // Validate file size and type
      if (file.size > 10 * 1024 * 1024) { // 10MB
        throw new Error('File size too large')
      }
      
      if (!file.type.startsWith('image/')) {
        throw new Error('Invalid file type')
      }

      const result = await userService.uploadProfilePicture(file)
      console.log('Profile picture uploaded:', result)
      return result
    } catch (error) {
      console.error('Failed to upload picture:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Get user statistics
   */
  async getUserStats() {
    try {
      const stats = await userService.getUserStats()
      console.log('User stats:', stats)
      return stats
    } catch (error) {
      console.error('Failed to get stats:', apiUtils.formatError(error))
      throw error
    }
  }
}

// ============================================================================
// CHAT SERVICE EXAMPLES
// ============================================================================

export const chatExamples = {
  /**
   * Send a message to AI
   */
  async sendMessage(message: string, conversationId?: string) {
    try {
      const response = conversationId 
        ? await chatService.continueConversation(conversationId, message)
        : await chatService.startConversation(message)
      
      console.log('AI response:', response)
      return response
    } catch (error) {
      console.error('Failed to send message:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Get conversation history
   */
  async getConversationHistory(conversationId: string) {
    try {
      const conversation = await chatService.getConversation(conversationId)
      console.log('Conversation:', conversation)
      return conversation
    } catch (error) {
      console.error('Failed to get conversation:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Get all user conversations
   */
  async getAllConversations(page: number = 1) {
    try {
      const conversations = await chatService.getConversations(page, 20)
      console.log('Conversations:', conversations)
      return conversations
    } catch (error) {
      console.error('Failed to get conversations:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Search conversations
   */
  async searchConversations(query: string) {
    try {
      const results = await chatService.searchConversations(query)
      console.log('Search results:', results)
      return results
    } catch (error) {
      console.error('Search failed:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Get suggested questions
   */
  async getSuggestedQuestions() {
    try {
      const suggestions = await chatService.getSuggestedQuestions()
      console.log('Suggested questions:', suggestions)
      return suggestions
    } catch (error) {
      console.error('Failed to get suggestions:', apiUtils.formatError(error))
      throw error
    }
  },

  /**
   * Rate a message
   */
  async rateMessage(messageId: string, rating: 'positive' | 'negative', feedback?: string) {
    try {
      const result = await chatService.rateMessage(messageId, rating, feedback)
      console.log('Message rated:', result)
      return result
    } catch (error) {
      console.error('Failed to rate message:', apiUtils.formatError(error))
      throw error
    }
  }
}

// ============================================================================
// ERROR HANDLING EXAMPLES
// ============================================================================

export const errorHandlingExamples = {
  /**
   * Handle API errors with retry
   */
  async handleWithRetry<T>(apiCall: () => Promise<T>) {
    try {
      return await apiUtils.retryWithBackoff(apiCall, 3, 1000)
    } catch (error) {
      if (apiUtils.isAuthError(error)) {
        // Redirect to login
        console.log('Authentication required')
        window.location.href = '/login'
      } else if (apiUtils.isNetworkError(error)) {
        // Show network error message
        console.log('Network error, please check your connection')
      } else {
        // Show generic error
        console.log('Error:', apiUtils.formatError(error))
      }
      throw error
    }
  },

  /**
   * Auto-refresh token before API calls
   */
  async makeAuthenticatedCall<T>(apiCall: () => Promise<T>) {
    try {
      // Try to refresh token if needed
      await authService.autoRefreshToken()
      
      // Make the API call
      return await apiCall()
    } catch (error) {
      if (apiUtils.isAuthError(error)) {
        // Token refresh failed, redirect to login
        await authService.logout()
        window.location.href = '/login'
      }
      throw error
    }
  }
}

// ============================================================================
// REACT HOOK EXAMPLES
// ============================================================================

export const reactHookExamples = `
// Example custom hooks using the services

import { useState, useEffect } from 'react'
import { authService, userService, chatService } from '@/lib/api'

// Authentication hook
export function useAuth() {
  const [user, setUser] = useState(authService.getCurrentUser())
  const [isAuthenticated, setIsAuthenticated] = useState(authService.isAuthenticated())

  const login = async (email: string, password: string) => {
    const response = await authService.login({ email, password })
    setUser(response.user)
    setIsAuthenticated(true)
    return response
  }

  const logout = async () => {
    await authService.logout()
    setUser(null)
    setIsAuthenticated(false)
  }

  return { user, isAuthenticated, login, logout }
}

// User profile hook
export function useUserProfile() {
  const [profile, setProfile] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchProfile = async () => {
      try {
        const data = await userService.getProfile()
        setProfile(data)
      } catch (error) {
        console.error('Failed to fetch profile:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchProfile()
  }, [])

  const updateProfile = async (updates) => {
    const updated = await userService.updateProfile(updates)
    setProfile(updated)
    return updated
  }

  return { profile, loading, updateProfile }
}

// Chat hook
export function useChat(conversationId?: string) {
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(false)

  const sendMessage = async (message: string) => {
    setLoading(true)
    try {
      const response = conversationId 
        ? await chatService.continueConversation(conversationId, message)
        : await chatService.startConversation(message)
      
      setMessages(prev => [...prev, response.message])
      return response
    } finally {
      setLoading(false)
    }
  }

  return { messages, loading, sendMessage }
}
`
