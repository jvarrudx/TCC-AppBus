import axios from 'axios'

// Instância base do Axios para o AppBus
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

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

// Interceptor de Requisição: Injeção do JWT Bearer Token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('appbus_access_token')
    if (token && !config.headers.Authorization) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Interceptor de Resposta: Gestão de 401 Unauthorized e Refresh Automático
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Ignora tentativas de login ou refresh que falharem
    if (
      originalRequest.url.includes('/token/') ||
      originalRequest.url.includes('/token/refresh/')
    ) {
      return Promise.reject(error)
    }

    if (error.response && error.response.status === 401 && !originalRequest._retry) {
      const refreshToken = localStorage.getItem('appbus_refresh_token')

      if (!refreshToken) {
        // Sem token de refresh, desloga e redireciona
        clearAuthAndRedirect()
        return Promise.reject(error)
      }

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
        const refreshResponse = await axios.post(
          (import.meta.env.VITE_API_URL || '/api') + '/token/refresh/',
          { refresh: refreshToken }
        )

        const newAccessToken = refreshResponse.data.access
        localStorage.setItem('appbus_access_token', newAccessToken)

        api.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`
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

    return Promise.reject(error)
  }
)

function clearAuthAndRedirect() {
  localStorage.removeItem('appbus_access_token')
  localStorage.removeItem('appbus_refresh_token')
  localStorage.removeItem('appbus_user')
  delete api.defaults.headers.common['Authorization']

  if (window.location.pathname !== '/login') {
    window.location.href = '/login'
  }
}

export default api
export { api }
