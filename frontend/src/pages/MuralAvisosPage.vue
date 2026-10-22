<template>
  <div class="mural-avisos-page q-gutter-y-md">
    <!-- BARRA SUPERIOR DE NAVEGAÇÃO -->
    <div class="row items-center justify-between q-mb-xs">
      <q-btn
        flat
        round
        dense
        icon="arrow_back"
        color="grey-4"
        to="/"
      >
        <q-tooltip>Voltar ao Início</q-tooltip>
      </q-btn>

      <div class="text-subtitle1 text-weight-bolder text-white flex items-center">
        <q-icon name="campaign" color="primary" size="26px" class="q-mr-xs" />
        Mural de Avisos
      </div>

      <div class="row items-center q-gutter-x-xs">
        <q-btn
          flat
          round
          dense
          icon="refresh"
          color="grey-4"
          :loading="loadingAvisos"
          @click="carregarAvisos"
        >
          <q-tooltip>Atualizar Comunicados</q-tooltip>
        </q-btn>

        <!-- BOTÃO DE DISPARO RÁPIDO NO TOPO (MOTORISTA / GESTOR) -->
        <q-btn
          v-if="podePublicar"
          color="primary"
          text-color="dark"
          dense
          no-caps
          icon="add"
          label="Novo"
          class="q-px-sm text-weight-bold"
          @click="abrirDialogNovoAviso"
        >
          <q-tooltip>Publicar Novo Comunicado</q-tooltip>
        </q-btn>
      </div>
    </div>

    <!-- 1. BARRA DE FILTROS RÁPIDOS POR TIPO -->
    <q-card class="dark-card q-pa-sm">
      <div class="row items-center justify-between q-col-gutter-xs">
        <div class="col-12 col-sm-7">
          <q-tabs
            v-model="filtroTipo"
            dense
            no-caps
            active-color="primary"
            indicator-color="primary"
            class="text-grey-4"
            shrink
            @update:model-value="carregarAvisos"
          >
            <q-tab name="TODOS" label="Todos" icon="forum" />
            <q-tab name="URGENTE" label="Urgentes" icon="warning" class="text-negative" />
            <q-tab name="ATRASO" label="Atrasos" icon="schedule" class="text-warning" />
            <q-tab name="MANUTENCAO" label="Manutenção" icon="build" />
            <q-tab name="GERAL" label="Gerais" icon="info" />
          </q-tabs>
        </div>

        <!-- FILTRO POR ROTA ESPECÍFICA -->
        <div class="col-12 col-sm-5">
          <q-select
            v-model="filtroRota"
            :options="opcoesRotas"
            dense
            outlined
            dark
            emit-value
            map-options
            options-dense
            label="Filtrar por Rota"
            class="text-caption"
            @update:model-value="carregarAvisos"
          >
            <template v-slot:prepend>
              <q-icon name="alt_route" size="18px" color="primary" />
            </template>
          </q-select>
        </div>
      </div>
    </q-card>

    <!-- 2. FEED DE COMUNICADOS -->
    <div v-if="loadingAvisos" class="text-center q-pa-xl">
      <q-spinner-dots color="primary" size="40px" />
      <div class="text-caption text-grey-5 q-mt-sm">Carregando comunicados do município...</div>
    </div>

    <div v-else-if="avisos.length === 0" class="text-center q-pa-xl">
      <q-card class="dark-card q-pa-lg">
        <q-icon name="check_circle_outline" color="positive" size="56px" class="q-mb-sm" />
        <div class="text-h6 text-weight-bold text-white">Nenhum Comunicado Ativo</div>
        <p class="text-caption text-grey-4 q-mt-xs q-mb-none">
          Não há avisos ou imprevistos pendentes para os filtros selecionados. A operação do transporte segue normalmente!
        </p>
      </q-card>
    </div>

    <div v-else class="q-gutter-y-sm">
      <q-card
        v-for="aviso in avisos"
        :key="aviso.id"
        class="dark-card aviso-card q-pa-md"
        :class="`tipo-border-${aviso.tipo.toLowerCase()}`"
      >
        <!-- CABEÇALHO DO COMUNICADO: AUTOR + HORÁRIO + TIPO -->
        <div class="row items-center justify-between q-mb-xs">
          <div class="row items-center q-gutter-x-sm">
            <q-avatar
              size="36px"
              :color="getAvatarBgColor(aviso.autor_papel)"
              :text-color="aviso.autor_papel === 'Motorista' ? 'dark' : 'white'"
            >
              <q-icon :name="getAvatarIcon(aviso.autor_papel)" size="20px" />
            </q-avatar>

            <div>
              <div class="text-subtitle2 text-weight-bolder text-white leading-tight">
                {{ aviso.autor_nome }}
              </div>
              <div class="row items-center q-gutter-x-xs text-caption text-grey-5" style="font-size: 0.72rem;">
                <q-badge
                  dense
                  :color="aviso.autor_papel === 'Motorista' ? 'primary' : 'secondary'"
                  :text-color="aviso.autor_papel === 'Motorista' ? 'dark' : 'white'"
                  class="text-weight-bold"
                >
                  {{ aviso.autor_papel }}
                </q-badge>

                <span v-if="aviso.rota_nome" class="text-grey-4">
                  • Linha: <strong class="text-white">{{ aviso.rota_nome }}</strong>
                </span>
                <span v-else class="text-grey-4">• Geral (Todas as Linhas)</span>
              </div>
            </div>
          </div>

          <div class="column items-end">
            <q-badge
              :color="getTipoBadgeColor(aviso.tipo)"
              :text-color="aviso.tipo === 'ATRASO' || aviso.tipo === 'GERAL' ? 'dark' : 'white'"
              class="text-weight-bolder q-px-sm q-py-xs"
            >
              <q-icon :name="getTipoIcon(aviso.tipo)" size="13px" class="q-mr-xs" />
              {{ aviso.tipo_display || aviso.tipo }}
            </q-badge>

            <span class="text-caption text-grey-5 q-mt-xs" style="font-size: 0.70rem;">
              {{ formatDataHora(aviso.criado_em) }}
            </span>
          </div>
        </div>

        <q-separator dark class="q-my-sm border-subtle" />

        <!-- CONTEÚDO DO COMUNICADO -->
        <div class="text-subtitle1 text-weight-bold text-white q-mb-xs">
          {{ aviso.titulo }}
        </div>
        <div class="text-body2 text-grey-3 message-content leading-relaxed">
          {{ aviso.mensagem }}
        </div>

        <!-- AÇÕES DO AUTOR OU GESTOR (INATIVAR / EXCLUIR) -->
        <div v-if="podeGerenciarAviso(aviso)" class="row justify-end q-mt-sm">
          <q-btn
            flat
            dense
            color="grey-5"
            size="sm"
            icon="delete_outline"
            label="Inativar Comunicado"
            no-caps
            :loading="inativandoId === aviso.id"
            @click="confirmarInativacao(aviso)"
          >
            <q-tooltip>Encerrar ou inativar este aviso do mural</q-tooltip>
          </q-btn>
        </div>
      </q-card>
    </div>

    <!-- 3. DIALOG DE DISPARO DE NOVO COMUNICADO (MOTORISTA / GESTOR) -->
    <q-dialog v-model="dialogNovoAviso" persistent maximized-mobile>
      <q-card class="dark-card dialog-aviso-card q-pa-md" style="min-width: 340px; max-width: 500px; width: 100%;">
        <div class="row items-center justify-between q-mb-sm">
          <div class="text-subtitle1 text-weight-bolder text-white flex items-center">
            <q-icon name="add_alert" color="primary" size="24px" class="q-mr-xs" />
            Novo Comunicado
          </div>
          <q-btn flat round dense icon="close" color="grey-4" v-close-popup />
        </div>

        <p class="text-caption text-grey-4 q-mb-md">
          Este aviso será enviado instantaneamente para os alunos e operadores do seu município.
        </p>

        <!-- RESPOSTAS RÁPIDAS (QUICK REPLIES) PARA MOTORISTAS EM TRÂNSITO -->
        <div v-if="authStore.isMotorista" class="q-mb-md">
          <div class="text-caption text-weight-bold text-primary q-mb-xs">
            ⚡ Respostas Rápidas (Toque para preencher):
          </div>
          <div class="row q-gutter-xs">
            <q-btn
              v-for="(qr, idx) in quickRepliesMotorista"
              :key="idx"
              outline
              dense
              no-caps
              size="sm"
              color="primary"
              :label="qr.label"
              class="q-px-xs"
              @click="aplicarQuickReply(qr)"
            />
          </div>
        </div>

        <q-form @submit.prevent="salvarNovoAviso" class="q-gutter-y-sm">
          <!-- TÍTULO -->
          <q-input
            v-model="formAviso.titulo"
            label="Título do Comunicado *"
            outlined
            dark
            dense
            counter
            maxlength="150"
            :rules="[val => !!val && val.trim().length >= 3 || 'Informe um título claro (mínimo 3 caracteres).']"
          >
            <template v-slot:prepend>
              <q-icon name="title" size="18px" color="primary" />
            </template>
          </q-input>

          <!-- TIPO DE COMUNICADO -->
          <div class="text-caption text-grey-4 text-weight-medium q-mb-xs">
            Classificação do Aviso:
          </div>
          <div class="row q-col-gutter-xs q-mb-xs">
            <div
              v-for="tipoOpt in tiposAvisoOpcoes"
              :key="tipoOpt.value"
              class="col-6"
            >
              <q-card
                v-ripple
                class="q-pa-xs cursor-pointer text-center rounded-borders transition-fast"
                :class="formAviso.tipo === tipoOpt.value ? 'selected-tipo-card' : 'unselected-tipo-card'"
                @click="formAviso.tipo = tipoOpt.value"
              >
                <div class="row items-center justify-center q-gutter-x-xs">
                  <q-icon :name="tipoOpt.icon" size="16px" :color="tipoOpt.color" />
                  <span class="text-caption text-weight-bold" :class="`text-${tipoOpt.color}`">
                    {{ tipoOpt.label }}
                  </span>
                </div>
              </q-card>
            </div>
          </div>

          <!-- ROTA ESPECÍFICA (OPCIONAL) -->
          <q-select
            v-model="formAviso.rota"
            :options="opcoesRotasForm"
            label="Rota / Linha Específica"
            outlined
            dark
            dense
            emit-value
            map-options
            options-dense
            hint="Deixe em 'Todas as Linhas' para emitir um aviso geral do município"
            class="text-caption"
          >
            <template v-slot:prepend>
              <q-icon name="directions_bus" size="18px" color="primary" />
            </template>
          </q-select>

          <!-- MENSAGEM LIVRE -->
          <q-input
            v-model="formAviso.mensagem"
            label="Mensagem Completa *"
            outlined
            dark
            dense
            type="textarea"
            rows="3"
            counter
            maxlength="1000"
            :rules="[val => !!val && val.trim().length >= 5 || 'Descreva a mensagem do aviso (mínimo 5 caracteres).']"
          />

          <!-- BOTÕES DE SUBMIT -->
          <div class="row justify-end q-gutter-x-sm q-mt-md">
            <q-btn flat color="grey-4" label="Cancelar" v-close-popup no-caps />
            <q-btn
              type="submit"
              color="primary"
              text-color="dark"
              label="Disparar Comunicado"
              icon="send"
              no-caps
              class="text-weight-bold"
              :loading="salvandoAviso"
            />
          </div>
        </q-form>
      </q-card>
    </q-dialog>

    <!-- 4. FLOATING ACTION BUTTON (FAB) PARA ENVIO RÁPIDO -->
    <q-page-sticky v-if="podePublicar" position="bottom-right" :offset="[18, 18]">
      <q-btn
        fab
        icon="campaign"
        color="primary"
        text-color="dark"
        class="shadow-5 animate-pulse-gentle"
        @click="abrirDialogNovoAviso"
      >
        <q-tooltip>Publicar Comunicado</q-tooltip>
      </q-btn>
    </q-page-sticky>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../stores/authStore'
import { avisosService } from '../services/api'

const $q = useQuasar()
const authStore = useAuthStore()

// Estados da Lista de Avisos
const avisos = ref([])
const loadingAvisos = ref(false)
const inativandoId = ref(null)

// Filtros
const filtroTipo = ref('TODOS')
const filtroRota = ref(null)
const rotas = ref([])

// Estado do Modal de Criação
const dialogNovoAviso = ref(false)
const salvandoAviso = ref(false)
const formAviso = ref({
  titulo: '',
  mensagem: '',
  tipo: 'GERAL',
  rota: null
})

// Opções de Tipos de Comunicado
const tiposAvisoOpcoes = [
  { value: 'GERAL', label: 'Geral', icon: 'campaign', color: 'primary' },
  { value: 'ATRASO', label: 'Atraso', icon: 'schedule', color: 'warning' },
  { value: 'MANUTENCAO', label: 'Manutenção', icon: 'build', color: 'info' },
  { value: 'URGENTE', label: 'Urgente', icon: 'warning', color: 'negative' }
]

// Respostas Rápidas para Motoristas em trânsito
const quickRepliesMotorista = [
  {
    label: '⏱️ Atraso 10m',
    titulo: 'Atraso Previsto: 10 Minutos',
    mensagem: 'Atenção alunos: Devido ao fluxo intenso de trânsito, o ônibus está com previsão de 10 minutos de atraso.',
    tipo: 'ATRASO'
  },
  {
    label: '⏱️ Atraso 20m',
    titulo: 'Atraso Previsto: 20 Minutos',
    mensagem: 'Atenção alunos: Devido a lentidão na rodovia, nossa previsão de chegada ao ponto possui atraso estimado de 20 minutos.',
    tipo: 'ATRASO'
  },
  {
    label: '🟢 Embarque Liberado',
    titulo: 'Embarque Liberado no Ponto',
    mensagem: 'O ônibus já se encontra estacionado no ponto de embarque. Podem se dirigir ao veículo com o QR Code pronto.',
    tipo: 'GERAL'
  },
  {
    label: '🚌 Veículo Reserva',
    titulo: 'Veículo Reserva em Operação',
    mensagem: 'Informamos que a linha de hoje está sendo operada por veículo reserva. Fiquem atentos à identificação na dianteira.',
    tipo: 'MANUTENCAO'
  },
  {
    label: '⚠️ Trânsito Intenso',
    titulo: 'Alerta de Trânsito no Trajeto',
    mensagem: 'Trânsito muito pesado no trajeto principal. Estamos trafegando com cautela.',
    tipo: 'URGENTE'
  }
]

// Permissões
const podePublicar = computed(() => {
  return authStore.isMotorista || authStore.isGestor
})

const podeGerenciarAviso = (aviso) => {
  if (authStore.isGestor) return true
  if (authStore.isMotorista && aviso.autor === authStore.user?.id) return true
  return false
}

// Opções para o filtro de Rotas
const opcoesRotas = computed(() => {
  const lista = [{ label: 'Todas as Rotas', value: null }]
  rotas.value.forEach(r => {
    lista.push({ label: r.nome, value: r.id })
  })
  return lista
})

// Opções para o formulário de Rotas
const opcoesRotasForm = computed(() => {
  const lista = [{ label: 'Todas as Linhas (Aviso Geral)', value: null }]
  rotas.value.forEach(r => {
    lista.push({ label: r.nome, value: r.id })
  })
  return lista
})

// Carregar Rotas do Município
const carregarRotas = async () => {
  try {
    const response = await avisosService.getRotas()
    rotas.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('Falha ao carregar rotas:', error)
  }
}

// Carregar Comunicados Ativos com Filtros
const carregarAvisos = async () => {
  loadingAvisos.value = true
  try {
    const params = {}
    if (filtroTipo.value && filtroTipo.value !== 'TODOS') {
      params.tipo = filtroTipo.value
    }
    if (filtroRota.value) {
      params.rota = filtroRota.value
    }

    const response = await avisosService.getAvisos(params)
    avisos.value = response.data?.results || response.data || []
  } catch (error) {
    console.error('Falha ao obter mural de avisos:', error)
    $q.notify({
      type: 'warning',
      icon: 'sync_problem',
      message: 'Não foi possível carregar os avisos do município.',
      position: 'bottom'
    })
  } finally {
    loadingAvisos.value = false
  }
}

// Abrir Dialog de Novo Aviso
const abrirDialogNovoAviso = () => {
  formAviso.value = {
    titulo: '',
    mensagem: '',
    tipo: authStore.isMotorista ? 'ATRASO' : 'GERAL',
    rota: filtroRota.value || null
  }
  dialogNovoAviso.value = true
}

// Aplicar Resposta Rápida (Quick Reply)
const aplicarQuickReply = (qr) => {
  formAviso.value.titulo = qr.titulo
  formAviso.value.mensagem = qr.mensagem
  formAviso.value.tipo = qr.tipo
}

// Salvar Novo Comunicado via POST
const salvarNovoAviso = async () => {
  salvandoAviso.value = true
  try {
    const payload = {
      titulo: formAviso.value.titulo.trim(),
      mensagem: formAviso.value.mensagem.trim(),
      tipo: formAviso.value.tipo,
      rota: formAviso.value.rota || null
    }

    await avisosService.createAviso(payload)

    $q.notify({
      type: 'positive',
      icon: 'campaign',
      message: 'Comunicado publicado com sucesso no mural!',
      position: 'bottom'
    })

    dialogNovoAviso.value = false
    await carregarAvisos()
  } catch (error) {
    console.error('Erro ao salvar comunicado:', error)
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: error.response?.data?.erro || 'Falha ao publicar comunicado. Verifique os dados.',
      position: 'bottom'
    })
  } finally {
    salvandoAviso.value = false
  }
}

// Confirmar e Executar Inativação via DELETE (Soft-Delete)
const confirmarInativacao = (aviso) => {
  $q.dialog({
    title: 'Inativar Comunicado',
    message: `Deseja realmente retirar o comunicado "${aviso.titulo}" do mural?`,
    cancel: {
      flat: true,
      label: 'Cancelar',
      color: 'grey-4'
    },
    ok: {
      color: 'negative',
      label: 'Sim, Inativar',
      noCaps: true
    },
    dark: true
  }).onOk(async () => {
    inativandoId.value = aviso.id
    try {
      await avisosService.inativarAviso(aviso.id)
      $q.notify({
        type: 'positive',
        icon: 'check',
        message: 'Aviso inativado do mural.',
        position: 'bottom'
      })
      await carregarAvisos()
    } catch (error) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: 'Não foi possível inativar o aviso.',
        position: 'bottom'
      })
    } finally {
      inativandoId.value = null
    }
  })
}

// Formatação e Helpers Visuais
const getAvatarIcon = (papel) => {
  if (papel === 'Motorista') return 'local_shipping'
  if (papel === 'Administrador') return 'admin_panel_settings'
  return 'campaign'
}

const getAvatarBgColor = (papel) => {
  if (papel === 'Motorista') return 'primary'
  if (papel === 'Administrador') return 'secondary'
  return 'grey-8'
}

const getTipoBadgeColor = (tipo) => {
  switch (tipo) {
    case 'URGENTE': return 'negative'
    case 'ATRASO': return 'warning'
    case 'MANUTENCAO': return 'info'
    default: return 'primary'
  }
}

const getTipoIcon = (tipo) => {
  switch (tipo) {
    case 'URGENTE': return 'warning'
    case 'ATRASO': return 'schedule'
    case 'MANUTENCAO': return 'build'
    default: return 'campaign'
  }
}

const formatDataHora = (dataStr) => {
  if (!dataStr) return '--:--'
  try {
    const d = new Date(dataStr)
    const options = {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    }
    return d.toLocaleString('pt-BR', options)
  } catch (e) {
    return '--:--'
  }
}

onMounted(async () => {
  await Promise.all([
    carregarRotas(),
    carregarAvisos()
  ])
})
</script>

<style scoped lang="scss">
.mural-avisos-page {
  max-width: 600px;
  margin: 0 auto;
}

.aviso-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  border-left: 4px solid transparent;

  &:hover {
    transform: translateY(-1px);
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.4);
  }
}

.tipo-border-urgente {
  border-left: 5px solid #C10015 !important;
}

.tipo-border-atraso {
  border-left: 5px solid #F2C037 !important;
}

.tipo-border-manutencao {
  border-left: 5px solid #31CCEC !important;
}

.tipo-border-geral {
  border-left: 5px solid #21BA45 !important;
}

.border-subtle {
  border-color: rgba(255, 255, 255, 0.08);
}

.message-content {
  white-space: pre-wrap;
  word-break: break-word;
}

.selected-tipo-card {
  background: rgba(242, 192, 55, 0.15);
  border: 1px solid #F2C037;
}

.unselected-tipo-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);

  &:hover {
    background: rgba(255, 255, 255, 0.06);
  }
}

.transition-fast {
  transition: all 0.15s ease-in-out;
}

.animate-pulse-gentle {
  animation: pulseGentle 3s infinite;
}

@keyframes pulseGentle {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(242, 192, 55, 0.4);
  }
  50% {
    box-shadow: 0 0 0 8px rgba(242, 192, 55, 0);
  }
}
</style>
