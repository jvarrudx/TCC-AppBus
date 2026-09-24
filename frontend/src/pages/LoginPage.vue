<template>
  <q-layout view="lHh Lpr lFf" class="bg-dark-page">
    <q-page-container>
      <q-page class="flex flex-center q-pa-md">
        <div class="login-wrapper full-width" style="max-width: 440px;">
          <!-- Cabeçalho / Logo -->
          <div class="text-center q-mb-lg">
            <div class="brand-badge q-mb-sm inline-block">
              <q-icon name="directions_bus" size="28px" color="dark" />
            </div>
            <h1 class="text-h4 text-weight-bolder text-white q-my-none">
              App<span class="text-primary">Bus</span>
            </h1>
            <p class="text-grey-5 q-mt-xs text-body2">
              Transporte Universitário Inteligente & Conectado
            </p>
          </div>

          <!-- Seletor Visual de Perfil (Mobile-First) -->
          <div class="profile-tabs-container q-mb-md">
            <div class="row no-wrap justify-between profile-chips">
              <button
                v-for="p in profiles"
                :key="p.role"
                type="button"
                :class="['profile-btn col', selectedProfile === p.role ? 'active' : '']"
                @click="selectProfile(p)"
              >
                <q-icon :name="p.icon" size="18px" class="q-mr-xs" />
                <span>{{ p.label }}</span>
              </button>
            </div>
          </div>

          <!-- Card de Autenticação -->
          <q-card class="dark-card q-pa-lg">
            <!-- Mensagem de Contexto do Perfil Selecionado -->
            <div class="profile-context-box q-pa-sm q-mb-md rounded-borders flex items-center">
              <q-avatar size="32px" :color="currentProfile.badgeColor" text-color="dark" class="q-mr-sm">
                <q-icon :name="currentProfile.icon" size="18px" />
              </q-avatar>
              <div>
                <div class="text-caption text-weight-bold text-white">{{ currentProfile.title }}</div>
                <div class="text-caption text-grey-5">{{ currentProfile.description }}</div>
              </div>
            </div>

            <!-- Formulário de Login -->
            <q-form @submit.prevent="handleLogin" class="q-gutter-y-md">
              <q-input
                v-model="email"
                type="email"
                outlined
                dark
                dense
                label="E-mail Institucional ou Cadastrado"
                color="primary"
                autocomplete="email"
                :rules="[val => !!val || 'Informe seu e-mail cadastrado']"
              >
                <template v-slot:prepend>
                  <q-icon name="alternate_email" color="grey-5" />
                </template>
              </q-input>

              <q-input
                v-model="password"
                :type="showPassword ? 'text' : 'password'"
                outlined
                dark
                dense
                label="Sua Senha de Acesso"
                color="primary"
                autocomplete="current-password"
                :rules="[val => !!val || 'Informe sua senha']"
              >
                <template v-slot:prepend>
                  <q-icon name="lock" color="grey-5" />
                </template>
                <template v-slot:append>
                  <q-icon
                    :name="showPassword ? 'visibility_off' : 'visibility'"
                    class="cursor-pointer"
                    color="grey-5"
                    @click="showPassword = !showPassword"
                  />
                </template>
              </q-input>

              <!-- Banner de Erro -->
              <q-banner
                v-if="errorMessage"
                rounded
                dense
                class="bg-negative text-white text-caption q-mt-sm"
              >
                <template v-slot:avatar>
                  <q-icon name="error_outline" size="20px" />
                </template>
                {{ errorMessage }}
              </q-banner>

              <!-- Botão Principal de Login (Amarelo Ônibus) -->
              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                class="full-width q-py-sm btn-bus-primary q-mt-md"
                size="lg"
                no-caps
                :loading="loading"
              >
                <q-icon name="login" size="20px" class="q-mr-sm" />
                <span>Entrar como {{ currentProfile.label }}</span>
              </q-btn>
            </q-form>

            <q-separator dark class="q-my-lg" />

            <!-- Rodapé do Card com Ações Secundárias -->
            <div class="column q-gutter-y-xs text-center">
              <router-link
                to="/registro"
                class="text-primary text-caption text-weight-medium text-decoration-none"
              >
                Ainda não tem cadastro de Aluno? Solicite adesão
              </router-link>
            </div>
          </q-card>

          <!-- Aviso de Conformidade LGPD -->
          <div class="text-center q-mt-md">
            <span class="text-caption text-grey-6 flex justify-center items-center">
              <q-icon name="verified_user" size="14px" class="q-mr-xs text-grey-5" />
              Ambiente Seguro e Protegido conforme a LGPD
            </span>
          </div>
        </div>
      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'

const $q = useQuasar()
const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const profiles = [
  {
    role: 'aluno',
    label: 'Aluno',
    icon: 'school',
    badgeColor: 'primary',
    title: 'Acesso do Estudante',
    description: 'Predição de demanda diária e embarque com QR Code.'
  },
  {
    role: 'motorista',
    label: 'Motorista',
    icon: 'sports_motorsports',
    badgeColor: 'secondary',
    title: 'Painel do Motorista',
    description: 'Abertura de viagens, conferência de rota e check-in.'
  },
  {
    role: 'administrador',
    label: 'Gestor',
    icon: 'admin_panel_settings',
    badgeColor: 'accent',
    title: 'Gestão Municipal',
    description: 'Monitoramento de rotas, frotas e conformidade LGPD.'
  }
]

const selectedProfile = ref('aluno')

const currentProfile = computed(() => {
  return profiles.find(p => p.role === selectedProfile.value) || profiles[0]
})

const selectProfile = (profile) => {
  selectedProfile.value = profile.role
  errorMessage.value = ''
}

const handleLogin = async () => {
  errorMessage.value = ''
  loading.value = true

  try {
    const user = await authStore.login({
      email: email.value.trim(),
      password: password.value
    })

    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: `Bem-vindo(a), ${user.pessoa?.nome || user.email}!`,
      caption: `Perfil ativo: ${user.role.toUpperCase()}`
    })

    const redirectPath = route.query.redirect || '/'
    router.push(redirectPath)
  } catch (err) {
    errorMessage.value = err.message || 'Falha ao autenticar. Verifique e-mail e senha.'
    $q.notify({
      type: 'negative',
      icon: 'warning',
      message: errorMessage.value
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped lang="scss">
.login-wrapper {
  animation: fadeIn 0.4s ease-out;
}

.brand-badge {
  background: #F2C037;
  padding: 12px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(242, 192, 55, 0.4);
}

.profile-chips {
  background: #121826;
  padding: 4px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  gap: 4px;
}

.profile-btn {
  background: transparent;
  border: none;
  color: #94A3B8;
  font-size: 0.85rem;
  font-weight: 600;
  padding: 10px 8px;
  border-radius: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;

  &:hover {
    color: #F8FAFC;
    background: rgba(255, 255, 255, 0.04);
  }

  &.active {
    background: #1E293B;
    color: #F2C037;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }
}

.profile-context-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.text-decoration-none {
  text-decoration: none;
  &:hover {
    text-decoration: underline;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
