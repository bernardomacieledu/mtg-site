<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Biblioteca Arcana</h1>
      <p class="page-hero-sub">Gerencie seus decks e coleção de cartas</p>
      <div class="hero-divider"><span class="hero-divider-gem">📚</span></div>
    </div>

    <div class="page-wrap">
      <div class="lib-tabs">
        <button v-for="tab in tabs" :key="tab.id"
          class="lib-tab" :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- ════ TAB: DECKS ════ -->
      <div v-if="activeTab === 'decks'" class="tab-content">
        <div class="items-grid">
          <div v-for="deck in decks" :key="deck.id"
            class="item-card" @click="router.push({ name: 'deck-detail', params: { id: deck.id } })">
            <div class="item-card-header">
              <div class="color-pips-sm">
                <span v-for="c in deck.colors" :key="c" class="pip-sm" :class="`pip-${c.toLowerCase()}`">{{ c }}</span>
              </div>
              <span v-if="deck.commander" class="commander-tag">👑 CMD</span>
            </div>
            <div class="item-card-name">{{ deck.name }}</div>
            <div class="item-card-meta">
              <span>{{ deck.total_cards }} cartas</span>
              <span>CMC {{ deck.avg_cmc }}</span>
            </div>
            <div v-if="deck.commander" class="item-commander">
              <img :src="deck.commander.image_url" :alt="deck.commander.name"
                class="commander-mini-img" @error="e=>e.target.style.display='none'" />
              <span class="commander-mini-name">{{ deck.commander.name }}</span>
            </div>
            <div class="item-card-actions">
              <button class="action-sm" @click.stop="openDeckModal(deck)">✏ Editar</button>
              <button class="action-sm danger" @click.stop="removeDeck(deck.id)">🗑</button>
            </div>
          </div>

          <div class="add-card" @click="openDeckModal()">
            <div class="add-icon">＋</div>
            <div class="add-label">Novo Deck</div>
            <div class="add-sub">Importe ou crie um deck</div>
          </div>
        </div>
      </div>

      <!-- ════ TAB: COLEÇÃO ════ -->
      <div v-if="activeTab === 'collection'" class="tab-content">
        <div v-if="!collection.cards?.length" class="items-grid">
          <div class="add-card" @click="openCollectionModal()">
            <div class="add-icon">＋</div>
            <div class="add-label">Importar Coleção</div>
            <div class="add-sub">Adicione suas cartas</div>
          </div>
        </div>

        <div v-else>
          <div v-if="collection.stats" class="stats-bar-inline">
            <div class="stat-chip">📦 <strong>{{ collection.stats.total_copies }}</strong> cópias</div>
            <div class="stat-chip">🃏 <strong>{{ collection.stats.total_unique }}</strong> únicas</div>
            <div class="stat-chip">📚 <strong>{{ collection.stats.total_sets }}</strong> sets</div>
            <div style="margin-left:auto;display:flex;gap:6px;">
              <button class="btn-ghost" style="font-size:0.62rem" @click="openCollectionModal()">+ Atualizar</button>
              <button class="btn-primary" style="font-size:0.62rem" @click="router.push({ name: 'collection-detail' })">📂 Abrir Coleção</button>
            </div>
          </div>

          <div v-for="(cards, cat) in previewByCategory" :key="cat" class="preview-cat">
  <div class="preview-cat-header" @click="toggleCat(cat)" style="cursor:pointer">
    {{ catIcon(cat) }} {{ catLabel(cat) }}
    <span class="col-group-count">{{ cards.reduce((a,c)=>a+c.qty,0) }}</span>
    <span style="margin-left:auto;font-size:0.65rem;color:var(--gold)">
      {{ collapseState[cat] ? '▶ expandir' : '▼ recolher' }}
    </span>
  </div>
  <div v-if="!collapseState[cat]" class="preview-grid">
    <div v-for="c in cards" :key="c.name"
      class="preview-card"
      @mouseenter="hovered = c"
      @mouseleave="hovered = null"
      @click="router.push({ name: 'card-detail', params: { name: c.name } })">
      <img :src="c.image_url" :alt="c.name" class="preview-img" @error="e=>e.target.src=''" />
      <div class="preview-qty">{{ c.qty }}×</div>
    </div>
  </div>
</div>
        </div>
      </div>
    </div>

    <!-- ════ MODAL: Deck ════ -->
    <Transition name="fade">
      <div v-if="showDeckModal" class="modal-overlay" @click.self="showDeckModal=false">
        <div class="import-modal">
          <button class="modal-close btn-ghost" @click="showDeckModal=false">✕</button>
          <h2 class="modal-title">{{ editingDeck ? '✏ Editar Deck' : '⚒ Novo Deck' }}</h2>
          <label class="field-label">Nome do Deck</label>
          <input v-model="deckForm.name" class="medieval-input" placeholder="Meu Deck..." style="margin-bottom:1rem" />
          <label class="field-label">Lista de Cartas</label>
          <textarea v-model="deckForm.text" class="medieval-input import-ta" rows="10"
            placeholder="1 Sol Ring&#10;4 Island&#10;1 Inspirit, Flagship Vessel..." />
          <div v-if="deckForm.legendaries.length" style="margin-top:1rem">
            <label class="field-label">👑 Comandante (qualquer lendário)</label>
            <select v-model="deckForm.commanderName" class="medieval-input">
              <option value="">— Nenhum —</option>
              <option v-for="c in deckForm.legendaries" :key="c.name" :value="c.name">
                {{ c.name }} — {{ c.type_line }}
              </option>
            </select>
          </div>
          <div v-if="deckForm.msg" class="form-msg" :class="deckForm.msg.startsWith('❌')?'err':'ok'">{{ deckForm.msg }}</div>
          <div style="display:flex;gap:8px;margin-top:1rem">
            <button class="btn-primary" style="flex:1" :disabled="deckForm.loading" @click="saveDeck">
              {{ deckForm.loading ? '⏳ Importando...' : '✦ Salvar Deck' }}
            </button>
            <button class="btn-ghost" @click="showDeckModal=false">Cancelar</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- ════ MODAL: Coleção ════ -->
    <Transition name="fade">
      <div v-if="showColModal" class="modal-overlay" @click.self="showColModal=false">
        <div class="import-modal">
          <button class="modal-close btn-ghost" @click="showColModal=false">✕</button>
          <h2 class="modal-title">📦 Importar Coleção</h2>
          <label class="field-label">Nome</label>
          <input v-model="colForm.name" class="medieval-input" placeholder="Minha Coleção..." style="margin-bottom:1rem" />
          <label class="field-label">Lista</label>
          <textarea v-model="colForm.text" class="medieval-input import-ta" rows="10"
            placeholder="4 Lightning Bolt&#10;2 Black Lotus&#10;20 Island..." />
          <div v-if="colForm.msg" class="form-msg" :class="colForm.msg.startsWith('❌')?'err':'ok'">{{ colForm.msg }}</div>
          <div style="display:flex;gap:8px;margin-top:1rem">
            <button class="btn-primary" style="flex:1" :disabled="colForm.loading" @click="importCollection">
              {{ colForm.loading ? '⏳ Importando...' : '✦ Importar' }}
            </button>
            <button class="btn-ghost" @click="showColModal=false">Cancelar</button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Hover preview global -->
    <Teleport to="body">
      <div v-if="hovered" class="global-hover-preview" :style="hoverStyle">
        <img :src="hovered.image_url" class="global-preview-img" />
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

const activeTab = ref('decks')
const tabs = [
  { id: 'decks',      icon: '⚔', label: 'Meus Decks' },
  { id: 'collection', icon: '📦', label: 'Minha Coleção' },
]

const hovered  = ref(null)
const mousePos = ref({ x: 0, y: 0 })

function onMouseMove(e) { mousePos.value = { x: e.clientX, y: e.clientY } }
onMounted(() => window.addEventListener('mousemove', onMouseMove))
onUnmounted(() => window.removeEventListener('mousemove', onMouseMove))

const hoverStyle = computed(() => {
  const x = mousePos.value.x + 20
  const y = mousePos.value.y - 100
  const clampedY = Math.max(10, Math.min(y, window.innerHeight - 350))
  const clampedX = x + 240 > window.innerWidth ? mousePos.value.x - 260 : x
  return { left: clampedX + 'px', top: clampedY + 'px' }
})

// ── Decks ─────────────────────────────────────────────────────────────────
const decks         = ref(JSON.parse(localStorage.getItem('mtg_decks') || '[]'))
const showDeckModal = ref(false)
const editingDeck   = ref(null)
const deckForm      = ref({ name:'', text:'', loading:false, msg:'', legendaries:[], commanderName:'' })

function saveDecksLocal() { localStorage.setItem('mtg_decks', JSON.stringify(decks.value)) }

function openDeckModal(deck = null) {
  editingDeck.value = deck
  deckForm.value = {
    name: deck?.name || '', text: deck?.raw_text || '',
    loading: false, msg: '',
    legendaries: deck?.legendaries || [],
    commanderName: deck?.commander?.name || '',
  }
  showDeckModal.value = true
}

function removeDeck(id) {
  decks.value = decks.value.filter(d => d.id !== id)
  saveDecksLocal()
}

async function saveDeck() {
  if (!deckForm.value.text.trim()) { deckForm.value.msg = '❌ Cole a lista.'; return }
  deckForm.value.loading = true; deckForm.value.msg = ''
  try {
    const { data } = await axios.post('/api/deck/import/', { text: deckForm.value.text })

    const commander = deckForm.value.commanderName
      ? data.legendary_creatures?.find(c => c.name === deckForm.value.commanderName) || null
      : (data.legendary_creatures?.length === 1 ? data.legendary_creatures[0] : null)

    const CAT_ORDER = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']
    const categorized = {}
    for (const cat of CAT_ORDER) {
      const cards = (data.categories[cat] || []).filter(c => c.name !== commander?.name)
      if (cards.length) categorized[cat] = cards
    }

    const deck = {
      id:          editingDeck.value?.id || Date.now().toString(),
      name:        deckForm.value.name || 'Deck sem nome',
      raw_text:    deckForm.value.text,
      cards:       data.cards,
      categorized,
      commander,
      legendaries: data.legendary_creatures || [],
      colors:      [...new Set(data.cards.flatMap(c => c.color_identity || []))],
      total_cards: data.stats.total_cards,
      avg_cmc:     data.stats.avg_cmc,
      not_found:   data.not_found,
    }

    if (editingDeck.value) {
      const idx = decks.value.findIndex(d => d.id === editingDeck.value.id)
      if (idx >= 0) decks.value[idx] = deck
    } else {
      decks.value.push(deck)
    }

    saveDecksLocal()
    deckForm.value.legendaries   = data.legendary_creatures || []
    deckForm.value.commanderName = commander?.name || ''
    deckForm.value.msg = `✔ ${data.stats.total_cards} cartas!`
    setTimeout(() => { showDeckModal.value = false }, 1000)
  } catch(e) {
    deckForm.value.msg = '❌ Erro ao importar.'
    console.error(e)
  } finally { deckForm.value.loading = false }
}

// ── Collection ────────────────────────────────────────────────────────────
const collection = ref(JSON.parse(localStorage.getItem('mtg_collection') ||
  '{"cards":[],"bySet":[],"byRarity":{},"byCategory":{},"stats":null,"name":"Minha Coleção"}'))
const showColModal = ref(false)
const colForm      = ref({ name:'Minha Coleção', text:'', loading:false, msg:'' })

const collapseState = ref({})
function toggleCat(cat) {
  collapseState.value[cat] = !collapseState.value[cat]
}

const CAT_ORDER_PREVIEW = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']
const previewByCategory = computed(() => {
  const result = {}
  for (const cat of CAT_ORDER_PREVIEW) {
    const cards = collection.value.byCategory?.[cat] || []
    if (cards.length) result[cat] = cards
  }
  return result
})

function openCollectionModal() {
  colForm.value = { name: collection.value.name || 'Minha Coleção', text:'', loading:false, msg:'' }
  showColModal.value = true
}

async function importCollection() {
  if (!colForm.value.text.trim()) { colForm.value.msg = '❌ Cole a lista.'; return }
  colForm.value.loading = true; colForm.value.msg = ''
  try {
    const { data } = await axios.post('/api/collection/import/', { text: colForm.value.text })
    collection.value = {
      name: colForm.value.name,
      cards: data.cards, bySet: data.by_set,
      byRarity: data.by_rarity, byCategory: data.by_category,
      stats: data.stats,
    }
    localStorage.setItem('mtg_collection', JSON.stringify(collection.value))
    colForm.value.msg = `✔ ${data.stats.total_unique} cartas importadas!`
    setTimeout(() => { showColModal.value = false }, 1000)
  } catch(e) {
    colForm.value.msg = '❌ Erro ao importar.'
    console.error(e)
  } finally { colForm.value.loading = false }
}

// ── Helpers ───────────────────────────────────────────────────────────────
const CAT_LABELS = { creature:'Criaturas', artifact:'Artefatos', enchantment:'Encantamentos', planeswalker:'Planeswalkers', instant:'Instantâneos', sorcery:'Feitiços', land:'Terrenos', other:'Outros' }
const CAT_ICONS  = { creature:'🐉', artifact:'⚙', enchantment:'✨', planeswalker:'⭐', instant:'⚡', sorcery:'📜', land:'🌲', other:'🃏' }
function catLabel(k) { return CAT_LABELS[k] || k }
function catIcon(k)  { return CAT_ICONS[k]  || '🃏' }
</script>

<style scoped>
.lib-tabs { display:flex; gap:4px; margin-bottom:2rem; border-bottom:1px solid rgba(184,134,11,0.2); }
.lib-tab  { font-family:'Cinzel',serif; font-size:0.75rem; letter-spacing:2px; padding:10px 24px; background:transparent; border:none; border-bottom:2px solid transparent; color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s; margin-bottom:-1px; }
.lib-tab.active { color:var(--gold-shine); border-bottom-color:var(--gold-shine); }
.tab-content { min-height:400px; }

.items-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(230px,1fr)); gap:1rem; }
.item-card  { background:linear-gradient(135deg,rgba(26,19,10,0.95),rgba(13,10,6,0.95)); border:1px solid rgba(184,134,11,0.22); border-radius:4px; padding:1.2rem; cursor:pointer; transition:all 0.25s; display:flex; flex-direction:column; gap:8px; }
.item-card:hover { border-color:var(--gold); transform:translateY(-3px); box-shadow:0 8px 24px rgba(0,0,0,0.4); }
.item-card-header { display:flex; align-items:center; justify-content:space-between; }
.item-card-name   { font-family:'Cinzel',serif; font-size:0.95rem; color:var(--aged-white); font-weight:700; }
.item-card-meta   { display:flex; gap:10px; font-size:0.7rem; color:var(--parchment-xdk); }
.item-commander   { display:flex; align-items:center; gap:8px; padding:6px; background:rgba(0,0,0,0.2); border-radius:2px; border:1px solid rgba(184,134,11,0.15); }
.commander-mini-img  { width:32px; height:44px; object-fit:cover; border-radius:2px; }
.commander-mini-name { font-family:'Cinzel',serif; font-size:0.62rem; color:var(--parchment-dk); }
.commander-tag    { font-family:'Cinzel',serif; font-size:0.52rem; color:var(--gold); }
.item-card-actions { display:flex; gap:6px; margin-top:auto; padding-top:8px; border-top:1px solid rgba(184,134,11,0.1); }
.action-sm { font-family:'Cinzel',serif; font-size:0.58rem; padding:4px 10px; background:rgba(0,0,0,0.2); border:1px solid rgba(184,134,11,0.2); border-radius:2px; color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s; }
.action-sm:hover { border-color:var(--gold); color:var(--gold); }
.action-sm.danger:hover { border-color:var(--crimson-lt); color:var(--crimson-lt); }

.add-card { border:2px dashed rgba(184,134,11,0.25); border-radius:4px; padding:2rem; display:flex; flex-direction:column; align-items:center; justify-content:center; gap:8px; cursor:pointer; transition:all 0.2s; min-height:140px; }
.add-card:hover { border-color:var(--gold); background:rgba(184,134,11,0.05); }
.add-icon  { font-size:2rem; color:rgba(184,134,11,0.4); }
.add-label { font-family:'Cinzel',serif; font-size:0.8rem; letter-spacing:2px; color:var(--parchment-xdk); }
.add-sub   { font-size:0.7rem; color:rgba(184,134,11,0.4); font-style:italic; }

.color-pips-sm { display:flex; gap:4px; }
.pip-sm { width:18px; height:18px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.5rem; font-weight:700; }
.pip-w{background:#c8b896;color:#1a0f00} .pip-u{background:#1a3a6b;color:#a8d4f5}
.pip-b{background:#2a1a3e;color:#c8a8f5} .pip-r{background:#6b1a1a;color:#f5a8a8}
.pip-g{background:#1a3a1a;color:#a8f5a8}

.stats-bar-inline { display:flex; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:2rem; padding:10px 14px; background:rgba(0,0,0,0.2); border:1px solid rgba(184,134,11,0.15); border-radius:3px; }
.stat-chip { font-family:'Cinzel',serif; font-size:0.65rem; color:var(--parchment-xdk); }
.stat-chip strong { color:var(--gold); }

.preview-cat { margin-bottom:2rem; }
.preview-cat-header { font-family:'Cinzel',serif; font-size:0.75rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); display:flex; align-items:center; gap:10px; margin-bottom:10px; padding-bottom:6px; border-bottom:1px solid rgba(184,134,11,0.15); }
.col-group-count { font-size:0.58rem; background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.18); padding:2px 8px; border-radius:2px; }
.preview-grid { display:flex; flex-wrap:wrap; gap:6px; }
.preview-card { position:relative; width:80px; cursor:pointer; border-radius:3px; overflow:hidden; border:1px solid rgba(184,134,11,0.15); transition:all 0.2s; flex-shrink:0; }
.preview-card:hover { border-color:var(--gold); transform:translateY(-4px) scale(1.05); z-index:10; }
.preview-img  { width:100%; display:block; }
.preview-qty  { position:absolute; top:2px; left:2px; background:rgba(0,0,0,0.85); color:var(--gold-shine); font-family:'Cinzel',serif; font-size:0.55rem; font-weight:700; padding:1px 4px; border-radius:2px; }
.preview-more { width:80px; height:112px; display:flex; align-items:center; justify-content:center; border:1px dashed rgba(184,134,11,0.3); border-radius:3px; cursor:pointer; font-family:'Cinzel',serif; font-size:0.6rem; color:var(--gold); transition:all 0.2s; flex-shrink:0; }
.preview-more:hover { border-color:var(--gold); background:rgba(184,134,11,0.08); }

.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.8); display:flex; align-items:center; justify-content:center; z-index:500; }
.import-modal  { background:linear-gradient(135deg,#1a130a,#0d0a06); border:1px solid var(--gold); border-radius:4px; padding:2rem; width:90vw; max-width:500px; position:relative; max-height:90vh; overflow-y:auto; }
.modal-title   { font-family:'Cinzel Decorative',serif; font-size:1.1rem; color:var(--gold-shine); margin-bottom:1rem; }
.modal-close   { position:absolute; top:12px; right:12px; }
.import-ta     { font-family:'Courier New',monospace; font-size:0.78rem; resize:vertical; min-height:180px; line-height:1.6; }
.form-msg      { font-family:'Cinzel',serif; font-size:0.62rem; margin-top:8px; text-align:center; }
.form-msg.ok { color:var(--gold); } .form-msg.err { color:var(--crimson-lt); }
.fade-enter-active,.fade-leave-active{transition:opacity 0.25s}
.fade-enter-from,.fade-leave-to{opacity:0}
</style>
