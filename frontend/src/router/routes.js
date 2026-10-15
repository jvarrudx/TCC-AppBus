const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../pages/LoginPage.vue'),
    meta: { requiresAuth: false, title: 'Login | AppBus' }
  },
  {
    path: '/registro',
    name: 'registro',
    component: () => import('../pages/RegisterPage.vue'),
    meta: { requiresAuth: false, title: 'Cadastro de Aluno | AppBus' }
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
      },
      {
        path: 'admin/aprovacoes',
        name: 'admin-aprovacoes',
        component: () => import('../pages/admin/AdminApprovalQueuePage.vue'),
        meta: { title: 'Fila de Aprovação | AppBus' }
      },
      {
        path: 'admin/frota',
        name: 'admin-frota',
        component: () => import('../pages/admin/AdminFleetPage.vue'),
        meta: { title: 'Gestão de Frota e Rotas | AppBus' }
      },
      {
        path: 'admin/qrcode',
        name: 'admin-qrcode',
        component: () => import('../pages/admin/AdminQRCodePage.vue'),
        meta: { title: 'Emissão de QR Code | AppBus' }
      },
      {
        path: 'motorista',
        name: 'driver-panel',
        component: () => import('../pages/driver/DriverPanelPage.vue'),
        meta: { title: 'Painel do Motorista | AppBus' }
      },
      {
        path: 'aluno/qrcode',
        name: 'aluno-qrcode',
        component: () => import('../pages/student/StudentQRScannerPage.vue'),
        meta: { title: 'Embarque Óptico | AppBus' }
      },
      {
        path: 'aluno/perfil',
        name: 'aluno-perfil',
        component: () => import('../pages/student/StudentProfilePage.vue'),
        meta: { title: 'Perfil & Privacidade | AppBus' }
      }
    ]
  },
  {
    path: '/:catchAll(.*)*',
    redirect: '/'
  }
]

export default routes
