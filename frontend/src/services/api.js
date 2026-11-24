import api from '../boot/axios'

export const avisosService = {
  getAvisos(params = {}) {
    return api.get('/avisos/', { params })
  },
  createAviso(data) {
    return api.post('/avisos/', data)
  },
  inativarAviso(id) {
    return api.delete(`/avisos/${id}/`)
  },
  getRotas() {
    return api.get('/rotas/')
  }
}

export default api
export { api }
