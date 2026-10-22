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
    <q-card class="dark-card q-pa-md q-mb-md border-mural-highlight cursor-pointer" @click="$router.push('/mural')">
      <div class="row items-center justify-between q-mb-xs">
        <div class="row items-center">
          <q-avatar size="32px" color="primary" text-color="dark" class="q-mr-sm">
            <q-icon name="campaign" size="18px" />
          </q-avatar>
          <div>
            <div class="text-subtitle2 text-weight-bold text-white leading-tight">
              Mural de Avisos & Comunicados
            </div>
            <div class="text-caption text-grey-4" style="font-size: 0.72rem;">
              Linhas municipais em tempo real
            </div>
          </div>
        </div>

        <q-btn
          flat
          dense
          no-caps
          color="primary"
          label="Ver Mural"
          icon-right="arrow_forward"
          size="sm"
          to="/mural"
        />
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

    <!-- PAINEL EXECUTIVO: Gestor Municipal (Etapa 3.3) -->
    <div v-if="authStore.isGestor" class="q-gutter-y-md q-mb-md">
      <!-- Cards de Métricas em Tempo Real -->
      <div class="row q-col-gutter-sm">
        <!-- Fila de Pendências -->
        <div class="col-12 col-sm-4">
          <q-card
            class="dark-card q-pa-md cursor-pointer metric-card"
            :class="{ 'border-pending': metricas.pendentes > 0 }"
            @click="$router.push('/admin/aprovacoes')"
          >
            <div class="row items-center justify-between">
              <div>
                <div class="text-caption text-grey-4">Fila de Aprovação</div>
                <div class="text-h4 text-weight-bolder" :class="metricas.pendentes > 0 ? 'text-primary' : 'text-white'">
                  {{ metricas.pendentes }}
                </div>
                <div class="text-caption text-grey-5">aguardando deferimento</div>
              </div>
              <q-avatar size="42px" :color="metricas.pendentes > 0 ? 'primary' : 'grey-8'" :text-color="metricas.pendentes > 0 ? 'dark' : 'grey-4'">
                <q-icon name="how_to_reg" size="24px" />
              </q-avatar>
            </div>
          </q-card>
        </div>

        <!-- Frota Ativa -->
        <div class="col-6 col-sm-4">
          <q-card class="dark-card q-pa-md cursor-pointer metric-card" @click="$router.push('/admin/frota')">
            <div class="row items-center justify-between">
              <div>
                <div class="text-caption text-grey-4">Frota Operacional</div>
                <div class="text-h4 text-weight-bolder text-white">
                  {{ metricas.onibus }}
                </div>
                <div class="text-caption text-grey-5">ônibus cadastrados</div>
              </div>
              <q-avatar size="42px" color="grey-8" text-color="primary">
                <q-icon name="directions_bus" size="24px" />
              </q-avatar>
            </div>
          </q-card>
        </div>

        <!-- Rotas Ativas -->
        <div class="col-6 col-sm-4">
          <q-card class="dark-card q-pa-md cursor-pointer metric-card" @click="$router.push('/admin/frota')">
            <div class="row items-center justify-between">
              <div>
                <div class="text-caption text-grey-4">Rotas & Linhas</div>
                <div class="text-h4 text-weight-bolder text-white">
                  {{ metricas.rotas }}
                </div>
                <div class="text-caption text-grey-5">itinerários ativos</div>
              </div>
              <q-avatar size="42px" color="grey-8" text-color="primary">
                <q-icon name="alt_route" size="24px" />
              </q-avatar>
            </div>
          </q-card>
        </div>
      </div>

      <!-- Atalhos de Gestão e Emissão de QR Code -->
      <q-card class="dark-card q-pa-md">
        <div class="text-subtitle1 text-weight-bold text-white q-mb-sm flex items-center">
          <q-icon name="admin_panel_settings" size="20px" class="q-mr-xs text-primary" />
          Ações Rápidas de Gestão Municipal
        </div>

        <div class="row q-col-gutter-sm">
          <div class="col-12 col-sm-4">
            <q-btn
              color="primary"
              text-color="dark"
              class="full-width q-py-sm btn-bus-primary text-weight-bold"
              icon="how_to_reg"
              label="Avaliar Fila de Alunos"
              no-caps
              to="/admin/aprovacoes"
            />
          </div>
          <div class="col-12 col-sm-4">
            <q-btn
              outline
              color="primary"
              class="full-width q-py-sm"
              icon="directions_bus"
              label="Gerenciar Frota e Rotas"
              no-caps
              to="/admin/frota"
            />
          </div>
          <div class="col-12 col-sm-4">
            <q-btn
              outline
              color="primary"
              class="full-width q-py-sm"
              icon="qr_code_2"
              label="Imprimir Cartaz QR Code"
              no-caps
              to="/admin/qrcode"
            />
          </div>
        </div>
      </q-card>
    </div>

    <!-- Módulo Operacional do Aluno (Carteirinha Digital, Viagem do Dia e Predição Automática) -->
    <StudentHomeSection v-if="authStore.isAluno" class="q-mb-md" />

    <!-- Card Operacional: Motorista (Controle de Viagem) -->
    <q-card v-if="authStore.isMotorista" class="dark-card q-pa-md q-mb-md">
      <div class="text-subtitle1 text-weight-bold text-primary flex items-center q-mb-xs">
        <q-icon name="departure_board" size="20px" class="q-mr-xs" />
        Painel de Viagem & Embarques
      </div>
      <p class="text-caption text-grey-4">
        Inicie a rota do dia para habilitar o check-in dos passageiros e monitorar a lotação em tempo real.
      </p>

      <div class="q-gutter-y-sm q-mt-sm">
        <q-btn
          color="primary"
          text-color="dark"
          class="full-width btn-bus-primary"
          size="md"
          to="/motorista"
          no-caps
        >
          <q-icon name="play_arrow" size="20px" class="q-mr-xs" />
          Instanciar / Gerenciar Viagem
        </q-btn>

        <q-btn
          outline
          color="primary"
          class="full-width"
          size="md"
          to="/motorista"
          no-caps
        >
          <q-icon name="person_add" size="20px" class="q-mr-xs" />
          Check-in Manual de Passageiro
        </q-btn>
      </div>
    </q-card>

    <!-- Card de Status do Sistema & Backend Health -->
    <q-card class="dark-card q-pa-md">
      <div class="text-subtitle2 text-weight-bold text-grey-3 flex items-center justify-between q-mb-sm">
        <span>Conectividade do Sistema</span>
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
})
</script>

<style scoped lang="scss">
.metric-card {
  transition: transform 0.2s ease, border-color 0.2s ease;
  &:hover {
    transform: translateY(-2px);
  }
}

.border-pending {
  border: 1px solid #F2C037;
}

.border-mural-highlight {
  border: 1px solid rgba(242, 192, 55, 0.3);
  transition: all 0.2s ease;

  &:hover {
    border-color: #F2C037;
    box-shadow: 0 4px 18px rgba(242, 192, 55, 0.15);
  }
}

.preview-aviso-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
}
</style>
