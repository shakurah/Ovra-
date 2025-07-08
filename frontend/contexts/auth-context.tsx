"use client"

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authService, userService, type LoginRequest, type RegisterRequest, type User } from '@/lib/services'
import { getErrorMessage, isAuthError } from '@/utils/api'



interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (credentials: LoginRequest) => Promise<void>
  register: (userData: RegisterRequest) => Promise<void>
  logout: () => Promise<void>
  refreshAuth: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()

  const isAuthenticated = !!user

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      console.log('AuthContext: Initializing auth state...')
      try {
        const storedUser = authService.getCurrentUser()
        const accessToken = authService.getStoredToken()
        const refreshToken = authService.getStoredRefreshToken()

        console.log('AuthContext: Stored user:', !!storedUser, 'Access token:', !!accessToken, 'Refresh token:', !!refreshToken)

        if (storedUser && accessToken) {
          console.log('AuthContext: Setting user from localStorage')
          setUser(storedUser)

          // Only try auto-refresh if we have a refresh token
          if (refreshToken) {
            try {
              await authService.autoRefreshToken()
            } catch (error) {
              console.log('AuthContext: Auto-refresh failed:', error)
            }
          }

          // Verify token is still valid by fetching user profile
          try {
            console.log('AuthContext: Verifying token validity...')
            const freshUserData = await userService.getProfile()
            console.log('AuthContext: Token valid, updated user data')
            setUser(freshUserData)
          } catch (error) {
            console.log('AuthContext: Token validation failed:', error)
            // If we have a refresh token, try to use it
            if (refreshToken) {
              try {
                console.log('AuthContext: Attempting token refresh...')
                await authService.refreshToken()
                const freshUserData = await userService.getProfile()
                console.log('AuthContext: Token refreshed successfully')
                setUser(freshUserData)
              } catch (refreshError) {
                console.log('AuthContext: Token refresh failed, clearing auth state')
                // If refresh fails, clear auth state
                await authService.logout()
                setUser(null)
              }
            } else {
              console.log('AuthContext: No refresh token available, clearing auth state')
              // If no refresh token and validation failed, clear auth state
              await authService.logout()
              setUser(null)
            }
          }
        } else {
          console.log('AuthContext: Missing stored credentials, clearing auth state')
          // Clear any partial auth state
          await authService.logout()
          setUser(null)
        }
      } catch (error) {
        console.error('AuthContext: Error initializing auth:', error)
        await authService.logout()
        setUser(null)
      } finally {
        console.log('AuthContext: Auth initialization complete, isLoading = false')
        setIsLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (credentials: LoginRequest) => {
    try {
      setIsLoading(true)
      const response = await authService.login(credentials)
      setUser(response.user)
      router.push('/chat')
    } catch (error) {
      console.error('Login error:', error)
      throw new Error(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const register = async (userData: RegisterRequest) => {
    try {
      setIsLoading(true)
      const response = await authService.register(userData)
      setUser(response.user)
      router.push('/chat')
    } catch (error) {
      console.error('Registration error:', error)
      throw new Error(getErrorMessage(error))
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      setIsLoading(true)
      await authService.logout()
      setUser(null)
      router.push('/login')
    } catch (error) {
      console.error('Logout error:', error)
      // Still clear local state even if API call fails
      setUser(null)
      router.push('/login')
    } finally {
      setIsLoading(false)
    }
  }

  const refreshAuth = async () => {
    try {
      await authService.refreshToken()
      // Refresh user profile
      const profile = await userService.getProfile()
      setUser(profile)
    } catch (error) {
      console.error('Token refresh error:', error)
      // If refresh fails, logout user
      await logout()
    }
  }

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshAuth
  }

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  )
}
