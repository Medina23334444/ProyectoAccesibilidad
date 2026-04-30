<script setup>
import {ref} from 'vue'
import api from './services/api' // Importamos el servicio que creaste

const archivo = ref(null)
const cargando = ref(false)
const pasoActual = ref('')
const resultadoHtml = ref(null)

const seleccionarArchivo = (e) => {
  archivo.value = e.target.files[0]
  resultadoHtml.value = null
}

const iniciarProceso = async () => {
  if (!archivo.value) return

  cargando.value = true
  try {
    // 1. Llamada al componente de VALIDACIÓN (RF01)
    pasoActual.value = 'Validando estructura del PDF...'
    const docValidado = await api.subirPDF(archivo.value)

    // 2. Llamada al componente de CONVERSIÓN (RF02)
    pasoActual.value = 'Generando versión HTML accesible...'
    const conversion = await api.convertirAHTML(docValidado.id)

    // 3. Resultado final
    resultadoHtml.value = conversion
    pasoActual.value = '¡Proceso completado con éxito!'

    // Abrir automáticamente el archivo generado
    window.open(`https://127.0.0.1:8000${conversion.url_archivo}`, '_blank')

  } catch (error) {
    pasoActual.value = 'Error: ' + (error.response?.data?.error || 'No se pudo conectar con el servidor')
    console.error(error)
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="app-wrapper">
    <div class="blob"></div>

    <div class="container">
      <header class="header">
        <div class="logo-unl">UNL</div>
        <h1>Gestor de Accesibilidad</h1>
        <p>Transformación inteligente de PDF a HTML Semántico</p>
      </header>

      <main class="main-card">
        <div class="upload-section">
          <input type="file" @change="seleccionarArchivo" accept=".pdf" id="file-input"
                 class="hidden-input"/>
          <label for="file-input" class="drop-zone" :class="{ 'file-selected': archivo }">
            <div class="icon">📁</div>
            <div class="text">
              <span class="main-text">{{
                  archivo ? archivo.name : 'Arrastra o selecciona un PDF'
                }}</span>
              <span class="sub-text" v-if="!archivo">Tamaño máximo recomendado: 10MB</span>
            </div>
          </label>

          <button @click="iniciarProceso" :disabled="!archivo || cargando" class="btn-primary">
            <span v-if="!cargando">Iniciar Conversión</span>
            <div v-else class="loader-container">
              <div class="spinner"></div>
              <span>Procesando...</span>
            </div>
          </button>
        </div>

        <transition name="fade">
          <div v-if="pasoActual" class="status-indicator">
            <div class="progress-line"
                 :class="{ 'loading': cargando, 'error': pasoActual.includes('Error') }"></div>
            <p :class="{ 'text-error': pasoActual.includes('Error') }">
              {{ pasoActual }}
            </p>
          </div>
        </transition>

        <transition name="slide-up">
          <div v-if="resultadoHtml" class="result-card">
            <div class="result-header">
              <span class="badge">Resultado Exitoso</span>
              <h3>Análisis de Estructura</h3>
            </div>

            <div class="stats-grid">
              <div class="stat-item">
                <span class="label">Etiquetas</span>
                <span class="value">{{ resultadoHtml.cantidad_etiquetas }}</span>
              </div>
              <div class="stat-item">
                <span class="label">Accesibilidad</span>
                <span class="value accent">{{ resultadoHtml.nivel_accesibilidad }}</span>
              </div>
            </div>

            <div class="action-area">
              <a :href="'https://127.0.0.1:8000' + resultadoHtml.url_archivo" target="_blank"
                 class="btn-view">
                👁️ Abrir Documento Accesible
              </a>
            </div>
          </div>
        </transition>
      </main>

      <footer class="footer">
        &copy; 2024 Universidad Nacional de Loja - Ingeniería en Sistemas
      </footer>
    </div>
  </div>
</template>


<style scoped>
/* Variables de color UNL */
:root {
  --primary: #1e40af; /* Azul UNL */
  --secondary: #42b883; /* Verde Vue */
  --bg-app: #f8fafc;
  --text-main: #1e293b;
  --error: #ef4444;
}

/* Nota: En algunos navegadores, dentro de <style scoped>,
   es mejor usar el selector del contenedor principal si :root falla */
.app-wrapper {
  --primary: #1e40af;
  --secondary: #42b883;
  --bg-app: #f8fafc;
  --text-main: #1e293b;
  --error: #ef4444;

  min-height: 100vh;
  background: var(--bg-app);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  position: relative;
  overflow: hidden;
}

/* Fondo decorativo */
.blob {
  position: absolute;
  width: 500px;
  height: 500px;
  background: linear-gradient(135deg, #dbeafe 0%, #f0fdf4 100%);
  filter: blur(80px);
  z-index: 0;
  top: -100px;
  right: -100px;
}

.container {
  width: 100%;
  max-width: 550px;
  z-index: 1;
}

.header {
  text-align: center;
  margin-bottom: 2rem;
}

.logo-unl {
  font-weight: 900;
  font-size: 1.5rem;
  color: var(--primary);
  letter-spacing: -1px;
}

h1 {
  color: var(--text-main);
  font-size: 1.8rem;
  margin: 0.5rem 0;
}

.main-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(10px);
  padding: 2rem;
  border-radius: 24px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.05), 0 10px 10px -5px rgba(0, 0, 0, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.5);
}

/* Zona de carga estilo Dropzone */
.drop-zone {
  border: 2px dashed #e2e8f0;
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.drop-zone:hover {
  border-color: var(--primary);
  background: #f1f5f9;
}

.file-selected {
  border-style: solid;
  border-color: var(--secondary);
  background: #f0fdf4;
}

.icon {
  font-size: 2.5rem;
}

.main-text {
  display: block;
  font-weight: 600;
  color: var(--text-main);
}

.sub-text {
  font-size: 0.8rem;
  color: #64748b;
}

.btn-primary {
  margin-top: 1.5rem;
  width: 100%;
  padding: 1rem;
  border-radius: 12px;
  border: none;
  background: var(--text-main);
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
}

.btn-primary:hover:not(:disabled) {
  background: #000;
  transform: translateY(-2px);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Indicador de carga */
.spinner {
  width: 18px;
  height: 18px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* Tarjeta de resultados */
.result-card {
  margin-top: 2rem;
  background: #fff;
  border-radius: 16px;
  padding: 1.5rem;
  border: 1px solid #e2e8f0;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin: 1.5rem 0;
}

.stat-item {
  background: #f8fafc;
  padding: 1rem;
  border-radius: 12px;
  text-align: center;
}

.stat-item .label {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
}

.stat-item .value {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-main);
}

.stat-item .value.accent {
  color: var(--primary);
}

.btn-view {
  display: block;
  text-align: center;
  background: var(--secondary);
  color: white;
  text-decoration: none;
  padding: 0.8rem;
  border-radius: 10px;
  font-weight: 600;
}

/* Animaciones */
.slide-up-enter-active, .fade-enter-active {
  transition: all 0.4s ease-out;
}

.slide-up-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-enter-from {
  opacity: 0;
}

.footer {
  text-align: center;
  margin-top: 2rem;
  font-size: 0.8rem;
  color: #94a3b8;
}

.hidden-input {
  display: none;
}
</style>

