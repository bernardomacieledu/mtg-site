<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Biblioteca Pessoal</h1>
      <p class="page-hero-sub">Gerencie sua coleção de cartas mágicas</p>
      <div class="hero-divider"><span class="hero-divider-gem">📦</span></div>
    </div>

    <div class="page-wrap">
      <div class="collection-layout">

        <!-- ── SIDEBAR ── -->
        <aside class="col-sidebar">

          <div class="sidebar-section">
            <label class="field-label">📚 Nome da Coleção</label>
            <input v-model="collectionName" class="medieval-input" placeholder="Minha Coleção..." />
          </div>

          <div class="sidebar-section">
            <label class="field-label">⬆ Importar Lista</label>
            <textarea
              v-model="importText"
              class="medieval-input import-textarea"
              placeholder="Cole sua lista:&#10;4 Lightning Bolt&#10;2 Black Lotus&#10;1 Sol Ring&#10;..."
              rows="10"
            />
            <button
              class="btn-primary"
              style="width:100%;margin-top:8px;"
              :disabled="importing || !importText.trim()"
              @click="doImport"
            >{{ importing ? '⏳ Buscando...' : '✦ Importar' }}</button>
            <div v-if="importMsg" class="import-msg" :class="importMsg.startsWith('❌') ? 'err' : 'ok'">
              {{ importMsg }}
            </div>
          </div>

          <!-- Stats -->
          <div v-if="stats" class="sidebar-section stats-panel">
            <div class="field-label">📊 Resumo da Coleção</div>

            <div class="stat-row"><span>Total de cópias</span><strong>{{ stats.total_copies }}</strong></div>
            <div class="stat-row"><span>Cartas únicas</span><strong>{{ stats.total_unique }}</strong></div>
            <div class="stat-row"><span>Sets diferentes</span><strong>{{ stats.total_sets }}</strong></div>

            <div class="stat-divider" />

            <div class="field-label" style="margin-bottom:6px">Por Raridade</div>
            <div v-for="(count, rarity) in stats.rarity_counts" :key="rarity" class="stat-row">
              <span :class="`rarity-dot rarity-${rarity}`">{{ rarityLabel(rarity) }}</span>
              <strong>{{ count }}</strong>
            </div>

            <div class="stat-divider" />

            <div class="field-label" style="margin-bottom:6px">💰 Valor Estimado</div>
            <div class="value-display">
              <div class="value-item">
                <span>Normal</span>
                <strong>US$ {{ stats.estimated_value.toFixed(2) }}</strong>
              </div>
              <div v-if="stats.estimated_value_foil > 0" class="value-item foil">
                <span>✨ Foil</span>
                <strong>US$ {{ stats.estimated_value_foil.toFixed(2) }}</strong>
              </div>
            </div>
          </div>

          <!-- Not found -->
          <div v-if="notFound.length" class="sidebar-section not-found-panel">
            <div class="field-label" style="color:var(--crimson-lt)">⚠ Não encontradas ({{ notFound.length }})</div>
            <div v-for="name in notFound" :key="name" class="not-found-item">{{ name }}</div>
          </div>

          <!-- Export -->
          <div v-if="allCards.length" class="sidebar-section">
            <label class="field-label">⬇ Exportar Coleção</label>
            <div style="display:flex;gap:8px;">
              <button class="btn-primary" style="flex:1;font-size:0.62rem" @click="doExportJson">📄 JSON</button>
              <button class="btn-ghost"   style="flex:1;font-size:0.62rem" @click="doExportText">📋 Lista</button>
            </div>
          </div>

        </aside>

        <!-- ── MAIN ── -->
        <main class="col-main">

          <!-- Empty -->
          <div v-if="!allCards.length && !importing" class="empty-col">
            <div class="empty-title">✦ Coleção Vazia ✦</div>
            <p class="empty-sub">Importe uma lista para começar sua biblioteca</p>
            <pre class="sample-code">4 Lightning Bolt
2 Tarmogoyf
1 Black Lotus
20 Island</pre>
          </div>

          <!-- Skeleton -->
          <div v-if="importing" class="skeleton-grid">
            <div v-for="i in 16" :key="i" class="card-skeleton" />
          </div>

          <!-- View switcher -->
          <div v-if="allCards.length" class="view-controls">
            <div class="view-tabs">
              <button v-for="v in views" :key="v.id"
                class="view-tab" :class="{ active: activeView === v.id }"
                @click="activeView = v.id">
                {{ v.icon }} {{ v.label }}
              </button>
            </div>
            <div class="search-filter">
              <input v-model="filterText" class="medieval-input" style="font-size:0.8rem;padding:7px 12px;"
                placeholder="Filtrar cartas..." />
            </div>
          </div>

          <!-- VIEW: Por Set -->
          <template v-if="activeView === 'set' && allCards.length">
            <div v-for="setGroup in filteredBySets" :key="setGroup.set_code" class="set-group">
              <div class="set-group-header">
                <img :src="`https://svgs.scryfall.io/sets/${setGroup.set_code.toLowerCase()}.svg`"
                     class="set-icon-sm" @error="e => e.target.style.display='none'" />
                <span class="set-group-name">{{ setGroup.set_name }}</span>
                <span class="set-group-code cinzel-caps">{{ setGroup.set_code.toUpperCase() }}</span>
                <span class="set-group-count">{{ setGroup.cards.reduce((s,c)=>s+c.qty,0) }} cópias</span>
              </div>
              <div class="cards-grid-col">
                <CollectionCard
                  v-for="card in setGroup.cards.filter(c => matchesFilter(c))"
                  :key="card.name + setGroup.set_code"
                  :card="card"
                  :mana-symbols="symbols"
                  @click="selectedCard = card"
                />
              </div>
            </div>
          </template>

          <!-- VIEW: Por Raridade -->
          <template v-if="activeView === 'rarity' && allCards.length">
            <div v-for="r in ['mythic','rare','uncommon','common','special']" :key="r">
              <div v-if="filteredByRarity[r]?.length" class="rarity-group">
                <div class="rarity-group-header">
                  <span :class="`rarity-badge rarity-${r}`">{{ rarityLabel(r) }}</span>
                  <span class="set-group-count">{{ filteredByRarity[r].reduce((s,c)=>s+c.qty,0) }} cópias</span>
                </div>
                <div class="cards-grid-col">
                  <CollectionCard
                    v-for="card in filteredByRarity[r]"
                    :key="card.name + r"
                    :card="card"
                    :mana-symbols="symbols"
                    @click="selectedCard = card"
                  />
                </div>
              </div>
            </div>
          </template>

          <!-- VIEW: Por Categoria -->
          <template v-if="activeView === 'category' && allCards.length">
            <div v-for="(cards, cat) in filteredByCategory" :key="cat" class="cat-group">
              <div class="cat-group-header">
                <span class="cat-icon">{{ catIcon(cat) }}</span>
                <span class="cat-name">{{ catLabel(cat) }}</span>
                <span class="set-group-count">{{ cards.reduce((s,c)=>s+c.qty,0) }} cópias</span>
              </div>
              <div class="cards-grid-col">
                <CollectionCard
                  v-for="card in cards"
                  :key="card.name + cat"
                  :card="card"
                  :mana-symbols="symbols"
                  @click="selectedCard = card"
                />
              </div>
            </div>
          </template>

          <!-- VIEW: Todas -->
          <template v-if="activeView === 'all' && allCards.length">
            <div class="cards-grid-col">
              <CollectionCard
                v-for="card in filteredAll"
                :key="card.name"
                :card="card"
                :mana-symbols="symbols"
                @click="selectedCard = card"
              />
            </div>
          </template>

        </main>
      </div>
    </div>

    <!-- ── Card Modal ── -->
    <Transition name="fade">
      <div v-if="selectedCard" class="modal-overlay" @click.self="selectedCard = null">
        <div class="card-modal">
          <button class="modal-close btn-ghost" @click="selectedCard = null">✕</button>
          <div class="modal-content">
            <img :src="selectedCard.image_url" :alt="selectedCard.name" class="modal-img"
                 @error="e => e.target.style.display='none'" />
            <div class="modal-info">
              <div class="modal-qty-badge">{{ selectedCard.qty }}× na coleção</div>
              <h2 class="modal-name">{{ selectedCard.name }}</h2>
              <div v-html="renderMana(selectedCard.mana_cost)" style="margin:6px 0" />
              <div class="modal-type">{{ selectedCard.type_line }}</div>
              <div class="modal-oracle">{{ selectedCard.oracle_text }}</div>
              <div v-if="selectedCard.power != null" class="modal-pt">
                {{ selectedCard.power }} / {{ selectedCard.toughness }}
              </div>
              <div class="modal-meta">
                <span class="rarity-badge" :class="`rarity-${selectedCard.rarity}`">{{ selectedCard.rarity }}</span>
                <span style="font-size:0.7rem;color:var(--parchment-xdk)">{{ selectedCard.set_name }}</span>
              </div>
              <div v-if="Object.keys(selectedCard.prices||{}).length" class="modal-prices">
                <div class="field-label" style="margin-bottom:6px">💰 Preços</div>
                <div class="prices-row">
                  <div v-if="selectedCard.prices.usd" class="price-chip">
                    <span>Normal</span><strong>US$ {{ selectedCard.prices.usd }}</strong>
                  </div>
                  <div v-if="selectedCard.prices.usd_foil" class="price-chip foil">
                    <span>✨ Foil</span><strong>US$ {{ selectedCard.prices.usd_foil }}</strong>
                  </div>
                  <div v-if="selectedCard.prices.eur" class="price-chip">
                    <span>EUR</span><strong>€ {{ selectedCard.prices.eur }}</strong>
                  </div>
                </div>
                <div class="total-value-card">
                  Valor total desta carta:
                  <strong>US$ {{ (parseFloat(selectedCard.prices.usd||0) * selectedCard.qty).toFixed(2) }}</strong>
                  ({{ selectedCard.qty }}×)
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import api from '@/composables/api'
import { useMana } from '@/composables/useMana'

// ── Inline CollectionCard component ──────────────────────────────────────────
const CollectionCard = {
  props: { card: Object, manaSymbols: Object },
  emits: ['click'],
  template: `
    <div class="col-card" @click="$emit('click')">
      <div class="col-card-qty">{{ card.qty }}×</div>
      <img :src="card.image_url" :alt="card.name" class="col-card-img" loading="lazy"
           @error="e => e.target.src = ''" />
      <div class="col-card-footer">
        <span class="col-card-name">{{ card.name }}</span>
        <span class="rarity-dot" :class="'rarity-dot-' + card.rarity"></span>
      </div>
    </div>
  `,
}

const { symbols } = useMana()

const collectionName = ref('Minha Coleção')
const importText     = ref('')
const importing      = ref(false)
const importMsg      = ref('')
const allCards       = ref([])
const bySets         = ref([])
const byRarity       = ref({})
const byCategory     = ref({})
const notFound       = ref([])
const stats          = ref(null)
const selectedCard   = ref(null)
const activeView     = ref('all')
const filterText     = ref('')

const views = [
  { id: 'all',      icon: '🃏', label: 'Todas' },
  { id: 'set',      icon: '📦', label: 'Por Set' },
  { id: 'rarity',   icon: '💎', label: 'Por Raridade' },
  { id: 'category', icon: '🐉', label: 'Por Tipo' },
]

const CAT_LABELS = { creature:'Criaturas', artifact:'Artefatos', enchantment:'Encantamentos', planeswalker:'Planeswalkers', instant:'Instantâneos', sorcery:'Feitiços', land:'Terrenos', other:'Outros' }
const CAT_ICONS  = { creature:'🐉', artifact:'⚙', enchantment:'✨', planeswalker:'⭐', instant:'⚡', sorcery:'📜', land:'🌲', other:'🃏' }
const RARITY_LABELS = { mythic:'Mítica', rare:'Rara', uncommon:'Incomum', common:'Comum', special:'Especial' }

function catLabel(k) { return CAT_LABELS[k] || k }
function catIcon(k)  { return CAT_ICONS[k]  || '🃏' }
function rarityLabel(r) { return RARITY_LABELS[r] || r }

function matchesFilter(card) {
  if (!filterText.value) return true
  const q = filterText.value.toLowerCase()
  return card.name.toLowerCase().includes(q) ||
         card.type_line?.toLowerCase().includes(q) ||
         card.oracle_text?.toLowerCase().includes(q)
}

const filteredAll      = computed(() => allCards.value.filter(matchesFilter))
const filteredBySets   = computed(() => bySets.value.map(s => ({
  ...s, cards: s.cards.filter(matchesFilter)
})).filter(s => s.cards.length))
const filteredByRarity = computed(() => {
  const result = {}
  for (const [r, cards] of Object.entries(byRarity.value)) {
    const filtered = cards.filter(matchesFilter)
    if (filtered.length) result[r] = filtered
  }
  return result
})
const filteredByCategory = computed(() => {
  const result = {}
  const ORDER = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']
  for (const cat of ORDER) {
    const cards = (byCategory.value[cat] || []).filter(matchesFilter)
    if (cards.length) result[cat] = cards
  }
  return result
})

function renderMana(cost) {
  if (!cost) return ''
  return cost.replace(/\{([^}]+)\}/g, (match) => {
    const uri = symbols.value[match]
    return uri ? `<img src="${uri}" class="ms" style="width:16px;height:16px" alt="${match}">` : match
  })
}

async function doImport() {
  if (!importText.value.trim() || importing.value) return
  importing.value = true
  importMsg.value = ''
  allCards.value = []; bySets.value = []; byRarity.value = {}
  byCategory.value = {}; notFound.value = []; stats.value = null

  try {
    const { data } = await api.post('/collection/import/', { text: importText.value })
    allCards.value   = data.cards
    bySets.value     = data.by_set
    byRarity.value   = data.by_rarity
    byCategory.value = data.by_category
    notFound.value   = data.not_found
    stats.value      = data.stats
    importMsg.value  = `✔ ${data.stats.total_unique} cartas importadas (${data.stats.total_copies} cópias)`
    setTimeout(() => { importMsg.value = '' }, 4000)
  } catch(e) {
    importMsg.value = '❌ Erro ao importar.'
    console.error(e)
  } finally {
    importing.value = false
  }
}

async function doExportJson() {
  const { data } = await api.post('/collection/export/', {
    name: collectionName.value, cards: allCards.value,
  })
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${collectionName.value.replace(/\s+/g,'_')}_colecao.json`
  a.click(); URL.revokeObjectURL(url)
}

function doExportText() {
  let text = `// ${collectionName.value}\n// ${stats.value?.total_copies} cópias · ${stats.value?.total_unique} únicas\n\n`
  for (const [cat, cards] of Object.entries(filteredByCategory.value)) {
    text += `// ${catLabel(cat)}\n`
    for (const c of cards) text += `${c.qty} ${c.name}\n`
    text += '\n'
  }
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${collectionName.value.replace(/\s+/g,'_')}_colecao.txt`
  a.click(); URL.revokeObjectURL(url)
}
</script>

<style scoped>
.collection-layout { display:grid; grid-template-columns:280px 1fr; gap:2rem; align-items:start; }

/* Sidebar */
.col-sidebar { display:flex; flex-direction:column; gap:1.2rem; position:sticky; top:88px; max-height:calc(100vh - 120px); overflow-y:auto; }
.sidebar-section { background:linear-gradient(135deg,rgba(26,19,10,0.95),rgba(13,10,6,0.95)); border:1px solid rgba(184,134,11,0.22); border-radius:3px; padding:1rem; }
.import-textarea { font-family:'Courier New',monospace; font-size:0.78rem; resize:vertical; min-height:140px; line-height:1.6; }
.import-msg { font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:1px; margin-top:6px; text-align:center; }
.import-msg.ok  { color:var(--gold); }
.import-msg.err { color:var(--crimson-lt); }

/* Stats */
.stats-panel { display:flex; flex-direction:column; gap:5px; }
.stat-row    { display:flex; justify-content:space-between; font-size:0.78rem; color:var(--parchment-dk); padding:3px 0; border-bottom:1px solid rgba(184,134,11,0.08); }
.stat-row strong { color:var(--gold); font-family:'Cinzel',serif; }
.stat-divider { height:1px; background:rgba(184,134,11,0.15); margin:6px 0; }
.rarity-dot  { font-family:'Cinzel',serif; font-size:0.65rem; }
.rarity-dot.rarity-mythic   { color:#e07820; }
.rarity-dot.rarity-rare     { color:#d4a017; }
.rarity-dot.rarity-uncommon { color:#a8c6d4; }
.rarity-dot.rarity-common   { color:#94a3b8; }
.value-display { display:flex; gap:8px; flex-wrap:wrap; }
.value-item  { background:rgba(0,0,0,0.3); border:1px solid rgba(184,134,11,0.2); border-radius:2px; padding:6px 10px; text-align:center; flex:1; }
.value-item span   { display:block; font-family:'Cinzel',serif; font-size:0.55rem; letter-spacing:1px; color:var(--gold); }
.value-item strong { display:block; font-size:0.9rem; color:var(--aged-white); }
.value-item.foil   { border-color:rgba(160,200,255,0.25); }
.not-found-panel { border-color:rgba(139,26,26,0.3); }
.not-found-item  { font-size:0.7rem; color:var(--crimson-lt); padding:2px 0; }

/* Main */
.col-main { min-width:0; }

.empty-col   { text-align:center; padding:5rem 2rem; }
.empty-title { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); margin-bottom:1rem; }
.empty-sub   { font-style:italic; color:var(--parchment-xdk); margin-bottom:1.5rem; }
.sample-code { background:rgba(0,0,0,0.4); border:1px solid rgba(184,134,11,0.2); border-radius:3px; padding:12px 16px; font-family:'Courier New',monospace; font-size:0.8rem; color:var(--parchment-dk); white-space:pre; display:inline-block; text-align:left; }

/* Skeleton */
.skeleton-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:8px; }
.card-skeleton  { height:170px; background:linear-gradient(90deg,rgba(184,134,11,0.05) 25%,rgba(184,134,11,0.1) 50%,rgba(184,134,11,0.05) 75%); background-size:200% 100%; border-radius:4px; animation:shimmer 1.5s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* View controls */
.view-controls { display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.view-tabs     { display:flex; gap:4px; flex-wrap:wrap; }
.view-tab {
  font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:1px;
  padding:6px 14px; background:rgba(0,0,0,0.2);
  border:1px solid rgba(184,134,11,0.2); border-radius:2px;
  color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s;
}
.view-tab:hover  { border-color:var(--gold); color:var(--parchment); }
.view-tab.active { border-color:var(--gold-shine); background:rgba(184,134,11,0.12); color:var(--gold-shine); }
.search-filter   { flex:1; min-width:160px; }

/* Group headers */
.set-group, .rarity-group, .cat-group { margin-bottom:2.5rem; }
.set-group-header, .rarity-group-header, .cat-group-header {
  display:flex; align-items:center; gap:10px;
  padding-bottom:8px; margin-bottom:10px;
  border-bottom:1px solid rgba(184,134,11,0.2);
}
.set-icon-sm   { width:22px; height:22px; filter:invert(0.85) sepia(0.3); opacity:0.8; }
.set-group-name, .cat-name { font-family:'Cinzel',serif; font-size:0.85rem; font-weight:700; color:var(--aged-white); flex:1; letter-spacing:2px; }
.set-group-code { font-size:0.55rem; letter-spacing:3px; color:rgba(184,134,11,0.5); }
.set-group-count { font-family:'Cinzel',serif; font-size:0.6rem; color:var(--gold); background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.2); padding:2px 8px; border-radius:2px; }
.cat-icon { font-size:1.1rem; }

/* Cards grid */
.cards-grid-col { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:8px; }

/* Collection card */
:deep(.col-card) {
  position:relative; border-radius:4px; overflow:hidden;
  border:1px solid rgba(184,134,11,0.18); cursor:pointer;
  transition:all 0.25s; background:#0d0a06;
}
:deep(.col-card:hover) { transform:translateY(-4px); border-color:var(--gold); box-shadow:0 8px 20px rgba(0,0,0,0.5); }
:deep(.col-card-qty) { position:absolute; top:4px; left:4px; background:rgba(0,0,0,0.88); color:var(--gold-shine); font-family:'Cinzel',serif; font-size:0.65rem; font-weight:700; padding:2px 6px; border-radius:2px; z-index:2; }
:deep(.col-card-img) { width:100%; display:block; min-height:80px; }
:deep(.col-card-footer) { display:flex; align-items:center; justify-content:space-between; padding:3px 5px; background:rgba(0,0,0,0.6); }
:deep(.col-card-name) { font-family:'Cinzel',serif; font-size:0.42rem; color:var(--parchment-dk); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
:deep(.rarity-dot-mythic)   { width:8px; height:8px; background:#e07820; border-radius:50%; flex-shrink:0; display:inline-block; }
:deep(.rarity-dot-rare)     { width:8px; height:8px; background:#d4a017; border-radius:50%; flex-shrink:0; display:inline-block; }
:deep(.rarity-dot-uncommon) { width:8px; height:8px; background:#a8c6d4; border-radius:50%; flex-shrink:0; display:inline-block; }
:deep(.rarity-dot-common)   { width:8px; height:8px; background:#94a3b8; border-radius:50%; flex-shrink:0; display:inline-block; }
:deep(.rarity-dot-special)  { width:8px; height:8px; background:#c8a8f5; border-radius:50%; flex-shrink:0; display:inline-block; }

/* Modal */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.8); display:flex; align-items:center; justify-content:center; z-index:500; }
.card-modal { background:linear-gradient(135deg,#1a130a,#0d0a06); border:1px solid var(--gold); border-radius:4px; padding:2rem; max-width:660px; width:90vw; position:relative; max-height:90vh; overflow-y:auto; }
.modal-close { position:absolute; top:12px; right:12px; }
.modal-content { display:flex; gap:1.5rem; }
.modal-img  { width:200px; border-radius:6px; flex-shrink:0; }
.modal-info { flex:1; min-width:0; }
.modal-qty-badge { font-family:'Cinzel',serif; font-size:0.6rem; letter-spacing:2px; color:var(--gold); background:rgba(184,134,11,0.12); border:1px solid rgba(184,134,11,0.3); border-radius:2px; padding:3px 10px; display:inline-block; margin-bottom:8px; }
.modal-name  { font-family:'Cinzel Decorative',serif; font-size:1.1rem; color:var(--gold-shine); margin-bottom:4px; }
.modal-type  { font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); opacity:0.8; margin-bottom:8px; }
.modal-oracle { font-style:italic; color:var(--parchment-dk); line-height:1.65; font-size:0.85rem; background:rgba(0,0,0,0.3); border-left:2px solid rgba(184,134,11,0.3); padding:8px 12px; border-radius:0 2px 2px 0; margin-bottom:8px; }
.modal-pt    { font-family:'Cinzel',serif; font-size:1rem; color:var(--gold-shine); font-weight:700; }
.modal-meta  { display:flex; align-items:center; gap:10px; margin-top:8px; }
.modal-prices { margin-top:12px; padding-top:10px; border-top:1px solid rgba(184,134,11,0.15); }
.prices-row  { display:flex; gap:8px; flex-wrap:wrap; margin-bottom:8px; }
.price-chip  { background:rgba(0,0,0,0.3); border:1px solid rgba(184,134,11,0.2); border-radius:2px; padding:5px 10px; text-align:center; }
.price-chip span   { display:block; font-family:'Cinzel',serif; font-size:0.52rem; letter-spacing:1px; color:var(--gold); }
.price-chip strong { display:block; font-size:0.85rem; color:var(--aged-white); }
.price-chip.foil   { border-color:rgba(160,200,255,0.3); }
.total-value-card  { font-size:0.75rem; color:var(--parchment-xdk); font-style:italic; }
.total-value-card strong { color:var(--gold-shine); }

.fade-enter-active,.fade-leave-active{transition:opacity 0.25s}
.fade-enter-from,.fade-leave-to{opacity:0}

@media(max-width:900px){
  .collection-layout { grid-template-columns:1fr; }
  .col-sidebar { position:static; max-height:none; }
  .modal-content { flex-direction:column; }
  .modal-img { width:100%; max-width:200px; }
}
</style>