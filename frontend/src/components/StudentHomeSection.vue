<template>
  <div class="student-home-section q-gutter-y-md">
    <!-- 1. CARTEIRINHA DIGITAL DO ESTUDANTE -->
    <q-card class="student-id-card q-pa-md text-white">
      <div class="row items-center justify-between q-mb-xs">
        <div class="row items-center">
          <q-avatar size="32px" color="primary" text-color="dark" class="q-mr-xs text-weight-bolder">
            <q-icon name="directions_bus" size="18px" />
          </q-avatar>
          <span class="text-caption text-weight-bolder text-uppercase tracking-wider">
            App<span class="text-primary">Bus</span> • Passe Digital
          </span>
        </div>

        <q-badge
          :color="statusBadgeColor"
          :text-color="authStore.isAlunoAprovado ? 'white' : 'dark'"
          class="text-weight-bold q-px-sm q-py-xs"
        >
          <q-icon :name="statusIcon" size="13px" class="q-mr-xs" />
          {{ statusLabel }}
        </q-badge>
      </div>

      <!-- Dados Centrais do Aluno -->
      <div class="row items-center q-mt-sm">
        <q-avatar size="56px" color="grey-9" text-color="primary" class="q-mr-md avatar-border">
          <q-icon name="school" size="32px" />
        </q-avatar>

        <div class="col">
          <div class="text-h6 text-weight-bolder leading-tight text-white">
            {{ authStore.userNome }}
          </div>
          <div class="text-caption text-grey-4">
            Matrícula: <strong class="text-white">{{ matriculaDisplay }}</strong>
          </div>
          <div class="text-caption text-primary text-weight-medium">
            {{ instituicaoDisplay }}
          </div>
        </div>
      </div>

      <!-- Município e Rodapé da Carteirinha -->
      <div class="q-mt-sm q-pt-xs border-top-subtle row items-center justify-between text-caption text-grey-4">
        <span>{{ clienteNomeDisplay }}</span>
        <span class="text-grey-5" style="font-size: 0.70rem;">Ano Letivo 2026</span>
      </div>
    </q-card>

    <!-- Alerta Informativo se Pendente ou Rejeitado -->
    <q-banner
      v-if="!authStore.isAlunoAprovado"
      rounded
      dense
      class="bg-warning text-dark text-caption q-pa-sm text-weight-medium"
    >
      <template v-slot:avatar>
        <q-icon name="info" size="20px" color="dark" />
      </template>
      <span v-if="authStore.isAlunoPendente">
        Seu cadastro está em análise pela prefeitura municipal. Você poderá embarcar assim que for aprovado.
      </span>
      <span v-else>
        Seu cadastro foi recusado pela prefeitura. Entre em contato com a Secretaria de Transporte.
      </span>
    </q-banner>

    <!-- 2. CARD DA VIAGEM DE HOJE & STATUS EM TEMPO REAL -->
    <q-card class="dark-card q-pa-md">
      <div class="row items-center justify-between q-mb-xs">
        <div class="text-subtitle1 text-weight-bold text-white flex items-center">
          <q-icon name="departure_board" color="primary" size="22px" class="q-mr-xs" />
          Ônibus Universitário Hoje
        </div>
        <q-btn flat round dense icon="refresh" color="grey-4" size="sm" :loading="loadingViagem" @click="fetchViagemAtiva" />
      </div>

      <!-- Caso haja viagem ativa no município -->
      <div v-if="viagemAtiva" class="q-mt-sm">
        <div class="active-trip-box q-pa-sm q-mb-sm">
          <div class="row items-center justify-between q-mb-xs">
            <q-badge color="positive" class="text-weight-bold animate-pulse">
              ÔNIBUS EM TRÂNSITO
            </q-badge>
            <span class="text-caption text-grey-4">
              Iniciado às {{ formatHora(viagemAtiva.hora_inicio) }}
            </span>
          </div>

          <div class="text-subtitle2 text-weight-bolder text-white">
            {{ viagemAtiva.rota_nome }}
          </div>

          <div class="row items-center q-gutter-x-sm q-mt-xs">
            <q-chip dense dark color="grey-8" text-color="white" icon="directions_bus" size="sm">
              Placa: <strong class="q-ml-xs text-primary">{{ viagemAtiva.onibus_placa }}</strong>
            </q-chip>
            <q-chip dense dark color="grey-8" text-color="white" icon="swap_horiz" size="sm">
              Sentido: <strong class="q-ml-xs text-primary">{{ viagemAtiva.sentido_display }}</strong>
            </q-chip>
          </div>

          <!-- Lotação Atual do Ônibus -->
          <div class="q-mt-sm">
            <div class="row justify-between text-caption text-grey-4 q-mb-xs" style="font-size: 0.72rem;">
              <span>Lotação: {{ viagemAtiva.total_embarcados }} / {{ viagemAtiva.capacidade_onibus }} passageiros</span>
              <span class="text-weight-bold" :class="viagemAtiva.vagas_restantes <= 0 ? 'text-negative' : 'text-primary'">
                {{ viagemAtiva.vagas_restantes }} vagas restantes
              </span>
            </div>
            <q-linear-progress
              :value="(viagemAtiva.total_embarcados || 0) / (viagemAtiva.capacidade_onibus || 1)"
              color="primary"
              track-color="grey-9"
              size="6px"
              rounded
            />
          </div>
        </div>
      </div>

      <!-- Caso nenhuma viagem esteja ativa agora -->
      <div v-else class="text-center q-pa-md text-grey-4">
        <q-icon name="schedule" size="36px" class="q-mb-xs text-grey-6" />
        <div class="text-subtitle2 text-weight-medium text-white">
          Aguardando Início da Linha
        </div>
        <div class="text-caption text-grey-5" style="font-size: 0.75rem;">
          O motorista ainda não iniciou o trajeto de hoje. Confirme sua demanda abaixo para garantir sua vaga.
        </div>
      </div>
    </q-card>

    <!-- 3. PREDIÇÃO DE DEMANDA AUTOMÁTICA ("VOU / NÃO VOU") -->
    <q-card class="dark-card q-pa-md">
      <div class="row items-center justify-between q-mb-xs">
        <div>
          <div class="text-subtitle1 text-weight-bold text-primary flex items-center">
            <q-icon name="today" size="20px" class="q-mr-xs" />
            Minha Intenção de Viagem
          </div>
          <div class="text-caption text-grey-4">
            {{ dataHojeFormatada }}
          </div>
        </div>

        <!-- Indicador de Sincronização Automática & Botão Recarregar -->
        <div class="row items-center q-gutter-x-xs">
          <q-spinner-dots v-if="loadingPredicao || savingPredicao" color="primary" size="18px" />
          <span
            class="text-caption text-weight-bold"
            :class="statusSyncClass"
            style="font-size: 0.72rem;"
          >
            {{ statusSyncLabel }}
          </span>
          <q-btn
            flat
            round
            dense
            icon="refresh"
            color="grey-4"
            size="sm"
            :loading="loadingPredicao"
            @click="fetchPredicaoHoje"
          >
            <q-tooltip>Atualizar Intenção e Totais</q-tooltip>
          </q-btn>
        </div>
      </div>

      <p class="text-caption text-grey-4 q-mb-md" style="font-size: 0.78rem;">
        Selecione abaixo se você utilizará o transporte hoje. O salvamento é <strong>automático e em tempo real</strong>.
      </p>

      <!-- Botões Grandes Táteis de Predição (Toggles com PATCH Automático) -->
      <div class="row q-col-gutter-sm">
        <!-- TOGGLE IDA -->
        <div class="col-6">
          <q-btn
            :color="vaiIda ? 'primary' : 'grey-9'"
            :text-color="vaiIda ? 'dark' : 'grey-4'"
            :outline="!vaiIda"
            class="full-width q-py-md btn-toggle-demand text-weight-bolder"
            no-caps
            :disable="loadingPredicao"
            :loading="savingPredicao && ultimoToggled === 'ida'"
            @click="toggleAndSave('ida')"
          >
            <div class="column items-center text-center">
              <q-icon :name="vaiIda ? 'check_circle' : 'cancel'" size="28px" class="q-mb-xs" :color="vaiIda ? 'dark' : 'grey-5'" />
              <span class="text-subtitle2 leading-tight">
                {{ vaiIda ? 'VOU NA IDA' : 'NÃO VOU NA IDA' }}
              </span>
              <span class="text-caption" style="font-size: 0.65rem;">
                {{ vaiIda ? 'Ida Confirmada' : 'Dispensado' }} (Bairro ➔ Campus)
              </span>
            </div>
          </q-btn>
        </div>

        <!-- TOGGLE VOLTA -->
        <div class="col-6">
          <q-btn
            :color="vaiVolta ? 'primary' : 'grey-9'"
            :text-color="vaiVolta ? 'dark' : 'grey-4'"
            :outline="!vaiVolta"
            class="full-width q-py-md btn-toggle-demand text-weight-bolder"
            no-caps
            :disable="loadingPredicao"
            :loading="savingPredicao && ultimoToggled === 'volta'"
            @click="toggleAndSave('volta')"
          >
            <div class="column items-center text-center">
              <q-icon :name="vaiVolta ? 'check_circle' : 'cancel'" size="28px" class="q-mb-xs" :color="vaiVolta ? 'dark' : 'grey-5'" />
              <span class="text-subtitle2 leading-tight">
                {{ vaiVolta ? 'VOLTO NO ÔNIBUS' : 'NÃO VOLTAREI' }}
              </span>
              <span class="text-caption" style="font-size: 0.65rem;">
                {{ vaiVolta ? 'Volta Confirmada' : 'Dispensado' }} (Campus ➔ Bairro)
              </span>
            </div>
          </q-btn>
        </div>
      </div>

      <!-- Resumo Coletivo dos Colegas -->
      <div class="q-mt-md q-pa-sm community-box text-center">
        <div class="text-caption text-grey-4" style="font-size: 0.74rem;">
          <q-icon name="groups" size="16px" color="primary" class="q-mr-xs" />
          Previsão coletiva hoje:
          <strong class="text-primary">{{ totalColegasIda }}</strong> confirmados na ida e
          <strong class="text-primary">{{ totalColegasVolta }}</strong> na volta.
        </div>
      </div>
    </q-card>

    <!-- 4. CARD CTA: EMBARQUE COM QR CODE (ETAPA 4.2) -->
    <q-card class="dark-card q-pa-md text-center">
      <div class="row items-center justify-center q-mb-xs">
        <q-icon name="qr_code_scanner" color="primary" size="32px" class="q-mr-xs" />
        <div class="text-subtitle1 text-weight-bolder text-white">
          Embarque Óptico
        </div>
      </div>
      <p class="text-caption text-grey-4 q-mb-md">
        Ao entrar no ônibus, aponte a câmera para o QR Code fixado junto à porta.
      </p>

      <q-btn
        color="primary"
        text-color="dark"
        class="full-width q-py-md btn-bus-primary text-weight-bolder text-subtitle1"
        icon="qr_code_2"
        label="LER QR CODE DO ÔNIBUS"
        no-caps
        to="/aluno/qrcode"
      />
    </q-card>

    <!-- 5. GESTÃO DE PERFIL E PRIVACIDADE LGPD (ETAPA 4.3) -->
    <div class="row justify-center q-my-xs">
      <q-btn
        flat
        dense
        color="grey-4"
        icon="manage_accounts"
        label="Meu Perfil & Governança LGPD"
        class="text-caption text-weight-medium"
        no-caps
        to="/aluno/perfil"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'
import api from '../boot/axios'

const $q = useQuasar()
const authStore = useAuthStore()

// Estados da Predição
const vaiIda = ref(false)
const vaiVolta = ref(false)
const temRegistro = ref(false)
const loadingPredicao = ref(false)
const savingPredicao = ref(false)
const ultimoToggled = ref(null)
const totalColegasIda = ref(0)
const totalColegasVolta = ref(0)

// Estados da Viagem Ativa do Município
const viagemAtiva = ref(null)
const loadingViagem = ref(false)

// Data local no formato YYYY-MM-DD (sem desvio de fuso horário UTC)
const getTodayIso = () => {
  const d = new Date()
  const year = d.getFullYear()
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

const statusSyncLabel = computed(() => {
  if (loadingPredicao.value) return 'Carregando...'
  if (savingPredicao.value) return 'Salvando...'
  if (temRegistro.value) return '✓ Sincronizado'
  return 'Aguardando confirmação'
})

const statusSyncClass = computed(() => {
  if (savingPredicao.value || loadingPredicao.value) return 'text-primary'
  if (temRegistro.value) return 'text-positive'
  return 'text-grey-5'
})

// Computeds da Carteirinha Digital
const matriculaDisplay = computed(() => {
  return authStore.alunoMatricula || authStore.user?.aluno?.matricula || '20269988'
})

const instituicaoDisplay = computed(() => {
  return authStore.alunoInstituicao || authStore.user?.aluno?.instituicao_nome || 'Universidade Regional Credenciada'
})

const clienteNomeDisplay = computed(() => {
  return authStore.alunoClienteNome || authStore.user?.aluno?.cliente_nome || 'Transporte Universitário Municipal'
})

const statusBadgeColor = computed(() => {
  if (authStore.isAlunoAprovado) return 'positive'
  if (authStore.isAlunoPendente) return 'warning'
  return 'negative'
})

const statusIcon = computed(() => {
  if (authStore.isAlunoAprovado) return 'verified'
  if (authStore.isAlunoPendente) return 'hourglass_empty'
  return 'block'
})

const statusLabel = computed(() => {
  if (authStore.isAlunoAprovado) return 'APROVADO'
  if (authStore.isAlunoPendente) return 'EM ANÁLISE'
  return 'REJEITADO'
})

const dataHojeFormatada = computed(() => {
  const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' }
  const hoje = new Date().toLocaleDateString('pt-BR', options)
  return hoje.charAt(0).toUpperCase() + hoje.slice(1)
})

const formatHora = (dataStr) => {
  if (!dataStr) return '--:--'
  try {
    const d = new Date(dataStr)
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch (e) {
    return '--:--'
  }
}

// Carregar Predição Existente de Hoje
const fetchPredicaoHoje = async () => {
  loadingPredicao.value = true
  const todayIso = getTodayIso()
  try {
    const response = await api.get('/operacao/predicao/', {
      params: { data: todayIso }
    })
    const data = response.data
    if (data.registrado) {
      vaiIda.value = Boolean(data.vai_ida)
      vaiVolta.value = Boolean(data.vai_volta)
      temRegistro.value = true
    } else {
      vaiIda.value = false
      vaiVolta.value = false
      temRegistro.value = false
    }
    totalColegasIda.value = data.total_colegas_ida || 0
    totalColegasVolta.value = data.total_colegas_volta || 0
  } catch (error) {
    console.error('Falha ao obter previsão do dia:', error)
    $q.notify({
      type: 'warning',
      icon: 'sync_problem',
      message: 'Não foi possível carregar a previsão de hoje. Clique no botão de atualizar.',
      position: 'bottom'
    })
  } finally {
    loadingPredicao.value = false
  }
}

// Consultar Viagem Ativa do Município
const fetchViagemAtiva = async () => {
  loadingViagem.value = true
  try {
    const response = await api.get('/operacao/viagem/ativa/')
    if (response.data.ativa) {
      viagemAtiva.value = response.data.viagem
    } else {
      viagemAtiva.value = null
    }
  } catch (error) {
    viagemAtiva.value = null
  } finally {
    loadingViagem.value = false
  }
}

// Alternar e Despachar Automaticamente via PATCH
const toggleAndSave = async (tipo) => {
  if (!authStore.isAlunoAprovado) {
    $q.notify({
      type: 'warning',
      icon: 'hourglass_empty',
      message: 'Seu cadastro precisa estar aprovado pela prefeitura para enviar previsão de viagem.'
    })
    return
  }

  ultimoToggled.value = tipo

  // Tátil: Alternar valor imediatamente na UI
  const novoValor = tipo === 'ida' ? !vaiIda.value : !vaiVolta.value
  if (tipo === 'ida') {
    vaiIda.value = novoValor
  } else if (tipo === 'volta') {
    vaiVolta.value = novoValor
  }

  // Feedback háptico se suportado pelo smartphone
  try {
    if (window.navigator?.vibrate) {
      window.navigator.vibrate(40)
    }
  } catch (e) {
    // Ignora
  }

  // Disparo automático reativo do PATCH (Etapa 4.1)
  savingPredicao.value = true
  const todayIso = getTodayIso()

  try {
    const response = await api.patch('/operacao/predicao/', {
      data: todayIso,
      vai_ida: vaiIda.value,
      vai_volta: vaiVolta.value
    })

    if (response.data) {
      temRegistro.value = true
      totalColegasIda.value = response.data.total_colegas_ida ?? totalColegasIda.value
      totalColegasVolta.value = response.data.total_colegas_volta ?? totalColegasVolta.value
    }

    const mensagemNotificacao = tipo === 'ida'
      ? (vaiIda.value ? 'Ida confirmada! Sua presença foi reservada (Bairro ➔ Campus).' : 'Ida cancelada. Vaga liberada no trajeto de ida.')
      : (vaiVolta.value ? 'Volta confirmada! Sua presença foi reservada (Campus ➔ Bairro).' : 'Volta cancelada. Vaga liberada no trajeto de volta.')

    $q.notify({
      type: 'positive',
      icon: 'cloud_done',
      message: mensagemNotificacao,
      timeout: 2000,
      position: 'bottom'
    })
  } catch (error) {
    // Em caso de erro, reverte
    if (tipo === 'ida') vaiIda.value = !vaiIda.value
    if (tipo === 'volta') vaiVolta.value = !vaiVolta.value

    $q.notify({
      type: 'negative',
      icon: 'error',
      message: error.response?.data?.erro || error.response?.data?.data?.[0] || 'Falha ao salvar previsão de viagem.',
      position: 'bottom',
      timeout: 3000
    })
  } finally {
    savingPredicao.value = false
  }
}

onMounted(async () => {
  await Promise.all([
    fetchPredicaoHoje(),
    fetchViagemAtiva()
  ])
})
</script>

<style scoped lang="scss">
.student-home-section {
  max-width: 480px;
  margin: 0 auto;
}

.student-id-card {
  background: linear-gradient(135deg, #1A2234 0%, #0F172A 100%);
  border: 1px solid rgba(242, 192, 55, 0.35);
  border-radius: 16px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.6);
}

.avatar-border {
  border: 2px solid #F2C037;
}

.border-top-subtle {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.active-trip-box {
  background: rgba(33, 186, 69, 0.08);
  border: 1px solid rgba(33, 186, 69, 0.3);
  border-radius: 12px;
}

.btn-toggle-demand {
  border-radius: 14px;
  min-height: 84px;
  transition: all 0.2s ease-in-out;
}

.community-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
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
</style>
