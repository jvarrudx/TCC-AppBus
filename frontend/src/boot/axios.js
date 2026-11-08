import axios from 'axios'

// Instância base do Axios para o AppBus
// withCredentials: true garante que cookies HttpOnly sejam transmitidos nas requisições da mesma origem / CORS
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// Armazenamento estritamente em memória volátil (Zero Disk Storage / Imune a XSS)
let inMemoryAccessToken = null

export const setAuthToken = (token) => {
  inMemoryAccessToken = token
  if (token) {
    api.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete api.defaults.headers.common['Authorization']
  }
}

export const getAuthToken = () => inMemoryAccessToken

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// Interceptor de Requisição: Injeção do JWT Bearer Token a partir da memória
api.interceptors.request.use(
  (config) => {
    if (inMemoryAccessToken && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${inMemoryAccessToken}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor de Resposta: Gestão de 401 Unauthorized e Refresh Automático via Cookie HttpOnly
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Ignora tentativas de login, refresh ou logout que falharem
    if (
      !originalRequest ||
      originalRequest.url?.includes('/token/') ||
      originalRequest.url?.includes('/token/refresh/') ||
      originalRequest.url?.includes('/token/logout/')
    ) {
      return Promise.reject(error)
    }

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch((err) => Promise.reject(err))
      }

      originalRequest._retry = true
      isRefreshing = true

      try {
        // Envia requisição com withCredentials: true (navegador anexa o Cookie HttpOnly 'appbus_refresh_token')
        const refreshResponse = await api.post('/token/refresh/')

        const newAccessToken = refreshResponse.data.access
        setAuthToken(newAccessToken)

        try {
          const { useAuthStore } = await import('../stores/authStore')
          const authStore = useAuthStore()
          authStore.accessToken = newAccessToken
          if (refreshResponse.data.user) {
            authStore.user = refreshResponse.data.user
          }
        } catch (_) {}

        originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`
        processQueue(null, newAccessToken)
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        clearAuthAndRedirect()
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }

    if (error.response && error.response.status === 403) {
      // Erro de autorização / RBAC no backend
      console.warn('[AppBus API 403] Acesso negado pelo servidor:', error.config?.url)
    }

    return Promise.reject(error)
  }
)

export function clearAuthAndRedirect(reason = 'Sua sessão expirou por segurança. Por favor, acesse novamente.') {
  setAuthToken(null)
  localStorage.removeItem('appbus_access_token')
  localStorage.removeItem('appbus_refresh_token')
  localStorage.removeItem('appbus_user')
  sessionStorage.setItem('appbus_logout_reason', reason)

  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export default api
export { api }
