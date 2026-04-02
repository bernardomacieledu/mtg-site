import { ref } from 'vue'
import { getManaSymbols } from './api'

// Singleton global — carregado uma vez, reativo em toda a app
const symbols  = ref({})
const loaded   = ref(false)
let   loadPromise = null

export async function initMana() {
  if (loaded.value) return
  if (loadPromise) return loadPromise
  loadPromise = getManaSymbols()
    .then(({ data }) => { symbols.value = data.symbols || {} })
    .catch(() => { symbols.value = {} })
    .finally(() => { loaded.value = true })
  return loadPromise
}

export function useMana() {
  function renderMana(text) {
    if (!text) return ''
    return text.replace(/\{([^}]+)\}/g, (match) => {
      const uri = symbols.value[match]
      return uri
        ? `<img src="${uri}" class="ms" alt="${match}" title="${match}">`
        : `<span class="mana-text">{${match.slice(1,-1)}}</span>`
    })
  }
  return { symbols, loaded, renderMana }
}
