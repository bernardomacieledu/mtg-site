<template>
  <div>
    <div class="back-bar">
      <button class="btn-ghost" @click="router.push({ name: 'library' })">◂ Biblioteca</button>
    </div>

    <div class="page-hero">
      <h1 class="page-hero-title">{{ collection.name || 'Minha Coleção' }}</h1>
      <p class="page-hero-sub" v-if="collection.stats">
        {{ collection.stats.total_copies }} cópias · {{ collection.stats.total_unique }} únicas · {{ collection.stats.total_sets }} sets
      </p>
      <div class="hero-divider"><span class="hero-divider-gem">📦</span></div>
    </div>

    <div class="page-wrap">
      <!-- Controls -->
      <div class="col-controls">
        <div class="view-tabs">
          <button v-for="v in views" :key="v.id" class="view-tab"
            :class="{ active: activeView === v.id }" @click="activeView = v.id">
            {{ v.icon }} {{ v.label }}
          </button>
        </div>
        <input v-model="filterText" class="medieval-input"
          style="flex:1;max-width:240px;font-size:0.78rem;padding:7px 12px"
          placeholder="Filtrar cartas..." />
        <div style="display:flex;gap:6px;margin-left:auto">
          <button class="btn-ghost" style="font-size:0.62rem" @click="exportJson">📄 JSON</button>
          <button class="btn-ghost" style="font-size:0.62rem" @click="exportText">📋 Lista</button>
        </div>
      </div>

      <div v-if="loadingCollection" class="spinner-wrap">
        <div class="spinner"></div>
        <span class="spinner-text">Abrindo a coleção...</span>
      </div>

      <div v-else-if="!collection.cards?.length" class="empty-state">
        <div class="empty-title">✦ Coleção Vazia ✦</div>
        <p class="empty-sub">Volte à Biblioteca e importe sua coleção</p>
        <button class="btn-ghost" style="margin-top:1.5rem" @click="router.push({name:'library'})">◂ Voltar</button>
      </div>

      <!-- VIEW: Por Tipo -->
      <template v-if="activeView === 'type' && collection.cards?.length">
        <div v-for="(cards, cat) in filteredByCategory" :key="cat" class="cat-section">
          <div class="cat-header">
            <span class="cat-icon">{{ catIcon(cat) }}</span>
            <span class="cat-name">{{ catLabel(cat) }}</span>
            <span class="cat-count">{{ cards.reduce((a,c)=>a+c.qty,0) }} cópias</span>
          </div>
          <div class="cards-grid-col">
            <CardTile v-for="c in cards" :key="c.name" :card="c"
              :active-img="activeImgs[c.name] || c.image_url"
              :hovered="hovered?.name === c.name"
              @mouseenter="setHover(c)"
              @mouseleave="hovered = null"
              @click="router.push({ name: 'card-detail', params: { name: c.name } })"
              @change-print="(url) => changeCardImg(c.name, url)" />
          </div>
        </div>
      </template>

      <!-- VIEW: Por Set -->
      <template v-if="activeView === 'set' && collection.cards?.length">
        <div v-for="s in filteredBySets" :key="s.set_code" class="cat-section">
          <div class="cat-header">
            <img :src="`https://svgs.scryfall.io/sets/${s.set_code.toLowerCase()}.svg`"
              style="width:22px;height:22px;filter:invert(0.85) sepia(0.3);opacity:0.8"
              @error="e=>e.target.style.display='none'" />
            <span class="cat-name">{{ s.set_name }}</span>
            <span class="cat-count">{{ s.cards.reduce((a,c)=>a+c.qty,0) }} cópias</span>
          </div>
          <div class="cards-grid-col">
            <CardTile v-for="c in s.cards.filter(matchFilter)" :key="c.name" :card="c"
              :active-img="activeImgs[c.name] || c.image_url"
              :hovered="hovered?.name === c.name"
              @mouseenter="setHover(c)"
              @mouseleave="hovered = null"
              @click="router.push({ name: 'card-detail', params: { name: c.name } })"
              @change-print="(url) => changeCardImg(c.name, url)" />
          </div>
        </div>
      </template>

      <!-- VIEW: Por Raridade -->
      <template v-if="activeView === 'rarity' && collection.cards?.length">
        <div v-for="r in ['mythic','rare','uncommon','common']" :key="r">
          <div v-if="filteredByRarity[r]?.length" class="cat-section">
            <div class="cat-header">
              <span class="rarity-badge" :class="`rarity-${r}`">{{ rarityLabel(r) }}</span>
              <span class="cat-count">{{ filteredByRarity[r].reduce((a,c)=>a+c.qty,0) }} cópias</span>
            </div>
            <div class="cards-grid-col">
              <CardTile v-for="c in filteredByRarity[r]" :key="c.name" :card="c"
                :active-img="activeImgs[c.name] || c.image_url"
                :hovered="hovered?.name === c.name"
                @mouseenter="setHover(c)"
                @mouseleave="hovered = null"
                @click="router.push({ name: 'card-detail', params: { name: c.name } })"
                @change-print="(url) => changeCardImg(c.name, url)" />
            </div>
          </div>
        </div>
      </template>

      <!-- VIEW: Todas -->
      <template v-if="activeView === 'all' && collection.cards?.length">
        <div class="cards-grid-col">
          <CardTile v-for="c in filteredAll" :key="c.name" :card="c"
            :active-img="activeImgs[c.name] || c.image_url"
            :hovered="hovered?.name === c.name"
            @mouseenter="setHover(c)"
            @mouseleave="hovered = null"
            @click="router.push({ name: 'card-detail', params: { name: c.name } })"
            @change-print="(url) => changeCardImg(c.name, url)" />
        </div>
      </template>

    </div>

    <!-- Global hover preview -->
    <Teleport to="body">
      <div v-if="hovered" class="global-hover-preview" :style="hoverStyle">
        <img :src="activeImgs[hovered.name] || hovered.image_url" class="global-preview-img" />
        <!-- Print switcher no hover -->
        <div v-if="hovered.prints?.length > 1" class="preview-prints">
          <button v-for="p in hovered.prints" :key="p.set_code"
            class="preview-print-btn"
            :class="{ active: (activeImgs[hovered.name] || hovered.image_url) === p.image_url }"
            :title="p.set_code + ' · ' + p.release_date"
            @click.stop="changeCardImg(hovered.name, p.image_url)">
            <img :src="`https://svgs.scryfall.io/sets/${p.set_code.toLowerCase()}.svg`"
              @error="e=>e.target.style.display='none'"
              style="width:14px;height:14px;filter:invert(0.9)" />
            <span>{{ p.set_code.toUpperCase() }}</span>
          </button>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, defineComponent, h } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/composables/api'
import { useCollectionsStore } from '@/stores/collections'
import { apiExportCollection } from '@/composables/api'

const router = useRouter()
const route  = useRoute()
const store  = useCollectionsStore()

// ── CardTile component ────────────────────────────────────────────────────
const CardTile = defineComponent({
  props: {
    card:      { type: Object, required: true },
    activeImg: { type: String,  default: '' },
    hovered:   { type: Boolean, default: false },
  },
  emits: ['click','mouseenter','mouseleave','change-print'],
  setup(props, { emit }) {
    const showPrints = ref(false)
    return () => h('div', {
      class: ['col-card', props.hovered ? 'col-hovered' : ''],
      onClick: () => emit('click'),
      onMouseenter: () => { emit('mouseenter'); showPrints.value = true },
      onMouseleave: () => { emit('mouseleave'); showPrints.value = false },
    }, [
      h('div', { class: 'col-qty' }, `${props.card.qty}×`),
      h('img', {
        src: props.activeImg || props.card.image_url,
        alt: props.card.name,
        class: 'col-img',
        loading: 'lazy',
        onError: (e) => { e.target.src = '' },
      }),
      h('div', { class: 'col-footer' }, [
        h('span', { class: 'col-name' }, props.card.name),
        h('span', { class: `rdot rdot-${props.card.rarity}` }),
      ]),
      // Print switcher na parte inferior do card ao hover
      (showPrints.value && props.card.prints?.length > 1) ? h('div', {
        class: 'card-prints-bar',
        onClick: (e) => e.stopPropagation(),
      }, props.card.prints.slice(0, 6).map(p =>
        h('button', {
          class: ['print-pip', (props.activeImg || props.card.image_url) === p.image_url ? 'active' : ''],
          title: p.set_code,
          onClick: (e) => { e.stopPropagation(); emit('change-print', p.image_url) },
        }, [
          h('img', {
            src: `https://svgs.scryfall.io/sets/${p.set_code.toLowerCase()}.svg`,
            style: 'width:10px;height:10px;filter:invert(0.9)',
            onError: (e) => { e.target.style.display='none' },
          })
        ])
      )) : null,
    ])
  }
})

// ── State ─────────────────────────────────────────────────────────────────
const EMPTY_COLLECTION = {
  name: 'Minha Coleção', cards: [], bySet: [], byRarity: {}, byCategory: {}, stats: null,
}

const collection = ref({ ...EMPTY_COLLECTION })
const loadingCollection = ref(true)

/** Aceita tanto o formato do backend (snake_case) quanto o do localStorage. */
function normalizeCollection(data) {
  return {
    id:         data.id,
    name:       data.name || 'Minha Coleção',
    cards:      data.cards || [],
    bySet:      data.bySet || data.by_set || [],
    byRarity:   data.byRarity || data.by_rarity || {},
    byCategory: data.byCategory || data.by_category || {},
    stats:      data.stats || null,
  }
}

async function loadCollection() {
  loadingCollection.value = true
  try {
    const id = route.params.id
    if (id) {
      // Coleção específica (backend quando logado, localStorage quando não)
      const data = await store.getCollection(id)
      collection.value = data ? normalizeCollection(data) : { ...EMPTY_COLLECTION }
    } else {
      // Rota legada: primeira coleção salva, com fallback para o rascunho local
      await store.loadList()
      const first = store.list[0]
      if (first) {
        const data = await store.getCollection(first.id)
        collection.value = data ? normalizeCollection(data) : { ...EMPTY_COLLECTION }
      } else {
        let legacy = null
        try { legacy = JSON.parse(localStorage.getItem('mtg_collection')) } catch { legacy = null }
        collection.value = legacy ? normalizeCollection(legacy) : { ...EMPTY_COLLECTION }
      }
    }
  } finally {
    loadingCollection.value = false
  }
}

const activeView  = ref('type')
const filterText  = ref('')
const hovered     = ref(null)
const mousePos    = ref({ x: 0, y: 0 })
const activeImgs  = ref({}) // name -> image_url ativo

const views = [
  { id:'type',   icon:'🐉', label:'Por Tipo' },
  { id:'all',    icon:'🃏', label:'Todas' },
  { id:'set',    icon:'📦', label:'Por Set' },
  { id:'rarity', icon:'💎', label:'Por Raridade' },
]

function onMouseMove(e) { mousePos.value = { x: e.clientX, y: e.clientY } }
onMounted(() => window.addEventListener('mousemove', onMouseMove))
onUnmounted(() => window.removeEventListener('mousemove', onMouseMove))

const hoverStyle = computed(() => {
  const x = mousePos.value.x + 24
  const y = mousePos.value.y - 120
  const clampedY = Math.max(10, Math.min(y, window.innerHeight - 420))
  const clampedX = x + 260 > window.innerWidth ? mousePos.value.x - 290 : x
  return { left: clampedX + 'px', top: clampedY + 'px' }
})

function setHover(card) { hovered.value = card }

function changeCardImg(name, url) {
  activeImgs.value = { ...activeImgs.value, [name]: url }
  // Persiste no localStorage
  const saved = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}')
  saved[name] = url
  localStorage.setItem('mtg_active_imgs', JSON.stringify(saved))
}

onMounted(async () => {
  // Restaura imagens salvas
  try { activeImgs.value = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}') }
  catch { activeImgs.value = {} }
  await loadCollection()
})

watch(() => route.params.id, loadCollection)

function matchFilter(card) {
  if (!filterText.value) return true
  const q = filterText.value.toLowerCase()
  return card.name.toLowerCase().includes(q) || card.type_line?.toLowerCase().includes(q)
}

const CAT_ORDER = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']

const filteredByCategory = computed(() => {
  const result = {}
  for (const cat of CAT_ORDER) {
    const cards = (collection.value.byCategory?.[cat] || []).filter(matchFilter)
    if (cards.length) result[cat] = cards
  }
  return result
})
const filteredBySets = computed(() =>
  (collection.value.bySet || [])
    .map(s => ({ ...s, cards: s.cards.filter(matchFilter) }))
    .filter(s => s.cards.length)
)
const filteredByRarity = computed(() => {
  const result = {}
  for (const [r, cards] of Object.entries(collection.value.byRarity || {})) {
    const f = cards.filter(matchFilter); if (f.length) result[r] = f
  }
  return result
})
const filteredAll = computed(() => (collection.value.cards || []).filter(matchFilter))

async function exportJson() {
  const id = route.params.id
  // Quando a coleção tem id salvo, busca fresca do servidor — não depende do
  // que está carregado na tela no momento, e traz as estatísticas também.
  if (id) {
    try {
      const { data } = await apiExportCollection(id)
      const a = Object.assign(document.createElement('a'), {
        href: URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })),
        download: `${data.collection_name || 'colecao'}.json`,
      })
      a.click()
      return
    } catch {
      // segue para o método antigo se o endpoint novo falhar por algum motivo
    }
  }

  const { data } = await api.post('/collection/export/', {
    name: collection.value.name, cards: collection.value.cards
  })
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([JSON.stringify(data,null,2)],{type:'application/json'})),
    download: `${collection.value.name || 'colecao'}.json`
  }); a.click()
}

function exportText() {
  let text = `// ${collection.value.name}\n\n`
  for (const [cat, cards] of Object.entries(filteredByCategory.value)) {
    text += `// ${catLabel(cat)}\n`
    for (const c of cards) text += `${c.qty} ${c.name}\n`
    text += '\n'
  }
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([text],{type:'text/plain'})),
    download: `${collection.value.name || 'colecao'}.txt`
  }); a.click()
}

const CAT_LABELS = { creature:'Criaturas', artifact:'Artefatos', enchantment:'Encantamentos', planeswalker:'Planeswalkers', instant:'Instantâneos', sorcery:'Feitiços', land:'Terrenos', other:'Outros' }
const CAT_ICONS  = { creature:'🐉', artifact:'⚙', enchantment:'✨', planeswalker:'⭐', instant:'⚡', sorcery:'📜', land:'🌲', other:'🃏' }
const RARITY_LABELS = { mythic:'Mítica', rare:'Rara', uncommon:'Incomum', common:'Comum' }
function catLabel(k)    { return CAT_LABELS[k] || k }
function catIcon(k)     { return CAT_ICONS[k]  || '🃏' }
function rarityLabel(r) { return RARITY_LABELS[r] || r }
</script>

<style scoped>
.back-bar { max-width:1400px; margin:0 auto; padding:1.5rem 1.5rem 0; }
.col-controls { display:flex; align-items:center; gap:1rem; margin-bottom:2rem; flex-wrap:wrap; }
.view-tabs { display:flex; gap:4px; flex-wrap:wrap; }
.view-tab  { font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:1px; padding:6px 14px; background:rgba(0,0,0,0.2); border:1px solid rgba(184,134,11,0.2); border-radius:2px; color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s; }
.view-tab.active { border-color:var(--gold-shine); background:rgba(184,134,11,0.1); color:var(--gold-shine); }
.empty-state { text-align:center; padding:6rem 2rem; }
.empty-title { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); margin-bottom:1rem; }
.empty-sub   { font-style:italic; color:var(--parchment-xdk); }
.cat-section { margin-bottom:2.5rem; }
.cat-header  { display:flex; align-items:center; gap:10px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(184,134,11,0.2); }
.cat-icon    { font-size:1.1rem; }
.cat-name    { font-family:'Cinzel',serif; font-size:0.85rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--aged-white); flex:1; }
.cat-count   { font-family:'Cinzel',serif; font-size:0.6rem; color:var(--gold); background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.2); padding:3px 10px; border-radius:2px; }
.cards-grid-col { display:grid; grid-template-columns:repeat(auto-fill,minmax(120px,1fr)); gap:10px; }

/* CardTile */
:deep(.col-card) { position:relative; border-radius:3px; overflow:hidden; border:1px solid rgba(184,134,11,0.15); cursor:pointer; transition:all 0.2s; background:#0d0a06; }
:deep(.col-card:hover), :deep(.col-hovered) { border-color:var(--gold); transform:translateY(-4px); box-shadow:0 6px 20px rgba(0,0,0,0.5); }
:deep(.col-qty)  { position:absolute; top:3px; left:3px; background:rgba(0,0,0,0.88); color:var(--gold-shine); font-family:'Cinzel',serif; font-size:0.6rem; font-weight:700; padding:1px 5px; border-radius:2px; z-index:2; }
:deep(.col-img)  { width:100%; display:block; }
:deep(.col-footer) { display:flex; align-items:center; justify-content:space-between; padding:3px 5px; background:rgba(0,0,0,0.7); }
:deep(.col-name) { font-family:'Cinzel',serif; font-size:0.42rem; color:var(--parchment-dk); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }
:deep(.rdot) { width:7px; height:7px; border-radius:50%; flex-shrink:0; margin-left:3px; display:inline-block; }
:deep(.rdot-mythic){background:#e07820} :deep(.rdot-rare){background:#d4a017}
:deep(.rdot-uncommon){background:#a8c6d4} :deep(.rdot-common){background:#94a3b8}

/* Print switcher na carta */
:deep(.card-prints-bar) {
  position:absolute; bottom:0; left:0; right:0;
  display:flex; gap:3px; padding:4px 5px;
  background:rgba(0,0,0,0.88); flex-wrap:wrap;
  border-top:1px solid rgba(184,134,11,0.3);
  z-index:10;
}
:deep(.print-pip) {
  width:18px; height:18px; border-radius:2px;
  background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.25);
  cursor:pointer; display:flex; align-items:center; justify-content:center;
  transition:all 0.15s; padding:0;
}
:deep(.print-pip:hover), :deep(.print-pip.active) {
  background:rgba(184,134,11,0.3); border-color:var(--gold);
}

/* Preview hover global */
.preview-prints {
  display:flex; flex-wrap:wrap; gap:4px; margin-top:8px;
  background:rgba(0,0,0,0.85); border-radius:4px; padding:6px;
  border:1px solid rgba(184,134,11,0.3);
}
.preview-print-btn {
  display:flex; align-items:center; gap:4px;
  background:rgba(184,134,11,0.08); border:1px solid rgba(184,134,11,0.2);
  border-radius:2px; padding:3px 7px; cursor:pointer; transition:all 0.15s;
}
.preview-print-btn:hover, .preview-print-btn.active {
  background:rgba(184,134,11,0.2); border-color:var(--gold);
}
.preview-print-btn span {
  font-family:'Cinzel',serif; font-size:0.5rem; color:var(--parchment-dk);
}
</style>