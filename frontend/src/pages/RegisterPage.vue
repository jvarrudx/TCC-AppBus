<template>
  <q-layout view="lHh Lpr lFf" class="bg-dark-page">
    <q-page-container>
      <q-page class="flex flex-center q-pa-md">
        <div class="register-wrapper full-width" style="max-width: 520px;">
          <!-- Header -->
          <div class="text-center q-mb-lg">
            <div class="brand-badge q-mb-sm inline-block cursor-pointer" @click="$router.push('/login')">
              <q-icon name="arrow_back" size="22px" color="dark" class="q-mr-xs" />
              <q-icon name="directions_bus" size="28px" color="dark" />
            </div>
            <h1 class="text-h4 text-weight-bolder text-white q-my-none">
              Cadastro de <span class="text-primary">Aluno</span>
            </h1>
            <p class="text-grey-5 q-mt-xs text-body2">
              Adesão ao Sistema Municipal de Transporte Universitário
            </p>
          </div>

          <q-card class="dark-card q-pa-lg">
            <q-form @submit.prevent="handleRegister" class="q-gutter-y-md">

              <!-- Seção 1: Dados Pessoais -->
              <div class="row items-center q-mt-xs">
                <q-icon name="person" color="primary" size="20px" class="q-mr-xs" />
                <span class="text-subtitle2 text-primary text-weight-bold">1. Dados Pessoais e Titularidade</span>
              </div>

              <q-input
                v-model="form.nome"
                outlined
                dark
                dense
                label="Nome Completo Civil *"
                color="primary"
                :rules="[val => !!val && val.trim().length >= 3 || 'Informe seu nome completo (mínimo 3 caracteres)']"
              />
              
              <div class="row q-col-gutter-sm">
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model="form.cpf"
                    outlined
                    dark
                    dense
                    label="CPF *"
                    mask="###.###.###-##"
                    unmasked-value
                    color="primary"
                    :rules="[
                      val => !!val || 'CPF é obrigatório',
                      val => validateCpf(val) || 'CPF inválido (dígitos verificadores)'
                    ]"
                  />
                </div>
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model="form.data_nascimento"
                    type="date"
                    outlined
                    dark
                    dense
                    label="Data de Nascimento *"
                    color="primary"
                    :rules="[val => !!val || 'Data de nascimento é obrigatória']"
                    @update:model-value="checkMaioridade"
                  />
                </div>
              </div>

              <!-- Seção Condicional LGPD: Menor de Idade -->
              <transition name="q-transition--slide-down">
                <div v-if="isMenorIdade" class="bg-amber-10-dim q-pa-md rounded-borders q-mt-sm border-amber">
                  <div class="text-caption text-amber-5 text-weight-bold q-mb-xs flex items-center">
                    <q-icon name="verified_user" size="18px" class="q-mr-xs" />
                    Consentimento Assistido (LGPD Art. 14 / Menor de 18 Anos)
                  </div>
                  <p class="text-grey-4 text-caption q-mb-sm">
                    Como você tem menos de 18 anos, a legislação exige a representação ou assistência de um responsável legal.
                  </p>
                  <q-input
                    v-model="form.responsavel_legal_cpf"
                    outlined
                    dark
                    dense
                    label="CPF do Responsável Legal *"
                    mask="###.###.###-##"
                    unmasked-value
                    color="amber"
                    :rules="[
                      val => !isMenorIdade || !!val || 'Obrigatório para menores de 18 anos',
                      val => !isMenorIdade || validateCpf(val) || 'CPF do responsável inválido'
                    ]"
                  />
                </div>
              </transition>

              <!-- Seção 2: Vínculo Institucional & Multi-Tenancy -->
              <div class="row items-center q-mt-lg">
                <q-icon name="apartment" color="primary" size="20px" class="q-mr-xs" />
                <span class="text-subtitle2 text-primary text-weight-bold">2. Vínculo Municipal & Ensino</span>
              </div>

              <!-- Seleção Dinâmica de Prefeitura (Tenant) -->
              <q-select
                v-model="form.cliente_id"
                :options="prefeiturasOptions"
                emit-value
                map-options
                outlined
                dark
                dense
                label="Prefeitura / Município Concedente *"
                color="primary"
                :loading="loadingAdesao"
                :rules="[val => !!val || 'Selecione o município de origem']"
                @update:model-value="onPrefeituraChange"
              >
                <template v-slot:no-option>
                  <q-item>
                    <q-item-section class="text-grey">Nenhum município credenciado no momento</q-item-section>
                  </q-item>
                </template>
              </q-select>
              
              <div class="row q-col-gutter-sm">
                <div class="col-12 col-sm-6">
                  <!-- Seleção Reativa de Instituições filtrada pela prefeitura -->
                  <q-select
                    v-model="form.instituicao_id"
                    :options="instituicoesOptions"
                    emit-value
                    map-options
                    outlined
                    dark
                    dense
                    label="Instituição de Ensino *"
                    color="primary"
                    :disable="!form.cliente_id"
                    :rules="[val => !!val || 'Selecione sua faculdade/escola']"
                  >
                    <template v-slot:no-option>
                      <q-item>
                        <q-item-section class="text-grey">Nenhuma instituição para este município</q-item-section>
                      </q-item>
                    </template>
                  </q-select>
                </div>
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model="form.matricula"
                    outlined
                    dark
                    dense
                    label="Nº de Matrícula Acadêmica *"
                    color="primary"
                    :rules="[val => !!val && val.trim().length >= 2 || 'Matrícula é obrigatória']"
                  />
                </div>
              </div>

              <!-- Seção 3: Credenciais de Acesso -->
              <div class="row items-center q-mt-lg">
                <q-icon name="lock" color="primary" size="20px" class="q-mr-xs" />
                <span class="text-subtitle2 text-primary text-weight-bold">3. Credenciais de Acesso</span>
              </div>

              <q-input
                v-model="form.email"
                type="email"
                outlined
                dark
                dense
                label="E-mail Institucional ou Pessoal *"
                color="primary"
                autocomplete="email"
                :rules="[
                  val => !!val || 'E-mail é obrigatório',
                  val => /.+@.+\..+/.test(val) || 'Informe um e-mail válido'
                ]"
              />

              <div class="row q-col-gutter-sm">
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model="form.password"
                    :type="showPassword ? 'text' : 'password'"
                    outlined
                    dark
                    dense
                    label="Senha de Acesso *"
                    color="primary"
                    autocomplete="new-password"
                    :rules="[
                      val => !!val || 'Senha é obrigatória',
                      val => val.length >= 8 || 'Mínimo de 8 caracteres'
                    ]"
                  >
                    <template v-slot:append>
                      <q-icon
                        :name="showPassword ? 'visibility_off' : 'visibility'"
                        class="cursor-pointer"
                        color="grey-5"
                        @click="showPassword = !showPassword"
                      />
                    </template>
                  </q-input>
                </div>
                <div class="col-12 col-sm-6">
                  <q-input
                    v-model="confirmPassword"
                    :type="showPassword ? 'text' : 'password'"
                    outlined
                    dark
                    dense
                    label="Confirmar Senha *"
                    color="primary"
                    autocomplete="new-password"
                    :rules="[
                      val => !!val || 'Confirmação necessária',
                      val => val === form.password || 'As senhas não coincidem'
                    ]"
                  />
                </div>
              </div>

              <!-- Termos de Uso (LGPD) -->
              <div class="bg-dark-page q-pa-sm rounded-borders q-mt-md consent-card">
                <q-checkbox v-model="form.termo_aceito" color="primary" dark>
                  <span class="text-caption text-grey-4">
                    Li e concordo expressamente com os
                    <a href="#" class="text-primary text-weight-bold" @click.prevent.stop="openTermos">
                      Termos de Uso e Política de Privacidade
                    </a>.
                  </span>
                </q-checkbox>
                <div v-if="termoError" class="text-negative text-caption q-ml-xl q-pb-xs font-medium">
                  {{ termoError }}
                </div>
              </div>

              <!-- Banner de Erros Globais da API -->
              <q-banner v-if="errorMessage" rounded dense class="bg-negative text-white text-caption q-mt-sm">
                <template v-slot:avatar>
                  <q-icon name="error_outline" size="20px" />
                </template>
                <div style="white-space: pre-line;">{{ errorMessage }}</div>
              </q-banner>

              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                class="full-width q-py-sm btn-bus-primary q-mt-lg"
                size="lg"
                no-caps
                :loading="loading"
              >
                <q-icon name="person_add" size="20px" class="q-mr-sm" />
                <span>Solicitar Cadastro de Aluno</span>
              </q-btn>
            </q-form>

            <q-separator dark class="q-my-lg" />

            <!-- Link para tela de Login -->
            <div class="text-center">
              <span class="text-grey-5 text-caption">Já possui cadastro ativo? </span>
              <router-link
                to="/login"
                class="text-primary text-caption text-weight-bold text-decoration-none"
              >
                Fazer Login
              </router-link>
            </div>
          </q-card>
        </div>

        <!-- Modal de Termos de Uso (LGPD) -->
        <q-dialog v-model="showTermosDialog" persistent>
          <q-card class="dark-card" style="min-width: 360px; max-width: 600px;">
            <q-card-section class="row items-center q-pb-none">
              <q-icon name="gavel" color="primary" size="24px" class="q-mr-sm" />
              <div class="text-h6 text-white text-weight-bold">
                Termos de Uso e LGPD
              </div>
              <q-space />
              <q-btn icon="close" flat round dense color="grey-5" v-close-popup />
            </q-card-section>

            <q-card-section class="q-pt-sm">
              <div v-if="documentoLegal" class="text-caption text-grey-5 q-mb-sm">
                Versão: <strong class="text-white">{{ documentoLegal.versao }}</strong> • Publicação: {{ formatDate(documentoLegal.data_publicacao) }}
              </div>
            </q-card-section>

            <q-separator dark />

            <q-card-section class="text-grey-3 text-body2 scroll terms-content" style="max-height: 55vh">
              <div v-if="loadingTermos" class="text-center q-pa-xl">
                <q-spinner color="primary" size="2.5em" />
                <div class="text-caption text-grey-5 q-mt-sm">Carregando termos vigentes...</div>
              </div>
              <div v-else-if="documentoLegal" class="terms-rendered-text" style="white-space: pre-wrap; line-height: 1.6;">
                {{ documentoLegal.conteudo }}
              </div>
              <div v-else class="text-negative text-center q-pa-md">
                Não foi possível carregar os termos vigentes no momento.
              </div>
            </q-card-section>

            <q-separator dark />

            <q-card-actions align="right" class="q-pa-md">
              <q-btn flat label="Fechar" color="grey-5" v-close-popup />
              <q-btn
                color="primary"
                text-color="dark"
                label="Aceitar e Fechar"
                no-caps
                @click="aceitarTermoPeloModal"
              />
            </q-card-actions>
          </q-card>
        </q-dialog>

      </q-page>
    </q-page-container>
  </q-layout>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import api from '../boot/axios'

const $q = useQuasar()
const router = useRouter()

const loading = ref(false)
const loadingAdesao = ref(false)
const showPassword = ref(false)
const confirmPassword = ref('')
const errorMessage = ref('')
const termoError = ref('')

// Controle LGPD
const isMenorIdade = ref(false)
const showTermosDialog = ref(false)
const loadingTermos = ref(false)
const documentoLegal = ref(null)

// Lista dinâmica de Prefeituras e Instituições obtidas do Backend
const prefeiturasRaw = ref([])

const form = reactive({
  nome: '',
  email: '',
  password: '',
  cpf: '',
  data_nascimento: '',
  responsavel_legal_cpf: '',
  cliente_id: null,
  instituicao_id: null,
  matricula: '',
  documento_legal_id: null,
  termo_aceito: false
})

// Algoritmo oficial de validação de CPF (Receita Federal)
const validateCpf = (cpf) => {
  if (!cpf) return false
  const clean = String(cpf).replace(/\D/g, '')
  if (clean.length !== 11) return false
  if (/^(\d)\1{10}$/.test(clean)) return false

  let sum = 0
  for (let i = 1; i <= 9; i++) sum += parseInt(clean.substring(i - 1, i)) * (11 - i)
  let rest = (sum * 10) % 11
  if (rest === 10 || rest === 11) rest = 0
  if (rest !== parseInt(clean.substring(9, 10))) return false

  sum = 0
  for (let i = 1; i <= 10; i++) sum += parseInt(clean.substring(i - 1, i)) * (12 - i)
  rest = (sum * 10) % 11
  if (rest === 10 || rest === 11) rest = 0
  if (rest !== parseInt(clean.substring(10, 11))) return false

  return true
}

// Opções computadas de Prefeituras
const prefeiturasOptions = computed(() => {
  return prefeiturasRaw.value.map(p => ({
    label: p.nome,
    value: p.id,
    instituicoes: p.instituicoes
  }))
})

// Opções computadas de Instituições vinculadas estritamente ao município selecionado
const instituicoesOptions = computed(() => {
  if (!form.cliente_id) return []
  const pref = prefeiturasRaw.value.find(p => p.id === form.cliente_id)
  if (!pref || !pref.instituicoes) return []
  return pref.instituicoes.map(inst => ({
    label: inst.sigla ? `${inst.nome} (${inst.sigla})` : inst.nome,
    value: inst.id
  }))
})

const onPrefeituraChange = () => {
  form.instituicao_id = null
}

const checkMaioridade = (dateStr) => {
  if (!dateStr) return
  const birthDate = new Date(dateStr)
  const today = new Date()
  let age = today.getFullYear() - birthDate.getFullYear()
  const m = today.getMonth() - birthDate.getMonth()
  if (m < 0 || (m === 0 && today.getDate() < birthDate.getDate())) {
    age--
  }
  isMenorIdade.value = age < 18
  if (!isMenorIdade.value) {
    form.responsavel_legal_cpf = ''
  }
}

// Busca Prefeituras e Instituições da rota pública
const fetchDadosAdesao = async () => {
  loadingAdesao.value = true
  try {
    const res = await api.get('/public/dados-adesao/')
    prefeiturasRaw.value = res.data || []
    if (prefeiturasRaw.value.length === 1) {
      form.cliente_id = prefeiturasRaw.value[0].id
    }
  } catch (error) {
    console.error('Erro ao carregar municípios credenciados:', error)
  } finally {
    loadingAdesao.value = false
  }
}

// Busca Termos Vigentes
const fetchTermos = async () => {
  loadingTermos.value = true
  try {
    const res = await api.get('/documentos-legais/vigentes/')
    if (res.data && res.data.length > 0) {
      documentoLegal.value = res.data.find(d => d.tipo === 'TERMOS_DE_USO') || res.data[0]
      form.documento_legal_id = documentoLegal.value.id
    }
  } catch (error) {
    console.warn('Erro ao buscar termos de uso:', error)
  } finally {
    loadingTermos.value = false
  }
}

const openTermos = () => {
  showTermosDialog.value = true
  if (!documentoLegal.value) {
    fetchTermos()
  }
}

const aceitarTermoPeloModal = () => {
  form.termo_aceito = true
  termoError.value = ''
  showTermosDialog.value = false
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    return new Date(dateStr).toLocaleDateString('pt-BR')
  } catch (e) {
    return dateStr
  }
}

const handleRegister = async () => {
  errorMessage.value = ''
  termoError.value = ''

  if (!form.termo_aceito) {
    termoError.value = 'É obrigatório aceitar os Termos de Uso e Política de Privacidade.'
    return
  }

  if (form.password !== confirmPassword.value) {
    errorMessage.value = 'A confirmação de senha não confere com a senha informada.'
    return
  }

  loading.value = true
  try {
    const payload = { ...form }
    
    // Deleta cpf do responsavel caso seja maior de idade
    if (!isMenorIdade.value) {
      delete payload.responsavel_legal_cpf
    }
    
    // Remove documento_legal_id se nulo (backend inferirá o mais recente)
    if (!payload.documento_legal_id) {
      delete payload.documento_legal_id
    }

    await api.post('/auth/registro-aluno/', payload)
    
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: 'Cadastro de Aluno realizado com sucesso!',
      caption: 'Acesse o sistema com suas credenciais.',
      timeout: 5000
    })
    
    router.push({
      path: '/login',
      query: { email: form.email, registered: 'true' }
    })
  } catch (error) {
    if (error.response && error.response.data) {
      const errs = error.response.data
      let msg = 'Erro no cadastro de aluno:\n'
      for (const [key, value] of Object.entries(errs)) {
        const valStr = Array.isArray(value) ? value.join(' ') : value
        msg += `• ${key}: ${valStr}\n`
      }
      errorMessage.value = msg.trim()
    } else {
      errorMessage.value = 'Falha de comunicação com o servidor de autenticação.'
    }
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchDadosAdesao()
  fetchTermos()
})
</script>

<style scoped lang="scss">
.register-wrapper {
  animation: fadeIn 0.3s ease-out;
}

.brand-badge {
  background: #F2C037;
  padding: 10px 14px;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(242, 192, 55, 0.35);
  display: inline-flex;
  align-items: center;
  transition: transform 0.2s ease;

  &:hover {
    transform: translateY(-2px);
  }
}

.bg-amber-10-dim {
  background-color: rgba(242, 192, 55, 0.08);
}

.border-amber {
  border: 1px solid rgba(242, 192, 55, 0.28);
}

.consent-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  transition: border-color 0.2s ease;

  &:hover {
    border-color: rgba(242, 192, 55, 0.4);
  }
}

a {
  text-decoration: none;
  &:hover {
    text-decoration: underline;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
