<template>
  <div class="student-profile-page q-gutter-y-md">
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
        <q-icon name="manage_accounts" color="primary" size="24px" class="q-mr-xs" />
        Perfil & Privacidade
      </div>

      <q-btn
        flat
        round
        dense
        icon="refresh"
        color="grey-4"
        :loading="loadingPerfil"
        @click="carregarPerfil"
      >
        <q-tooltip>Atualizar Dados</q-tooltip>
      </q-btn>
    </div>

    <!-- 1. CARTÃO DE IDENTIDADE E STATUS ACADÊMICO -->
    <q-card class="dark-card q-pa-md">
      <div class="row items-center q-gutter-x-md">
        <q-avatar size="64px" color="grey-9" text-color="primary" class="avatar-border">
          <q-icon name="account_circle" size="48px" />
        </q-avatar>

        <div class="col">
          <div class="text-h6 text-weight-bolder text-white leading-tight">
            {{ perfil?.nome || authStore.userNome }}
          </div>
          <div class="text-caption text-grey-4">
            {{ perfil?.email || authStore.user?.email }}
          </div>

          <div class="row items-center q-gutter-x-xs q-mt-xs">
            <q-badge
              :color="statusBadgeColor"
              :text-color="isAprovado ? 'white' : 'dark'"
              class="text-weight-bold"
            >
              <q-icon :name="statusIcon" size="13px" class="q-mr-xs" />
              {{ statusLabel }}
            </q-badge>

            <q-badge color="grey-8" text-color="grey-3">
              Matrícula: {{ perfil?.aluno?.matricula || authStore.alunoMatricula }}
            </q-badge>
          </div>
        </div>
      </div>
    </q-card>

    <!-- 2. DADOS CADASTRAIS TRANSPARENTES (LGPD ART. 18, II) -->
    <q-card class="dark-card q-pa-md">
      <div class="text-subtitle1 text-weight-bold text-white flex items-center q-mb-sm">
        <q-icon name="badge" color="primary" size="22px" class="q-mr-xs" />
        Dados Cadastrais do Titular
      </div>

      <div class="q-gutter-y-sm text-body2">
        <div class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">Nome Completo:</span>
          <strong class="text-white">{{ perfil?.nome || authStore.userNome }}</strong>
        </div>

        <div class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">CPF (Mascarado):</span>
          <span class="text-primary text-weight-medium">{{ perfil?.cpf_mascarado || '***.***.***-**' }}</span>
        </div>

        <div class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">Data de Nascimento:</span>
          <span class="text-grey-3">{{ formatData(perfil?.data_nascimento) }}</span>
        </div>

        <div class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">Instituição de Ensino:</span>
          <span class="text-grey-3">
            {{ perfil?.aluno?.instituicao_nome || authStore.alunoInstituicao }}
            <span v-if="perfil?.aluno?.instituicao_sigla" class="text-primary text-weight-bold">
              ({{ perfil?.aluno?.instituicao_sigla }})
            </span>
          </span>
        </div>

        <div class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">Prefeitura / Município:</span>
          <span class="text-grey-3">{{ perfil?.aluno?.cliente_nome || authStore.alunoClienteNome }}</span>
        </div>

        <div v-if="perfil?.endereco" class="row justify-between py-xs border-subtle">
          <span class="text-grey-5">Endereço Residencial:</span>
          <span class="text-grey-3 text-right">
            {{ perfil.endereco.logradouro }}, {{ perfil.endereco.numero }} - {{ perfil.endereco.bairro }}/{{ perfil.endereco.cidade }}
          </span>
        </div>
      </div>
    </q-card>

    <!-- 3. GOVERNANÇA, CONSENTIMENTO & BASE LEGAL (LGPD) -->
    <q-card class="dark-card q-pa-md">
      <div class="text-subtitle1 text-weight-bold text-white flex items-center q-mb-sm">
        <q-icon name="verified_user" color="primary" size="22px" class="q-mr-xs" />
        Consentimento e Privacidade (LGPD)
      </div>

      <p class="text-caption text-grey-4 q-mb-sm">
        O tratamento dos seus dados é fundamentado na <strong>Execução de Políticas Públicas</strong> (Art. 7º, V da LGPD)
        para gestão de frotas e segurança do transporte universitário gratuito.
      </p>

      <div class="q-pa-sm consent-box rounded-borders q-mb-sm text-caption text-grey-3">
        <div class="row justify-between q-mb-xs">
          <span class="text-grey-5">Termos de Uso e Adesão:</span>
          <strong class="text-primary">Versão {{ perfil?.aluno?.consentimento?.documento_versao || '1.0' }} (Aceito)</strong>
        </div>
        <div class="row justify-between q-mb-xs">
          <span class="text-grey-5">Data do Consentimento:</span>
          <span>{{ formatDataHora(perfil?.aluno?.consentimento?.data_consentimento) }}</span>
        </div>
        <div v-if="perfil?.aluno?.consentimento?.ip_origem" class="row justify-between">
          <span class="text-grey-5">Endereço IP Registrado:</span>
          <span class="text-grey-4">{{ perfil?.aluno?.consentimento?.ip_origem }}</span>
        </div>
      </div>
    </q-card>

    <!-- 4. DIREITO AO ESQUECIMENTO & REVOGAÇÃO DE CONTA (LGPD ART. 18, VI) -->
    <q-card class="dark-card q-pa-md border-danger">
      <div class="row items-center q-mb-xs text-negative">
        <q-icon name="shield" size="24px" class="q-mr-xs" />
        <span class="text-subtitle1 text-weight-bolder">Gerenciar Privacidade da Conta</span>
      </div>

      <p class="text-caption text-grey-4 q-mb-md">
        Conforme o Art. 18 da Lei Geral de Proteção de Dados, você tem o direito de revogar seu consentimento e solicitar a
        <strong>eliminação irreversível dos seus dados pessoais</strong> (No Hard Deletes).
      </p>

      <q-banner rounded dense class="bg-dark-page text-grey-4 text-caption q-pa-sm q-mb-md border-subtle">
        <template v-slot:avatar>
          <q-icon name="info" color="warning" />
        </template>
        A anonimização desvinculará seu nome, CPF, data de nascimento e e-mail permanentemente, revogando o passe estudantil.
        Registros operacionais de viagens serão mantidos de forma anônima para comprovação fiscal.
      </q-banner>

      <q-btn
        outline
        color="negative"
        class="full-width q-py-sm text-weight-bold"
        icon="delete_forever"
        label="Revogar Consentimento e Excluir Minha Conta"
        no-caps
        @click="abrirModalExclusao"
      />
    </q-card>

    <!-- MODAL DE CONFIRMAÇÃO CRÍTICA DE EXCLUSÃO (LGPD) -->
    <q-dialog v-model="modalExclusao" persistent>
      <q-card class="bg-dark text-white q-pa-md" style="max-width: 440px; width: 100%; border: 2px solid #C10015;">
        <q-card-section class="row items-center q-pb-none">
          <q-avatar icon="warning" color="negative" text-color="white" />
          <div class="text-h6 text-weight-bold q-ml-sm text-negative">
            Atenção: Ação Irreversível!
          </div>
        </q-card-section>

        <q-card-section class="q-pt-sm">
          <p class="text-body2 text-grey-3">
            Você está prestes a revogar o consentimento de dados do <strong>AppBus</strong>. Seus dados pessoais civis serão
            <strong>anonimizados imediatamente</strong> e sua conta será desativada.
          </p>

          <q-checkbox
            v-model="confirmacaoExpressa"
            dark
            color="negative"
            label="Estou ciente de que perderei o direito ao transporte e a ação não poderá ser desfeita."
            class="text-caption q-mb-md"
          />

          <q-input
            v-model="senhaConfirmacao"
            outlined
            dense
            dark
            type="password"
            label="Digite sua senha atual para confirmar a titularidade"
            color="negative"
            :rules="[val => !!val || 'A senha é obrigatória para autorizar a anonimização.']"
          >
            <template v-slot:prepend>
              <q-icon name="lock" color="negative" />
            </template>
          </q-input>
        </q-card-section>

        <q-card-actions align="right" class="q-gutter-x-sm">
          <q-btn
            flat
            label="Cancelar"
            color="grey-4"
            v-close-popup
            :disable="excluindoConta"
          />
          <q-btn
            color="negative"
            label="Confirmar Anonimização"
            icon="delete_forever"
            :loading="excluindoConta"
            :disable="!confirmacaoExpressa || !senhaConfirmacao"
            @click="executarAnonimizacao"
          />
        </q-card-actions>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { useAuthStore } from '../../stores/authStore'
import api from '../../boot/axios'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const perfil = ref(null)
const loadingPerfil = ref(false)

// Estados do modal de exclusão LGPD
const modalExclusao = ref(false)
const confirmacaoExpressa = ref(false)
const senhaConfirmacao = ref('')
const excluindoConta = ref(false)

const isAprovado = computed(() => {
  return String(perfil.value?.aluno?.status_aprovacao || authStore.user?.status_aprovacao || '').toUpperCase() === 'APROVADO'
})

const isPendente = computed(() => {
  return String(perfil.value?.aluno?.status_aprovacao || authStore.user?.status_aprovacao || '').toUpperCase() === 'PENDENTE'
})

const statusBadgeColor = computed(() => {
  if (isAprovado.value) return 'positive'
  if (isPendente.value) return 'warning'
  return 'negative'
})

const statusIcon = computed(() => {
  if (isAprovado.value) return 'verified'
  if (isPendente.value) return 'hourglass_empty'
  return 'block'
})

const statusLabel = computed(() => {
  if (isAprovado.value) return 'APROVADO'
  if (isPendente.value) return 'EM ANÁLISE'
  return 'REJEITADO'
})

const formatData = (dataStr) => {
  if (!dataStr) return 'Não informada'
  try {
    const [ano, mes, dia] = dataStr.split('-')
    return `${dia}/${mes}/${ano}`
  } catch (e) {
    return dataStr
  }
}

const formatDataHora = (dataHoraStr) => {
  if (!dataHoraStr) return 'No cadastro do aplicativo'
  try {
    const d = new Date(dataHoraStr)
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (e) {
    return dataHoraStr
  }
}

const carregarPerfil = async () => {
  loadingPerfil.value = true
  try {
    const response = await api.get('/auth/perfil/')
    perfil.value = response.data
  } catch (error) {
    console.warn('Falha ao carregar perfil detalhado, usando dados da sessão:', error)
  } finally {
    loadingPerfil.value = false
  }
}

const abrirModalExclusao = () => {
  confirmacaoExpressa.value = false
  senhaConfirmacao.value = ''
  modalExclusao.value = true
}

const executarAnonimizacao = async () => {
  if (!confirmacaoExpressa.value || !senhaConfirmacao.value) return

  excluindoConta.value = true
  try {
    const response = await api.post('/auth/solicitar-exclusao/', {
      password: senhaConfirmacao.value,
      confirmacao: true
    })

    modalExclusao.value = false

    $q.notify({
      type: 'positive',
      icon: 'shield',
      message: response.data?.mensagem || 'Sua conta e dados pessoais foram devidamente anonimizados.',
      timeout: 5000,
      position: 'top'
    })

    // Efetua logout e direciona para login
    authStore.logout()
    router.push('/login')
  } catch (error) {
    console.error('Erro na solicitação de anonimização:', error)
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: error.response?.data?.password?.[0] ||
               error.response?.data?.erro ||
               'Falha ao processar solicitação de exclusão. Verifique sua senha.'
    })
  } finally {
    excluindoConta.value = false
  }
}

onMounted(async () => {
  await carregarPerfil()
})
</script>

<style scoped lang="scss">
.student-profile-page {
  max-width: 480px;
  margin: 0 auto;
}

.avatar-border {
  border: 2px solid #F2C037;
}

.border-subtle {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.consent-box {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.border-danger {
  border: 1px solid rgba(193, 0, 21, 0.4);
}
</style>
