<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Grimório das Cartas</h1>
      <p class="page-hero-sub">
        {{ loading ? 'Consultando os arquivos arcanos...' : `${total.toLocaleString('pt-BR')} artefatos mágicos catalogados` }}
      </p>
      <div class="hero-divider"><span class="hero-divider-gem">❖</span></div>
    </div>

    <div class="page-wrap">
      <SearchBar
        :sets="sets"
        :initial-filters="initialFilters"
        @search="onSearch"
      />

      <div class="results-bar">
        <span class="results-info">
          Exibindo <strong>{{ cards.length }}</strong> de
          <strong>{{ total.toLocaleString('pt-BR') }}</strong> tomos
          <em v-if="activeFilters.q"> · "{{ activeFilters.q }}"</em>
          <em v-if="activeFilters.set && setName"> · {{ setName }}</em>
          <em v-if="activeFilters.type"> · {{ activeFilters.type }}</em>
        </span>
        <div class="results-right">
          <button
            v-if="activeFilters.set"
            class="btn-ghost export-set-btn"
            :disabled="exportando"
            :title="`Exportar toda a coleção ${setName || activeFilters.set} em JSON`"
            @click="exportarColecaoAtual"
          >{{ exportando ? '⏳ Exportando...' : '⬇ Exportar coleção (JSON)' }}</button>
          <span class="results-info">
            Página <strong>{{ page }}</strong> / <strong>{{ totalPages }}</strong>
          </span>
        </div>
      </div>

      <div v-if="loading" class="spinner-wrap">
        <div class="spinner"></div>
        <span class="spinner-text">Consultando o Grimório...</span>
      </div>

      <TransitionGroup v-else name="cards-grid" tag="div" class="cards-grid">
        <CardItem v-for="card in cards" :key="card.name" :card="card" />
      </TransitionGroup>

      <div v-if="loadError" class="load-error">⚠ {{ loadError }}</div>

      <div v-if="!loading && !loadError && cards.length === 0" class="no-results">
        <div class="no-results-title">✦ Nenhum Artefato Encontrado ✦</div>
        <p class="no-results-sub">Os arquivos do Nexus não revelam cartas para estes critérios.</p>
      </div>

      <Pagination :page="page" :total-pages="totalPages" @change="onPageChange" />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getCards, getSets, exportGameSet } from '@/composables/api'
import CardItem   from '@/components/CardItem.vue'
import SearchBar  from '@/components/SearchBar.vue'
import Pagination from '@/components/Pagination.vue'

const route  = useRoute()
const router = useRouter()

const cards        = ref([])
const sets         = ref([])
const total        = ref(0)
const totalPages   = ref(1)
const page         = ref(1)
const loading      = ref(false)
const loadError    = ref('')
const exportando   = ref(false)
const activeFilters = reactive({})

// Parâmetros aceitos na URL e repassados à API.
// Era uma lista fixa que não incluía os filtros novos (legendary, keywords,
// sort...): o SearchBar os emitia, iam para a URL e eram descartados aqui,
// então a API nunca os recebia.
const PARAMS = [
  'q', 'set', 'rarity', 'type', 'cmc', 'cmc_op', 'colors', 'color_mode',
  'legendary', 'nonlegendary', 'keywords', 'keyword_mode', 'sort',
  'date_from', 'date_to',
]

function paramsDaUrl(query) {
  const saida = {}
  for (const chave of PARAMS) saida[chave] = query[chave] || ''
  if (!saida.cmc_op) saida.cmc_op = '='
  if (!saida.sort)   saida.sort = 'release_desc'
  return saida
}

const initialFilters = computed(() => paramsDaUrl(route.query))

const setName = computed(() => sets.value.find(s => s.code === activeFilters.set)?.name || '')

async function fetchCards(filters) {
  loading.value = true
  loadError.value = ''
  Object.assign(activeFilters, filters)
  try {
    const { data } = await getCards({ ...filters, page: page.value })
    cards.value      = data.results
    total.value      = data.count
    totalPages.value = data.total_pages
  } catch (error) {
    console.error(error)
    cards.value = []
    total.value = 0
    totalPages.value = 1
    loadError.value = 'Não foi possível carregar as cartas. Verifique se a API está no ar.'
  } finally { loading.value = false }
}

async function fetchSets() {
  try { const { data } = await getSets(); sets.value = data.sets } catch {}
}

async function exportarColecaoAtual() {
  const code = activeFilters.set
  if (!code) return
  exportando.value = true
  try {
    const { data } = await exportGameSet(code)
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })),
      download: `colecao-${code}.json`,
    })
    a.click()
  } catch (erro) {
    alert('Não foi possível exportar esta coleção.')
  } finally {
    exportando.value = false
  }
}

function onSearch(filters) {
  // Só atualiza a URL: o watch abaixo é a única origem de fetch.
  // Antes o onSearch buscava E trocava a query, disparando duas requisições.
  router.push({ query: { ...cleanQuery(filters), page: 1 } })
}

function onPageChange(newPage) {
  router.push({ query: { ...route.query, page: newPage } })
}

function cleanQuery(filters) {
  // remove chaves vazias para a URL não ficar poluída
  return Object.fromEntries(Object.entries(filters).filter(([, value]) => value !== '' && value != null))
}

function filtersFromQuery(query) {
  return paramsDaUrl(query)
}

watch(() => route.query, (query) => {
  page.value = Math.max(1, parseInt(query.page, 10) || 1)
  fetchCards(filtersFromQuery(query))
}, { immediate: false })

onMounted(() => {
  fetchSets()
  page.value = Math.max(1, parseInt(route.query.page, 10) || 1)
  fetchCards(initialFilters.value)
})
</script>

<style scoped>
.cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 1.4rem;
}
.cards-grid-enter-active { transition: opacity 0.4s ease, transform 0.4s ease; }
.cards-grid-enter-from   { opacity: 0; transform: translateY(18px); }
.cards-grid-move         { transition: transform 0.4s ease; }
.results-bar   { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.4rem; flex-wrap:wrap; gap:10px; }
.results-right { display:flex; align-items:center; gap:14px; }
.export-set-btn { font-size:0.66rem; padding:6px 12px; white-space:nowrap; }
.results-info { font-family:'Cinzel',serif; font-size:0.72rem; letter-spacing:2px; color:var(--parchment-xdk); }
.results-info strong { color:var(--gold); }
.load-error   { text-align:center; padding:2.4rem 1rem; color:#e8b0b0; background:rgba(120,40,40,0.12); border:1px solid rgba(200,90,90,0.3); border-radius:3px; }
.no-results   { text-align:center; padding:5rem 2rem; }
.no-results-title { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); margin-bottom:1rem; }
.no-results-sub   { font-style:italic; color:var(--parchment-xdk); }
</style>
