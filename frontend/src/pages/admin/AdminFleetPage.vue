<template>
  <q-page class="q-py-md">
    <!-- Header -->
    <div class="row items-center justify-between q-mb-md">
      <div>
        <div class="row items-center">
          <q-btn flat round dense icon="arrow_back" color="grey-4" class="q-mr-sm" @click="$router.push('/')" />
          <h1 class="text-h5 text-weight-bold text-white q-my-none">
            Frota, Rotas & <span class="text-primary">Motoristas</span>
          </h1>
        </div>
        <p class="text-caption text-grey-5 q-mt-xs q-mb-none">
          Gestão de ônibus municipais, condutores autorizados e itinerários
        </p>
      </div>

      <!-- Abas de Navegação Frota / Motoristas / Rotas -->
      <q-tabs
        v-model="tab"
        dense
        no-caps
        active-color="primary"
        indicator-color="primary"
        class="text-grey-4"
      >
        <q-tab name="frota" icon="directions_bus" label="Frota de Ônibus" />
        <q-tab name="motoristas" icon="badge" label="Motoristas" />
        <q-tab name="rotas" icon="alt_route" label="Rotas e Itinerários" />
      </q-tabs>
    </div>

    <!-- Painel 1: Frota de Ônibus -->
    <div v-if="tab === 'frota'">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-subtitle1 text-white text-weight-bold flex items-center">
          <q-icon name="directions_bus" size="20px" class="q-mr-xs text-primary" />
          Veículos Cadastrados ({{ onibusList.length }})
        </div>
        <div class="row q-gutter-x-sm">
          <q-btn
            outline
            color="primary"
            icon="refresh"
            size="sm"
            no-caps
            :loading="loadingOnibus"
            @click="fetchOnibus"
          />
          <q-btn
            color="primary"
            text-color="dark"
            icon="add"
            label="Cadastrar Ônibus"
            size="sm"
            class="btn-bus-primary text-weight-bold"
            no-caps
            @click="openNovoOnibusModal"
          />
        </div>
      </div>

      <!-- Error State Ônibus -->
      <div v-if="errorOnibus && !loadingOnibus" class="text-center q-pa-xl dark-card rounded-borders border-danger q-mb-md">
        <q-icon name="error_outline" size="52px" color="negative" class="q-mb-sm" />
        <div class="text-h6 text-white text-weight-bold">Falha ao carregar frota de veículos</div>
        <p class="text-caption text-grey-4 q-mt-xs q-mb-md">
          {{ errorOnibus }}
        </p>
        <q-btn
          color="primary"
          text-color="dark"
          icon="refresh"
          label="Tentar Novamente"
          class="btn-bus-primary text-weight-bold"
          no-caps
          @click="fetchOnibus"
        />
      </div>

      <!-- Loader -->
      <div v-else-if="loadingOnibus" class="text-center q-pa-xl">
        <q-spinner-dots color="primary" size="48px" />
        <div class="text-caption text-grey-4 q-mt-sm">Carregando frota de veículos...</div>
      </div>

      <!-- Empty State -->
      <div v-else-if="onibusList.length === 0" class="text-center q-pa-xl dark-card rounded-borders">
        <q-icon name="directions_bus_filled" size="64px" color="grey-7" class="q-mb-sm" />
        <div class="text-h6 text-grey-4">Nenhum ônibus cadastrado</div>
        <p class="text-caption text-grey-5">Cadastre o primeiro veículo da frota municipal.</p>
        <q-btn color="primary" text-color="dark" label="Adicionar Ônibus" no-caps @click="openNovoOnibusModal" />
      </div>

      <!-- Grid de Veículos -->
      <div v-else class="row q-col-gutter-md">
        <div v-for="bus in onibusList" :key="bus.id" class="col-12 col-md-6">
          <q-card class="dark-card q-pa-md h-100 flex column justify-between vehicle-card">
            <div>
              <div class="row items-center justify-between q-mb-xs">
                <div class="text-h6 text-weight-bolder text-white flex items-center">
                  <span class="placa-badge q-mr-sm">{{ bus.placa }}</span>
                </div>
                <q-badge
                  :color="bus.ativo ? 'positive' : 'grey-7'"
                  :text-color="bus.ativo ? 'white' : 'grey-3'"
                  class="cursor-pointer text-weight-bold"
                  @click="toggleStatusOnibus(bus)"
                >
                  {{ bus.ativo ? 'Em Operação' : 'Inativo' }}
                  <q-tooltip>Clique para alternar status operacional</q-tooltip>
                </q-badge>
              </div>

              <div class="text-subtitle2 text-primary q-mt-xs">
                {{ bus.modelo_detalhe?.marca }} {{ bus.modelo_detalhe?.nome }}
              </div>

              <div class="row q-col-gutter-x-md text-caption text-grey-4 q-mt-sm">
                <div>
                  <q-icon name="event_seat" size="16px" class="q-mr-xs text-grey-5" />
                  <span>Capacidade: <strong>{{ bus.capacidade }} assentos</strong></span>
                </div>
              </div>

              <div class="q-mt-sm text-caption text-grey-5">
                <span>UUID Operacional:</span>
                <span class="text-grey-4 uuid-text q-ml-xs">{{ bus.id_operacional }}</span>
              </div>
            </div>

            <div class="row items-center justify-between q-mt-md q-pt-sm border-top-dark">
              <span class="text-caption text-grey-5">
                Status: <strong :class="bus.ativo ? 'text-positive' : 'text-grey-5'">{{ bus.ativo ? 'Pronto para Linha' : 'Parado para Manutenção' }}</strong>
              </span>
              <q-btn
                flat
                dense
                round
                :icon="bus.ativo ? 'toggle_on' : 'toggle_off'"
                :color="bus.ativo ? 'positive' : 'grey-5'"
                size="md"
                @click="toggleStatusOnibus(bus)"
              >
                <q-tooltip>{{ bus.ativo ? 'Desativar Ônibus' : 'Ativar Ônibus' }}</q-tooltip>
              </q-btn>
            </div>
          </q-card>
        </div>
      </div>
    </div>

    <!-- Painel 2: Motoristas (Gestão e Cadastro) -->
    <div v-else-if="tab === 'motoristas'">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-subtitle1 text-white text-weight-bold flex items-center">
          <q-icon name="badge" size="20px" class="q-mr-xs text-primary" />
          Motoristas Autorizados ({{ motoristasList.length }})
        </div>
        <div class="row q-gutter-x-sm">
          <q-btn
            outline
            color="primary"
            icon="refresh"
            size="sm"
            no-caps
            :loading="loadingMotoristas"
            @click="fetchMotoristas"
          />
          <q-btn
            color="primary"
            text-color="dark"
            icon="person_add"
            label="Cadastrar Motorista"
            size="sm"
            class="btn-bus-primary text-weight-bold"
            no-caps
            @click="openNovoMotoristaModal"
          />
        </div>
      </div>

      <!-- Error State Motoristas -->
      <div v-if="errorMotoristas && !loadingMotoristas" class="text-center q-pa-xl dark-card rounded-borders border-danger q-mb-md">
        <q-icon name="error_outline" size="52px" color="negative" class="q-mb-sm" />
        <div class="text-h6 text-white text-weight-bold">Falha ao carregar motoristas</div>
        <p class="text-caption text-grey-4 q-mt-xs q-mb-md">{{ errorMotoristas }}</p>
        <q-btn
          color="primary"
          text-color="dark"
          icon="refresh"
          label="Tentar Novamente"
          class="btn-bus-primary text-weight-bold"
          no-caps
          @click="fetchMotoristas"
        />
      </div>

      <!-- Loader Motoristas -->
      <div v-else-if="loadingMotoristas" class="text-center q-pa-xl">
        <q-spinner-dots color="primary" size="48px" />
        <div class="text-caption text-grey-4 q-mt-sm">Carregando condutores autorizados...</div>
      </div>

      <!-- Empty State Motoristas -->
      <div v-else-if="motoristasList.length === 0" class="text-center q-pa-xl dark-card rounded-borders">
        <q-icon name="sports_motorsports" size="64px" color="grey-7" class="q-mb-sm" />
        <div class="text-h6 text-grey-4">Nenhum motorista cadastrado</div>
        <p class="text-caption text-grey-5">Cadastre os motoristas que conduzirão as rotas municipais.</p>
        <q-btn color="primary" text-color="dark" label="Cadastrar Motorista" no-caps @click="openNovoMotoristaModal" />
      </div>

      <!-- Grid de Motoristas -->
      <div v-else class="row q-col-gutter-md">
        <div v-for="mot in motoristasList" :key="mot.id" class="col-12 col-md-6">
          <q-card class="dark-card q-pa-md h-100 flex column justify-between vehicle-card">
            <div>
              <div class="row items-center justify-between q-mb-xs">
                <div class="text-subtitle1 text-weight-bold text-white flex items-center">
                  <q-icon name="person" size="20px" class="q-mr-xs text-primary" />
                  {{ mot.nome }}
                </div>
                <q-badge
                  :color="mot.ativo ? 'positive' : 'grey-7'"
                  :text-color="mot.ativo ? 'white' : 'grey-3'"
                  class="cursor-pointer text-weight-bold"
                  @click="toggleStatusMotorista(mot)"
                >
                  {{ mot.ativo ? 'Ativo' : 'Inativo' }}
                  <q-tooltip>Clique para alternar status do motorista</q-tooltip>
                </q-badge>
              </div>

              <div class="row q-col-gutter-x-md text-caption text-grey-4 q-mt-sm">
                <div>
                  <q-icon name="badge" size="16px" class="q-mr-xs text-grey-5" />
                  <span>CNH: <strong>{{ mot.cnh }}</strong> (Cat. {{ mot.categoria_cnh || 'D' }})</span>
                </div>
                <div>
                  <q-icon name="fingerprint" size="16px" class="q-mr-xs text-grey-5" />
                  <span>CPF: <strong>{{ mot.cpf }}</strong></span>
                </div>
              </div>

              <div v-if="mot.email" class="q-mt-xs text-caption text-grey-4">
                <q-icon name="email" size="16px" class="q-mr-xs text-grey-5" />
                <span>Login: <strong>{{ mot.email }}</strong></span>
              </div>
            </div>

            <div class="row items-center justify-between q-mt-md q-pt-sm border-top-dark">
              <span class="text-caption text-grey-5">
                Operação: <strong :class="mot.ativo ? 'text-positive' : 'text-grey-5'">{{ mot.ativo ? 'Habilitado para Viagens' : 'Suspenso / Inativo' }}</strong>
              </span>
              <q-btn
                flat
                dense
                round
                :icon="mot.ativo ? 'toggle_on' : 'toggle_off'"
                :color="mot.ativo ? 'positive' : 'grey-5'"
                size="md"
                @click="toggleStatusMotorista(mot)"
              >
                <q-tooltip>{{ mot.ativo ? 'Desativar Motorista' : 'Ativar Motorista' }}</q-tooltip>
              </q-btn>
            </div>
          </q-card>
        </div>
      </div>
    </div>

    <!-- Painel 3: Rotas & Itinerários -->
    <div v-else-if="tab === 'rotas'">
      <div class="row items-center justify-between q-mb-md">
        <div class="text-subtitle1 text-white text-weight-bold flex items-center">
          <q-icon name="alt_route" size="20px" class="q-mr-xs text-primary" />
          Rotas e Itinerários Cadastrados ({{ rotasList.length }})
        </div>
        <div class="row q-gutter-x-sm">
          <q-btn
            outline
            color="primary"
            icon="refresh"
            size="sm"
            no-caps
            :loading="loadingRotas"
            @click="fetchRotas"
          />
          <q-btn
            color="primary"
            text-color="dark"
            icon="add"
            label="Cadastrar Rota"
            size="sm"
            class="btn-bus-primary text-weight-bold"
            no-caps
            @click="openNovaRotaModal"
          />
        </div>
      </div>

      <!-- Error State Rotas -->
      <div v-if="errorRotas && !loadingRotas" class="text-center q-pa-xl dark-card rounded-borders border-danger q-mb-md">
        <q-icon name="error_outline" size="52px" color="negative" class="q-mb-sm" />
        <div class="text-h6 text-white text-weight-bold">Falha ao carregar rotas</div>
        <p class="text-caption text-grey-4 q-mt-xs q-mb-md">{{ errorRotas }}</p>
        <q-btn
          color="primary"
          text-color="dark"
          icon="refresh"
          label="Tentar Novamente"
          class="btn-bus-primary text-weight-bold"
          no-caps
          @click="fetchRotas"
        />
      </div>

      <!-- Loader Rotas -->
      <div v-else-if="loadingRotas" class="text-center q-pa-xl">
        <q-spinner-dots color="primary" size="48px" />
        <div class="text-caption text-grey-4 q-mt-sm">Carregando rotas municipais...</div>
      </div>

      <!-- Empty State Rotas -->
      <div v-else-if="rotasList.length === 0" class="text-center q-pa-xl dark-card rounded-borders">
        <q-icon name="route" size="64px" color="grey-7" class="q-mb-sm" />
        <div class="text-h6 text-grey-4">Nenhuma rota cadastrada</div>
        <p class="text-caption text-grey-5">Cadastre o primeiro itinerário para o transporte.</p>
        <q-btn color="primary" text-color="dark" label="Adicionar Rota" no-caps @click="openNovaRotaModal" />
      </div>

      <!-- Lista de Rotas -->
      <div v-else class="q-gutter-y-sm">
        <q-card v-for="rota in rotasList" :key="rota.id" class="dark-card q-pa-md">
          <div class="row items-center justify-between">
            <div>
              <div class="row items-center q-gutter-x-sm">
                <span class="text-subtitle1 text-weight-bold text-white">{{ rota.nome }}</span>
                <q-badge
                  :color="rota.ativo ? 'positive' : 'grey-7'"
                  :text-color="rota.ativo ? 'white' : 'grey-3'"
                  class="cursor-pointer text-weight-bold"
                  @click="toggleStatusRota(rota)"
                >
                  {{ rota.ativo ? 'Ativa' : 'Desativada' }}
                  <q-tooltip>Clique para alternar status da rota</q-tooltip>
                </q-badge>
              </div>

              <!-- Paradas / Instituições Atendidas -->
              <div class="q-mt-sm">
                <span class="text-caption text-grey-5">Itinerário de Paradas:</span>
                <div v-if="rota.paradas && rota.paradas.length > 0" class="row q-gutter-xs q-mt-xs">
                  <q-chip
                    v-for="(p, idx) in rota.paradas"
                    :key="p.id || idx"
                    size="sm"
                    color="grey-9"
                    text-color="primary"
                    icon="place"
                  >
                    {{ idx + 1 }}º: {{ p.instituicao_nome }}
                  </q-chip>
                </div>
                <div v-else class="text-caption text-grey-6 italic q-mt-xs">
                  Nenhuma parada específica vinculada
                </div>
              </div>
            </div>

            <div>
              <q-btn
                flat
                dense
                round
                :icon="rota.ativo ? 'visibility_off' : 'visibility'"
                :color="rota.ativo ? 'grey-4' : 'positive'"
                @click="toggleStatusRota(rota)"
              >
                <q-tooltip>{{ rota.ativo ? 'Desativar Rota' : 'Ativar Rota' }}</q-tooltip>
              </q-btn>
            </div>
          </div>
        </q-card>
      </div>
    </div>

    <!-- Modal Novo Ônibus -->
    <q-dialog v-model="showNovoOnibusModal">
      <q-card class="dark-card" style="min-width: 340px; max-width: 480px;">
        <q-card-section>
          <div class="text-h6 text-white text-weight-bold">Cadastrar Novo Veículo</div>
          <div class="text-caption text-grey-5">Insira os dados do ônibus para vinculação à frota</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit.prevent="salvarNovoOnibus" class="q-gutter-y-sm">
            <q-input
              v-model="novoOnibus.placa"
              outlined
              dark
              dense
              label="Placa do Veículo (ex: ABC1D23) *"
              color="primary"
              mask="NNNNNNN"
              :rules="[val => !!val && val.length >= 7 || 'Placa obrigatória (7 caracteres)']"
            />

            <q-select
              v-model="novoOnibus.modelo"
              :options="modelosOptions"
              emit-value
              map-options
              outlined
              dark
              dense
              label="Modelo do Veículo *"
              color="primary"
              :rules="[val => !!val || 'Selecione o modelo']"
            />

            <q-input
              v-model.number="novoOnibus.capacidade"
              type="number"
              outlined
              dark
              dense
              label="Capacidade de Assentos *"
              color="primary"
              :rules="[val => val > 0 || 'Informe a capacidade de passageiros']"
            />

            <div class="row justify-end q-gutter-x-sm q-mt-md">
              <q-btn flat label="Cancelar" color="grey-5" v-close-popup />
              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                label="Salvar Veículo"
                class="btn-bus-primary"
                no-caps
                :loading="salvandoOnibus"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Modal Novo Motorista -->
    <q-dialog v-model="showNovoMotoristaModal">
      <q-card class="dark-card" style="min-width: 360px; max-width: 520px;">
        <q-card-section>
          <div class="text-h6 text-white text-weight-bold">Cadastrar Novo Motorista</div>
          <div class="text-caption text-grey-5">Crie as credenciais e autorização de condução do motorista</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit.prevent="salvarNovoMotorista" class="q-gutter-y-sm">
            <q-input
              v-model="novoMotorista.nome"
              outlined
              dark
              dense
              label="Nome Completo *"
              color="primary"
              :rules="[val => !!val && val.trim().length >= 3 || 'Informe o nome completo']"
            />

            <div class="row q-col-gutter-sm">
              <div class="col-12 col-sm-6">
                <q-input
                  v-model="novoMotorista.cpf"
                  outlined
                  dark
                  dense
                  label="CPF *"
                  mask="###.###.###-##"
                  unmasked-value
                  color="primary"
                  :rules="[val => !!val && val.length === 11 || 'CPF de 11 dígitos']"
                />
              </div>
              <div class="col-12 col-sm-6">
                <q-input
                  v-model="novoMotorista.data_nascimento"
                  type="date"
                  outlined
                  dark
                  dense
                  label="Data de Nascimento *"
                  stack-label
                  color="primary"
                  :rules="[val => !!val || 'Data obrigatória']"
                />
              </div>
            </div>

            <div class="row q-col-gutter-sm">
              <div class="col-12 col-sm-8">
                <q-input
                  v-model="novoMotorista.cnh"
                  outlined
                  dark
                  dense
                  label="Número do Registro CNH *"
                  color="primary"
                  :rules="[val => !!val && val.trim().length >= 5 || 'CNH obrigatória']"
                />
              </div>
              <div class="col-12 col-sm-4">
                <q-select
                  v-model="novoMotorista.categoria_cnh"
                  :options="['D', 'E', 'C', 'B', 'AB', 'AD', 'AE']"
                  outlined
                  dark
                  dense
                  label="Cat. CNH *"
                  color="primary"
                  :rules="[val => !!val || 'Selecione']"
                />
              </div>
            </div>

            <q-input
              v-model="novoMotorista.email"
              type="email"
              outlined
              dark
              dense
              label="E-mail de Login do Motorista *"
              color="primary"
              :rules="[val => !!val && /.+@.+\..+/.test(val) || 'E-mail válido é obrigatório']"
            />

            <q-input
              v-model="novoMotorista.password"
              :type="mostrarSenhaMotorista ? 'text' : 'password'"
              outlined
              dark
              dense
              label="Senha Inicial de Acesso (Mín. 8 caracteres) *"
              color="primary"
              :rules="[val => !!val && val.length >= 8 || 'Mínimo de 8 caracteres']"
            >
              <template v-slot:append>
                <q-icon
                  :name="mostrarSenhaMotorista ? 'visibility_off' : 'visibility'"
                  class="cursor-pointer"
                  @click="mostrarSenhaMotorista = !mostrarSenhaMotorista"
                />
              </template>
            </q-input>

            <div class="row justify-end q-gutter-x-sm q-mt-md">
              <q-btn flat label="Cancelar" color="grey-5" v-close-popup />
              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                label="Cadastrar Motorista"
                class="btn-bus-primary"
                no-caps
                :loading="salvandoMotorista"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

    <!-- Modal Nova Rota -->
    <q-dialog v-model="showNovaRotaModal">
      <q-card class="dark-card" style="min-width: 340px; max-width: 480px;">
        <q-card-section>
          <div class="text-h6 text-white text-weight-bold">Cadastrar Nova Rota</div>
          <div class="text-caption text-grey-5">Defina a nomenclatura e status do itinerário</div>
        </q-card-section>

        <q-card-section class="q-pt-none">
          <q-form @submit.prevent="salvarNovaRota" class="q-gutter-y-sm">
            <q-input
              v-model="novaRota.nome"
              outlined
              dark
              dense
              label="Nome da Rota (ex: Rota 03 - Noturno) *"
              color="primary"
              :rules="[val => !!val || 'Nome da rota é obrigatório']"
            />

            <div class="row justify-end q-gutter-x-sm q-mt-md">
              <q-btn flat label="Cancelar" color="grey-5" v-close-popup />
              <q-btn
                type="submit"
                color="primary"
                text-color="dark"
                label="Salvar Rota"
                class="btn-bus-primary"
                no-caps
                :loading="salvandoRota"
              />
            </div>
          </q-form>
        </q-card-section>
      </q-card>
    </q-dialog>

  </q-page>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useQuasar } from 'quasar'
import api from '../../boot/axios'

const $q = useQuasar()

const tab = ref('frota')

const loadingOnibus = ref(false)
const errorOnibus = ref(null)
const salvandoOnibus = ref(false)
const onibusList = ref([])
const showNovoOnibusModal = ref(false)

const loadingMotoristas = ref(false)
const errorMotoristas = ref(null)
const salvandoMotorista = ref(false)
const motoristasList = ref([])
const showNovoMotoristaModal = ref(false)
const mostrarSenhaMotorista = ref(false)

const loadingRotas = ref(false)
const errorRotas = ref(null)
const salvandoRota = ref(false)
const rotasList = ref([])
const showNovaRotaModal = ref(false)

const modelosRaw = ref([])

const novoOnibus = reactive({
  placa: '',
  modelo: null,
  capacidade: 44,
  ativo: true
})

const novoMotorista = reactive({
  nome: '',
  cpf: '',
  data_nascimento: '1985-01-01',
  cnh: '',
  categoria_cnh: 'D',
  email: '',
  password: ''
})

const novaRota = reactive({
  nome: '',
  ativo: true
})

const modelosOptions = computed(() => {
  return modelosRaw.value.map(m => ({
    label: `${m.marca} - ${m.nome}`,
    value: m.id
  }))
})

const fetchOnibus = async () => {
  loadingOnibus.value = true
  errorOnibus.value = null
  try {
    const res = await api.get('/veiculos/onibus/')
    onibusList.value = res.data?.results || res.data || []
  } catch (error) {
    const msg = error.response?.data?.detail ||
                error.response?.data?.erro ||
                'Falha ao carregar a frota de ônibus municipais.'
    errorOnibus.value = msg
    $q.notify({
      type: 'negative',
      icon: 'warning',
      message: 'Erro ao consultar frota de ônibus.'
    })
  } finally {
    loadingOnibus.value = false
  }
}

const fetchMotoristas = async () => {
  loadingMotoristas.value = true
  errorMotoristas.value = null
  try {
    const res = await api.get('/motoristas/')
    motoristasList.value = res.data?.results || res.data || []
  } catch (error) {
    const msg = error.response?.data?.detail ||
                error.response?.data?.erro ||
                'Falha ao consultar condutores autorizados.'
    errorMotoristas.value = msg
    $q.notify({
      type: 'negative',
      icon: 'warning',
      message: 'Erro ao consultar motoristas.'
    })
  } finally {
    loadingMotoristas.value = false
  }
}

const fetchRotas = async () => {
  loadingRotas.value = true
  errorRotas.value = null
  try {
    const res = await api.get('/rotas/')
    rotasList.value = res.data?.results || res.data || []
  } catch (error) {
    const msg = error.response?.data?.detail ||
                error.response?.data?.erro ||
                'Falha ao consultar itinerários de rotas municipais.'
    errorRotas.value = msg
    $q.notify({
      type: 'negative',
      icon: 'warning',
      message: 'Erro ao consultar rotas municipais.'
    })
  } finally {
    loadingRotas.value = false
  }
}

const toggleStatusOnibus = (bus) => {
  const novoStatus = !bus.ativo
  const acaoTexto = novoStatus ? 'ativar' : 'inativar'
  $q.dialog({
    title: `${novoStatus ? 'Ativar' : 'Inativar'} Veículo`,
    message: `Deseja realmente ${acaoTexto} o ônibus com placa ${bus.placa}? ${!novoStatus ? 'Ele não poderá ser alocado para novas viagens.' : ''}`,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-5' },
    ok: { label: 'Confirmar', color: novoStatus ? 'primary' : 'negative' },
    dark: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.patch(`/veiculos/onibus/${bus.id}/`, { ativo: novoStatus })
      bus.ativo = novoStatus
      $q.notify({
        type: 'positive',
        icon: 'check_circle',
        message: `Status do veículo ${bus.placa} atualizado para ${novoStatus ? 'Em Operação' : 'Inativo'}.`
      })
    } catch (err) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: err.response?.data?.detail || 'Erro ao atualizar status do veículo.'
      })
    }
  })
}

const toggleStatusMotorista = (mot) => {
  const novoStatus = !mot.ativo
  const acaoTexto = novoStatus ? 'ativar' : 'inativar'
  $q.dialog({
    title: `${novoStatus ? 'Ativar' : 'Inativar'} Motorista`,
    message: `Deseja realmente ${acaoTexto} o motorista ${mot.nome}? ${!novoStatus ? 'Ele não poderá iniciar viagens operacionais.' : ''}`,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-5' },
    ok: { label: 'Confirmar', color: novoStatus ? 'primary' : 'negative' },
    dark: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.patch(`/motoristas/${mot.id}/`, { ativo: novoStatus })
      mot.ativo = novoStatus
      $q.notify({
        type: 'positive',
        icon: 'check_circle',
        message: `Motorista ${mot.nome} ${novoStatus ? 'ativado' : 'inativado'} com sucesso.`
      })
    } catch (err) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: err.response?.data?.detail || 'Erro ao atualizar status do motorista.'
      })
    }
  })
}

const toggleStatusRota = (rota) => {
  const novoStatus = !rota.ativo
  const acaoTexto = novoStatus ? 'ativar' : 'desativar'
  $q.dialog({
    title: `${novoStatus ? 'Ativar' : 'Desativar'} Rota`,
    message: `Deseja realmente ${acaoTexto} a rota "${rota.nome}"?`,
    cancel: { label: 'Cancelar', flat: true, color: 'grey-5' },
    ok: { label: 'Confirmar', color: novoStatus ? 'primary' : 'warning' },
    dark: true,
    persistent: true
  }).onOk(async () => {
    try {
      await api.patch(`/rotas/${rota.id}/`, { ativo: novoStatus })
      rota.ativo = novoStatus
      $q.notify({
        type: 'positive',
        icon: 'check_circle',
        message: `Rota ${rota.nome} ${novoStatus ? 'ativada' : 'desativada'} com sucesso.`
      })
    } catch (err) {
      $q.notify({
        type: 'negative',
        icon: 'error',
        message: err.response?.data?.detail || 'Erro ao atualizar status da rota.'
      })
    }
  })
}

const fetchModelos = async () => {
  try {
    const res = await api.get('/veiculos/modelos/')
    modelosRaw.value = res.data?.results || res.data || []
  } catch (error) {
    console.error('Erro ao buscar modelos:', error)
  }
}

const openNovoOnibusModal = () => {
  novoOnibus.placa = ''
  novoOnibus.capacidade = 44
  if (modelosOptions.value.length > 0) {
    novoOnibus.modelo = modelosOptions.value[0].value
  }
  showNovoOnibusModal.value = true
}

const salvarNovoOnibus = async () => {
  salvandoOnibus.value = true
  try {
    await api.post('/veiculos/onibus/', {
      placa: novoOnibus.placa.toUpperCase().trim(),
      modelo: novoOnibus.modelo,
      capacidade: novoOnibus.capacidade,
      ativo: true
    })
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: 'Veículo adicionado com sucesso!'
    })
    showNovoOnibusModal.value = false
    await fetchOnibus()
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: error.response?.data?.placa?.[0] || 'Erro ao cadastrar ônibus.'
    })
  } finally {
    salvandoOnibus.value = false
  }
}

const openNovoMotoristaModal = () => {
  novoMotorista.nome = ''
  novoMotorista.cpf = ''
  novoMotorista.data_nascimento = '1985-01-01'
  novoMotorista.cnh = ''
  novoMotorista.categoria_cnh = 'D'
  novoMotorista.email = ''
  novoMotorista.password = ''
  showNovoMotoristaModal.value = true
}

const salvarNovoMotorista = async () => {
  salvandoMotorista.value = true
  try {
    await api.post('/motoristas/', {
      nome: novoMotorista.nome.trim(),
      cpf: novoMotorista.cpf.trim(),
      data_nascimento: novoMotorista.data_nascimento,
      cnh: novoMotorista.cnh.trim(),
      categoria_cnh: novoMotorista.categoria_cnh,
      email: novoMotorista.email.trim().toLowerCase(),
      password: novoMotorista.password,
      ativo: true
    })
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: 'Motorista cadastrado com sucesso! Credenciais geradas.'
    })
    showNovoMotoristaModal.value = false
    await fetchMotoristas()
  } catch (error) {
    const errorMsg = error.response?.data?.email?.[0] ||
                     error.response?.data?.cpf?.[0] ||
                     error.response?.data?.cnh?.[0] ||
                     error.response?.data?.password?.[0] ||
                     error.response?.data?.detail ||
                     'Erro ao cadastrar motorista.'
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: errorMsg
    })
  } finally {
    salvandoMotorista.value = false
  }
}

const openNovaRotaModal = () => {
  novaRota.nome = ''
  showNovaRotaModal.value = true
}

const salvarNovaRota = async () => {
  salvandoRota.value = true
  try {
    await api.post('/rotas/', {
      nome: novaRota.nome.trim(),
      ativo: true
    })
    $q.notify({
      type: 'positive',
      icon: 'check_circle',
      message: 'Rota cadastrada com sucesso!'
    })
    showNovaRotaModal.value = false
    await fetchRotas()
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: error.response?.data?.nome?.[0] || 'Erro ao cadastrar rota.'
    })
  } finally {
    salvandoRota.value = false
  }
}

onMounted(() => {
  fetchOnibus()
  fetchMotoristas()
  fetchRotas()
  fetchModelos()
})
</script>

<style scoped lang="scss">
.vehicle-card {
  border-top: 3px solid #F2C037;
}

.placa-badge {
  background: #fff;
  color: #000;
  padding: 3px 8px;
  border-radius: 6px;
  font-family: monospace;
  font-weight: 900;
  letter-spacing: 1px;
  border: 2px solid #000;
  box-shadow: 0 2px 6px rgba(0,0,0,0.5);
}

.uuid-text {
  font-family: monospace;
  font-size: 0.7rem;
  word-break: break-all;
}

.border-danger {
  border: 1px solid rgba(193, 0, 21, 0.4);
}
</style>
