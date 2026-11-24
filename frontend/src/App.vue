<template>
  <router-view />
</template>

<script setup>
import { onMounted } from 'vue'
import { useQuasar } from 'quasar'

const $q = useQuasar()

// Garante o Dark Mode ativado por padrão em qualquer ambiente
onMounted(() => {
  $q.dark.set(true)
})
</script>

<style>
/* Reset base e transição suave */
#app {
  min-height: 100vh;
  background-color: #0B0F19;
  color: #F8FAFC;
}
</style>
