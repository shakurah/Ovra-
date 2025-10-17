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

export async function refreshAccessToken(refreshToken: string) {
  const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/token/refresh/`, {
     method: "POST",
     headers: { "Content-Type": "application/json" },
     body: JSON.stringify({ refresh: refreshToken }) // <-- must be "refresh"
   })
   const data = await res.json()
   if (!res.ok) {
     throw data
   }
   if (data.access) localStorage.setItem("accessToken", data.access)
   if (data.refresh) localStorage.setItem("refreshToken", data.refresh) // rotate if provided
   return data
 }
 
 export async function getValidAccessToken() {
   let access = localStorage.getItem("accessToken");
   const refresh = localStorage.getItem("refreshToken");
   if (!access && !refresh) throw new Error("no tokens");
   // Optional: check expiry of access token client-side if you decode it
   // Try using current access; if a request fails with 401 call refreshAccessToken
   return access;
 }
 
async function fetchWithAuth(url: string, options: RequestInit = {}) {
  let accessToken = localStorage.getItem("accessToken");
  const refreshToken = localStorage.getItem("refreshToken");
  if (!accessToken && !refreshToken) throw new Error("no tokens");

  if (accessToken) {
    options.headers = {
      ...options.headers,
      "Authorization": `Bearer ${accessToken}`,
    }
  }
  let res = await fetch(url, options);
  if (res.status === 401 && refreshToken) {
    // Access token might be expired, try to refresh
    try {
      const data = await refreshAccessToken(refreshToken);
      accessToken = data.access;
      options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${accessToken}`,
      }
      res = await fetch(url, options); // Retry original request
    }
    catch (error) {
      // Refresh failed, logout user
      localStorage.removeItem("accessToken");
      localStorage.removeItem("refreshToken");
      throw new Error("Session expired, please log in again.");
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    const error = new Error(errorData.error || errorData.message || "API request failed");
    throw error;
  }
  return res;
}
export { fetchWithAuth }
