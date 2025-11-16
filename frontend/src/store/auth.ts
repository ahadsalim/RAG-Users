import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'
import { User } from '@/types/chat'

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
  
  // Actions
  login: (email: string, password: string) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => void
  refreshAccessToken: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
  verifyTwoFactor: (code: string) => Promise<void>
  setTokens: (accessToken: string, refreshToken: string, user?: User) => void
  clearError: () => void
}

interface RegisterData {
  email: string
  password: string
  first_name?: string
  last_name?: string
  phone_number?: string
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      user: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/login/`, {
            email,
            password,
          })
          
          const { access, refresh, user, requires_2fa } = response.data
          
          if (requires_2fa) {
            // Store tokens temporarily and wait for 2FA
            set({ 
              isLoading: false,
              error: 'لطفا کد تایید دو عاملی را وارد کنید'
            })
            return
          }
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          
          // Set axios default header
          axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.detail || 'خطا در ورود',
          })
          throw error
        }
      },
      
      register: async (data: RegisterData) => {
        set({ isLoading: true, error: null })
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/register/`, data)
          
          // Auto login after registration
          const { access, refresh, user } = response.data
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          
          axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.detail || 'خطا در ثبت‌نام',
          })
          throw error
        }
      },
      
      logout: () => {
        const refreshToken = get().refreshToken
        
        // Call logout API
        if (refreshToken) {
          axios.post(`${API_URL}/api/v1/auth/logout/`, {
            refresh_token: refreshToken
          }).catch(() => {})
        }
        
        // Clear state
        set({
          user: null,
          accessToken: null,
          refreshToken: null,
          isAuthenticated: false,
          error: null,
        })
        
        // Clear axios header
        delete axios.defaults.headers.common['Authorization']
      },
      
      refreshAccessToken: async () => {
        const refreshToken = get().refreshToken
        if (!refreshToken) {
          get().logout()
          return
        }
        
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/token/refresh/`, {
            refresh: refreshToken,
          })
          
          const { access } = response.data
          
          set({ accessToken: access })
          axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        } catch (error) {
          get().logout()
          throw error
        }
      },
      
      updateProfile: async (data: Partial<User>) => {
        set({ isLoading: true, error: null })
        try {
          const response = await axios.patch(`${API_URL}/api/v1/auth/profile/`, data)
          
          set({
            user: response.data,
            isLoading: false,
            error: null,
          })
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.detail || 'خطا در به‌روزرسانی پروفایل',
          })
          throw error
        }
      },
      
      verifyTwoFactor: async (code: string) => {
        set({ isLoading: true, error: null })
        try {
          const response = await axios.post(`${API_URL}/api/v1/auth/login/2fa/`, {
            code,
          })
          
          const { access, refresh, user } = response.data
          
          set({
            user,
            accessToken: access,
            refreshToken: refresh,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          })
          
          axios.defaults.headers.common['Authorization'] = `Bearer ${access}`
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.response?.data?.detail || 'کد تایید نامعتبر است',
          })
          throw error
        }
      },
      
      setTokens: (accessToken: string, refreshToken: string, user?: User) => {
        set({
          accessToken,
          refreshToken,
          isAuthenticated: true,
          ...(user && { user }),
        })
        axios.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      },
      
      clearError: () => set({ error: null }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
)

// Setup axios interceptor for token refresh
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        await useAuthStore.getState().refreshAccessToken()
        return axios(originalRequest)
      } catch (refreshError) {
        useAuthStore.getState().logout()
        window.location.href = '/auth/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)
