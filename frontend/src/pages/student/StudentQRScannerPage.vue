<template>
  <div class="qr-scanner-page">
    <!-- BARRA SUPERIOR DE NAVEGAÇÃO -->
    <div class="row items-center justify-between q-mb-md">
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
        <q-icon name="qr_code_scanner" color="primary" size="24px" class="q-mr-xs" />
        Embarque Óptico
      </div>

      <q-btn
        flat
        round
        dense
        :icon="torchActive ? 'flash_on' : 'flash_off'"
        :color="torchActive ? 'primary' : 'grey-5'"
        :disable="!hasTorch"
        @click="toggleTorch"
      >
        <q-tooltip>{{ torchActive ? 'Desativar Lanterna' : 'Ativar Lanterna' }}</q-tooltip>
      </q-btn>
    </div>

    <!-- 1. TELA VERDE: SUCESSO DE EMBARQUE -->
    <transition name="fade-scale">
      <div v-if="embarqueSucesso" class="fullscreen-result success-screen q-pa-lg text-center flex flex-center">
        <q-card class="result-card bg-dark text-white q-pa-lg">
          <!-- Ícone animado pulsante -->
          <div class="icon-circle bg-positive q-mx-auto q-mb-md">
            <q-icon name="check_circle" size="64px" color="white" class="animate-bounce" />
          </div>

          <div class="text-h5 text-weight-bolder text-positive q-mb-xs">
            EMBARQUE CONFIRMADO!
          </div>
          <div class="text-caption text-grey-4 q-mb-md">
            Sua passagem foi validada e registrada no sistema do município.
          </div>

          <q-separator dark class="q-my-sm" />

          <!-- Detalhes do Embarque -->
          <div class="q-gutter-y-xs text-left q-py-sm">
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Linha / Rota:</span>
              <strong class="text-white">{{ embarqueData?.rota_nome || 'Linha Regular' }}</strong>
            </div>
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Veículo (Placa):</span>
              <strong class="text-primary">{{ embarqueData?.onibus_placa || '---' }}</strong>
            </div>
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Aluno:</span>
              <strong class="text-white">{{ embarqueData?.aluno_nome || authStore.userNome }}</strong>
            </div>
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Matrícula:</span>
              <span class="text-grey-3">{{ embarqueData?.matricula || authStore.alunoMatricula }}</span>
            </div>
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Horário:</span>
              <span class="text-grey-3">{{ formatDataHora(embarqueData?.timestamp) }}</span>
            </div>
            <div class="row justify-between text-body2">
              <span class="text-grey-5">Validação:</span>
              <span class="text-positive text-weight-bold">QR Code Óptico (App)</span>
            </div>
          </div>

          <q-banner rounded dense class="bg-grey-9 text-grey-3 text-caption q-mt-md text-left">
            <template v-slot:avatar>
              <q-icon name="info" color="primary" />
            </template>
            Apresente esta tela ao motorista caso solicitado durante a checagem no embarque.
          </q-banner>

          <div class="q-mt-lg q-gutter-y-sm">
            <q-btn
              color="primary"
              text-color="dark"
              class="full-width q-py-sm text-weight-bold"
              label="Concluir e Voltar ao Início"
              icon="home"
              no-caps
              to="/"
            />
            <q-btn
              flat
              color="grey-4"
              class="full-width q-py-sm"
              label="Efetuar Outro Embarque"
              icon="refresh"
              no-caps
              @click="resetScanner"
            />
          </div>
        </q-card>
      </div>
    </transition>

    <!-- 2. TELA VERMELHA: ERRO OU DUPLICIDADE DE EMBARQUE -->
    <transition name="fade-scale">
      <div v-if="embarqueErro" class="fullscreen-result error-screen q-pa-lg text-center flex flex-center">
        <q-card class="result-card bg-dark text-white q-pa-lg">
          <div class="icon-circle bg-negative q-mx-auto q-mb-md">
            <q-icon name="cancel" size="64px" color="white" class="animate-shake" />
          </div>

          <div class="text-h5 text-weight-bolder text-negative q-mb-xs">
            EMBARQUE NÃO AUTORIZADO
          </div>
          <div class="text-body2 text-grey-3 q-my-md q-pa-sm error-box">
            {{ erroMensagem }}
          </div>

          <div class="text-caption text-grey-5 q-mb-md">
            Verifique com o motorista ou confirme se este veículo possui uma viagem em andamento para o seu município.
          </div>

          <div class="q-mt-md q-gutter-y-sm">
            <q-btn
              color="negative"
              text-color="white"
              class="full-width q-py-sm text-weight-bold"
              label="Tentar Novamente"
              icon="refresh"
              no-caps
              @click="resetScanner"
            />
            <q-btn
              flat
              color="grey-4"
              class="full-width q-py-sm"
              label="Voltar ao Início"
              icon="home"
              no-caps
              to="/"
            />
          </div>
        </q-card>
      </div>
    </transition>

    <!-- 3. VIEWPORT DA CÂMERA E LEITOR ÓPTICO -->
    <div v-show="!embarqueSucesso && !embarqueErro" class="scanner-container">
      <q-card class="dark-card scanner-card q-pa-none overflow-hidden">
        <!-- ÁREA DO VÍDEO DO SCANNER -->
        <div class="camera-wrapper relative-position">
          <div id="appbus-qr-reader" class="qr-viewport"></div>

          <!-- MOLDURA DE MIRA HOLOGRÁFICA / SCANLINE -->
          <div v-if="isScanning" class="scanner-reticle-overlay">
            <div class="corner-bracket top-left"></div>
            <div class="corner-bracket top-right"></div>
            <div class="corner-bracket bottom-left"></div>
            <div class="corner-bracket bottom-right"></div>
            <div class="laser-scanline"></div>
          </div>

          <!-- Loading overlay durante validação do token com o backend -->
          <div v-if="validandoEmbarque" class="validation-overlay column items-center justify-center">
            <q-spinner-cube color="primary" size="52px" class="q-mb-md" />
            <div class="text-subtitle1 text-weight-bold text-white">Validando Embarque...</div>
            <div class="text-caption text-grey-4">Conferindo autenticidade e status da viagem</div>
          </div>
        </div>

        <!-- ORIENTAÇÃO AO USUÁRIO -->
        <div class="q-pa-md text-center bg-dark">
          <div class="text-subtitle2 text-weight-bold text-white q-mb-xs flex items-center justify-center">
            <q-icon name="center_focus_strong" color="primary" size="20px" class="q-mr-xs" />
            Aponte para o QR Code do Ônibus
          </div>
          <div class="text-caption text-grey-4">
            O código impresso fica fixado ao lado da porta de entrada do veículo.
          </div>
        </div>
      </q-card>

      <!-- ALERTA / CONTINGÊNCIA SE A CÂMERA FALHAR OU EM TESTES DE NAVEGADOR -->
      <div class="q-mt-md">
        <q-expansion-item
          dense
          dense-toggle
          expand-separator
          icon="tune"
          label="Simulação de Testes / Entrada Manual"
          header-class="text-grey-4 text-caption"
          class="dark-card rounded-borders"
        >
          <q-card class="bg-dark-page q-pa-md text-white">
            <p class="text-caption text-grey-4 q-mb-sm">
              Caso esteja em um navegador sem webcam ou para validação ágil, digite ou cole o UUID do QR Code do veículo:
            </p>

            <q-input
              v-model="manualUuid"
              outlined
              dense
              dark
              label="UUID do QR Code do Ônibus"
              placeholder="Ex: 12345678-1234-1234-1234-123456789abc"
              color="primary"
              class="q-mb-sm"
            >
              <template v-slot:prepend>
                <q-icon name="badge" color="primary" />
              </template>
            </q-input>

            <div class="row q-gutter-x-sm">
              <q-btn
                color="primary"
                text-color="dark"
                class="col text-weight-bold"
                label="Validar UUID Manual"
                icon="send"
                no-caps
                :loading="validandoEmbarque"
                :disable="!manualUuid"
                @click="onScanSuccess(manualUuid)"
              />

              <q-btn
                outline
                color="grey-4"
                label="Usar Ônibus em Viagem Ativa"
                icon="departure_board"
                no-caps
                :loading="buscandoViagem"
                @click="preencherOnibusAtivo"
              />
            </div>
          </q-card>
        </q-expansion-item>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useQuasar } from 'quasar'
import { Html5Qrcode } from 'html5-qrcode'
import { useAuthStore } from '../../stores/authStore'
import api from '../../boot/axios'

const $q = useQuasar()
const router = useRouter()
const authStore = useAuthStore()

const SCANNER_ELEMENT_ID = 'appbus-qr-reader'
let html5QrCode = null

// Estados do fluxo
const isScanning = ref(false)
const validandoEmbarque = ref(false)
const embarqueSucesso = ref(false)
const embarqueErro = ref(false)
const embarqueData = ref(null)
const erroMensagem = ref('')
const torchActive = ref(false)
const hasTorch = ref(false)

// Estados para teste manual
const manualUuid = ref('')
const buscandoViagem = ref(false)

const formatDataHora = (isoStr) => {
  if (!isoStr) return '--:--'
  try {
    const d = new Date(isoStr)
    return d.toLocaleString('pt-BR', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch (e) {
    return isoStr
  }
}

// Inicializa a câmera usando Html5Qrcode
const startScanner = async () => {
  await nextTick()
  try {
    if (!html5QrCode) {
      html5QrCode = new Html5Qrcode(SCANNER_ELEMENT_ID)
    }

    const config = {
      fps: 12,
      qrbox: { width: 250, height: 250 },
      aspectRatio: 1.0,
      experimentalFeatures: {
        useBarCodeDetectorIfSupported: true
      }
    }

    await html5QrCode.start(
      { facingMode: 'environment' },
      config,
      (decodedText) => {
        onScanSuccess(decodedText)
      },
      () => {
        // Quadro sem QR code, continua escaneando
      }
    )

    isScanning.value = true

    // Checa suporte a lanterna
    try {
      const capabilities = html5QrCode.getRunningTrackCapabilities()
      hasTorch.value = !!(capabilities && capabilities.torch)
    } catch (e) {
      hasTorch.value = false
    }
  } catch (err) {
    console.warn('Câmera indisponível ou permissão negada:', err)
    isScanning.value = false
  }
}

const stopScanner = async () => {
  if (html5QrCode && html5QrCode.isScanning) {
    try {
      await html5QrCode.stop()
      await html5QrCode.clear()
    } catch (e) {
      console.warn('Erro ao pausar scanner:', e)
    }
    isScanning.value = false
  }
}

const toggleTorch = async () => {
  if (!hasTorch.value || !html5QrCode) return
  try {
    torchActive.value = !torchActive.value
    await html5QrCode.applyVideoConstraints({
      advanced: [{ torch: torchActive.value }]
    })
  } catch (e) {
    console.warn('Falha ao alternar lanterna:', e)
  }
}

// Quando um QR Code é decodificado com sucesso
const onScanSuccess = async (qrCodeUuid) => {
  if (validandoEmbarque.value) return

  const uuidSanitizado = (qrCodeUuid || '').trim()
  if (!uuidSanitizado) return

  // Para o leitor óptico imediatamente para evitar leituras repetidas
  await stopScanner()

  // Feedback vibratório no celular
  try {
    if (window.navigator?.vibrate) {
      window.navigator.vibrate([100, 50, 100])
    }
  } catch (e) {
    // Ignora
  }

  validandoEmbarque.value = true
  embarqueSucesso.value = false
  embarqueErro.value = false
  erroMensagem.value = ''

  try {
    const response = await api.post('/operacao/embarque/qrcode/', {
      qr_code_uuid: uuidSanitizado
    })

    embarqueData.value = response.data
    embarqueSucesso.value = true

    // Notificação de sucesso
    $q.notify({
      type: 'positive',
      icon: 'verified',
      message: 'Embarque confirmado com sucesso!',
      position: 'top',
      timeout: 2500
    })
  } catch (error) {
    console.error('Erro na validação do embarque:', error)
    embarqueErro.value = true
    erroMensagem.value =
      error.response?.data?.erro ||
      'Não foi possível registrar o embarque. Verifique se o ônibus possui viagem ativa ou se você já embarcou.'

    $q.notify({
      type: 'negative',
      icon: 'block',
      message: erroMensagem.value,
      position: 'top',
      timeout: 3500
    })
  } finally {
    validandoEmbarque.value = false
  }
}

// Reinicia o leitor óptico após erro ou para novo embarque
const resetScanner = async () => {
  embarqueSucesso.value = false
  embarqueErro.value = false
  embarqueData.value = null
  erroMensagem.value = ''
  manualUuid.value = ''
  await startScanner()
}

// Utilitário de apoio para pré-preencher o UUID do ônibus ativo de hoje
const preencherOnibusAtivo = async () => {
  buscandoViagem.value = true
  try {
    const response = await api.get('/operacao/viagem/ativa/')
    if (response.data.ativa && response.data.viagem) {
      // Obter os dados completos do veículo
      const veiculoId = response.data.viagem.onibus_id
      const onibusResp = await api.get(`/veiculos/onibus/${veiculoId}/`)
      if (onibusResp.data?.qr_code_uuid) {
        manualUuid.value = onibusResp.data.qr_code_uuid
        $q.notify({
          type: 'positive',
          icon: 'directions_bus',
          message: `Ônibus ativo selecionado: ${response.data.viagem.onibus_placa}`
        })
      }
    } else {
      $q.notify({
        type: 'warning',
        icon: 'info',
        message: 'Nenhum ônibus em viagem ativa no seu município agora.'
      })
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'error',
      message: 'Falha ao consultar ônibus em viagem ativa.'
    })
  } finally {
    buscandoViagem.value = false
  }
}

onMounted(async () => {
  await startScanner()
})

onBeforeUnmount(async () => {
  await stopScanner()
})
</script>

<style scoped lang="scss">
.qr-scanner-page {
  max-width: 480px;
  margin: 0 auto;
}

.scanner-card {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  background: #0B0F19;
}

.camera-wrapper {
  width: 100%;
  min-height: 340px;
  background: #000000;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.qr-viewport {
  width: 100%;
  max-width: 100%;
  min-height: 340px;
}

/* Moldura holográfica de escaneamento */
.scanner-reticle-overlay {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 240px;
  height: 240px;
  pointer-events: none;
  border-radius: 12px;
}

.corner-bracket {
  position: absolute;
  width: 28px;
  height: 28px;
  border: 4px solid #F2C037;
}

.corner-bracket.top-left {
  top: 0;
  left: 0;
  border-right: none;
  border-bottom: none;
  border-top-left-radius: 8px;
}

.corner-bracket.top-right {
  top: 0;
  right: 0;
  border-left: none;
  border-bottom: none;
  border-top-right-radius: 8px;
}

.corner-bracket.bottom-left {
  bottom: 0;
  left: 0;
  border-right: none;
  border-top: none;
  border-bottom-left-radius: 8px;
}

.corner-bracket.bottom-right {
  bottom: 0;
  right: 0;
  border-left: none;
  border-top: none;
  border-bottom-right-radius: 8px;
}

.laser-scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 3px;
  background: linear-gradient(90deg, transparent, #F2C037, transparent);
  box-shadow: 0 0 12px #F2C037;
  animation: scan 2.2s ease-in-out infinite alternate;
}

@keyframes scan {
  0% {
    top: 5%;
  }
  100% {
    top: 95%;
  }
}

.validation-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(11, 15, 25, 0.92);
  z-index: 10;
}

/* Telas cheias de feedback (Sucesso / Erro) */
.fullscreen-result {
  min-height: 80vh;
}

.result-card {
  width: 100%;
  max-width: 440px;
  border-radius: 20px;
  box-shadow: 0 15px 35px rgba(0, 0, 0, 0.7);
}

.success-screen .result-card {
  border: 2px solid #21BA45;
}

.error-screen .result-card {
  border: 2px solid #C10015;
}

.icon-circle {
  width: 88px;
  height: 88px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-box {
  background: rgba(193, 0, 21, 0.12);
  border: 1px solid rgba(193, 0, 21, 0.3);
  border-radius: 8px;
}

.animate-bounce {
  animation: bounce 1.2s infinite;
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8px);
  }
}

.animate-shake {
  animation: shake 0.6s cubic-bezier(0.36, 0.07, 0.19, 0.97) both;
}

@keyframes shake {
  10%, 90% {
    transform: translate3d(-1px, 0, 0);
  }
  20%, 80% {
    transform: translate3d(2px, 0, 0);
  }
  30%, 50%, 70% {
    transform: translate3d(-4px, 0, 0);
  }
  40%, 60% {
    transform: translate3d(4px, 0, 0);
  }
}

.fade-scale-enter-active,
.fade-scale-leave-active {
  transition: all 0.25s ease-out;
}

.fade-scale-enter-from,
.fade-scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
