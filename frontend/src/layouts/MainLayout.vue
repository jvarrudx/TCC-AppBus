<template>
  <q-layout view="hHh lpR fFf" class="bg-dark-page">
    <!-- Header Mobile-First -->
    <q-header elevated class="bg-dark text-white q-py-xs" style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
      <q-toolbar>
        <!-- Botão Menu Drawer (Aparece para Gestores) -->
        <q-btn
          v-if="authStore.isGestor"
          flat
          dense
          round
          icon="menu"
          color="primary"
          class="q-mr-sm"
          @click="leftDrawerOpen = !leftDrawerOpen"
        >
          <q-tooltip>Menu do Gestor</q-tooltip>
        </q-btn>

        <div class="row items-center cursor-pointer" @click="$router.push('/')">
          <q-avatar size="34px" color="primary" text-color="dark" class="q-mr-sm">
            <q-icon name="directions_bus" size="20px" />
          </q-avatar>
          <q-toolbar-title class="text-weight-bold text-h6">
            App<span class="text-primary">Bus</span>
          </q-toolbar-title>
        </div>

        <q-space />

        <!-- Atalhos Rápidos no Header (Desktop) para Gestor -->
        <div v-if="authStore.isGestor" class="gt-sm row q-gutter-x-xs q-mr-md">
          <q-btn flat dense no-caps label="Início" icon="home" size="sm" to="/" />
          <q-btn flat dense no-caps label="Mural" icon="campaign" size="sm" to="/mural" />
          <q-btn flat dense no-caps label="Fila de Alunos" icon="how_to_reg" size="sm" to="/admin/aprovacoes" />
          <q-btn flat dense no-caps label="Frota & Rotas" icon="directions_bus" size="sm" to="/admin/frota" />
          <q-btn flat dense no-caps label="Emitir QR Code" icon="qr_code_2" size="sm" to="/admin/qrcode" />
        </div>

        <!-- Atalhos Rápidos para Motorista -->
        <div v-if="authStore.isMotorista" class="row q-gutter-x-xs q-mr-md">
          <q-btn flat dense no-caps label="Início" icon="home" size="sm" to="/" />
          <q-btn flat dense no-caps label="Mural" icon="campaign" size="sm" to="/mural" />
          <q-btn flat dense no-caps label="Painel Operacional" icon="sports_motorsports" size="sm" to="/motorista" text-color="primary" />
        </div>

        <!-- Atalhos Rápidos para Aluno -->
        <div v-if="authStore.isAluno" class="row q-gutter-x-xs q-mr-sm">
          <q-btn flat dense no-caps label="Início" icon="home" size="sm" to="/" />
          <q-btn flat dense no-caps label="Mural" icon="campaign" size="sm" to="/mural" />
          <q-btn flat dense no-caps label="Embarcar" icon="qr_code_scanner" size="sm" to="/aluno/qrcode" text-color="primary" />
          <q-btn flat dense no-caps label="Perfil" icon="manage_accounts" size="sm" to="/aluno/perfil" />
        </div>

        <!-- Informações do Usuário e Papel Ativo -->
        <div class="row items-center q-gutter-x-sm">
          <div class="column text-right gt-xs">
            <span class="text-caption text-weight-bold text-white">{{ authStore.userNome }}</span>
            <span class="text-caption text-primary text-uppercase text-weight-bolder" style="font-size: 0.65rem;">
              {{ authStore.role }}
            </span>
          </div>

          <q-btn flat round dense icon="logout" color="grey-4" @click="handleLogout">
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
    <q-page-container>
      <div class="app-container-mobile q-pa-md">
        <router-view />
      </div>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const leftDrawerOpen = ref(false)

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
.border-bottom {
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
.font-bold {
  font-weight: 700;
}
</style>
