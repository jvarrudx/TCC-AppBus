const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/LoginPage.vue'),
    meta: { requiresAuth: false, title: 'Login | AppBus' }
  },
  {
    path: '/',
    component: () => import('../layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'home',
        component: () => import('../pages/HomePage.vue'),
        meta: { title: 'Início | AppBus' }
      }
    ]
  },
  {
    path: '/:catchAll(.*)*',
    redirect: '/'
  }
]

export default routes
