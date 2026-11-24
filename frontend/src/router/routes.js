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
        meta: { title: 'Início | AppBus', roles: ['aluno', 'motorista', 'administrador'] }
      },
      {
        path: 'admin/aprovacoes',
        name: 'admin-aprovacoes',
        component: () => import('../pages/admin/AdminApprovalQueuePage.vue'),
        meta: { title: 'Fila de Aprovação | AppBus', roles: ['administrador'] }
      },
      {
        path: 'admin/frota',
        name: 'admin-frota',
        component: () => import('../pages/admin/AdminFleetPage.vue'),
        meta: { title: 'Gestão de Frota e Rotas | AppBus', roles: ['administrador'] }
      },
      {
        path: 'admin/qrcode',
        name: 'admin-qrcode',
        component: () => import('../pages/admin/AdminQRCodePage.vue'),
        meta: { title: 'Emissão de QR Code | AppBus', roles: ['administrador'] }
      },
      {
        path: 'motorista',
        name: 'driver-panel',
        component: () => import('../pages/driver/DriverPanelPage.vue'),
        meta: { title: 'Painel do Motorista | AppBus', roles: ['motorista', 'administrador'] }
      },
      {
        path: 'aluno/qrcode',
        name: 'aluno-qrcode',
        component: () => import('../pages/student/StudentQRScannerPage.vue'),
        meta: { title: 'Embarque Óptico | AppBus', roles: ['aluno', 'administrador'] }
      },
      {
        path: 'aluno/perfil',
        name: 'aluno-perfil',
        component: () => import('../pages/student/StudentProfilePage.vue'),
        meta: { title: 'Perfil & Privacidade | AppBus', roles: ['aluno', 'administrador'] }
      },
      {
        path: 'mural',
        name: 'mural-avisos',
        component: () => import('../pages/MuralAvisosPage.vue'),
        meta: { title: 'Mural de Avisos | AppBus', roles: ['aluno', 'motorista', 'administrador'] }
      }
    ]
  },
  {
    path: '/:catchAll(.*)*',
    redirect: '/'
  }
]

export default routes
