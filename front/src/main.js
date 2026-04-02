import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { initMana } from './composables/useMana'
import './style.css'

// Carrega símbolos de mana ANTES de montar a app
initMana().finally(() => {
  const app = createApp(App)
  app.use(createPinia())
  app.use(router)
  app.mount('#app')
})
