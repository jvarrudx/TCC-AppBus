import { defineStore } from 'pinia'
import api, { setAuthToken } from '../boot/axios'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // Access token estritamente em memória volátil (Zero Disk Storage / Blindagem contra XSS)
    accessToken: null,
    user: null,
    isInitialized: false,
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
    statusAprovacao: (state) => state.user?.status_aprovacao || null,
    alunoMatricula: (state) => state.user?.aluno?.matricula || null,
    alunoInstituicao: (state) => state.user?.aluno?.instituicao_nome || null,
    alunoSigla: (state) => state.user?.aluno?.instituicao_sigla || null,
    alunoClienteNome: (state) => state.user?.aluno?.cliente_nome || null,
    isAlunoAprovado: (state) => String(state.user?.status_aprovacao || '').toUpperCase() === 'APROVADO',
    isAlunoPendente: (state) => String(state.user?.status_aprovacao || '').toUpperCase() === 'PENDENTE',
    isAlunoRejeitado: (state) => String(state.user?.status_aprovacao || '').toUpperCase() === 'REJEITADO',
  },

  actions: {
    async initAuth() {
      if (this.isInitialized) return this.isAuthenticated
      this.loading = true
      try {
        // Tenta silenciosamente renovar o access token usando o Cookie HttpOnly 'appbus_refresh_token'
        const response = await api.post('/token/refresh/')
        const { access, user } = response.data

        this.accessToken = access
        this.user = user
        setAuthToken(access)
        return true
      } catch (e) {
        this.accessToken = null
        this.user = null
        setAuthToken(null)
        return false
      } finally {
        this.isInitialized = true
        this.loading = false
      }
    },

    async login({ email, password }) {
      this.loading = true
      this.errorMessage = null
      try {
        // O backend Django injeta o refresh_token no Cookie HttpOnly 'appbus_refresh_token'
        const response = await api.post('/token/', { email, password })
        const { access, user } = response.data

        this.accessToken = access
        this.user = user
        this.isInitialized = true
        setAuthToken(access)

        // Limpeza defensiva contra credenciais legadas na Web Storage API
        localStorage.removeItem('appbus_access_token')
        localStorage.removeItem('appbus_refresh_token')
        localStorage.removeItem('appbus_user')

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

    async logout() {
      try {
        await api.post('/token/logout/')
      } catch (e) {
        // Prossegue mesmo se a requisição ao servidor falhar
      } finally {
        this.accessToken = null
        this.user = null
        this.errorMessage = null
        this.isInitialized = true
        setAuthToken(null)

        localStorage.removeItem('appbus_access_token')
        localStorage.removeItem('appbus_refresh_token')
        localStorage.removeItem('appbus_user')
      }
    },

    setUser(userData) {
      this.user = userData
    },

    async checkSession() {
      if (!this.accessToken) {
        return await this.initAuth()
      }
      return true
    }
  }
})
