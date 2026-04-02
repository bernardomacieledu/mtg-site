<template>
  <div v-if="!deck" class="spinner-wrap" style="height:80vh">
    <div class="spinner"></div>
    <span class="spinner-text">Carregando deck...</span>
  </div>

  <div v-else>
    <div class="back-bar">
      <button class="btn-ghost" @click="router.push({ name: 'library' })">◂ Biblioteca</button>
    </div>

    <div class="page-hero">
      <div class="deck-hero-colors">
        <span v-for="c in deck.colors" :key="c" class="pip-lg" :class="`pip-${c.toLowerCase()}`">{{ c }}</span>
      </div>
      <h1 class="page-hero-title">{{ deck.name }}</h1>
      <p class="page-hero-sub">{{ deck.total_cards }} cartas · CMC médio {{ deck.avg_cmc }}</p>
      <div class="hero-divider"><span class="hero-divider-gem">⚔</span></div>
    </div>

    <div class="page-wrap">

      <!-- Commander -->
      <div v-if="deck.commander" class="commander-section">
        <div class="commander-banner">
          <span class="commander-crown">👑</span>
          <span class="cinzel-caps">Comandante</span>
        </div>
        <div class="commander-card-full">
          <div class="commander-art-wrap"
            @mouseenter="hovered = deck.commander"
            @mouseleave="hovered = null">
            <img
              :src="activeImgs[deck.commander.name] || deck.commander.image_url"
              :alt="deck.commander.name"
              class="commander-img-full"
              @error="e=>e.target.style.display='none'"
              @click="router.push({ name: 'card-detail', params: { name: deck.commander.name } })"
              style="cursor:pointer"
            />
            <!-- Print switcher do comandante -->
            <div v-if="deck.commander.prints?.length > 1" class="cmd-prints">
              <button v-for="p in deck.commander.prints" :key="p.set_code"
                class="cmd-print-btn"
                :class="{ active: (activeImgs[deck.commander.name] || deck.commander.image_url) === p.image_url }"
                :title="p.set_code + ' · ' + p.release_date"
                @click="changeCardImg(deck.commander.name, p.image_url)">
                <img :src="`https://svgs.scryfall.io/sets/${p.set_code.toLowerCase()}.svg`"
                  @error="e=>e.target.style.display='none'"
                  style="width:14px;height:14px;filter:invert(0.9)" />
                <span>{{ p.set_code.toUpperCase() }}</span>
              </button>
            </div>
          </div>
          <div class="commander-details">
            <h2 class="commander-full-name">{{ deck.commander.name }}</h2>
            <div v-html="renderMana(deck.commander.mana_cost)" style="margin:8px 0" />
            <div class="detail-type">{{ deck.commander.type_line }}</div>
            <div class="detail-oracle">{{ deck.commander.oracle_text }}</div>
            <div class="detail-meta">
              <span class="rarity-badge" :class="`rarity-${deck.commander.rarity}`">{{ deck.commander.rarity }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Controls -->
      <div class="deck-controls">
        <div class="view-tabs">
          <button class="view-tab" :class="{ active: view==='grid' }" @click="view='grid'">⊞ Grid</button>
          <button class="view-tab" :class="{ active: view==='list' }" @click="view='list'">☰ Lista</button>
        </div>
        <div style="margin-left:auto;display:flex;gap:8px">
          <button class="btn-ghost" style="font-size:0.62rem" @click="exportJson">📄 JSON</button>
          <button class="btn-ghost" style="font-size:0.62rem" @click="exportText">📋 Lista</button>
          <button class="btn-ghost" style="font-size:0.62rem" @click="openEdit">✏ Editar</button>
        </div>
      </div>

      <div v-if="deck.not_found?.length" class="not-found-bar">
        ⚠ Não encontradas: {{ deck.not_found.join(', ') }}
      </div>

      <!-- GRID VIEW -->
      <template v-if="view === 'grid'">
        <div v-for="(cards, cat) in deck.categorized" :key="cat" class="cat-section">
          <div class="cat-header">
            <span class="cat-icon">{{ catIcon(cat) }}</span>
            <span class="cat-name">{{ catLabel(cat) }}</span>
            <span class="cat-count">{{ cards.reduce((a,c)=>a+c.qty,0) }} cartas</span>
          </div>
          <div class="cards-grid-deck">
            <div v-for="card in cards" :key="card.name"
              class="deck-card"
              @mouseenter="hovered = card"
              @mouseleave="hovered = null">
              <div class="deck-card-qty">{{ card.qty }}×</div>
              <img
                :src="activeImgs[card.name] || card.image_url"
                :alt="card.name"
                class="deck-card-img"
                loading="lazy"
                @error="e=>e.target.src=''"
                @click="router.push({ name: 'card-detail', params: { name: card.name } })"
                style="cursor:pointer"
              />
              <!-- Print switcher no card -->
              <div v-if="card.prints?.length > 1" class="card-prints-bar"
                @click.stop>
                <button v-for="p in card.prints.slice(0,6)" :key="p.set_code"
                  class="print-pip"
                  :class="{ active: (activeImgs[card.name] || card.image_url) === p.image_url }"
                  :title="p.set_code"
                  @click="changeCardImg(card.name, p.image_url)">
                  <img :src="`https://svgs.scryfall.io/sets/${p.set_code.toLowerCase()}.svg`"
                    @error="e=>e.target.style.display='none'"
                    style="width:10px;height:10px;filter:invert(0.9)" />
                </button>
              </div>
              <div class="deck-card-footer">
                <span class="deck-card-name">{{ card.name }}</span>
                <span class="rdot" :class="'rdot-' + card.rarity"></span>
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- LIST VIEW -->
      <template v-else>
        <div v-for="(cards, cat) in deck.categorized" :key="cat" class="cat-section">
          <div class="cat-header">
            <span class="cat-icon">{{ catIcon(cat) }}</span>
            <span class="cat-name">{{ catLabel(cat) }}</span>
            <span class="cat-count">{{ cards.reduce((a,c)=>a+c.qty,0) }}</span>
          </div>
          <div class="list-rows">
            <div v-for="card in cards" :key="card.name" class="list-row"
              @mouseenter="hovered = card"
              @mouseleave="hovered = null">
              <span class="list-qty">{{ card.qty }}×</span>
              <span class="list-name" style="cursor:pointer"
                @click="router.push({ name: 'card-detail', params: { name: card.name } })">
                {{ card.name }}
              </span>
              <span class="list-mana" v-html="renderMana(card.mana_cost)" />
              <span class="list-type">{{ card.type_line }}</span>
              <!-- Print select na lista -->
              <select v-if="card.prints?.length > 1"
                class="print-select"
                :value="activeImgs[card.name] || card.image_url"
                @change="changeCardImg(card.name, $event.target.value)"
                @click.stop>
                <option v-for="p in card.prints" :key="p.set_code" :value="p.image_url">
                  {{ p.set_code.toUpperCase() }} · {{ p.release_date?.slice(0,4) }}
                </option>
              </select>
              <span class="rarity-badge" :class="`rarity-${card.rarity}`" style="font-size:0.52rem">{{ card.rarity }}</span>
            </div>
          </div>
        </div>
      </template>

    </div>

    <!-- Global hover preview -->
    <Teleport to="body">
      <div v-if="hovered" class="global-hover-preview" :style="hoverStyle">
        <img :src="activeImgs[hovered.name] || hovered.image_url" class="global-preview-img" />
      </div>
    </Teleport>

    <!-- Edit modal -->
    <Transition name="fade">
      <div v-if="showEdit" class="modal-overlay" @click.self="showEdit=false">
        <div class="import-modal">
          <button class="modal-close btn-ghost" @click="showEdit=false">✕</button>
          <h2 class="modal-title">✏ Editar Deck</h2>
          <label class="field-label">Nome</label>
          <input v-model="editForm.name" class="medieval-input" style="margin-bottom:1rem" />
          <label class="field-label">Lista</label>
          <textarea v-model="editForm.text" class="medieval-input" rows="10"
            style="font-family:'Courier New',monospace;font-size:0.78rem;resize:vertical;min-height:180px" />
          <div v-if="editForm.legendaries.length" style="margin-top:1rem">
            <label class="field-label">👑 Comandante (qualquer lendário)</label>
            <select v-model="editForm.commanderName" class="medieval-input">
              <option value="">— Nenhum —</option>
              <option v-for="c in editForm.legendaries" :key="c.name" :value="c.name">
                {{ c.name }} — {{ c.type_line }}
              </option>
            </select>
          </div>
          <div v-if="editForm.msg" class="form-msg" :class="editForm.msg.startsWith('❌')?'err':'ok'">{{ editForm.msg }}</div>
          <div style="display:flex;gap:8px;margin-top:1rem">
            <button class="btn-primary" style="flex:1" :disabled="editForm.loading" @click="saveEdit">
              {{ editForm.loading ? '⏳...' : '✦ Salvar' }}
            </button>
            <button class="btn-ghost" @click="showEdit=false">Cancelar</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { useMana } from '@/composables/useMana'

const route  = useRoute()
const router = useRouter()
const { symbols } = useMana()

const deck      = ref(null)
const view      = ref('grid')
const hovered   = ref(null)
const showEdit  = ref(false)
const editForm  = ref({ name:'', text:'', loading:false, msg:'', legendaries:[], commanderName:'' })
const mousePos  = ref({ x: 0, y: 0 })
const activeImgs = ref({})

function onMouseMove(e) { mousePos.value = { x: e.clientX, y: e.clientY } }
onMounted(() => {
  window.addEventListener('mousemove', onMouseMove)
  const decks = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
  deck.value  = decks.find(d => d.id === route.params.id) || null
  // Restaura imagens salvas
  const saved = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}')
  activeImgs.value = saved
})
onUnmounted(() => window.removeEventListener('mousemove', onMouseMove))

const hoverStyle = computed(() => {
  const x = mousePos.value.x + 24
  const y = mousePos.value.y - 120
  const clampedY = Math.max(10, Math.min(y, window.innerHeight - 380))
  const clampedX = x + 260 > window.innerWidth ? mousePos.value.x - 280 : x
  return { left: clampedX + 'px', top: clampedY + 'px' }
})

function changeCardImg(name, url) {
  activeImgs.value = { ...activeImgs.value, [name]: url }
  const saved = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}')
  saved[name] = url
  localStorage.setItem('mtg_active_imgs', JSON.stringify(saved))
}

function renderMana(cost) {
  if (!cost) return ''
  return cost.replace(/\{([^}]+)\}/g, (match) => {
    const uri = symbols.value[match]
    return uri ? `<img src="${uri}" class="ms" style="width:16px;height:16px" alt="${match}">` : match
  })
}

function openEdit() {
  editForm.value = {
    name: deck.value.name, text: deck.value.raw_text,
    loading: false, msg: '',
    legendaries: deck.value.legendaries || [],
    commanderName: deck.value.commander?.name || '',
  }
  showEdit.value = true
}

async function saveEdit() {
  if (!editForm.value.text.trim()) return
  editForm.value.loading = true
  try {
    const { data } = await axios.post('/api/deck/import/', { text: editForm.value.text })
    const commander = editForm.value.commanderName
      ? data.legendary_creatures?.find(c => c.name === editForm.value.commanderName) || null
      : null

    const CAT_ORDER = ['creature','artifact','enchantment','planeswalker','instant','sorcery','land','other']
    const categorized = {}
    for (const cat of CAT_ORDER) {
      const cards = (data.categories[cat] || []).filter(c => c.name !== commander?.name)
      if (cards.length) categorized[cat] = cards
    }

    const updated = {
      ...deck.value,
      name: editForm.value.name,
      raw_text: editForm.value.text,
      cards: data.cards, categorized, commander,
      legendaries: data.legendary_creatures || [],
      colors: [...new Set(data.cards.flatMap(c => c.color_identity || []))],
      total_cards: data.stats.total_cards,
      avg_cmc: data.stats.avg_cmc,
    }

    deck.value = updated
    const decks = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
    const idx   = decks.findIndex(d => d.id === deck.value.id)
    if (idx >= 0) decks[idx] = updated
    localStorage.setItem('mtg_decks', JSON.stringify(decks))
    editForm.value.msg = '✔ Salvo!'
    setTimeout(() => { showEdit.value = false }, 800)
  } catch(e) {
    editForm.value.msg = '❌ Erro.'
  } finally { editForm.value.loading = false }
}

function exportJson() {
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([JSON.stringify(deck.value,null,2)],{type:'application/json'})),
    download: `${deck.value.name}.json`
  }); a.click()
}

function exportText() {
  let text = `// ${deck.value.name}\n`
  if (deck.value.commander) text += `// Comandante: ${deck.value.commander.name}\n\n`
  for (const [cat, cards] of Object.entries(deck.value.categorized || {})) {
    text += `// ${catLabel(cat)}\n`
    for (const c of cards) text += `${c.qty} ${c.name}\n`
    text += '\n'
  }
  const a = Object.assign(document.createElement('a'), {
    href: URL.createObjectURL(new Blob([text],{type:'text/plain'})),
    download: `${deck.value.name}.txt`
  }); a.click()
}

const CAT_LABELS = { creature:'Criaturas', artifact:'Artefatos', enchantment:'Encantamentos', planeswalker:'Planeswalkers', instant:'Instantâneos', sorcery:'Feitiços', land:'Terrenos', other:'Outros' }
const CAT_ICONS  = { creature:'🐉', artifact:'⚙', enchantment:'✨', planeswalker:'⭐', instant:'⚡', sorcery:'📜', land:'🌲', other:'🃏' }
function catLabel(k) { return CAT_LABELS[k] || k }
function catIcon(k)  { return CAT_ICONS[k]  || '🃏' }
</script>

<style scoped>
.back-bar { max-width:1400px; margin:0 auto; padding:1.5rem 1.5rem 0; }

.commander-section { margin-bottom:3rem; }
.commander-banner  { display:flex; align-items:center; gap:10px; margin-bottom:12px; }
.commander-crown   { font-size:1.4rem; }
.commander-card-full { display:flex; gap:1.5rem; background:linear-gradient(135deg,rgba(26,19,10,0.95),rgba(13,10,6,0.95)); border:2px solid var(--gold); border-radius:4px; padding:1.5rem; }
.commander-art-wrap  { flex-shrink:0; position:relative; }
.commander-img-full  { width:200px; border-radius:6px; display:block; box-shadow:0 12px 32px rgba(0,0,0,0.6); }
.cmd-prints { display:flex; flex-wrap:wrap; gap:4px; margin-top:8px; }
.cmd-print-btn { display:flex; align-items:center; gap:4px; background:rgba(0,0,0,0.4); border:1px solid rgba(184,134,11,0.25); border-radius:2px; padding:3px 7px; cursor:pointer; transition:all 0.15s; }
.cmd-print-btn:hover, .cmd-print-btn.active { background:rgba(184,134,11,0.2); border-color:var(--gold); }
.cmd-print-btn span { font-family:'Cinzel',serif; font-size:0.5rem; color:var(--parchment-dk); }
.commander-details   { flex:1; }
.commander-full-name { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold-shine); margin-bottom:4px; }
.detail-type   { font-family:'Cinzel',serif; font-size:0.7rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); opacity:0.8; margin-bottom:10px; }
.detail-oracle { font-style:italic; color:var(--parchment-dk); line-height:1.6; font-size:0.9rem; margin-bottom:10px; background:rgba(0,0,0,0.3); border-left:2px solid rgba(184,134,11,0.3); padding:8px 12px; border-radius:0 2px 2px 0; }
.detail-meta   { display:flex; align-items:center; gap:10px; }

.deck-hero-colors { display:flex; justify-content:center; gap:8px; margin-bottom:12px; }
.pip-lg { width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:700; }
.pip-w{background:#c8b896;color:#1a0f00} .pip-u{background:#1a3a6b;color:#a8d4f5}
.pip-b{background:#2a1a3e;color:#c8a8f5} .pip-r{background:#6b1a1a;color:#f5a8a8}
.pip-g{background:#1a3a1a;color:#a8f5a8}

.deck-controls { display:flex; align-items:center; gap:1rem; margin-bottom:1.5rem; flex-wrap:wrap; }
.view-tabs { display:flex; gap:4px; }
.view-tab  { font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:1px; padding:6px 14px; background:rgba(0,0,0,0.2); border:1px solid rgba(184,134,11,0.2); border-radius:2px; color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s; }
.view-tab.active { border-color:var(--gold-shine); background:rgba(184,134,11,0.1); color:var(--gold-shine); }
.not-found-bar { font-family:'Cinzel',serif; font-size:0.62rem; color:var(--crimson-lt); background:rgba(139,26,26,0.1); border:1px solid rgba(139,26,26,0.3); border-radius:3px; padding:8px 14px; margin-bottom:1.5rem; }

.cat-section { margin-bottom:2.5rem; }
.cat-header  { display:flex; align-items:center; gap:10px; margin-bottom:12px; padding-bottom:8px; border-bottom:1px solid rgba(184,134,11,0.2); }
.cat-icon    { font-size:1.1rem; }
.cat-name    { font-family:'Cinzel',serif; font-size:0.85rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--aged-white); flex:1; }
.cat-count   { font-family:'Cinzel',serif; font-size:0.6rem; color:var(--gold); background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.2); padding:3px 10px; border-radius:2px; }

/* Grid */
.cards-grid-deck { display:grid; grid-template-columns:repeat(auto-fill,minmax(130px,1fr)); gap:10px; }
.deck-card { position:relative; border-radius:4px; overflow:hidden; border:1px solid rgba(184,134,11,0.2); background:#0d0a06; transition:all 0.25s; }
.deck-card:hover { transform:translateY(-4px); border-color:var(--gold); box-shadow:0 8px 20px rgba(0,0,0,0.5); }
.deck-card-qty  { position:absolute; top:4px; left:4px; background:rgba(0,0,0,0.88); color:var(--gold-shine); font-family:'Cinzel',serif; font-size:0.62rem; font-weight:700; padding:2px 6px; border-radius:2px; z-index:3; }
.deck-card-img  { width:100%; display:block; }
.deck-card-footer { display:flex; align-items:center; justify-content:space-between; padding:3px 6px; background:rgba(0,0,0,0.7); }
.deck-card-name { font-family:'Cinzel',serif; font-size:0.42rem; color:var(--parchment-dk); overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }

/* Print switcher no card grid */
.card-prints-bar {
  position:absolute; bottom:20px; left:0; right:0;
  display:flex; gap:3px; padding:4px 5px;
  background:rgba(0,0,0,0.88); flex-wrap:wrap;
  z-index:10; border-top:1px solid rgba(184,134,11,0.3);
}
.print-pip {
  width:18px; height:18px; border-radius:2px;
  background:rgba(184,134,11,0.1); border:1px solid rgba(184,134,11,0.25);
  cursor:pointer; display:flex; align-items:center; justify-content:center; padding:0;
  transition:all 0.15s;
}
.print-pip:hover, .print-pip.active { background:rgba(184,134,11,0.3); border-color:var(--gold); }

/* List */
.list-rows { display:flex; flex-direction:column; gap:2px; }
.list-row  { display:flex; align-items:center; gap:10px; padding:7px 12px; border-radius:2px; border-left:2px solid transparent; transition:all 0.15s; background:rgba(0,0,0,0.12); }
.list-row:hover { background:rgba(184,134,11,0.07); border-left-color:var(--gold); }
.list-qty  { font-family:'Cinzel',serif; font-size:0.68rem; color:var(--gold); min-width:28px; }
.list-name { font-size:0.85rem; color:var(--parchment); flex:1; }
.list-mana { display:flex; gap:1px; flex-shrink:0; }
.list-type { font-size:0.68rem; color:var(--parchment-xdk); min-width:160px; font-style:italic; }
.print-select { background:#0d0a06; border:1px solid rgba(184,134,11,0.3); border-radius:2px; color:var(--parchment-dk); font-size:0.6rem; padding:2px 5px; outline:none; max-width:120px; }

.rdot { width:7px; height:7px; border-radius:50%; flex-shrink:0; display:inline-block; margin-left:3px; }
.rdot-mythic{background:#e07820} .rdot-rare{background:#d4a017}
.rdot-uncommon{background:#a8c6d4} .rdot-common{background:#94a3b8}

.modal-overlay { position:fixed; inset:0; background:rgba(0,0,0,0.8); display:flex; align-items:center; justify-content:center; z-index:500; }
.import-modal  { background:linear-gradient(135deg,#1a130a,#0d0a06); border:1px solid var(--gold); border-radius:4px; padding:2rem; width:90vw; max-width:500px; position:relative; max-height:90vh; overflow-y:auto; }
.modal-title   { font-family:'Cinzel Decorative',serif; font-size:1.1rem; color:var(--gold-shine); margin-bottom:1rem; }
.modal-close   { position:absolute; top:12px; right:12px; }
.form-msg      { font-family:'Cinzel',serif; font-size:0.62rem; margin-top:8px; text-align:center; }
.form-msg.ok { color:var(--gold); } .form-msg.err { color:var(--crimson-lt); }
.fade-enter-active,.fade-leave-active{transition:opacity 0.25s}
.fade-enter-from,.fade-leave-to{opacity:0}

@media(max-width:800px){ .commander-card-full{flex-direction:column} .commander-img-full{width:100%;max-width:220px} }
</style>