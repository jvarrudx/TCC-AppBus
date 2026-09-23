<template>
  <div class="container">
    <header class="header">
      <div class="badge">TCC - Ciência da Computação</div>
      <h1>AppBus</h1>
      <p class="subtitle">Sistema Inteligente de Transporte Universitário</p>
    </header>

    <main class="card">
      <h2>Status da Infraestrutura</h2>
      <div class="status-grid">
        <div class="status-item">
          <span class="dot success"></span>
          <div>
            <strong>Frontend (Vue 3 + Vite)</strong>
            <p>Serviço rodando na porta 5173</p>
          </div>
        </div>

        <div class="status-item">
          <span :class="['dot', backendStatus.ok ? 'success' : 'pending']"></span>
          <div>
            <strong>Backend (Django REST Framework)</strong>
            <p>{{ backendStatus.message }}</p>
          </div>
        </div>

        <div class="status-item">
          <span :class="['dot', backendStatus.dbOk ? 'success' : 'pending']"></span>
          <div>
            <strong>Banco de Dados (PostgreSQL 15+)</strong>
            <p>{{ backendStatus.dbMessage }}</p>
          </div>
        </div>
      </div>

      <button class="btn" @click="checkBackend">
        Testar Conexão com API Django
      </button>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const backendStatus = ref({
  ok: false,
  message: 'Aguardando verificação...',
  dbOk: false,
  dbMessage: 'Aguardando verificação...'
})

const checkBackend = async () => {
  backendStatus.value.message = 'Verificando...'
  try {
    const res = await axios.get('http://localhost:8000/api/health/')
    backendStatus.value.ok = res.data.status === 'healthy'
    backendStatus.value.message = `Conectado (${res.data.service})`
    backendStatus.value.dbOk = res.data.database.connected
    backendStatus.value.dbMessage = `PostgreSQL Conectado (${res.data.database.engine})`
  } catch (err) {
    backendStatus.value.ok = false
    backendStatus.value.message = 'Erro ao conectar à API Django na porta 8000'
    backendStatus.value.dbOk = false
    backendStatus.value.dbMessage = 'Não foi possível testar o banco via API'
  }
}

onMounted(() => {
  checkBackend()
})
</script>

<style>
:root {
  --primary: #2563eb;
  --primary-hover: #1d4ed8;
  --bg: #0f172a;
  --card-bg: #1e293b;
  --text: #f8fafc;
  --text-muted: #94a3b8;
  --success: #22c55e;
  --warning: #f59e0b;
}

body {
  margin: 0;
  font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
  background-color: var(--bg);
  color: var(--text);
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.container {
  max-width: 600px;
  width: 90%;
  padding: 2rem 0;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background-color: rgba(37, 99, 235, 0.2);
  color: #60a5fa;
  border-radius: 9999px;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 0.75rem;
}

h1 {
  font-size: 2.5rem;
  margin: 0 0 0.5rem 0;
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: var(--text-muted);
  font-size: 1rem;
  margin: 0;
}

.card {
  background-color: var(--card-bg);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.4);
}

.card h2 {
  font-size: 1.25rem;
  margin-top: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 0.75rem;
}

.status-grid {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  margin-bottom: 2rem;
}

.status-item {
  display: flex;
  align-items: flex-start;
  gap: 1rem;
}

.status-item p {
  margin: 0.25rem 0 0 0;
  font-size: 0.875rem;
  color: var(--text-muted);
}

.dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-top: 0.25rem;
  flex-shrink: 0;
}

.dot.success {
  background-color: var(--success);
  box-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
}

.dot.pending {
  background-color: var(--warning);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
}

.btn {
  width: 100%;
  padding: 0.85rem;
  background-color: var(--primary);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn:hover {
  background-color: var(--primary-hover);
}
</style>
