<template>
  <div class="driver-panel q-pb-xl">
    <!-- Banner de Status de Conectividade / Offline-First -->
    <div v-if="!isOnline" class="offline-banner q-pa-sm q-mb-md text-center text-weight-bold">
      <q-icon name="wifi_off" size="18px" class="q-mr-xs" />
      <span>Modo Offline: Operando sem sinal de rede. Embarques serão salvos localmente.</span>
    </div>

    <div v-else-if="offlineQueue.length > 0" class="sync-banner q-pa-sm q-mb-md row items-center justify-between">
      <div class="row items-center">
        <q-icon name="cloud_upload" size="20px" class="q-mr-sm text-primary" />
        <span class="text-caption text-weight-bold text-white">
          {{ offlineQueue.length }} check-in(s) offline pendentes de sincronização
        </span>
      </div>
      <q-btn
        dense
        no-caps
        color="primary"
        text-color="dark"
        size="sm"
        label="Sincronizar Agora"
        icon="sync"
        :loading="syncing"
        @click="syncOfflineQueue"
      />
    </div>

    <!-- Header da Página do Motorista -->
    <div class="row items-center justify-between q-mb-md">
      <div>
        <h1 class="text-h6 text-weight-bolder text-white q-my-none flex items-center">
          <q-icon name="directions_bus" color="primary" size="26px" class="q-mr-xs" />
          Painel do Motorista
        </h1>
        <p class="text-caption text-grey-4 q-mb-none">
          Operação de Viagem & Validação de Embarques
        </p>
      </div>

      <q-badge
        :color="isOnline ? 'positive' : 'warning'"
        :text-color="isOnline ? 'white' : 'dark'"
        class="q-pa-xs text-weight-bold"
      >
        <q-icon :name="isOnline ? 'wifi' : 'wifi_off'" size="14px" class="q-mr-xs" />
        {{ isOnline ? 'Online' : 'Offline' }}
      </q-badge>
    </div>

    <!-- Loading State Inicial -->
    <div v-if="loadingInitial" class="column items-center justify-center q-pa-xl">
      <q-spinner-dots color="primary" size="48px" />
      <span class="text-caption text-grey-4 q-mt-sm">Verificando status operacional...</span>
    </div>

    <!-- Error State Inicial -->
    <div v-else-if="errorInitial" class="text-center q-pa-xl dark-card rounded-borders border-danger">
      <q-icon name="cloud_off" size="52px" color="negative" class="q-mb-sm" />
      <div class="text-h6 text-white text-weight-bold">Falha ao conectar com o serviço de viagens</div>
      <p class="text-caption text-grey-4 q-mt-xs q-mb-md">
        {{ errorInitial }}
      </p>
      <q-btn
        color="primary"
        text-color="dark"
        icon="refresh"
        label="Tentar Novamente"
        class="btn-bus-primary text-weight-bold"
        no-caps
        @click="recarregarPainelInicial"
      />
    </div>

    <!-- ========================================================================= -->
    <!-- ESTADO 1: NENHUMA VIAGEM EM ANDAMENTO -> TELA DE INICIAR VIAGEM           -->
    <!-- ========================================================================= -->
    <div v-else-if="!viagemAtiva">
      <q-card class="dark-card q-pa-md">
        <div class="text-subtitle1 text-weight-bold text-primary flex items-center q-mb-xs">
          <q-icon name="play_circle" size="22px" class="q-mr-xs" />
          Iniciar Nova Viagem
        </div>
        <p class="text-caption text-grey-4 q-mb-md">
          Selecione a rota planejada e o veículo para abrir o período de embarque estudantil.
        </p>

        <!-- Formulário de Inicialização -->
        <q-form @submit.prevent="iniciarViagem" class="q-gutter-y-md">
          <!-- Seleção de Rota -->
          <div>
            <label class="text-caption text-weight-bold text-grey-3 block q-mb-xs">
              Rota Municipal *
            </label>
            <q-select
              v-model="formIniciar.rota_id"
              :options="rotasOptions"
              option-value="id"
              option-label="label"
              emit-value
              map-options
              filled
              dark
              color="primary"
              bg-color="dark"
              dense
              popup-content-class="bg-dark text-white"
              :loading="loadingRotas"
              placeholder="Selecione a rota"
              :rules="[val => !!val || 'Selecione uma rota obrigatória']"
            >
              <template v-slot:prepend>
                <q-icon name="alt_route" color="primary" />
              </template>
            </q-select>
          </div>

          <!-- Seleção de Ônibus -->
          <div>
            <label class="text-caption text-weight-bold text-grey-3 block q-mb-xs">
              Ônibus da Frota *
            </label>
            <q-select
              v-model="formIniciar.onibus_id"
              :options="onibusOptions"
              option-value="id"
              option-label="label"
              emit-value
              map-options
              filled
              dark
              color="primary"
              bg-color="dark"
              dense
              popup-content-class="bg-dark text-white"
              :loading="loadingOnibus"
              placeholder="Selecione o veículo"
              :rules="[val => !!val || 'Selecione um ônibus obrigatório']"
            >
              <template v-slot:prepend>
                <q-icon name="directions_bus" color="primary" />
              </template>
            </q-select>
          </div>

          <!-- Sentido da Viagem (Ida vs Volta) - Botões Grandes de Toque -->
          <div>
            <label class="text-caption text-weight-bold text-grey-3 block q-mb-xs">
              Sentido do Trajeto *
            </label>
            <div class="row q-col-gutter-sm">
              <div class="col-6">
                <q-btn
                  :color="formIniciar.sentido === 'ida' ? 'primary' : 'grey-9'"
                  :text-color="formIniciar.sentido === 'ida' ? 'dark' : 'grey-4'"
                  :outline="formIniciar.sentido !== 'ida'"
                  class="full-width q-py-md text-weight-bold btn-touch"
                  no-caps
                  @click="formIniciar.sentido = 'ida'"
                >
                  <q-icon name="arrow_forward" size="20px" class="q-mr-xs" />
                  <div class="column text-left">
                    <span class="text-subtitle2 leading-tight">IDA</span>
                    <span class="text-caption" style="font-size: 0.68rem;">Bairro ➔ Faculdade</span>
                  </div>
                </q-btn>
              </div>

              <div class="col-6">
                <q-btn
                  :color="formIniciar.sentido === 'volta' ? 'primary' : 'grey-9'"
                  :text-color="formIniciar.sentido === 'volta' ? 'dark' : 'grey-4'"
                  :outline="formIniciar.sentido !== 'volta'"
                  class="full-width q-py-md text-weight-bold btn-touch"
                  no-caps
                  @click="formIniciar.sentido = 'volta'"
                >
                  <q-icon name="arrow_back" size="20px" class="q-mr-xs" />
                  <div class="column text-left">
                    <span class="text-subtitle2 leading-tight">VOLTA</span>
                    <span class="text-caption" style="font-size: 0.68rem;">Faculdade ➔ Bairro</span>
                  </div>
                </q-btn>
              </div>
            </div>
          </div>

          <!-- Botão Tático de Iniciar Viagem -->
          <q-btn
            type="submit"
            color="primary"
            text-color="dark"
            class="full-width q-py-md btn-bus-primary text-weight-bolder text-h6 q-mt-lg"
            :loading="startingViagem"
            icon="play_arrow"
            label="INICIAR VIAGEM"
            no-caps
          />
        </q-form>
      </q-card>
    </div>

    <!-- ========================================================================= -->
    <!-- ESTADO 2: VIAGEM EM ANDAMENTO -> DASHBOARD E VALIDAÇÃO DE PASSAGEIROS     -->
    <!-- ========================================================================= -->
    <div v-else>
      <!-- Card Superior: Informações da Viagem Ativa -->
      <q-card class="dark-card q-pa-md q-mb-md">
        <div class="row items-center justify-between q-mb-xs">
          <div class="row items-center">
            <q-badge color="positive" class="q-mr-sm text-weight-bold animate-pulse">
              EM ANDAMENTO
            </q-badge>
            <span class="text-caption text-grey-4">
              Iniciada às {{ formatHora(viagemAtiva.hora_inicio) }}
            </span>
          </div>

          <q-btn
            flat
            dense
            round
            icon="refresh"
            color="primary"
            :loading="refreshingDashboard"
            @click="refreshDashboard"
          >
            <q-tooltip>Atualizar Métricas</q-tooltip>
          </q-btn>
        </div>

        <div class="text-h6 text-weight-bolder text-white">
          {{ viagemAtiva.rota_nome }}
        </div>

        <div class="row items-center q-gutter-x-sm q-mt-xs">
          <q-chip dense dark color="grey-8" text-color="white" icon="directions_bus">
            Placa: <strong class="q-ml-xs text-primary">{{ viagemAtiva.onibus_placa }}</strong>
          </q-chip>
          <q-chip dense dark color="grey-8" text-color="white" icon="swap_horiz">
            Sentido: <strong class="q-ml-xs text-primary">{{ viagemAtiva.sentido_display }}</strong>
          </q-chip>
        </div>

        <!-- Contadores Táticos em Tempo Real -->
        <div class="row q-col-gutter-sm q-mt-sm">
          <div class="col-6 col-sm-3">
            <div class="kpi-card text-center q-pa-sm">
              <div class="text-caption text-grey-4">Previstos</div>
              <div class="text-h5 text-weight-bolder text-primary">
                {{ viagemAtiva.total_previstos }}
              </div>
              <div class="text-caption text-grey-5" style="font-size: 0.65rem;">
                Intenção confirmada
              </div>
            </div>
          </div>

          <div class="col-6 col-sm-3">
            <div class="kpi-card text-center q-pa-sm">
              <div class="text-caption text-grey-4">Embarcados</div>
              <div class="text-h5 text-weight-bolder text-positive">
                {{ totalEmbarcadosCalculado }}
              </div>
              <div class="text-caption text-grey-5" style="font-size: 0.65rem;">
                Check-in validado
              </div>
            </div>
          </div>

          <div class="col-6 col-sm-3">
            <div class="kpi-card text-center q-pa-sm">
              <div class="text-caption text-grey-4">Vagas Livres</div>
              <div class="text-h5 text-weight-bolder" :class="vagasRestantesCalculadas <= 0 ? 'text-negative' : 'text-white'">
                {{ vagasRestantesCalculadas }}
              </div>
              <div class="text-caption text-grey-5" style="font-size: 0.65rem;">
                Capacidade: {{ viagemAtiva.capacidade_onibus }}
              </div>
            </div>
          </div>

          <div class="col-6 col-sm-3">
            <div class="kpi-card text-center q-pa-sm">
              <div class="text-caption text-grey-4">Ocupação</div>
              <div class="text-h5 text-weight-bolder" :class="ocupacaoCor">
                {{ percentualOcupacaoCalculado }}%
              </div>
              <div class="text-caption text-grey-5" style="font-size: 0.65rem;">
                Lotação relativa
              </div>
            </div>
          </div>
        </div>

        <!-- Barra de Ocupação da Frota -->
        <div class="q-mt-sm">
          <q-linear-progress
            :value="percentualOcupacaoCalculado / 100"
            :color="ocupacaoBarColor"
            track-color="grey-9"
            size="8px"
            rounded
          />
        </div>

        <!-- Botão para Concluir Viagem -->
        <div class="q-mt-md">
          <q-btn
            outline
            color="negative"
            class="full-width q-py-sm text-weight-bold"
            icon="stop_circle"
            label="CONCLUIR OPERAÇÃO DA VIAGEM"
            no-caps
            :loading="finishingViagem"
            @click="confirmarConclusaoViagem"
          />
        </div>
      </q-card>

      <!-- ===================================================================== -->
      <!-- SEÇÃO DE VALIDAÇÃO MANUAL DE PASSAGEIRO (CHECK-IN CONTINGENCIAL)      -->
      <!-- ===================================================================== -->
      <q-card class="dark-card q-pa-md">
        <div class="row items-center justify-between q-mb-xs">
          <div class="text-subtitle1 text-weight-bold text-white flex items-center">
            <q-icon name="how_to_reg" color="primary" size="22px" class="q-mr-xs" />
            Check-in Manual de Passageiro
          </div>
          <q-badge color="grey-8" text-color="grey-3">Contingência</q-badge>
        </div>
        <p class="text-caption text-grey-4 q-mb-md">
          Valide o embarque de alunos sem bateria ou sem sinal de internet no smartphone.
        </p>

        <!-- Campo de Busca em Tempo Real -->
        <q-input
          v-model="termoBusca"
          filled
          dark
          color="primary"
          bg-color="dark"
          dense
          clearable
          debounce="300"
          placeholder="Buscar por nome, CPF ou matrícula..."
          @update:model-value="buscarAlunos"
        >
          <template v-slot:prepend>
            <q-icon name="search" color="primary" />
          </template>
          <template v-slot:append>
            <q-spinner v-if="loadingBusca" color="primary" size="20px" />
          </template>
        </q-input>

        <!-- Lista de Resultados de Alunos -->
        <div class="q-mt-md q-gutter-y-sm">
          <div v-if="alunosResultado.length === 0 && !loadingBusca" class="text-center q-pa-md text-grey-5">
            <q-icon name="person_search" size="36px" class="q-mb-xs text-grey-6" />
            <div class="text-caption">Nenhum aluno encontrado para a busca informada.</div>
          </div>

          <q-card
            v-for="aluno in alunosResultado"
            :key="aluno.id"
            class="aluno-checkin-item q-pa-sm"
            :class="{ 'aluno-embarcado': aluno.ja_embarcou }"
          >
            <div class="row items-center justify-between">
              <div class="row items-center col-8">
                <q-avatar size="38px" color="grey-8" text-color="primary" class="q-mr-sm">
                  <q-icon name="school" size="20px" />
                </q-avatar>
                <div>
                  <div class="text-subtitle2 text-weight-bold text-white leading-tight">
                    {{ aluno.nome }}
                  </div>
                  <div class="text-caption text-grey-4" style="font-size: 0.72rem;">
                    Mat: <span class="text-white">{{ aluno.matricula }}</span> | CPF: {{ aluno.cpf_mascarado }}
                  </div>
                  <div class="text-caption text-primary" style="font-size: 0.70rem;">
                    {{ aluno.instituicao_nome }} {{ aluno.instituicao_sigla ? `(${aluno.instituicao_sigla})` : '' }}
                  </div>
                </div>
              </div>

              <!-- Ação de Check-in -->
              <div class="col-4 text-right">
                <q-chip
                  v-if="aluno.ja_embarcou"
                  dense
                  color="positive"
                  text-color="white"
                  icon="check_circle"
                  class="text-weight-bold"
                >
                  Embarcado
                </q-chip>

                <q-btn
                  v-else
                  color="primary"
                  text-color="dark"
                  class="text-weight-bold btn-bus-primary"
                  size="sm"
                  no-caps
                  icon="check"
                  label="Embarcar"
                  :loading="aluno.validando"
                  @click="registrarEmbarqueManual(aluno)"
                />
              </div>
            </div>
          </q-card>
        </div>
      </q-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useQuasar } from 'quasar'
import api from '../../boot/axios'

const $q = useQuasar()

// Conectividade e Fila Offline
const isOnline = ref(window.navigator.onLine)
const offlineQueue = ref([])
const syncing = ref(false)

// Estados de Carga
const loadingInitial = ref(true)
const errorInitial = ref(null)
const loadingRotas = ref(false)
const loadingOnibus = ref(false)
const startingViagem = ref(false)
const finishingViagem = ref(false)
const refreshingDashboard = ref(false)
const loadingBusca = ref(false)

// Dados do Painel
const viagemAtiva = ref(null)
const rotas = ref([])
const frotaOnibus = ref([])
const termoBusca = ref('')
const alunosResultado = ref([])

// Form Iniciar Viagem
const formIniciar = reactive({
  rota_id: null,
  onibus_id: null,
  sentido: 'ida'
})

// Chave do LocalStorage para contingência offline
const OFFLINE_STORAGE_KEY = 'appbus_offline_checkins'

// Options computadas para os seletores
const rotasOptions = computed(() => {
  return rotas.value.map(r => ({
    id: r.id,
    label: `${r.nome} (${r.paradas ? r.paradas.length : 0} paradas)`
  }))
})

const onibusOptions = computed(() => {
  return frotaOnibus.value.map(o => ({
    id: o.id,
    label: `${o.placa} - ${o.modelo_nome || 'Ônibus'} (${o.capacidade} lugares)`
  }))
})

// Métricas computadas considerando check-ins offline locais
const totalEmbarcadosCalculado = computed(() => {
  if (!viagemAtiva.value) return 0
  const offlineDaViagem = offlineQueue.value.filter(item => item.viagem_id === viagemAtiva.value.viagem_id).length
  return (viagemAtiva.value.total_embarcados || 0) + offlineDaViagem
})

const vagasRestantesCalculadas = computed(() => {
  if (!viagemAtiva.value) return 0
  const capacidade = viagemAtiva.value.capacidade_onibus || 0
  return Math.max(0, capacidade - totalEmbarcadosCalculado.value)
})

const percentualOcupacaoCalculado = computed(() => {
  if (!viagemAtiva.value || !viagemAtiva.value.capacidade_onibus) return 0
  const capacidade = viagemAtiva.value.capacidade_onibus
  const ocupacao = (totalEmbarcadosCalculado.value / capacidade) * 100
  return Math.min(100, Math.round(ocupacao * 10) / 10)
})

const ocupacaoCor = computed(() => {
  const p = percentualOcupacaoCalculado.value
  if (p >= 100) return 'text-negative'
  if (p >= 80) return 'text-warning'
  return 'text-positive'
})

const ocupacaoBarColor = computed(() => {
  const p = percentualOcupacaoCalculado.value
  if (p >= 100) return 'negative'
  if (p >= 80) return 'warning'
  return 'positive'
})

// Funções de Inicialização e Ciclo de Vida
const formatHora = (dataStr) => {
  if (!dataStr) return '--:--'
  try {
    const d = new Date(dataStr)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return '--:--'
  }
}

const loadOfflineQueue = () => {
  try {
    const raw = localStorage.getItem(OFFLINE_STORAGE_KEY)
    offlineQueue.value = raw ? JSON.parse(raw) : []
  } catch (e) {
    offlineQueue.value = []
  }
}

const saveOfflineQueue = () => {
  try {
    localStorage.setItem(OFFLINE_STORAGE_KEY, JSON.stringify(offlineQueue.value))
  } catch (e) {
    console.error('Falha ao salvar fila offline', e)
  }
}

// Verifica se há viagem ativa para este motorista hoje
const fetchViagemAtiva = async () => {
  errorInitial.value = null
  try {
    const response = await api.get('/operacao/viagem/ativa/')
    if (response.data.ativa) {
      viagemAtiva.value = response.data.viagem
      await buscarAlunos()
    } else {
      viagemAtiva.value = null
      await carregarDadosIniciais()
    }
  } catch (error) {
    console.error('Erro ao verificar viagem ativa:', error)
    if (!error.response || error.code === 'ERR_NETWORK') {
      errorInitial.value = 'Sem conexão com o servidor. Verifique seu sinal de rede ou tente novamente.'
    } else {
      errorInitial.value = error.response?.data?.detail || error.response?.data?.erro || 'Falha ao sincronizar painel operacional.'
    }
  } finally {
    loadingInitial.value = false
  }
}

const recarregarPainelInicial = async () => {
  errorInitial.value = null
  loadingInitial.value = true
  await fetchViagemAtiva()
}

// Carrega rotas e ônibus da prefeitura do motorista
const carregarDadosIniciais = async () => {
  loadingRotas.value = true
  loadingOnibus.value = true
  try {
    const [resRotas, resOnibus] = await Promise.all([
      api.get('/rotas/'),
      api.get('/veiculos/onibus/')
    ])
    rotas.value = resRotas.data.results || resRotas.data || []
    frotaOnibus.value = resOnibus.data.results || resOnibus.data || []

    if (rotas.value.length > 0 && !formIniciar.rota_id) {
      formIniciar.rota_id = rotas.value[0].id
    }
    if (frotaOnibus.value.length > 0 && !formIniciar.onibus_id) {
      formIniciar.onibus_id = frotaOnibus.value[0].id
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: 'Falha ao carregar opções de rotas ou frota municipal.'
    })
  } finally {
    loadingRotas.value = false
    loadingOnibus.value = false
  }
}

// Disparo da Ação: Iniciar Viagem
const iniciarViagem = async () => {
  if (!formIniciar.rota_id || !formIniciar.onibus_id) {
    $q.notify({
      type: 'warning',
      icon: 'warning',
      message: 'Selecione uma rota e um ônibus para iniciar a operação.'
    })
    return
  }

  startingViagem.value = true
  try {
    const payload = {
      rota_id: formIniciar.rota_id,
      onibus_id: formIniciar.onibus_id,
      sentido: formIniciar.sentido
    }
    const response = await api.post('/operacao/viagem/iniciar/', payload)
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: 'Viagem iniciada com sucesso! Embarques liberados.'
    })
    // Recarrega o estado completo via endpoint de viagem ativa
    await fetchViagemAtiva()
  } catch (error) {
    const msg = error.response?.data?.erro || 
                error.response?.data?.detail || 
                'Não foi possível iniciar a viagem. Verifique se o ônibus já está em operação.'
    $q.notify({
      type: 'negative',
      icon: 'report_problem',
      message: msg
    })
  } finally {
    startingViagem.value = false
  }
}

// Atualizar métricas do dashboard
const refreshDashboard = async () => {
  if (!viagemAtiva.value) return
  refreshingDashboard.value = true
  try {
    const response = await api.get(`/operacao/viagem/${viagemAtiva.value.viagem_id}/dashboard/`)
    viagemAtiva.value = response.data
    await buscarAlunos()
    $q.notify({
      type: 'info',
      icon: 'refresh',
      message: 'Métricas da viagem atualizadas.',
      timeout: 1200
    })
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: 'Falha ao atualizar métricas da viagem.'
    })
  } finally {
    refreshingDashboard.value = false
  }
}

// Concluir Viagem com diálogo confirmatório
const confirmarConclusaoViagem = () => {
  $q.dialog({
    title: 'Concluir Viagem',
    message: `Deseja realmente encerrar a viagem da ${viagemAtiva.value.rota_nome}? Esta ação consolida os embarques do trajeto.`,
    cancel: true,
    persistent: true,
    dark: true,
    ok: {
      label: 'Concluir Operação',
      color: 'negative',
      flat: false
    }
  }).onOk(async () => {
    finishingViagem.value = true
    try {
      await api.post(`/operacao/viagem/${viagemAtiva.value.viagem_id}/concluir/`)
      $q.notify({
        type: 'positive',
        icon: 'task_alt',
        message: 'Viagem concluída com sucesso!'
      })
      viagemAtiva.value = null
      alunosResultado.value = []
      termoBusca.value = ''
      await carregarDadosIniciais()
    } catch (error) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: error.response?.data?.erro || 'Erro ao concluir viagem.'
      })
    } finally {
      finishingViagem.value = false
    }
  })
}

// Busca rápida de alunos para check-in manual
const buscarAlunos = async () => {
  if (!viagemAtiva.value) return
  loadingBusca.value = true
  try {
    const params = {
      q: termoBusca.value || '',
      viagem_id: viagemAtiva.value.viagem_id
    }
    const response = await api.get('/operacao/alunos/busca/', { params })
    const alunos = response.data || []

    // Cruzar com a fila offline local para manter status consistente
    const offlineAlunosIds = new Set(
      offlineQueue.value
        .filter(item => item.viagem_id === viagemAtiva.value.viagem_id)
        .map(item => item.aluno_id)
    )

    alunosResultado.value = alunos.map(a => ({
      ...a,
      validando: false,
      ja_embarcou: a.ja_embarcou || offlineAlunosIds.has(a.id)
    }))
  } catch (error) {
    console.error('Erro na busca de alunos:', error)
  } finally {
    loadingBusca.value = false
  }
}

// Registro de Embarque Manual (com suporte Offline-First)
const registrarEmbarqueManual = async (aluno) => {
  if (!viagemAtiva.value) return
  aluno.validando = true

  const checkinData = {
    viagem_id: viagemAtiva.value.viagem_id,
    aluno_id: aluno.id,
    aluno_nome: aluno.nome,
    timestamp: new Date().toISOString()
  }

  // Tática de feedback tátil para cabine do ônibus
  try {
    if (window.navigator?.vibrate) {
      window.navigator.vibrate(100)
    }
  } catch (e) {
    // Silently ignore
  }

  // Se o dispositivo estiver offline, salvar na fila local imediatamente
  if (!isOnline.value) {
    offlineQueue.value.push(checkinData)
    saveOfflineQueue()
    aluno.ja_embarcou = true
    aluno.validando = false
    $q.notify({
      type: 'warning',
      icon: 'save',
      message: `Sem sinal: Check-in de ${aluno.nome} gravado localmente!`
    })
    return
  }

  // Se online, tenta enviar direto para a API
  try {
    await api.post('/operacao/embarque/manual/', {
      viagem_id: checkinData.viagem_id,
      aluno_id: checkinData.aluno_id
    })

    aluno.ja_embarcou = true
    if (viagemAtiva.value.total_embarcados !== undefined) {
      viagemAtiva.value.total_embarcados += 1
    }

    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: `Embarque de ${aluno.nome} validado com sucesso!`
    })
  } catch (error) {
    // Se a falha for por erro de rede/timeout, enfileira offline
    if (!error.response || error.code === 'ERR_NETWORK') {
      offlineQueue.value.push(checkinData)
      saveOfflineQueue()
      aluno.ja_embarcou = true
      $q.notify({
        type: 'warning',
        icon: 'cloud_off',
        message: `Falha na conexão: Check-in de ${aluno.nome} armazenado na fila offline.`
      })
    } else {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: error.response?.data?.erro || 'Erro ao validar embarque.'
      })
    }
  } finally {
    aluno.validando = false
  }
}

// Sincronização da Fila Offline com a API
const syncOfflineQueue = async () => {
  if (offlineQueue.value.length === 0 || syncing.value) return
  syncing.value = true

  let syncCount = 0
  const remaining = []

  for (const item of offlineQueue.value) {
    try {
      await api.post('/operacao/embarque/manual/', {
        viagem_id: item.viagem_id,
        aluno_id: item.aluno_id
      })
      syncCount++
    } catch (error) {
      // Se já foi registrado anteriormente (400 duplicidade), consideramos sincronizado
      const erroMsg = error.response?.data?.erro || ''
      if (erroMsg.includes('já possui embarque registrado')) {
        syncCount++
      } else {
        remaining.push(item)
      }
    }
  }

  offlineQueue.value = remaining
  saveOfflineQueue()
  syncing.value = false

  if (syncCount > 0) {
    $q.notify({
      type: 'positive',
      icon: 'cloud_done',
      message: `${syncCount} embarque(s) offline sincronizado(s) com a base central!`
    })
    await refreshDashboard()
  }
}

// Listeners de Conectividade
const handleOnline = () => {
  isOnline.value = true
  syncOfflineQueue()
}

const handleOffline = () => {
  isOnline.value = false
}

onMounted(async () => {
  loadOfflineQueue()
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)
  await fetchViagemAtiva()
})

onUnmounted(() => {
  window.removeEventListener('online', handleOnline)
  window.removeEventListener('offline', handleOffline)
})
</script>

<style scoped lang="scss">
.driver-panel {
  max-width: 600px;
  margin: 0 auto;
}

.offline-banner {
  background: #B45309;
  color: #FEF3C7;
  border-radius: 8px;
  font-size: 0.82rem;
}

.sync-banner {
  background: #1E293B;
  border: 1px solid #334155;
  border-radius: 8px;
}

.btn-touch {
  border-radius: 12px;
  min-height: 58px;
}

.kpi-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
}

.aluno-checkin-item {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  transition: all 0.2s ease;

  &.aluno-embarcado {
    border-color: rgba(33, 186, 69, 0.4);
    background: rgba(33, 186, 69, 0.05);
  }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

.border-danger {
  border: 1px solid rgba(193, 0, 21, 0.4);
}
</style>
