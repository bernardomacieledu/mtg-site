<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Forja de Decks</h1>
      <p class="page-hero-sub">Importe, analise e exporte seus grimórios arcanos</p>
      <div class="hero-divider"><span class="hero-divider-gem">⚒</span></div>
    </div>

    <div class="page-wrap">
      <div class="builder-layout">

        <!-- ── LEFT: Import + Controls ── -->
        <aside class="builder-sidebar">

          <!-- Deck name -->
          <div class="sidebar-section">
            <label class="field-label">📜 Nome do Deck</label>
            <input v-model="deckName" class="medieval-input" placeholder="Meu Grimório..." />
          </div>

          <!-- Import textarea -->
          <div class="sidebar-section">
            <label class="field-label">⬆ Importar Lista</label>
            <textarea
              v-model="importText"
              class="medieval-input import-textarea"
              placeholder="Cole sua lista aqui:&#10;1 Lightning Bolt&#10;4 Mountain&#10;1 Karn Liberated&#10;..."
              rows="12"
            />
            <button
              class="btn-primary"
              style="width:100%;margin-top:8px;"
              :disabled="importing || !importText.trim()"
              @click="importDeck"
            >
              {{ importing ? '⏳ Buscando cartas...' : '✦ Importar Deck' }}
            </button>
            <div v-if="importProgress" class="import-progress">
              {{ importProgress }}
            </div>
          </div>

          <!-- Commander selection -->
          <div v-if="legendaryCreatures.length" class="sidebar-section">
            <label class="field-label">👑 Comandante</label>
            <div class="commander-list">
              <div
                v-for="card in legendaryCreatures"
                :key="card.name"
                class="commander-opt"
                :class="{ selected: commander?.name === card.name }"
                @click="setCommander(card)"
              >
                <img :src="card.image_url" class="commander-thumb" :alt="card.name"
                     @error="e => e.target.style.display='none'" />
                <div class="commander-info">
                  <div class="commander-name">{{ card.name }}</div>
                  <div class="commander-type" style="font-size:0.6rem;color:var(--parchment-xdk)">
                    {{ card.type_line }}
                  </div>
                  <div v-html="renderManaCost(card.mana_cost)" class="commander-cost" />
                </div>
                <span v-if="commander?.name === card.name" class="cinzel-caps"
                      style="color:var(--gold);font-size:0.55rem;">✦ CMD</span>
              </div>
            </div>
          </div>

          <!-- Stats -->
          <div v-if="stats" class="sidebar-section stats-box">
            <div class="field-label">📊 Estatísticas</div>
            <div class="stat-row"><span>Total de cartas</span><strong>{{ stats.total_cards }}</strong></div>
            <div class="stat-row"><span>Cartas únicas</span><strong>{{ stats.unique_cards }}</strong></div>
            <div class="stat-row"><span>CMC médio</span><strong>{{ stats.avg_cmc }}</strong></div>
            <div class="stat-row" v-for="(count, cat) in stats.by_category" :key="cat">
              <span>{{ categoryLabel(cat) }}</span><strong>{{ count }}</strong>
            </div>
            <!-- Color identity -->
            <div v-if="Object.keys(stats.color_identity).length" class="color-identity-row">
              <span class="field-label" style="margin-bottom:4px;">Identidade de cor</span>
              <div class="color-pips-display">
                <span
                  v-for="(count, color) in stats.color_identity"
                  :key="color"
                  class="color-pip-lg"
                  :class="`pip-${color.toLowerCase()}`"
                >{{ color }}</span>
              </div>
            </div>
          </div>

          <!-- Not found -->
          <div v-if="notFound.length" class="sidebar-section not-found-box">
            <div class="field-label" style="color:var(--crimson-lt)">⚠ Não encontradas</div>
            <div v-for="name in notFound" :key="name" class="not-found-item">{{ name }}</div>
          </div>

          <!-- Export -->
          <div v-if="allCards.length" class="sidebar-section">
            <label class="field-label">⬇ Exportar</label>
            <div style="display:flex;gap:8px;">
              <button class="btn-primary" style="flex:1;font-size:0.65rem;" @click="exportDeck">
                📄 JSON
              </button>
              <button class="btn-ghost" style="flex:1;font-size:0.65rem;" @click="exportText">
                📋 Lista
              </button>
            </div>
          </div>

        </aside>

        <!-- ── RIGHT: Card Grid by Category ── -->
        <main class="builder-main">

          <div v-if="!allCards.length && !importing" class="empty-builder">
            <div class="empty-title">✦ Grimório Vazio ✦</div>
            <p class="empty-sub">Importe uma lista de cartas para começar</p>
            <div class="sample-format">
              <div class="field-label">Formato aceito:</div>
              <pre class="sample-code">1 Karn Liberated
1 Sol Ring
4 Island
1 Lightning Bolt</pre>
            </div>
          </div>

          <!-- Loading skeleton -->
          <div v-if="importing" class="loading-grid">
            <div v-for="i in 12" :key="i" class="card-skeleton" />
          </div>

          <!-- Commander featured card -->
          <div v-if="commander" class="commander-feature">
            <div class="commander-banner">
              <span class="commander-crown">👑</span>
              <span class="cinzel-caps">Comandante</span>
            </div>
            <div class="commander-card-full">
              <img :src="commander.image_url" :alt="commander.name" class="commander-img-full" />
              <div class="commander-details">
                <h2 class="commander-full-name">{{ commander.name }}</h2>
                <div v-html="renderManaCost(commander.mana_cost)" style="margin:8px 0" />
                <div class="detail-type">{{ commander.type_line }}</div>
                <div class="detail-oracle">{{ commander.oracle_text }}</div>
                <div v-if="commander.power != null" class="detail-pt">
                  {{ commander.power }} / {{ commander.toughness }}
                </div>
                <div class="detail-meta">
                  <span class="rarity-badge" :class="`rarity-${commander.rarity}`">{{ commander.rarity }}</span>
                  <span class="cinzel-caps" style="font-size:0.55rem;color:var(--parchment-xdk)">{{ commander.set_name }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Categories -->
          <div
            v-for="(catCards, catKey) in categoriesFiltered"
            :key="catKey"
            class="category-section"
          >
            <div class="category-header">
              <span class="category-icon">{{ categoryIcon(catKey) }}</span>
              <span class="category-name">{{ categoryLabel(catKey) }}</span>
              <span class="category-count">{{ catCards.reduce((s,c)=>s+c.qty,0) }} cartas</span>
            </div>

            <div class="cards-grid-deck">
              <div
                v-for="card in catCards"
                :key="card.name"
                class="deck-card"
                :class="{ 'is-commander': commander?.name === card.name }"
                @click="selectedCard = card"
              >
                <div class="deck-card-qty">{{ card.qty }}×</div>
                <img
                  :src="card.image_url"
                  :alt="card.name"
                  class="deck-card-img"
                  loading="lazy"
                  @error="e => e.target.src = ''"
                />
                <div class="deck-card-overlay">
                  <div class="deck-card-name">{{ card.name }}</div>
                  <div v-html="renderManaCost(card.mana_cost)" class="deck-card-cost" />
                  <div v-if="card.power != null" class="deck-card-pt">
                    {{ card.power }}/{{ card.toughness }}
                  </div>
                </div>
                <div v-if="card.is_legendary_creature" class="legendary-crown">👑</div>
              </div>
            </div>
          </div>

        </main>
      </div>
    </div>

    <!-- ── Card Detail Modal ── -->
    <Transition name="fade">
      <div v-if="selectedCard" class="modal-overlay" @click.self="selectedCard = null">
        <div class="card-modal">
          <button class="modal-close btn-ghost" @click="selectedCard = null">✕</button>
          <div class="modal-content">
            <img :src="selectedCard.image_url" :alt="selectedCard.name" class="modal-img"
                 @error="e => e.target.style.display='none'" />
            <div class="modal-info">
              <h2 class="modal-name">{{ selectedCard.name }}</h2>
              <div v-html="renderManaCost(selectedCard.mana_cost)" style="margin:8px 0" />
              <div class="modal-type">{{ selectedCard.type_line }}</div>
              <div class="modal-oracle">{{ selectedCard.oracle_text }}</div>
              <div v-if="selectedCard.power != null" class="modal-pt">
                {{ selectedCard.power }} / {{ selectedCard.toughness }}
              </div>
              <div class="modal-meta">
                <span class="rarity-badge" :class="`rarity-${selectedCard.rarity}`">
                  {{ selectedCard.rarity }}
                </span>
                <span style="font-size:0.7rem;color:var(--parchment-xdk)">
                  {{ selectedCard.set_name }}
                </span>
              </div>
              <!-- Prices -->
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
              </div>
              <!-- Set commander button -->
              <div v-if="selectedCard.is_legendary_creature" style="margin-top:1rem">
                <button
                  class="btn-primary"
                  style="width:100%;font-size:0.7rem;"
                  @click="setCommander(selectedCard); selectedCard = null"
                >
                  👑 Definir como Comandante
                </button>
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
import axios from 'axios'
import { useMana } from '@/composables/useMana'

const { symbols } = useMana()

const deckName      = ref('Meu Deck')
const importText    = ref('')
const importing     = ref(false)
const importProgress = ref('')
const allCards      = ref([])
const categories    = ref({})
const legendaryCreatures = ref([])
const commander     = ref(null)
const notFound      = ref([])
const stats         = ref(null)
const selectedCard  = ref(null)

const CATEGORY_ORDER = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']
const CATEGORY_LABELS = {
  creature:'Criaturas', artifact:'Artefatos', enchantment:'Encantamentos',
  planeswalker:'Planeswalkers', instant:'Mágicas Instantâneas', sorcery:'Feitiços',
  land:'Terrenos', other:'Outros', commander:'Comandante',
}
const CATEGORY_ICONS = {
  creature:'🐉', artifact:'⚙', enchantment:'✨', planeswalker:'⭐',
  instant:'⚡', sorcery:'📜', land:'🌲', other:'🃏', commander:'👑',
}

const categoriesFiltered = computed(() => {
  const result = {}
  for (const key of CATEGORY_ORDER) {
    const cards = (categories.value[key] || []).filter(c =>
      commander.value ? c.name !== commander.value.name : true
    )
    if (cards.length) result[key] = cards
  }
  return result
})

function categoryLabel(k) { return CATEGORY_LABELS[k] || k }
function categoryIcon(k)  { return CATEGORY_ICONS[k] || '🃏' }

function renderManaCost(manaCost) {
  if (!manaCost) return ''
  return manaCost.replace(/\{([^}]+)\}/g, (match) => {
    const uri = symbols.value[match]
    return uri ? `<img src="${uri}" class="ms" style="width:16px;height:16px" alt="${match}">` : match
  })
}

async function importDeck() {
  if (!importText.value.trim()) return
  importing.value = true
  importProgress.value = 'Consultando Scryfall...'
  allCards.value = []
  categories.value = {}
  legendaryCreatures.value = []
  commander.value = null
  notFound.value = []
  stats.value = null

  try {
    const { data } = await axios.post('/api/deck/import/', { text: importText.value })
    allCards.value       = data.cards
    categories.value     = data.categories
    legendaryCreatures.value = data.legendary_creatures
    notFound.value       = data.not_found
    stats.value          = data.stats
    importProgress.value = `✔ ${data.cards.length} cartas importadas!`
    // Auto-select commander if only one legendary creature
    if (data.legendary_creatures.length === 1) {
      commander.value = data.legendary_creatures[0]
    }
    setTimeout(() => { importProgress.value = '' }, 3000)
  } catch (e) {
    importProgress.value = '❌ Erro ao importar. Verifique a lista.'
    console.error(e)
  } finally {
    importing.value = false
  }
}

function setCommander(card) {
  commander.value = card
}

async function exportDeck() {
  const { data } = await axios.post('/api/deck/export/', {
    name: deckName.value,
    commander: commander.value,
    cards: allCards.value,
    format: 'commander',
  })
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `${deckName.value.replace(/\s+/g, '_')}.json`
  a.click()
  URL.revokeObjectURL(url)
}

function exportText() {
  let text = `// ${deckName.value}\n`
  if (commander.value) text += `// Comandante: ${commander.value.name}\n\n`
  for (const [cat, cards] of Object.entries(categoriesFiltered.value)) {
    text += `// ${categoryLabel(cat)}\n`
    for (const c of cards) text += `${c.qty} ${c.name}\n`
    text += '\n'
  }
  const blob = new Blob([text], { type: 'text/plain' })
  const url  = URL.createObjectURL(blob)
  const a    = document.createElement('a')
  a.href     = url
  a.download = `${deckName.value.replace(/\s+/g, '_')}.txt`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<style scoped>
.builder-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 2rem;
  align-items: start;
}

/* ── Sidebar ── */
.builder-sidebar {
  display: flex; flex-direction: column; gap: 1.2rem;
  position: sticky; top: 88px; max-height: calc(100vh - 120px); overflow-y: auto;
}

.sidebar-section {
  background: linear-gradient(135deg, rgba(26,19,10,0.95), rgba(13,10,6,0.95));
  border: 1px solid rgba(184,134,11,0.22);
  border-radius: 3px; padding: 1rem;
}

.import-textarea {
  font-family: 'Courier New', monospace;
  font-size: 0.78rem;
  resize: vertical;
  min-height: 160px;
  line-height: 1.6;
}

.import-progress {
  font-family: 'Cinzel', serif; font-size: 0.65rem;
  letter-spacing: 1px; color: var(--gold); margin-top: 6px; text-align: center;
}

/* Commander list */
.commander-list { display: flex; flex-direction: column; gap: 6px; }
.commander-opt {
  display: flex; align-items: center; gap: 8px;
  border: 1px solid rgba(184,134,11,0.2); border-radius: 3px;
  padding: 6px 8px; cursor: pointer; transition: all 0.2s;
  background: rgba(0,0,0,0.2);
}
.commander-opt:hover  { border-color: var(--gold); background: rgba(184,134,11,0.08); }
.commander-opt.selected { border-color: var(--gold-shine); background: rgba(184,134,11,0.14); }
.commander-thumb { width: 36px; height: 50px; object-fit: cover; border-radius: 2px; flex-shrink: 0; }
.commander-name  { font-family:'Cinzel',serif; font-size:0.7rem; color:var(--aged-white); }

/* Stats */
.stats-box { display: flex; flex-direction: column; gap: 6px; }
.stat-row  { display:flex; justify-content:space-between; align-items:center; font-size:0.78rem; color:var(--parchment-dk); padding:3px 0; border-bottom:1px solid rgba(184,134,11,0.08); }
.stat-row strong { color: var(--gold); font-family:'Cinzel',serif; }
.color-identity-row { margin-top: 4px; }
.color-pips-display { display:flex; gap:6px; }
.color-pip-lg { width:24px; height:24px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.6rem; font-weight:bold; }
.pip-w{background:#c8b896;color:#1a0f00} .pip-u{background:#1a3a6b;color:#a8d4f5}
.pip-b{background:#2a1a3e;color:#c8a8f5} .pip-r{background:#6b1a1a;color:#f5a8a8}
.pip-g{background:#1a3a1a;color:#a8f5a8}

.not-found-box { border-color: rgba(139,26,26,0.4); }
.not-found-item { font-size:0.72rem; color:var(--crimson-lt); padding:2px 0; border-bottom:1px solid rgba(139,26,26,0.1); }

/* ── Main ── */
.builder-main { min-width: 0; }

.empty-builder { text-align:center; padding:5rem 2rem; }
.empty-title   { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); margin-bottom:1rem; }
.empty-sub     { font-style:italic; color:var(--parchment-xdk); margin-bottom:2rem; }
.sample-format { text-align:left; display:inline-block; }
.sample-code   { background:rgba(0,0,0,0.4); border:1px solid rgba(184,134,11,0.2); border-radius:3px; padding:12px 16px; font-family:'Courier New',monospace; font-size:0.8rem; color:var(--parchment-dk); white-space:pre; }

/* Loading skeleton */
.loading-grid  { display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:10px; }
.card-skeleton { height:182px; background:linear-gradient(90deg,rgba(184,134,11,0.05) 25%,rgba(184,134,11,0.1) 50%,rgba(184,134,11,0.05) 75%); background-size:200% 100%; border-radius:4px; animation:shimmer 1.5s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Commander feature */
.commander-feature { margin-bottom: 2.5rem; }
.commander-banner  { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
.commander-crown   { font-size:1.4rem; }
.commander-card-full { display:flex; gap:1.5rem; background:linear-gradient(135deg,rgba(26,19,10,0.95),rgba(13,10,6,0.95)); border:2px solid var(--gold); border-radius:4px; padding:1.5rem; }
.commander-img-full  { width:200px; border-radius:6px; flex-shrink:0; box-shadow:0 12px 32px rgba(0,0,0,0.6); }
.commander-details   { flex:1; min-width:0; }
.commander-full-name { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold-shine); margin-bottom:4px; }
.detail-type   { font-family:'Cinzel',serif; font-size:0.7rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); opacity:0.8; margin-bottom:10px; }
.detail-oracle { font-style:italic; color:var(--parchment-dk); line-height:1.6; font-size:0.9rem; margin-bottom:10px; background:rgba(0,0,0,0.3); border-left:2px solid rgba(184,134,11,0.3); padding:8px 12px; border-radius:0 2px 2px 0; }
.detail-pt     { font-family:'Cinzel',serif; font-size:1.1rem; color:var(--gold-shine); font-weight:700; }
.detail-meta   { display:flex; align-items:center; gap:10px; margin-top:10px; }

/* Category sections */
.category-section { margin-bottom: 2.5rem; }
.category-header  { display:flex; align-items:center; gap:10px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(184,134,11,0.2); }
.category-icon    { font-size:1.2rem; }
.category-name    { font-family:'Cinzel',serif; font-size:0.9rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--aged-white); flex:1; }
.category-count   { font-family:'Cinzel',serif; font-size:0.65rem; color:var(--gold); background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.2); padding:3px 10px; border-radius:2px; }

/* Deck card grid */
.cards-grid-deck { display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:10px; }

.deck-card {
  position:relative; border-radius:4px; overflow:hidden;
  border:1px solid rgba(184,134,11,0.2); cursor:pointer;
  transition:all 0.25s; background:#0d0a06;
}
.deck-card:hover { transform:translateY(-4px); border-color:var(--gold); box-shadow:0 8px 20px rgba(0,0,0,0.5); }
.deck-card.is-commander { border-color:var(--gold-shine); box-shadow:0 0 12px rgba(240,192,64,0.3); }
.deck-card-img     { width:100%; display:block; }
.deck-card-qty     { position:absolute; top:4px; left:4px; background:rgba(0,0,0,0.85); color:var(--gold-shine); font-family:'Cinzel',serif; font-size:0.65rem; font-weight:700; padding:2px 6px; border-radius:2px; z-index:2; }
.deck-card-overlay { position:absolute; bottom:0; left:0; right:0; background:linear-gradient(transparent,rgba(0,0,0,0.92)); padding:8px 6px 6px; }
.deck-card-name    { font-family:'Cinzel',serif; font-size:0.5rem; color:var(--aged-white); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.deck-card-cost    { display:flex; gap:1px; margin-top:2px; }
.deck-card-pt      { font-family:'Cinzel',serif; font-size:0.55rem; color:var(--gold-shine); font-weight:700; text-align:right; }
.legendary-crown   { position:absolute; top:4px; right:4px; font-size:0.8rem; z-index:2; }

/* ── Modal ── */
.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.8); display:flex; align-items:center; justify-content:center; z-index:500; }
.card-modal {
  background:linear-gradient(135deg,#1a130a,#0d0a06);
  border:1px solid var(--gold); border-radius:4px;
  padding:2rem; max-width:680px; width:90vw; position:relative;
  max-height:90vh; overflow-y:auto;
}
.modal-close { position:absolute; top:12px; right:12px; }
.modal-content { display:flex; gap:1.5rem; }
.modal-img     { width:220px; border-radius:6px; flex-shrink:0; }
.modal-info    { flex:1; min-width:0; }
.modal-name    { font-family:'Cinzel Decorative',serif; font-size:1.2rem; color:var(--gold-shine); margin-bottom:4px; }
.modal-type    { font-family:'Cinzel',serif; font-size:0.65rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); opacity:0.8; margin-bottom:8px; }
.modal-oracle  { font-style:italic; color:var(--parchment-dk); line-height:1.65; font-size:0.88rem; background:rgba(0,0,0,0.3); border-left:2px solid rgba(184,134,11,0.3); padding:8px 12px; border-radius:0 2px 2px 0; margin-bottom:10px; }
.modal-pt      { font-family:'Cinzel',serif; font-size:1rem; color:var(--gold-shine); font-weight:700; }
.modal-meta    { display:flex; align-items:center; gap:10px; margin-top:8px; }
.modal-prices  { margin-top:12px; padding-top:12px; border-top:1px solid rgba(184,134,11,0.15); }
.prices-row    { display:flex; gap:8px; flex-wrap:wrap; }
.price-chip    { background:rgba(0,0,0,0.3); border:1px solid rgba(184,134,11,0.2); border-radius:3px; padding:6px 12px; text-align:center; }
.price-chip span  { display:block; font-family:'Cinzel',serif; font-size:0.55rem; letter-spacing:1px; color:var(--gold); }
.price-chip strong{ display:block; font-size:0.9rem; color:var(--aged-white); }
.price-chip.foil  { border-color:rgba(160,200,255,0.3); }

.fade-enter-active,.fade-leave-active{transition:opacity 0.25s}
.fade-enter-from,.fade-leave-to{opacity:0}

@media (max-width:900px) {
  .builder-layout { grid-template-columns:1fr; }
  .builder-sidebar { position:static; max-height:none; }
  .modal-content  { flex-direction:column; }
  .modal-img      { width:100%; max-width:220px; }
  .commander-card-full { flex-direction:column; }
  .commander-img-full  { width:100%; max-width:200px; }
}
</style>
