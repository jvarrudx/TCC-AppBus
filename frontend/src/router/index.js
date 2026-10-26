import { createRouter, createWebHistory } from 'vue-router'
import routes from './routes'
import { useAuthStore } from '../stores/authStore'
import { Notify } from 'quasar'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

// Navigation Guard de Segurança e Multi-Perfis (RBAC)
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth !== false)

  if (to.meta.title) {
    document.title = to.meta.title
  }

  // Se a rota requer autenticação e o usuário não está autenticado
  if (requiresAuth && !authStore.isAuthenticated) {
    next({ name: 'login', query: { redirect: to.fullPath } })
    return
  }

  // Se já está autenticado e tenta acessar a página de login
  if (to.name === 'login' && authStore.isAuthenticated) {
    next({ name: 'home' })
    return
  }

  // Validação de Permissão por Perfil (RBAC)
  if (authStore.isAuthenticated && to.meta && Array.isArray(to.meta.roles)) {
    const userRole = (authStore.role || 'aluno').toLowerCase()
    const allowedRoles = to.meta.roles.map(r => r.toLowerCase())
    const isSuperuser = Boolean(authStore.user?.is_superuser)

    const hasPermission = isSuperuser || allowedRoles.includes(userRole)

    if (!hasPermission) {
      Notify.create({
        type: 'warning',
        icon: 'gpp_bad',
        message: 'Acesso Restrito',
        caption: `Seu perfil (${userRole.toUpperCase()}) não tem permissão para acessar esta área.`,
        position: 'top',
        timeout: 4000
      })
      next({ name: 'home' })
      return
    }
  }

  next()
})

export default router
