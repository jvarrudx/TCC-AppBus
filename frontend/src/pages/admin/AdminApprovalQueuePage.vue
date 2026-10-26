<template>
  <q-page class="q-py-md">
    <!-- Header da Fila -->
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="row items-center">
          <q-btn flat round dense icon="arrow_back" color="grey-4" class="q-mr-sm" @click="$router.push('/')" />
          <h1 class="text-h5 text-weight-bold text-white q-my-none">
            Fila de <span class="text-primary">Aprovação</span>
          </h1>
        </div>
        <p class="text-caption text-grey-5 q-mt-xs q-mb-none">
          Auditoria e deferimento de solicitações de transporte universitário
        </p>
      </div>

      <div class="row q-gutter-x-sm">
        <q-btn
          outline
          color="primary"
          icon="refresh"
          label="Atualizar"
          size="sm"
          no-caps
          :loading="loading"
          @click="fetchAlunos"
        />
      </div>
    </div>

    <!-- Barra de Filtros e Busca -->
    <q-card class="dark-card q-pa-sm q-mb-md">
      <div class="row q-col-gutter-sm items-center">
        <div class="col-12 col-sm-6">
          <q-input
            v-model="searchQuery"
            outlined
            dark
            dense
            placeholder="Buscar por nome, CPF ou matrícula..."
            color="primary"
            clearable
          >
            <template v-slot:prepend>
              <q-icon name="search" color="grey-5" />
            </template>
          </q-input>
        </div>
        <div class="col-12 col-sm-6">
          <q-btn-toggle
            v-model="statusFilter"
            spread
            no-caps
            rounded
            unelevated
            toggle-color="primary"
            toggle-text-color="dark"
            color="dark"
            text-color="grey-4"
            size="sm"
            :options="[
              { label: `Pendentes (${pendentesCount})`, value: 'PENDENTE' },
              { label: 'Aprovados', value: 'APROVADO' },
              { label: 'Rejeitados', value: 'REJEITADO' },
              { label: 'Todos', value: 'TODOS' }
            ]"
          />
        </div>
      </div>
    </q-card>

    <!-- Error State -->
    <div v-if="fetchError && !loading" class="text-center q-pa-xl dark-card rounded-borders border-danger">
      <q-icon name="error_outline" size="56px" color="negative" class="q-mb-sm" />
      <div class="text-h6 text-white text-weight-bold">Falha ao carregar fila de aprovação</div>
      <p class="text-caption text-grey-4 q-mt-xs q-mb-md">
        {{ fetchError }}
      </p>
      <q-btn
        color="primary"
        text-color="dark"
        icon="refresh"
        label="Tentar Novamente"
        class="btn-bus-primary text-weight-bold"
        no-caps
        @click="fetchAlunos"
      />
    </div>

    <!-- Estado Vazio -->
    <div v-else-if="!loading && filteredAlunos.length === 0" class="text-center q-pa-xl dark-card rounded-borders">
      <q-icon name="how_to_reg" size="64px" color="grey-7" class="q-mb-sm" />
      <div class="text-h6 text-grey-4">Nenhum aluno encontrado</div>
      <p class="text-caption text-grey-5">
        {{ statusFilter === 'PENDENTE' ? 'A fila de aprovação de novos cadastros está vazia!' : 'Nenhum registro com os filtros aplicados.' }}
      </p>
    </div>

    <!-- Loader com Skeleton / Spinner -->
    <div v-else-if="loading" class="text-center q-pa-xl">
      <q-spinner-dots color="primary" size="52px" />
      <div class="text-caption text-grey-4 q-mt-sm">Carregando solicitações de alunos com segurança multi-tenant...</div>
    </div>

    <!-- Lista de Cards de Alunos -->
    <div v-else class="q-gutter-y-sm">
      <q-card
        v-for="aluno in filteredAlunos"
        :key="aluno.id"
        class="dark-card student-card q-pa-md"
        :class="{ 'border-pending': aluno.status_aprovacao === 'PENDENTE' }"
      >
        <div class="row items-start justify-between">
          <!-- Identificação do Aluno -->
          <div class="col-12 col-md-8">
            <div class="row items-center q-gutter-x-sm q-mb-xs">
              <span class="text-subtitle1 text-weight-bold text-white">{{ aluno.nome }}</span>
              <q-badge :color="getStatusColor(aluno.status_aprovacao)" text-color="dark" class="text-weight-bold">
                {{ aluno.status_aprovacao_display || aluno.status_aprovacao }}
              </q-badge>
            </div>

            <div class="row q-col-gutter-x-md text-caption text-grey-4 q-mt-xs">
              <div>
                <q-icon name="badge" size="14px" class="q-mr-xs text-grey-5" />
                <span>CPF: {{ aluno.cpf || 'Não informado' }}</span>
              </div>
              <div>
                <q-icon name="school" size="14px" class="q-mr-xs text-grey-5" />
                <span>{{ aluno.instituicao_nome }} ({{ aluno.matricula }})</span>
              </div>
              <div>
                <q-icon name="email" size="14px" class="q-mr-xs text-grey-5" />
                <span>{{ aluno.email }}</span>
              </div>
            </div>

            <div class="text-caption text-grey-6 q-mt-xs">
              Solicitado em: {{ formatDateTime(aluno.data_solicitacao) }}
              <span v-if="aluno.avaliado_por_nome"> • Avaliado por: {{ aluno.avaliado_por_nome }}</span>
            </div>
          </div>

          <!-- Ações Rápidas de Aprovação/Rejeição -->
          <div class="col-12 col-md-4 row justify-end items-center q-gutter-x-sm q-mt-sm q-mt-md-none">
            <q-btn
              flat
              dense
              round
              icon="visibility"
              color="grey-4"
              @click="verDetalhes(aluno)"
            >
              <q-tooltip>Ver Detalhes do Aluno</q-tooltip>
            </q-btn>

            <template v-if="aluno.status_aprovacao === 'PENDENTE'">
              <q-btn
                outline
                color="negative"
                label="Rejeitar"
                icon="close"
                size="sm"
                no-caps
                :loading="actionLoadingId === aluno.id"
                @click="confirmarRejeicao(aluno)"
              />
              <q-btn
                unelevated
                color="primary"
                text-color="dark"
                label="Aprovar"
                icon="check"
                size="sm"
                class="btn-bus-primary text-weight-bold"
                no-caps
                :loading="actionLoadingId === aluno.id"
                @click="confirmarAprovacao(aluno)"
              />
            </template>
          </div>
        </div>
      </q-card>
    </div>

    <!-- Modal de Detalhes Completos do Aluno (LGPD Audit) -->
    <q-dialog v-model="showDetailModal">
      <q-card class="dark-card" style="min-width: 360px; max-width: 580px;">
        <q-card-section class="row items-center q-pb-none">
          <q-avatar size="38px" color="primary" text-color="dark" class="q-mr-sm">
            <q-icon name="school" size="22px" />
          </q-avatar>
          <div>
            <div class="text-h6 text-white text-weight-bold">{{ selectedAluno?.nome }}</div>
            <div class="text-caption text-grey-5">Matrícula: {{ selectedAluno?.matricula }}</div>
          </div>
          <q-space />
          <q-btn icon="close" flat round dense color="grey-5" v-close-popup />
        </q-card-section>

        <q-separator dark class="q-my-sm" />

        <q-card-section class="q-pt-xs text-body2 text-grey-3">
          <div class="q-gutter-y-sm">
            <div class="row">
              <span class="col-4 text-grey-5">E-mail:</span>
              <span class="col-8 text-white text-weight-medium">{{ selectedAluno?.email }}</span>
            </div>
            <div class="row">
              <span class="col-4 text-grey-5">CPF:</span>
              <span class="col-8 text-white">{{ selectedAluno?.cpf }}</span>
            </div>
            <div class="row">
              <span class="col-4 text-grey-5">Instituição:</span>
              <span class="col-8 text-white">{{ selectedAluno?.instituicao_nome }}</span>
            </div>
            <div class="row">
              <span class="col-4 text-grey-5">Status Cadastral:</span>
              <div class="col-8">
                <q-badge :color="getStatusColor(selectedAluno?.status_aprovacao)" text-color="dark">
                  {{ selectedAluno?.status_aprovacao_display || selectedAluno?.status_aprovacao }}
                </q-badge>
              </div>
            </div>
            <div class="row">
              <span class="col-4 text-grey-5">Data da Adesão:</span>
              <span class="col-8 text-grey-4">{{ formatDateTime(selectedAluno?.data_solicitacao) }}</span>
            </div>
          </div>
        </q-card-section>

        <q-separator dark />

        <q-card-actions align="right" class="q-pa-md">
          <q-btn flat label="Fechar" color="grey-5" v-close-popup />
          <template v-if="selectedAluno?.status_aprovacao === 'PENDENTE'">
            <q-btn
              outline
              color="negative"
              label="Rejeitar Solicitação"
              no-caps
              @click="confirmarRejeicao(selectedAluno)"
            />
            <q-btn
              color="primary"
              text-color="dark"
              label="Aprovar Aluno"
              no-caps
              class="btn-bus-primary"
              @click="confirmarAprovacao(selectedAluno)"
            />
          </template>
        </q-card-actions>
      </q-card>
    </q-dialog>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import api from '../../boot/axios'

const $q = useQuasar()

const loading = ref(false)
const fetchError = ref(null)
const actionLoadingId = ref(null)
const alunos = ref([])
const searchQuery = ref('')
const statusFilter = ref('PENDENTE')

const showDetailModal = ref(false)
const selectedAluno = ref(null)

const pendentesCount = computed(() => {
  return alunos.value.filter(a => a.status_aprovacao === 'PENDENTE').length
})

const filteredAlunos = computed(() => {
  return alunos.value.filter(aluno => {
    // Filtro por status
    if (statusFilter.value !== 'TODOS' && aluno.status_aprovacao !== statusFilter.value) {
      return false
    }

    // Busca textual
    if (searchQuery.value && searchQuery.value.trim() !== '') {
      const q = searchQuery.value.toLowerCase().trim()
      const matchNome = (aluno.nome || '').toLowerCase().includes(q)
      const matchCpf = (aluno.cpf || '').includes(q)
      const matchMatricula = (aluno.matricula || '').toLowerCase().includes(q)
      const matchInst = (aluno.instituicao_nome || '').toLowerCase().includes(q)
      return matchNome || matchCpf || matchMatricula || matchInst
    }

    return true
  })
})

const fetchAlunos = async () => {
  loading.value = true
  fetchError.value = null
  try {
    const res = await api.get('/alunos/')
    alunos.value = res.data?.results || res.data || []
  } catch (error) {
    const errorMsg = error.response?.data?.detail ||
                     error.response?.data?.erro ||
                     'Não foi possível consultar a fila de alunos no momento. Verifique sua conexão com o servidor.'
    fetchError.value = errorMsg
    $q.notify({
      type: 'negative',
      icon: 'cloud_off',
      message: 'Falha ao sincronizar fila de alunos da prefeitura.',
      timeout: 3500
    })
  } finally {
    loading.value = false
  }
}

const getStatusColor = (status) => {
  switch (status) {
    case 'APROVADO':
      return 'positive'
    case 'REJEITADO':
      return 'negative'
    case 'PENDENTE':
    default:
      return 'primary'
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dateStr
  }
}

const verDetalhes = (aluno) => {
  selectedAluno.value = aluno
  showDetailModal.value = true
}

const confirmarAprovacao = (aluno) => {
  $q.dialog({
    title: 'Aprovar Solicitação de Transporte',
    message: `Confirma a concessão do benefício de transporte universitário para ${aluno.nome}?`,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-5' },
    ok: { label: 'Confirmar Aprovação', color: 'primary', textColor: 'dark' },
    dark: true,
    persistent: true
  }).onOk(async () => {
    actionLoadingId.value = aluno.id
    try {
      await api.post(`/alunos/${aluno.id}/aprovar/`)
      $q.notify({
        type: 'positive',
        icon: 'check_circle',
        message: `Aluno ${aluno.nome} aprovado com sucesso!`
      })
      showDetailModal.value = false
      await fetchAlunos()
    } catch (err) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: err.response?.data?.detail || 'Erro ao processar aprovação.'
      })
    } finally {
      actionLoadingId.value = null
    }
  })
}

const confirmarRejeicao = (aluno) => {
  $q.dialog({
    title: 'Rejeitar Solicitação',
    message: `Tem certeza que deseja indeferir o pedido de transporte de ${aluno.nome}?`,
    cancel: { label: 'Voltar', flat: true, color: 'grey-5' },
    ok: { label: 'Confirmar Rejeição', color: 'negative' },
    dark: true,
    persistent: true
  }).onOk(async () => {
    actionLoadingId.value = aluno.id
    try {
      await api.post(`/alunos/${aluno.id}/rejeitar/`)
      $q.notify({
        type: 'warning',
        icon: 'block',
        message: `Solicitação de ${aluno.nome} rejeitada.`
      })
      showDetailModal.value = false
      await fetchAlunos()
    } catch (err) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: err.response?.data?.detail || 'Erro ao rejeitar aluno.'
      })
    } finally {
      actionLoadingId.value = null
    }
  })
}

onMounted(() => {
  fetchAlunos()
})
</script>

<style scoped lang="scss">
.student-card {
  transition: transform 0.2s ease, border-color 0.2s ease;
  border-left: 4px solid rgba(255, 255, 255, 0.1);

  &.border-pending {
    border-left-color: #F2C037;
  }

  &:hover {
    transform: translateY(-2px);
  }
}

.border-danger {
  border: 1px solid rgba(193, 0, 21, 0.4);
}
</style>
