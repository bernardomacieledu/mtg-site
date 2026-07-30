<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Coleções</h1>
      <p class="page-hero-sub">
        {{ loading ? 'Consultando os arquivos arcanos...'
                   : `${totalSets} coleções · ${totalCards.toLocaleString('pt-BR')} cartas catalogadas` }}
      </p>
      <div class="hero-divider"><span class="hero-divider-gem">❖</span></div>
    </div>

    <div class="page-wrap">
      <!-- Controles -->
      <div class="sets-controls">
        <input
          v-model="query"
          class="medieval-input"
          placeholder="Buscar por nome (Bloomburrow) ou código (BLB)..."
          @keyup.enter="fetchSets"
        />
        <div class="year-chips">
          <button class="year-chip" :class="{ active: !year }" @click="selectYear('')">Todas</button>
          <button
            v-for="y in visibleYears"
            :key="y"
            class="year-chip"
            :class="{ active: year === y }"
            @click="selectYear(y)"
          >{{ y }}</button>
        </div>
      </div>

      <div v-if="loading" class="spinner-wrap">
        <div class="spinner"></div>
        <span class="spinner-text">Abrindo os arquivos...</span>
      </div>

      <template v-else>
        <!-- Próximos lançamentos (coleções anunciadas, ainda não lançadas) -->
        <section v-if="!query && !year && upcoming.length" class="latest-block">
          <div class="section-head">
            <h2 class="section-title upcoming-title">⌛ Próximos Lançamentos ⌛</h2>
            <span class="section-sub">Coleções anunciadas — cartas reveladas até agora</span>
          </div>

          <div class="latest-grid">
            <article
              v-for="set in upcoming"
              :key="set.code"
              class="set-tile featured upcoming"
              @click="openSet(set)"
            >
              <span class="upcoming-badge">{{ daysUntil(set.released_at) }}</span>
              <button
                class="set-export-btn upcoming-export"
                title="Exportar cartas reveladas até agora, em JSON"
                :disabled="exportando === set.code"
                @click.stop="exportarSet(set)"
              >{{ exportando === set.code ? '⏳' : '⬇' }}</button>
              <img
                v-if="hasIcon(set)"
                :src="set.icon_svg_uri"
                :alt="set.code"
                class="set-tile-icon"
                @error="markIconFailed(set.code)"
              />
              <div v-else class="set-monogram">{{ set.code.toUpperCase() }}</div>
              <div class="set-tile-body">
                <h3 class="set-tile-name">{{ set.name }}</h3>
                <div class="set-tile-meta">
                  <span class="set-code-badge">{{ set.code.toUpperCase() }}</span>
                  <span>{{ formatDate(set.released_at) }}</span>
                </div>
                <div class="set-tile-count">
                  {{ set.unique_count.toLocaleString('pt-BR') }} cartas reveladas
                </div>
              </div>
              <div class="set-tile-cta">Ver cartas ▸</div>
            </article>
          </div>
        </section>

        <!-- Lançamentos recentes -->
        <section v-if="!query && !year && latest.length" class="latest-block">
          <div class="section-head">
            <h2 class="section-title">✦ Lançamentos Recentes ✦</h2>
            <span class="section-sub">As coleções mais novas do multiverso</span>
          </div>

          <div class="latest-grid">
            <article
              v-for="(set, index) in latest"
              :key="set.code"
              class="set-tile featured"
              :class="{ newest: index === 0 }"
              @click="openSet(set)"
            >
              <span v-if="index === 0" class="newest-badge">MAIS RECENTE</span>
              <img
                v-if="hasIcon(set)"
                :src="set.icon_svg_uri"
                :alt="set.code"
                class="set-tile-icon"
                @error="markIconFailed(set.code)"
              />
              <div v-else class="set-monogram">{{ set.code.toUpperCase() }}</div>
              <div class="set-tile-body">
                <h3 class="set-tile-name">{{ set.name }}</h3>
                <div class="set-tile-meta">
                  <span class="set-code-badge">{{ set.code.toUpperCase() }}</span>
                  <span>{{ formatDate(set.released_at) }}</span>
                </div>
                <div class="set-tile-count">
                  {{ set.unique_count.toLocaleString('pt-BR') }} cartas
                </div>
              </div>
              <button
                class="set-export-btn"
                title="Exportar coleção em JSON"
                :disabled="exportando === set.code"
                @click.stop="exportarSet(set)"
              >{{ exportando === set.code ? '⏳' : '⬇' }}</button>
              <div class="set-tile-cta">Ver cartas ▸</div>
            </article>
          </div>
        </section>

        <!-- Resultado da busca / listagem por ano -->
        <section v-for="group in years" :key="group.year" class="year-block">
          <div class="year-head">
            <span class="year-label">{{ group.year }}</span>
            <span class="year-count">{{ group.sets.length }} coleções</span>
            <div class="year-rule"></div>
          </div>

          <div class="sets-grid">
            <article
              v-for="set in group.sets"
              :key="set.code"
              class="set-tile"
              @click="openSet(set)"
            >
              <img
                v-if="hasIcon(set)"
                :src="set.icon_svg_uri"
                :alt="set.code"
                class="set-tile-icon sm"
                @error="markIconFailed(set.code)"
              />
              <div v-else class="set-monogram sm">{{ set.code.toUpperCase() }}</div>
              <button
                class="set-export-btn sm"
                title="Exportar coleção em JSON"
                :disabled="exportando === set.code"
                @click.stop="exportarSet(set)"
              >{{ exportando === set.code ? '⏳' : '⬇' }}</button>
              <div class="set-tile-body">
                <h3 class="set-tile-name sm" :title="`${set.name} (${set.code.toUpperCase()})`">
                  {{ set.name }}
                </h3>
                <div class="set-tile-meta">
                  <span class="set-code-badge">{{ set.code.toUpperCase() }}</span>
                  <span>{{ formatDate(set.released_at) }}</span>
                  <span class="meta-count">· {{ set.unique_count }} cartas</span>
                </div>
              </div>
              <div class="set-tile-qty">{{ set.unique_count }}</div>
            </article>
          </div>
        </section>

        <div v-if="!years.length" class="no-results">
          <div class="no-results-title">✦ Nenhuma Coleção Encontrada ✦</div>
          <p class="no-results-sub">Tente outro termo de busca ou remova o filtro de ano.</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { getCollections, exportGameSet } from '@/composables/api'

const router = useRouter()

const latest        = ref([])
const upcoming      = ref([])
const years         = ref([])
const availableYears = ref([])
const visibleYears  = ref([])
const totalSets     = ref(0)
const totalCards    = ref(0)
const loading       = ref(true)
const query         = ref('')
const year          = ref('')

let debounceTimer = null

async function fetchSets() {
  loading.value = true
  try {
    const { data } = await getCollections({ q: query.value, year: year.value, limit: 12 })
    latest.value          = data.latest || []
    upcoming.value        = data.upcoming || []
    years.value           = data.years || []
    totalSets.value       = data.total_sets || 0
    totalCards.value      = data.total_cards || 0
    availableYears.value  = data.available_years || []
    // mantém a lista de anos estável mesmo quando um filtro reduz o resultado
    if (!query.value && !year.value) visibleYears.value = availableYears.value.slice(0, 14)
  } catch (error) {
    console.error(error)
    latest.value = []
    upcoming.value = []
    years.value = []
  } finally {
    loading.value = false
  }
}

function selectYear(value) {
  year.value = year.value === value ? '' : value
  fetchSets()
}

function openSet(set) {
  router.push({ name: 'cards', query: { set: set.code } })
}

const exportando = ref('')

async function exportarSet(set) {
  exportando.value = set.code
  try {
    const { data } = await exportGameSet(set.code)
    const a = Object.assign(document.createElement('a'), {
      href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })),
      download: `colecao-${set.code}.json`,
    })
    a.click()
  } catch (erro) {
    alert('Não foi possível exportar esta coleção.')
  } finally {
    exportando.value = ''
  }
}

const iconesQuebrados = ref(new Set())

function hasIcon(set) {
  return !!set.icon_svg_uri && !iconesQuebrados.value.has(set.code)
}

function markIconFailed(code) {
  // Nem toda coleção tem ícone publicado; em vez de deixar um vazio,
  // exibimos o código como monograma.
  iconesQuebrados.value = new Set(iconesQuebrados.value).add(code)
}

function daysUntil(value) {
  if (!value) return 'EM BREVE'
  const dias = Math.ceil((new Date(value) - new Date()) / 86400000)
  if (dias <= 0) return 'HOJE'
  if (dias === 1) return 'AMANHÃ'
  if (dias <= 60) return `EM ${dias} DIAS`
  return 'EM BREVE'
}

function formatDate(value) {
  if (!value) return 'Data desconhecida'
  const [y, m, d] = value.split('-')
  return `${d}/${m}/${y}`
}

watch(query, () => {
  clearTimeout(debounceTimer)
  debounceTimer = setTimeout(fetchSets, 350)
})

onMounted(fetchSets)
</script>

<style scoped>
.sets-controls {
  display: flex; flex-wrap: wrap; gap: 1rem; align-items: center;
  margin-bottom: 2.2rem;
}
.sets-controls .medieval-input { flex: 1 1 300px; }

.year-chips { display: flex; flex-wrap: wrap; gap: 6px; }
.year-chip {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(184,134,11,0.25);
  color: var(--parchment-dk); border-radius: 2px; padding: 6px 11px;
  font-family: 'Cinzel', serif; font-size: 0.66rem; letter-spacing: 1px;
  cursor: pointer; transition: all 0.2s;
}
.year-chip:hover { border-color: var(--gold); color: var(--gold-shine); }
.year-chip.active { background: rgba(184,134,11,0.22); border-color: var(--gold); color: var(--gold-shine); }

.section-head { text-align: center; margin-bottom: 1.6rem; }
.section-title {
  font-family: 'Cinzel Decorative', serif; font-size: 1.25rem;
  color: var(--gold-shine); letter-spacing: 2px;
}
.section-sub { font-style: italic; font-size: 0.82rem; color: var(--parchment-xdk); }

.latest-block { margin-bottom: 3.4rem; }
.latest-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 1.1rem;
}
.sets-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 0.7rem;
}

.set-tile {
  display: flex; align-items: center; gap: 12px;
  background: linear-gradient(150deg, #1a130a 0%, #0f0b06 100%);
  border: 1px solid rgba(184,134,11,0.22); border-radius: 4px;
  padding: 12px 14px; cursor: pointer; position: relative;
  transition: transform 0.25s cubic-bezier(.23,1,.32,1), border-color 0.25s, box-shadow 0.25s;
}
.set-tile:hover {
  transform: translateY(-4px);
  border-color: var(--gold);
  box-shadow: 0 14px 28px rgba(0,0,0,0.55), 0 0 22px rgba(184,134,11,0.12);
}
.set-tile.featured { flex-direction: column; align-items: flex-start; padding: 20px 18px 16px; }
.set-tile.newest { border-color: rgba(184,134,11,0.6); box-shadow: 0 0 22px rgba(184,134,11,0.14); }

.upcoming-title { color: #9ec5e8; }
.set-tile.upcoming { border-color: rgba(120,170,220,0.45); }
.set-tile.upcoming:hover { border-color: #9ec5e8; box-shadow: 0 14px 28px rgba(0,0,0,0.55), 0 0 22px rgba(120,170,220,0.18); }
.set-tile.upcoming .set-tile-icon { filter: invert(0.85) sepia(0.15) hue-rotate(170deg); }
.upcoming-badge {
  position: absolute; top: 10px; right: 10px;
  font-family: 'Cinzel', serif; font-size: 0.5rem; letter-spacing: 2px;
  color: #0d1620; background: #9ec5e8;
  padding: 3px 7px; border-radius: 2px;
}

.set-export-btn {
  position: absolute; top: 10px; right: 10px; z-index: 2;
  width: 26px; height: 26px; padding: 0; line-height: 1;
  background: rgba(0,0,0,0.5); border: 1px solid rgba(184,134,11,0.4);
  border-radius: 3px; color: var(--gold); cursor: pointer; font-size: 0.85rem;
  transition: all 0.2s;
}
.set-export-btn:hover:not(:disabled) { background: var(--gold); color: var(--obsidian); }
.set-export-btn:disabled { opacity: 0.5; cursor: wait; }
.set-export-btn.sm { top: 6px; right: 6px; width: 22px; height: 22px; font-size: 0.72rem; }
/* O tile "upcoming" já tem o selo "EM X DIAS" no canto direito — o botão
   vai para o esquerdo, senão os dois se sobrepõem. */
.set-export-btn.upcoming-export { left: 10px; right: auto; }

.newest-badge {
  position: absolute; top: 10px; right: 10px;
  font-family: 'Cinzel', serif; font-size: 0.5rem; letter-spacing: 2px;
  color: var(--obsidian); background: var(--gold);
  padding: 3px 7px; border-radius: 2px;
}

.set-tile-icon { width: 52px; height: 52px; filter: invert(0.85) sepia(0.3); opacity: 0.9; }
.set-tile-icon.sm { width: 34px; height: 34px; flex-shrink: 0; }

.set-monogram {
  width: 52px; height: 52px; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  border: 1px solid rgba(184,134,11,0.45); border-radius: 50%;
  background: radial-gradient(circle, rgba(184,134,11,0.14), transparent);
  font-family: 'Cinzel', serif; font-size: 0.68rem; letter-spacing: 1px;
  color: var(--gold); text-align: center; line-height: 1;
}
.set-monogram.sm { width: 34px; height: 34px; font-size: 0.52rem; }

.set-tile-body { flex: 1; min-width: 0; }
.set-tile-name {
  font-family: 'Cinzel', serif; font-size: 1rem; color: var(--aged-white);
  margin: 8px 0 6px; line-height: 1.3;
}
.set-tile-name.sm {
  font-size: 0.82rem; margin: 0 0 5px;
  overflow-wrap: anywhere;
}
.set-tile-meta {
  display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  font-size: 0.68rem; color: var(--parchment-xdk); font-family: 'Cinzel', serif;
}
.set-code-badge {
  border: 1px solid rgba(184,134,11,0.4); color: var(--gold);
  padding: 1px 6px; border-radius: 2px; letter-spacing: 1px; font-size: 0.6rem;
}
.meta-count { color: var(--parchment-xdk); }
.set-tile-count { margin-top: 10px; font-size: 0.78rem; color: var(--parchment-dk); }
.set-tile-qty {
  font-family: 'Cinzel', serif; font-size: 0.72rem; color: var(--gold);
  flex-shrink: 0; opacity: 0.75;
}
.set-tile-cta {
  margin-top: 12px; align-self: flex-end;
  font-family: 'Cinzel', serif; font-size: 0.62rem; letter-spacing: 2px;
  color: var(--gold-shine); opacity: 0; transition: opacity 0.25s;
}
.set-tile:hover .set-tile-cta { opacity: 1; }

.year-block { margin-bottom: 2.4rem; }
.year-head { display: flex; align-items: center; gap: 12px; margin-bottom: 0.9rem; }
.year-label {
  font-family: 'Cinzel Decorative', serif; font-size: 1.05rem; color: var(--gold);
  letter-spacing: 2px;
}
.year-count { font-size: 0.66rem; color: var(--parchment-xdk); font-family: 'Cinzel', serif; }
.year-rule { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(184,134,11,0.4), transparent); }

.no-results { text-align: center; padding: 4rem 2rem; }
.no-results-title { font-family: 'Cinzel Decorative', serif; font-size: 1.3rem; color: var(--gold); margin-bottom: 0.8rem; }
.no-results-sub { font-style: italic; color: var(--parchment-xdk); }
</style>
