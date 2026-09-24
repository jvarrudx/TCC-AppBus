import { defineStore } from 'pinia'
import api from '../boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    accessToken: localStorage.getItem('appbus_access_token') || null,
    refreshToken: localStorage.getItem('appbus_refresh_token') || null,
    user: (() => {
      try {
        const stored = localStorage.getItem('appbus_user')
        return stored ? JSON.parse(stored) : null
      } catch (e) {
        return null
      }
    })(),
    loading: false,
    errorMessage: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    role: (state) => state.user?.role || 'visitante',
    isAluno: (state) => state.user?.role === 'aluno',
    isMotorista: (state) => state.user?.role === 'motorista',
    isGestor: (state) => state.user?.role === 'administrador' || !!state.user?.is_superuser,
    clienteId: (state) => state.user?.cliente_id || null,
    userNome: (state) => state.user?.pessoa?.nome || state.user?.email || 'Usuário',
    statusAprovacao: (state) => state.user?.status_aprovacao || null
  },

  actions: {
    async login({ email, password }) {
      this.loading = true
      this.errorMessage = null
      try {
        const response = await api.post('/token/', { email, password })
        const { access, refresh, user } = response.data

        this.accessToken = access
        this.refreshToken = refresh
        this.user = user

        localStorage.setItem('appbus_access_token', access)
        localStorage.setItem('appbus_refresh_token', refresh)
        localStorage.setItem('appbus_user', JSON.stringify(user))

        api.defaults.headers.common['Authorization'] = `Bearer ${access}`
        return user
      } catch (error) {
        const message = error.response?.data?.detail || 
                        error.response?.data?.non_field_errors?.[0] || 
                        'Falha na autenticação. Verifique suas credenciais.'
        this.errorMessage = message
        throw new Error(message)
      } finally {
        this.loading = false
      }
    },

    logout() {
      this.accessToken = null
      this.refreshToken = null
      this.user = null
      this.errorMessage = null

      localStorage.removeItem('appbus_access_token')
      localStorage.removeItem('appbus_refresh_token')
      localStorage.removeItem('appbus_user')

      delete api.defaults.headers.common['Authorization']
    },

    setUser(userData) {
      this.user = userData
      localStorage.setItem('appbus_user', JSON.stringify(userData))
    },

    async checkSession() {
      if (!this.accessToken) return false
      try {
        // Testa a conectividade ou integridade do token
        api.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
        return true
      } catch (e) {
        this.logout()
        return false
      }
    }
  }
})
