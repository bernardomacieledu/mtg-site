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

/**
 * URL do símbolo no Scryfall, montada localmente.
 *
 * O mapa vindo da API depende do seed_symbols ter rodado com rede; quando vem
 * vazio, os custos apareciam como texto ({1}{R}) no lugar dos ícones. As URLs
 * do Scryfall são públicas e estáveis, e o navegador as carrega direto.
 *   {R} -> R.svg   {2/W} -> 2W.svg   {W/U} -> WU.svg   {T} -> T.svg
 */
export function symbolUrl(simbolo) {
  const codigo = simbolo
    .replace(/[{}]/g, '')
    .replace(/\//g, '')
    .toUpperCase()
  if (!codigo) return null
  return `https://svgs.scryfall.io/card-symbols/${encodeURIComponent(codigo)}.svg`
}

export function useMana() {
  function renderMana(text) {
    if (!text) return ''
    return text.replace(/\{([^}]+)\}/g, (match) => {
      const uri = symbols.value[match] || symbolUrl(match)
      return uri
        ? `<img src="${uri}" class="ms" alt="${match}" title="${match}">`
        : `<span class="mana-text">{${match.slice(1, -1)}}</span>`
    })
  }
  return { symbols, loaded, renderMana, symbolUrl }
}
