import { create } from 'zustand'
import api from '../services/api'

// Simple persist implementation
const persist = (config) => (set, get, api) => {
  const stored = localStorage.getItem('auth-storage')
  if (stored) {
    try {
      const parsed = JSON.parse(stored)
      if (parsed.state) {
        set(parsed.state)
      }
    } catch (e) {
      // Ignore
    }
  }
  
  const result = config(set, get, api)
  
  // Save to localStorage on state changes
  const originalSetState = api.setState
  api.setState = (state, replace) => {
    originalSetState(state, replace)
    const currentState = get()
    localStorage.setItem('auth-storage', JSON.stringify({ state: currentState }))
  }
  
  return result
}

const useAuthStore = create(
  persist(
    (set) => ({
      user: null,
      token: null,
      isAuthenticated: false,
      
      login: async (email, password) => {
        try {
          const response = await api.post('/auth/login', new URLSearchParams({
            username: email,
            password: password,
          }))
          const { access_token } = response.data
          set({ token: access_token, isAuthenticated: true })
          api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
          
          // Fetch user info
          const userResponse = await api.get('/auth/me')
          set({ user: userResponse.data })
          
          return { success: true }
        } catch (error) {
          return { success: false, error: error.response?.data?.detail || 'Login failed' }
        }
      },
      
      register: async (email, password) => {
        try {
          await api.post('/auth/register', { email, password })
          return { success: true }
        } catch (error) {
          return { success: false, error: error.response?.data?.detail || 'Registration failed' }
        }
      },
      
      logout: () => {
        set({ user: null, token: null, isAuthenticated: false })
        delete api.defaults.headers.common['Authorization']
      },
      
      setUser: (user) => set({ user }),
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ token: state.token, user: state.user, isAuthenticated: state.isAuthenticated }),
    }
  )
)

export default useAuthStore

