import { createApp } from 'vue'
import { createPinia } from 'pinia'

// Quasar Framework & Plugins
import { Quasar, Notify, Dialog, Loading, Dark } from 'quasar'
import quasarLang from 'quasar/lang/pt-BR.js'

// Importações de Estilo e Ícones Quasar
import '@quasar/extras/material-icons/material-icons.css'
import 'quasar/src/css/index.sass'
import './css/app.scss'

import App from './App.vue'
import router from './router'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

app.use(Quasar, {
  plugins: {
    Notify,
    Dialog,
    Loading,
    Dark
  },
  lang: quasarLang,
  config: {
    dark: true, // Força o modo escuro como padrão em toda a aplicação
    notify: {
      position: 'top',
      timeout: 3000,
      textColor: 'white'
    },
    loading: {
      spinnerColor: 'primary'
    }
  }
})

app.mount('#app')
