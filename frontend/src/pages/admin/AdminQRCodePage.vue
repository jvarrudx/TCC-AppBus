<template>
  <q-page class="q-py-md">
    <!-- Header Não Imprimível -->
    <div class="no-print row items-center justify-between q-mb-md">
      <div>
        <div class="row items-center">
          <q-btn flat round dense icon="arrow_back" color="grey-4" class="q-mr-sm" @click="$router.push('/admin/frota')" />
          <h1 class="text-h5 text-weight-bold text-white q-my-none">
            Emissão de <span class="text-primary">QR Code do Veículo</span>
          </h1>
        </div>
        <p class="text-caption text-grey-5 q-mt-xs q-mb-none">
          Gere o cartaz de embarque com o UUID do ônibus para afixação e leitura óptica
        </p>
      </div>

      <div class="row q-gutter-x-sm">
        <q-btn
          color="primary"
          text-color="dark"
          icon="print"
          label="Imprimir Cartaz (PDF)"
          class="btn-bus-primary text-weight-bold"
          no-caps
          :disable="!selectedOnibus"
          @click="imprimirCartaz"
        />
        <q-btn
          outline
          color="primary"
          icon="download"
          label="Baixar PNG"
          no-caps
          :disable="!selectedOnibus"
          @click="baixarPng"
        />
      </div>
    </div>

    <!-- Seletor do Veículo (Não Imprimível) -->
    <q-card class="no-print dark-card q-pa-md q-mb-lg">
      <div class="row q-col-gutter-md items-center">
        <div class="col-12 col-md-6">
          <q-select
            v-model="selectedOnibusId"
            :options="onibusOptions"
            emit-value
            map-options
            outlined
            dark
            dense
            label="Selecione o Ônibus da Frota *"
            color="primary"
            :loading="loading"
            @update:model-value="generateQRCode"
          >
            <template v-slot:no-option>
              <q-item>
                <q-item-section class="text-grey">Nenhum ônibus cadastrado na frota</q-item-section>
              </q-item>
            </template>
          </q-select>
        </div>

        <div v-if="selectedOnibus" class="col-12 col-md-6 row items-center q-gutter-x-md text-caption text-grey-4">
          <div>
            Placa: <strong class="text-white">{{ selectedOnibus.placa }}</strong>
          </div>
          <div>
            Capacidade: <strong class="text-white">{{ selectedOnibus.capacidade }} Lugares</strong>
          </div>
          <div>
            Modelo: <strong class="text-white">{{ selectedOnibus.modelo_detalhe?.marca }} {{ selectedOnibus.modelo_detalhe?.nome }}</strong>
          </div>
        </div>
      </div>
    </q-card>

    <!-- Área de Visualização e Impressão do Cartaz A4 Oficial -->
    <div class="poster-container flex flex-center">
      <div v-if="selectedOnibus" id="printable-poster" class="a4-poster shadow-10">
        <!-- Topo do Cartaz -->
        <div class="poster-header text-center">
          <div class="poster-badge q-mb-sm">
            <q-icon name="directions_bus" size="36px" color="dark" />
          </div>
          <div class="poster-system-title">SISTEMA APPBUS</div>
          <div class="poster-main-title">TRANSPORTE UNIVERSITÁRIO</div>
          <div class="poster-subtitle">EMBARQUE DIGITAL VIA QR CODE</div>
        </div>

        <div class="poster-divider"></div>

        <!-- Dados do Veículo -->
        <div class="vehicle-info-box text-center">
          <div class="placa-display">{{ selectedOnibus.placa }}</div>
          <div class="vehicle-model">{{ selectedOnibus.modelo_detalhe?.marca }} {{ selectedOnibus.modelo_detalhe?.nome }}</div>
          <div class="vehicle-capacity">Capacidade Autorizada: {{ selectedOnibus.capacidade }} passageiros sentados</div>
        </div>

        <!-- Canvas do QR Code Central -->
        <div class="qr-canvas-wrapper text-center">
          <canvas ref="qrCanvas" class="qr-canvas"></canvas>
        </div>

        <!-- Instruções ao Estudante -->
        <div class="poster-instructions text-center">
          <div class="instruction-title">COMO REALIZAR SEU EMBARQUE:</div>
          <ol class="instruction-steps">
            <li>Abra o aplicativo <strong>AppBus</strong> no seu celular.</li>
            <li>Acesse a opção <strong>"Embarcar"</strong> no painel inicial.</li>
            <li>Aponte a câmera para este QR Code para registrar sua viagem.</li>
          </ol>
        </div>

        <div class="poster-divider"></div>

        <!-- Rodapé de Auditoria e UUID -->
        <div class="poster-footer text-center">
          <div class="uuid-hash">ID DO VEÍCULO: {{ selectedOnibus.qr_code_uuid }}</div>
          <div class="compliance-text">Em conformidade com a LGPD • Registro Digital Auditável do Transporte Municipal</div>
        </div>
      </div>

      <!-- Estado Quando Nenhum Ônibus Está Selecionado -->
      <div v-else class="text-center q-pa-xl dark-card rounded-borders full-width" style="max-width: 500px;">
        <q-icon name="qr_code_scanner" size="64px" color="grey-7" class="q-mb-sm" />
        <div class="text-h6 text-grey-4">Nenhum veículo selecionado</div>
        <p class="text-caption text-grey-5">
          Selecione um ônibus no menu acima para gerar o cartaz oficial de leitura óptica.
        </p>
      </div>
    </div>
  </q-page>
</template>

<script setup>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useQuasar } from 'quasar'
import QRCode from 'qrcode'
import api from '../../boot/axios'

const $q = useQuasar()
const route = useRoute()

const loading = ref(false)
const onibusList = ref([])
const selectedOnibusId = ref(null)
const qrCanvas = ref(null)

const selectedOnibus = computed(() => {
  return onibusList.value.find(b => b.id === selectedOnibusId.value) || null
})

const onibusOptions = computed(() => {
  return onibusList.value.map(b => ({
    label: `${b.placa} - ${b.modelo_detalhe?.marca || ''} ${b.modelo_detalhe?.nome || ''} (${b.capacidade} lug)`,
    value: b.id
  }))
})

const fetchOnibus = async () => {
  loading.value = true
  try {
    const res = await api.get('/veiculos/onibus/')
    onibusList.value = res.data?.results || res.data || []
    
    // Se veio id pela rota, seleciona
    if (route.query.onibusId) {
      const targetId = Number(route.query.onibusId)
      if (onibusList.value.some(b => b.id === targetId)) {
        selectedOnibusId.value = targetId
      }
    } else if (onibusList.value.length > 0) {
      selectedOnibusId.value = onibusList.value[0].id
    }

    if (selectedOnibusId.value) {
      await nextTick()
      generateQRCode()
    }
  } catch (error) {
    $q.notify({
      type: 'negative',
      icon: 'warning',
      message: 'Erro ao consultar lista de ônibus.'
    })
  } finally {
    loading.value = false
  }
}

const generateQRCode = async () => {
  if (!selectedOnibus.value) return
  await nextTick()
  if (!qrCanvas.value) return

  const uuidPayload = selectedOnibus.value.qr_code_uuid
  try {
    await QRCode.toCanvas(qrCanvas.value, String(uuidPayload), {
      width: 280,
      margin: 2,
      color: {
        dark: '#000000',
        light: '#ffffff'
      },
      errorCorrectionLevel: 'H'
    })
  } catch (err) {
    console.error('Falha ao renderizar QR Code:', err)
  }
}

const imprimirCartaz = () => {
  window.print()
}

const baixarPng = () => {
  if (!qrCanvas.value || !selectedOnibus.value) return
  const link = document.createElement('a')
  link.download = `qrcode_onibus_${selectedOnibus.value.placa}.png`
  link.href = qrCanvas.value.toDataURL('image/png')
  link.click()
}

onMounted(() => {
  fetchOnibus()
})
</script>

<style scoped lang="scss">
.poster-container {
  width: 100%;
}

/* Cartaz A4 Estilizado */
.a4-poster {
  width: 100%;
  max-width: 540px;
  background: #ffffff;
  color: #111111;
  padding: 32px 28px;
  border-radius: 12px;
  border: 4px solid #F2C037;
  font-family: 'Roboto', -apple-system, sans-serif;
}

.poster-header {
  .poster-badge {
    background: #F2C037;
    width: 58px;
    height: 58px;
    line-height: 58px;
    border-radius: 16px;
    margin: 0 auto 8px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .poster-system-title {
    font-size: 0.85rem;
    font-weight: 800;
    letter-spacing: 2px;
    color: #666;
  }
  .poster-main-title {
    font-size: 1.5rem;
    font-weight: 900;
    color: #111;
    letter-spacing: 0.5px;
  }
  .poster-subtitle {
    font-size: 0.9rem;
    font-weight: 700;
    color: #c99308;
    letter-spacing: 1px;
  }
}

.poster-divider {
  height: 2px;
  background: #e2e8f0;
  margin: 18px 0;
}

.vehicle-info-box {
  background: #f8fafc;
  padding: 12px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;

  .placa-display {
    font-family: monospace;
    font-size: 1.8rem;
    font-weight: 900;
    letter-spacing: 3px;
    color: #000;
  }
  .vehicle-model {
    font-weight: 700;
    font-size: 1rem;
    color: #334155;
  }
  .vehicle-capacity {
    font-size: 0.8rem;
    color: #64748b;
  }
}

.qr-canvas-wrapper {
  margin: 20px auto;
  padding: 12px;
  background: #ffffff;
  display: inline-block;
  border: 2px solid #000;
  border-radius: 10px;

  .qr-canvas {
    display: block;
    max-width: 100%;
    height: auto;
  }
}

.poster-instructions {
  background: #fffbeb;
  border: 1px solid #fde68a;
  border-radius: 8px;
  padding: 14px;

  .instruction-title {
    font-weight: 900;
    font-size: 0.85rem;
    color: #92400e;
    margin-bottom: 6px;
  }
  .instruction-steps {
    text-align: left;
    margin: 0;
    padding-left: 20px;
    font-size: 0.85rem;
    color: #78350f;
    line-height: 1.5;
  }
}

.poster-footer {
  .uuid-hash {
    font-family: monospace;
    font-size: 0.75rem;
    font-weight: 700;
    color: #334155;
    word-break: break-all;
  }
  .compliance-text {
    font-size: 0.7rem;
    color: #94a3b8;
    margin-top: 4px;
  }
}

/* Regras de Impressão A4 Limpa */
@media print {
  body * {
    visibility: hidden;
  }
  .no-print {
    display: none !important;
  }
  #printable-poster, #printable-poster * {
    visibility: visible;
  }
  #printable-poster {
    position: absolute;
    left: 0;
    top: 0;
    width: 100% !important;
    max-width: 100% !important;
    border: none !important;
    box-shadow: none !important;
    padding: 0 !important;
  }
}
</style>
