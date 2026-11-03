<template>
  <q-page class="q-py-md">
    <!-- Card de Boas-vindas e Perfil -->
    <q-card class="dark-card q-pa-md q-mb-md">
      <div class="row items-center no-wrap">
        <q-avatar size="52px" color="primary" text-color="dark" class="q-mr-md shadow-2">
          <q-icon :name="roleIcon" size="28px" />
        </q-avatar>
        <div>
          <div class="text-caption text-grey-4 text-uppercase">Painel Operacional</div>
          <div class="text-h6 text-weight-bold text-white leading-tight">
            Olá, {{ authStore.userNome }}
          </div>
          <div class="row items-center q-mt-xs">
            <q-badge :color="roleBadgeColor" text-color="dark" class="text-weight-bold q-mr-sm">
              {{ authStore.role.toUpperCase() }}
            </q-badge>
            <span v-if="authStore.clienteId" class="text-caption text-grey-5">
              Município #{{ authStore.clienteId }}
            </span>
          </div>
        </div>
      </div>
    </q-card>

    <!-- 0. MURAL DE AVISOS: COMUNICADOS RECENTES E ACESSO RÁPIDO -->
    <!-- 0. MURAL DE AVISOS: COMUNICADOS RECENTES E ACESSO RÁPIDO (ACTION CARD) -->
    <q-card class="dark-card action-card q-pa-md q-mb-md" @click="$router.push('/mural')">
      <div class="row items-center justify-between q-mb-xs">
        <div class="row items-center no-wrap">
          <div class="frosted-icon-circle q-mr-sm">
            <q-icon name="campaign" size="18px" color="primary" />
          </div>
          <div>
            <div class="text-subtitle2 text-weight-bold text-white leading-tight">
              Mural de Avisos & Comunicados
            </div>
            <div class="text-caption text-grey-4" style="font-size: 0.72rem;">
              Linhas municipais em tempo real
            </div>
          </div>
        </div>

        <div class="row items-center text-primary text-caption text-weight-bold">
          <span class="gt-xs q-mr-xs">Acessar Mural</span>
          <q-icon name="chevron_right" size="20px" />
        </div>
      </div>

      <!-- Preview do Aviso Mais Recente (se houver) -->
      <div v-if="ultimoAviso" class="q-mt-sm q-pa-sm rounded-borders preview-aviso-box">
        <div class="row items-center justify-between q-mb-xs">
          <q-badge
            :color="getBadgeColor(ultimoAviso.tipo)"
            :text-color="ultimoAviso.tipo === 'ATRASO' || ultimoAviso.tipo === 'GERAL' ? 'dark' : 'white'"
            class="text-weight-bolder"
          >
            {{ ultimoAviso.tipo_display || ultimoAviso.tipo }}
          </q-badge>
          <span class="text-caption text-grey-5" style="font-size: 0.68rem;">
            {{ formatHora(ultimoAviso.criado_em) }} • {{ ultimoAviso.autor_papel }}
          </span>
        </div>
        <div class="text-caption text-weight-bold text-white ellipsis">
          {{ ultimoAviso.titulo }}
        </div>
        <div class="text-caption text-grey-4 ellipsis" style="font-size: 0.72rem;">
          {{ ultimoAviso.mensagem }}
        </div>
      </div>

      <div v-else-if="!loadingAvisos" class="q-mt-xs text-caption text-grey-5" style="font-size: 0.74rem;">
        <q-icon name="check_circle" color="positive" size="14px" class="q-mr-xs" />
        Nenhum imprevisto ou aviso pendente no momento.
      </div>
    </q-card>

    <!-- PAINEL EXECUTIVO: Gestor Municipal (Consolidação em Action Cards Sem Duplicação) -->
    <div v-if="authStore.isGestor" class="q-gutter-y-md q-mb-md">
      <!-- Cards de Métricas e Navegação Direta -->
      <div class="row q-col-gutter-sm">
        <!-- Fila de Pendências -->
        <div class="col-12 col-sm-4">
          <q-card
            class="dark-card action-card q-pa-md metric-card"
            :class="{ 'border-pending-gold': metricas.pendentes > 0 }"
            @click="$router.push('/admin/aprovacoes')"
          >
            <div class="row items-center justify-between q-mb-xs">
              <span class="text-caption text-grey-4 text-weight-medium">Fila de Aprovação</span>
              <q-icon name="chevron_right" size="18px" color="grey-5" />
            </div>
            <div class="row items-center justify-between">
              <div>
                <div class="text-h4 text-weight-bolder" :class="metricas.pendentes > 0 ? 'text-primary' : 'text-white'">
                  {{ metricas.pendentes }}
                </div>
                <div class="text-caption text-grey-5">
                  {{ metricas.pendentes === 1 ? 'aluno aguardando' : 'alunos aguardando' }}
                </div>
              </div>
              <div class="frosted-icon-circle-lg" :class="{ 'frosted-primary': metricas.pendentes > 0 }">
                <q-icon name="how_to_reg" size="24px" :color="metricas.pendentes > 0 ? 'primary' : 'grey-4'" />
              </div>
            </div>
          </q-card>
        </div>

        <!-- Frota Ativa -->
        <div class="col-6 col-sm-4">
          <q-card class="dark-card action-card q-pa-md metric-card" @click="$router.push('/admin/frota')">
            <div class="row items-center justify-between q-mb-xs">
              <span class="text-caption text-grey-4 text-weight-medium">Frota</span>
              <q-icon name="chevron_right" size="18px" color="grey-5" />
            </div>
            <div class="row items-center justify-between">
              <div>
                <div class="text-h4 text-weight-bolder text-white">
                  {{ metricas.onibus }}
                </div>
                <div class="text-caption text-grey-5">ônibus da frota</div>
              </div>
              <div class="frosted-icon-circle-lg">
                <q-icon name="directions_bus" size="24px" color="primary" />
              </div>
            </div>
          </q-card>
        </div>

        <!-- Rotas Ativas -->
        <div class="col-6 col-sm-4">
          <q-card class="dark-card action-card q-pa-md metric-card" @click="$router.push('/admin/frota')">
            <div class="row items-center justify-between q-mb-xs">
              <span class="text-caption text-grey-4 text-weight-medium">Rotas & Linhas</span>
              <q-icon name="chevron_right" size="18px" color="grey-5" />
            </div>
            <div class="row items-center justify-between">
              <div>
                <div class="text-h4 text-weight-bolder text-white">
                  {{ metricas.rotas }}
                </div>
                <div class="text-caption text-grey-5">itinerários ativos</div>
              </div>
              <div class="frosted-icon-circle-lg">
                <q-icon name="alt_route" size="24px" color="primary" />
              </div>
            </div>
          </q-card>
        </div>
      </div>

      <!-- Ação Direta Útil de Gestão: Emissão de Cartaz QR Code (Sem redundância) -->
      <q-card class="dark-card action-card q-pa-md" @click="$router.push('/admin/qrcode')">
        <div class="row items-center justify-between no-wrap">
          <div class="row items-center no-wrap">
            <div class="frosted-icon-circle-lg q-mr-md">
              <q-icon name="qr_code_2" size="24px" color="primary" />
            </div>
            <div>
              <div class="text-subtitle2 text-weight-bold text-white">Cartazes QR Code para Embarque</div>
              <div class="text-caption text-grey-4">Gerar e imprimir cartazes oficiais para afixação nos veículos e pontos</div>
            </div>
          </div>
          <q-icon name="chevron_right" size="22px" color="grey-5" />
        </div>
      </q-card>
    </div>

    <!-- Módulo Operacional do Aluno (Carteirinha Digital, Viagem do Dia e Predição Automática) -->
    <StudentHomeSection v-if="authStore.isAluno" class="q-mb-md" />

    <!-- Card Operacional: Motorista (Único CTA de Alto Impacto sem Duplicação) -->
    <q-card v-if="authStore.isMotorista" class="dark-card q-pa-md q-mb-md">
      <div class="row items-center justify-between q-mb-xs">
        <div class="text-subtitle1 text-weight-bold text-primary flex items-center">
          <q-icon name="departure_board" size="20px" class="q-mr-xs" />
          Operação de Viagem
        </div>
        <q-badge
          v-if="viagemAtivaMotorista"
          color="positive"
          class="badge-live-pulse text-weight-bolder text-white q-px-sm"
        >
          AO VIVO
        </q-badge>
      </div>

      <p class="text-caption text-grey-4 q-mb-md">
        {{ viagemAtivaMotorista
          ? 'Você possui uma viagem em trânsito. Acompanhe a lotação em tempo real ou realize check-ins.'
          : 'Inicie a rota do dia para abrir o período de embarque dos estudantes.' }}
      </p>

      <!-- Botão Único Consolidado -->
      <q-btn
        color="primary"
        text-color="dark"
        class="full-width btn-bus-primary q-py-sm"
        size="md"
        to="/motorista"
        no-caps
      >
        <div class="row items-center justify-between full-width no-wrap q-px-xs">
          <div class="row items-center">
            <q-icon :name="viagemAtivaMotorista ? 'sports_motorsports' : 'play_arrow'" size="22px" class="q-mr-sm" />
            <span class="text-weight-bold">
              {{ viagemAtivaMotorista ? 'Acessar Painel da Viagem em Andamento' : 'Iniciar Viagem de Hoje' }}
            </span>
          </div>
          <q-icon name="arrow_forward" size="18px" />
        </div>
      </q-btn>
    </q-card>

    <!-- Card de Conectividade do Sistema: Exclusivo para Gestores (Zero Ruído para Aluno/Motorista) -->
    <q-card v-if="authStore.isGestor" class="dark-card q-pa-md">
      <div class="text-subtitle2 text-weight-bold text-grey-3 flex items-center justify-between q-mb-sm">
        <span class="flex items-center">
          <q-icon name="dns" size="16px" class="q-mr-xs text-primary" />
          Diagnóstico do Servidor (Gestão)
        </span>
        <q-btn flat round dense icon="refresh" size="sm" color="grey-5" @click="checkHealth" />
      </div>

      <div class="q-gutter-y-xs">
        <div class="row items-center justify-between text-caption text-grey-4">
          <span>Backend Django REST:</span>
          <span :class="backendOk ? 'text-positive text-weight-bold' : 'text-negative text-weight-bold'">
            {{ backendOk ? 'Conectado (Porta 8000)' : 'Desconectado' }}
          </span>
        </div>
        <div class="row items-center justify-between text-caption text-grey-4">
          <span>Banco PostgreSQL:</span>
          <span :class="dbOk ? 'text-positive text-weight-bold' : 'text-grey-5'">
            {{ dbOk ? 'Online & Saudável' : 'Aguardando' }}
          </span>
        </div>
        <div class="row items-center justify-between text-caption text-grey-4">
          <span>PWA Service Worker:</span>
          <span class="text-positive text-weight-bold">
            Ativo (Workbox)
          </span>
        </div>
      </div>
    </q-card>
  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'
import api from '../boot/axios'
import { avisosService } from '../services/api'
import StudentHomeSection from '../components/StudentHomeSection.vue'

const $q = useQuasar()
const authStore = useAuthStore()

const backendOk = ref(false)
const dbOk = ref(false)
const ultimoAviso = ref(null)
const loadingAvisos = ref(false)
const viagemAtivaMotorista = ref(null)

const metricas = reactive({
  pendentes: 0,
  onibus: 0,
  rotas: 0
})

const todayFormatted = computed(() => {
  return new Date().toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric'
  })
})

const roleIcon = computed(() => {
  if (authStore.isAluno) return 'school'
  if (authStore.isMotorista) return 'sports_motorsports'
  return 'admin_panel_settings'
})

const roleBadgeColor = computed(() => {
  if (authStore.isAluno) return 'primary'
  if (authStore.isMotorista) return 'secondary'
  return 'accent'
})

const getBadgeColor = (tipo) => {
  switch (tipo) {
    case 'URGENTE': return 'negative'
    case 'ATRASO': return 'warning'
    case 'MANUTENCAO': return 'info'
    default: return 'primary'
  }
}

const formatHora = (dataStr) => {
  if (!dataStr) return '--:--'
  try {
    const d = new Date(dataStr)
    return d.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return '--:--'
  }
}

const fetchUltimoAviso = async () => {
  loadingAvisos.value = true
  try {
    const response = await avisosService.getAvisos()
    const lista = response.data?.results || response.data || []
    if (lista.length > 0) {
      ultimoAviso.value = lista[0]
    } else {
      ultimoAviso.value = null
    }
  } catch (e) {
    ultimoAviso.value = null
  } finally {
    loadingAvisos.value = false
  }
}

const fetchMetricasAdmin = async () => {
  if (!authStore.isGestor) return
  try {
    const [resAlunos, resOnibus, resRotas] = await Promise.all([
      api.get('/alunos/fila-pendente/'),
      api.get('/veiculos/onibus/'),
      api.get('/rotas/')
    ])
    metricas.pendentes = resAlunos.data?.length || resAlunos.data?.count || 0
    metricas.onibus = resOnibus.data?.results?.length || resOnibus.data?.length || 0
    metricas.rotas = resRotas.data?.results?.length || resRotas.data?.length || 0
  } catch (e) {
    console.warn('Erro ao carregar métricas do painel:', e)
  }
}

const fetchViagemMotorista = async () => {
  if (!authStore.isMotorista) return
  try {
    const res = await api.get('/viagens/ativa/')
    viagemAtivaMotorista.value = res.data?.viagem || res.data || null
  } catch (e) {
    viagemAtivaMotorista.value = null
  }
}

const checkHealth = async () => {
  try {
    const res = await api.get('/health/')
    backendOk.value = res.data.status === 'healthy'
    dbOk.value = res.data.database?.connected || false
  } catch (e) {
    backendOk.value = false
    dbOk.value = false
  }
}

onMounted(() => {
  checkHealth()
  fetchUltimoAviso()
  if (authStore.isGestor) {
    fetchMetricasAdmin()
  }
  if (authStore.isMotorista) {
    fetchViagemMotorista()
  }
})
</script>

<style scoped lang="scss">
.frosted-icon-circle {
  width: 34px;
  height: 34px;
  border-radius: 10px;
  background: rgba(245, 158, 11, 0.12);
  border: 1px solid rgba(245, 158, 11, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}

.frosted-icon-circle-lg {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
}

.frosted-primary {
  background: rgba(245, 158, 11, 0.15) !important;
  border-color: rgba(245, 158, 11, 0.4) !important;
}

.border-pending-gold {
  border: 1px solid rgba(245, 158, 11, 0.45) !important;
  box-shadow: 0 4px 18px rgba(245, 158, 11, 0.12);
}

.preview-aviso-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
