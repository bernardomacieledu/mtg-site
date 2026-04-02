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
        <span class="results-info">
          Página <strong>{{ page }}</strong> / <strong>{{ totalPages }}</strong>
        </span>
      </div>

      <div v-if="loading" class="spinner-wrap">
        <div class="spinner"></div>
        <span class="spinner-text">Consultando o Grimório...</span>
      </div>

      <TransitionGroup v-else name="cards-grid" tag="div" class="cards-grid">
        <CardItem v-for="card in cards" :key="card.name" :card="card" />
      </TransitionGroup>

      <div v-if="!loading && cards.length === 0" class="no-results">
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
import { getCards, getSets } from '@/composables/api'
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
const activeFilters = reactive({})

// Lê filtros iniciais da URL
const initialFilters = computed(() => ({
  q: route.query.q || '', set: route.query.set || '',
  rarity: route.query.rarity || '', type: route.query.type || '',
  cmc: route.query.cmc || '', cmc_op: route.query.cmc_op || '=',
  colors: route.query.colors || '',
  date_from: route.query.date_from || '', date_to: route.query.date_to || '',
}))

const setName = computed(() => sets.value.find(s => s.code === activeFilters.set)?.name || '')

async function fetchCards(filters) {
  loading.value = true
  Object.assign(activeFilters, filters)
  try {
    const { data } = await getCards({ ...filters, page: page.value })
    cards.value      = data.results
    total.value      = data.count
    totalPages.value = data.total_pages
  } catch (e) { console.error(e) }
  finally { loading.value = false }
}

async function fetchSets() {
  try { const { data } = await getSets(); sets.value = data.sets } catch {}
}

function onSearch(f) {
  page.value = 1
  router.replace({ query: { ...f } })
  fetchCards(f)
}

function onPageChange(p) { page.value = p; fetchCards(activeFilters) }

watch(() => route.query, (q) => {
  fetchCards({
    q: q.q || '', set: q.set || '', rarity: q.rarity || '',
    type: q.type || '', cmc: q.cmc || '', cmc_op: q.cmc_op || '=',
    colors: q.colors || '', date_from: q.date_from || '', date_to: q.date_to || '',
  })
}, { immediate: false })

onMounted(() => {
  fetchSets()
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
.results-bar  { display:flex; align-items:center; justify-content:space-between; margin-bottom:1.4rem; }
.results-info { font-family:'Cinzel',serif; font-size:0.72rem; letter-spacing:2px; color:var(--parchment-xdk); }
.results-info strong { color:var(--gold); }
.no-results   { text-align:center; padding:5rem 2rem; }
.no-results-title { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); margin-bottom:1rem; }
.no-results-sub   { font-style:italic; color:var(--parchment-xdk); }
</style>
