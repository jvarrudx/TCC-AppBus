<template>
  <div class="app-container">
    <header class="app-header">
      <h1>AppBus</h1>
      <p>Sistema de Gestão de Transporte Intermunicipal</p>
    </header>
    <main class="app-main">
      <div class="card">
        <h2>Estrutura Inicial Carregada com Sucesso!</h2>
        <p>O ambiente Docker está configurado e pronto para o desenvolvimento.</p>
        <div class="status-indicator">
          <span class="dot live"></span>
          <span>Frontend rodando no Vite</span>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
// Componente principal inicial
</script>

<style>
:root {
  --primary-color: #3b82f6;
  --bg-color: #0f172a;
  --card-bg: #1e293b;
  --text-color: #f8fafc;
  --text-muted: #94a3b8;
}

body {
  margin: 0;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  background-color: var(--bg-color);
  color: var(--text-color);
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.app-container {
  max-width: 600px;
  width: 100%;
  padding: 2rem;
  text-align: center;
}

.app-header h1 {
  font-size: 3rem;
  margin: 0;
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.app-header p {
  color: var(--text-muted);
  margin-top: 0.5rem;
}

.app-main {
  margin-top: 2rem;
}

.card {
  background-color: var(--card-bg);
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.card h2 {
  margin-top: 0;
  font-size: 1.25rem;
}

.card p {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1.5rem;
  padding: 0.5rem 1rem;
  background-color: rgba(59, 130, 246, 0.1);
  border-radius: 9999px;
  font-size: 0.85rem;
  color: var(--primary-color);
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #22c55e;
  position: relative;
}

.dot.live::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background-color: #22c55e;
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(2.5);
    opacity: 0;
  }
}
</style>
