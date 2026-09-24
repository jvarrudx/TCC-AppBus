<template>
  <q-layout view="hHh lpR fFf" class="bg-dark-page">
    <!-- Header Mobile-First -->
    <q-header elevated class="bg-dark text-white q-py-xs" style="border-bottom: 1px solid rgba(255, 255, 255, 0.08);">
      <q-toolbar>
        <div class="row items-center cursor-pointer" @click="$router.push('/')">
          <q-avatar size="34px" color="primary" text-color="dark" class="q-mr-sm">
            <q-icon name="directions_bus" size="20px" />
          </q-avatar>
          <q-toolbar-title class="text-weight-bold text-h6">
            App<span class="text-primary">Bus</span>
          </q-toolbar-title>
        </div>

        <q-space />

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

    <!-- Conteúdo da Página -->
    <q-page-container>
      <div class="app-container-mobile q-pa-md">
        <router-view />
      </div>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

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
