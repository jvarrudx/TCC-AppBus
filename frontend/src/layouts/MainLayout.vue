<template>
  <q-layout view="hHh lpR fFf" class="bg-dark-page">
    <!-- Header Mobile Elegante com Efeito Glassmorphism -->
    <q-header class="app-header text-white">
      <q-toolbar class="q-px-md toolbar-compact">
        <!-- Botão Menu Drawer (Apenas para Gestor) -->
        <q-btn
          v-if="authStore.isGestor"
          flat
          dense
          round
          icon="menu"
          color="primary"
          class="q-mr-xs"
          @click="leftDrawerOpen = !leftDrawerOpen"
        >
          <q-tooltip>Menu Administrativo</q-tooltip>
        </q-btn>

        <!-- Logo AppBus Moderno -->
        <div class="row items-center cursor-pointer no-wrap logo-brand" @click="$router.push('/')">
          <div class="logo-avatar q-mr-sm">
            <q-icon name="directions_bus" size="20px" />
          </div>
          <div class="text-weight-bolder text-h6 text-white text-no-wrap tracking-tight">
            App<span class="text-primary">Bus</span>
          </div>
        </div>

        <q-space />

        <!-- Informações do Usuário e Logout -->
        <div class="row items-center q-gutter-x-sm no-wrap">
          <div class="user-pill row items-center no-wrap">
            <span class="text-caption text-weight-bold text-white q-mr-xs ellipsis" style="max-width: 110px;">
              {{ authStore.userNome?.split(' ')[0] }}
            </span>
            <q-badge :color="roleBadgeColor" text-color="dark" class="text-weight-bolder" style="font-size: 0.65rem;">
              {{ authStore.role }}
            </q-badge>
          </div>

          <q-btn
            flat
            round
            dense
            icon="logout"
            color="grey-4"
            class="btn-logout"
            @click="handleLogout"
          >
            <q-tooltip>Sair do AppBus</q-tooltip>
          </q-btn>
        </div>
      </q-toolbar>
    </q-header>

    <!-- Drawer Lateral para Gestores -->
    <q-drawer
      v-if="authStore.isGestor"
      v-model="leftDrawerOpen"
      side="left"
      overlay
      bordered
      dark
      class="bg-dark text-white"
    >
      <div class="q-pa-md text-center bg-dark-page border-bottom">
        <q-avatar size="48px" color="primary" text-color="dark" class="q-mb-sm">
          <q-icon name="admin_panel_settings" size="28px" />
        </q-avatar>
        <div class="text-subtitle1 text-weight-bold text-white">{{ authStore.userNome }}</div>
        <div class="text-caption text-primary text-uppercase text-weight-bold">
          Gestor Municipal
        </div>
        <div v-if="authStore.clienteId" class="text-caption text-grey-5">
          Tenant #{{ authStore.clienteId }}
        </div>
      </div>

      <q-list padding class="text-grey-3">
        <q-item-label header class="text-grey-5 text-uppercase text-weight-bold">
          Módulos Administrativos
        </q-item-label>

        <q-item clickable v-ripple to="/" exact active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="dashboard" />
          </q-item-section>
          <q-item-section>Painel Principal</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/aprovacoes" active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="how_to_reg" />
          </q-item-section>
          <q-item-section>Fila de Aprovação</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/frota" active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="directions_bus" />
          </q-item-section>
          <q-item-section>Frota & Rotas</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/admin/qrcode" active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="qr_code_2" />
          </q-item-section>
          <q-item-section>Emissão de QR Code</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/mural" active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="campaign" />
          </q-item-section>
          <q-item-section>Mural de Avisos</q-item-section>
        </q-item>

        <q-item clickable v-ripple to="/motorista" active-class="text-primary font-bold">
          <q-item-section avatar>
            <q-icon name="sports_motorsports" />
          </q-item-section>
          <q-item-section>Visão do Motorista</q-item-section>
        </q-item>

        <q-separator dark class="q-my-md" />

        <q-item clickable v-ripple @click="handleLogout" class="text-negative">
          <q-item-section avatar>
            <q-icon name="logout" color="negative" />
          </q-item-section>
          <q-item-section>Desconectar</q-item-section>
        </q-item>
      </q-list>
    </q-drawer>

    <!-- Conteúdo da Página -->
    <q-page-container class="app-page-container">
      <div class="app-container-mobile q-pa-md q-pb-xl">
        <router-view />
      </div>
    </q-page-container>

    <!-- Barra de Navegação Inferior Mobile-First (Bottom Bar) -->
    <q-footer elevated class="bg-dark text-white app-bottom-bar">
      <q-tabs
        no-caps
        dense
        active-color="primary"
        indicator-color="transparent"
        class="text-grey-4 bottom-tabs"
        align="justify"
      >
        <!-- Navegação do Aluno -->
        <template v-if="authStore.isAluno">
          <q-route-tab
            to="/"
            exact
            icon="home"
            label="Início"
            class="nav-tab-item"
          />
          <q-route-tab
            to="/aluno/qrcode"
            icon="qr_code_scanner"
            label="Embarcar"
            class="nav-tab-item tab-embarcar"
          />
          <q-route-tab
            to="/aluno/perfil"
            icon="manage_accounts"
            label="Perfil"
            class="nav-tab-item"
          />
        </template>

        <!-- Navegação do Motorista -->
        <template v-else-if="authStore.isMotorista">
          <q-route-tab
            to="/"
            exact
            icon="home"
            label="Início"
            class="nav-tab-item"
          />
          <q-route-tab
            to="/motorista"
            icon="sports_motorsports"
            label="Operação"
            class="nav-tab-item"
          />
        </template>

        <!-- Navegação do Gestor -->
        <template v-else-if="authStore.isGestor">
          <q-route-tab
            to="/"
            exact
            icon="home"
            label="Início"
            class="nav-tab-item"
          />
          <q-route-tab
            to="/admin/aprovacoes"
            icon="how_to_reg"
            label="Aprovações"
            class="nav-tab-item"
          />
          <q-route-tab
            to="/admin/frota"
            icon="directions_bus"
            label="Frota & Rotas"
            class="nav-tab-item"
          />
          <q-route-tab
            to="/admin/qrcode"
            icon="qr_code_2"
            label="Cartazes"
            class="nav-tab-item"
          />
        </template>
      </q-tabs>
    </q-footer>
  </q-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const leftDrawerOpen = ref(false)

const roleBadgeColor = computed(() => {
  if (authStore.isAluno) return 'primary'
  if (authStore.isMotorista) return 'secondary'
  return 'accent'
})

const handleLogout = () => {
  $q.dialog({
    title: 'Desconectar',
    message: 'Deseja realmente sair da sua conta no AppBus?',
    cancel: true,
    persistent: true,
    dark: true,
    ok: {
      label: 'Sair',
      color: 'negative',
      flat: false
    }
  }).onOk(() => {
    authStore.logout()
    $q.notify({
      type: 'info',
      icon: 'logout',
      message: 'Sessão encerrada com sucesso.'
    })
    router.push('/login')
  })
}
</script>

<style scoped lang="scss">
.app-header {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(17, 24, 39, 0.85);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
}

.toolbar-compact {
  min-height: 52px;
}

.logo-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  color: #090D16;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 10px rgba(245, 158, 11, 0.3);
}

.tracking-tight {
  letter-spacing: -0.02em;
}

.user-pill {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 9999px;
  padding: 3px 10px;
}

.text-no-wrap {
  white-space: nowrap;
}

.btn-logout {
  transition: transform 0.2s ease, color 0.2s ease;
  &:hover {
    color: #EF4444 !important;
    transform: scale(1.05);
  }
}

.app-page-container {
  min-height: 100vh;
}

/* Barra de Navegação Inferior (Floating Dock Bar) */
.app-bottom-bar {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(17, 24, 39, 0.88) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top-left-radius: 20px;
  border-top-right-radius: 20px;
  box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.5);
  padding-bottom: max(env(safe-area-inset-bottom, 0px), 6px);
}

.bottom-tabs {
  height: 60px;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;

  :deep(.q-tabs__content) {
    width: 100%;
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-around;
  }
}

.nav-tab-item {
  flex: 1 1 0px !important;
  max-width: 100% !important;
  min-width: 0 !important;
  min-height: 56px;
  padding: 4px 2px;
  transition: all 0.2s ease;

  :deep(.q-tab__content) {
    width: 100%;
    min-width: 0;
    padding: 0 2px;
  }

  :deep(.q-tab__icon) {
    font-size: 22px;
    margin-bottom: 2px;
    transition: transform 0.2s ease;
  }

  :deep(.q-tab__label) {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.1;
  }

  &:active {
    transform: scale(0.96);
  }
}

/* Destaque especial do botão de ação principal (Embarcar) */
.tab-embarcar {
  :deep(.q-tab__icon) {
    background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
    color: #090D16 !important;
    border-radius: 50%;
    width: 38px;
    height: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: -8px;
    margin-bottom: 2px;
    box-shadow: 0 4px 14px rgba(245, 158, 11, 0.45);
    font-size: 20px !important;
    transition: transform 0.15s ease;
  }
  :deep(.q-tab__label) {
    color: #F59E0B !important;
    font-weight: 700;
  }
  &:active :deep(.q-tab__icon) {
    transform: scale(0.92);
  }
}

/* Otimização responsiva para smartphones ultracompactos (<= 360px de largura) */
@media (max-width: 360px) {
  .bottom-tabs {
    height: 54px;
  }

  .nav-tab-item {
    min-height: 50px;
    padding: 2px 1px;

    :deep(.q-tab__icon) {
      font-size: 19px;
      margin-bottom: 1px;
    }

    :deep(.q-tab__label) {
      font-size: 0.65rem;
      letter-spacing: 0;
    }
  }
}

.border-bottom {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.font-bold {
  font-weight: 700;
}
</style>
