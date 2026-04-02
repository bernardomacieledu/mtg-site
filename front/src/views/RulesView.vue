<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Compêndio de Regras</h1>
      <p class="page-hero-sub">O Corpus Completo das Leis Arcanas do Magic: The Gathering</p>
      <div class="hero-divider"><span class="hero-divider-gem">🏛</span></div>
    </div>

    <div class="page-wrap">
      <div class="rules-layout">

        <!-- ── Sidebar TOC ── -->
        <aside class="toc-sidebar">
          <div class="toc-header">✦ Índice ✦</div>
          <div class="toc-search-wrap">
            <input v-model="tocFilter" type="text" class="toc-input" placeholder="Filtrar capítulos..." />
          </div>
          <ul class="toc-list">
            <li
              v-for="ch in filteredChapters"
              :key="ch.number"
            >
              <a
                :class="{ active: activeChapter === ch.number }"
                @click.prevent="scrollToChapter(ch.number)"
              >
                <span class="toc-num">{{ ch.number }}</span>
                {{ ch.title }}
              </a>
            </li>
          </ul>
        </aside>

        <!-- ── Main Content ── -->
        <main class="rules-main">
          <!-- Search bar -->
          <div class="rules-search-row">
            <input
              v-model="searchQ"
              type="text"
              class="medieval-input"
              placeholder="Buscar nas regras..."
              @keyup.enter="fetchRules"
            />
            <button class="btn-primary" @click="fetchRules">⚡ Buscar</button>
            <button v-if="searchQ" class="btn-ghost" @click="clearSearch">✕ Limpar</button>
            <span class="rules-count"><strong>{{ total }}</strong> regras</span>
          </div>

          <!-- Loading -->
          <div v-if="loading" class="spinner-wrap">
            <div class="spinner"></div>
            <span class="spinner-text">Abrindo o Compêndio...</span>
          </div>

          <!-- Chapters -->
          <div
            v-for="ch in chapters"
            :key="ch.number"
            :id="`chapter-${ch.number}`"
            class="chapter-block"
          >
            <div class="chapter-header" @click="toggle(ch.number)">
              <span class="chapter-roman">{{ ch.number }}</span>
              <span class="chapter-title-text">{{ ch.title }}</span>
              <span class="chapter-count">{{ ch.rules.length }} regras</span>
              <span class="chapter-chevron" :class="{ collapsed: collapsedChapters.has(ch.number) }">▼</span>
            </div>

            <Transition name="chapter-slide">
              <div v-if="!collapsedChapters.has(ch.number)" class="rules-list">
                <div
                  v-for="rule in ch.rules"
                  :key="rule.id"
                  class="rule-item"
                  :class="{ highlighted: searchQ && rule.rule_text.toLowerCase().includes(searchQ.toLowerCase()) }"
                >
                  <span class="rule-num">{{ rule.rule_number }}</span>
                  <span class="rule-text" v-html="highlight(rule.rule_text)" />
                </div>
              </div>
            </Transition>
          </div>

          <!-- Empty -->
          <div v-if="!loading && chapters.length === 0" class="no-results">
            <div class="no-results-title">✦ Nenhuma Regra Encontrada ✦</div>
            <p class="no-results-sub">Os arquivistas não encontraram regras para esta busca.</p>
          </div>
        </main>

      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { getRules } from '@/composables/api'

const chapters         = ref([])
const total            = ref(0)
const loading          = ref(false)
const searchQ          = ref('')
const tocFilter        = ref('')
const activeChapter    = ref('')
const collapsedChapters = ref(new Set())

const filteredChapters = computed(() => {
  const q = tocFilter.value.toLowerCase()
  return chapters.value.filter(c =>
    !q || c.title.toLowerCase().includes(q) || c.number.includes(q)
  )
})

async function fetchRules() {
  loading.value = true
  try {
    const { data } = await getRules({ q: searchQ.value })
    chapters.value = data.chapters
    total.value    = data.total
  } finally { loading.value = false }
}

function clearSearch() {
  searchQ.value = ''
  fetchRules()
}

function toggle(num) {
  const s = new Set(collapsedChapters.value)
  s.has(num) ? s.delete(num) : s.add(num)
  collapsedChapters.value = s
}

function scrollToChapter(num) {
  // Expand if collapsed
  if (collapsedChapters.value.has(num)) toggle(num)
  setTimeout(() => {
    const el = document.getElementById(`chapter-${num}`)
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 50)
}

function highlight(text) {
  if (!searchQ.value) return text
  const q = searchQ.value.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  return text.replace(new RegExp(q, 'gi'), m => `<mark>${m}</mark>`)
}

// IntersectionObserver for TOC active state
let observer = null
function setupObserver() {
  observer?.disconnect()
  observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        activeChapter.value = e.target.id.replace('chapter-', '')
      }
    })
  }, { rootMargin: '-15% 0px -75% 0px' })
  document.querySelectorAll('.chapter-block').forEach(el => observer.observe(el))
}

onMounted(async () => { await fetchRules(); setTimeout(setupObserver, 300) })
onUnmounted(() => observer?.disconnect())
</script>

<style scoped>
.rules-layout { display:grid; grid-template-columns:270px 1fr; gap:2rem; align-items:start; }

/* TOC */
.toc-sidebar { position:sticky; top:88px; background:linear-gradient(160deg,rgba(26,19,10,0.97),rgba(13,10,6,0.97)); border:1px solid rgba(184,134,11,0.22); border-radius:3px; overflow:hidden; }
.toc-header  { background:rgba(0,0,0,0.3); border-bottom:1px solid rgba(184,134,11,0.18); padding:12px; font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:4px; color:var(--gold); text-align:center; }
.toc-search-wrap { padding:10px 12px; border-bottom:1px solid rgba(184,134,11,0.12); }
.toc-input   { width:100%; background:rgba(0,0,0,0.4); border:1px solid rgba(184,134,11,0.25); border-radius:2px; color:var(--parchment); padding:6px 10px; font-family:'IM Fell English',serif; font-size:0.82rem; outline:none; }
.toc-input:focus { border-color:var(--gold); }
.toc-list    { padding:6px 0; max-height:68vh; overflow-y:auto; list-style:none; }
.toc-list li a {
  display:flex; align-items:center; gap:8px;
  padding:8px 14px; font-family:'Cinzel',serif; font-size:0.68rem;
  letter-spacing:1px; color:var(--parchment-dk);
  text-decoration:none; cursor:pointer; transition:all 0.2s;
  border-left:2px solid transparent;
}
.toc-list li a:hover,
.toc-list li a.active { color:var(--gold-shine); background:rgba(184,134,11,0.06); border-left-color:var(--gold); }
.toc-num { font-size:0.58rem; color:var(--gold); opacity:0.7; min-width:14px; }

/* Main */
.rules-main { min-width:0; }
.rules-search-row { display:flex; gap:10px; align-items:center; flex-wrap:wrap; margin-bottom:2rem; }
.rules-search-row .medieval-input { flex:1; min-width:180px; }
.rules-count { font-family:'Cinzel',serif; font-size:0.65rem; letter-spacing:2px; color:var(--parchment-xdk); white-space:nowrap; margin-left:auto; }
.rules-count strong { color:var(--gold); }

/* Chapter */
.chapter-block { margin-bottom:2.5rem; }
.chapter-header { display:flex; align-items:center; gap:1rem; margin-bottom:1rem; padding-bottom:10px; border-bottom:1px solid rgba(184,134,11,0.25); cursor:pointer; user-select:none; }
.chapter-roman  { font-family:'Cinzel Decorative',serif; font-size:1.4rem; color:var(--gold); text-shadow:0 0 14px rgba(184,134,11,0.4); min-width:36px; }
.chapter-title-text { font-family:'Cinzel',serif; font-size:0.95rem; font-weight:700; letter-spacing:3px; text-transform:uppercase; color:var(--aged-white); flex:1; }
.chapter-count  { font-family:'Cinzel',serif; font-size:0.58rem; letter-spacing:2px; color:var(--parchment-xdk); background:rgba(0,0,0,0.3); border:1px solid rgba(184,134,11,0.12); padding:3px 9px; border-radius:2px; }
.chapter-chevron { color:var(--gold); font-size:0.75rem; opacity:0.6; transition:transform 0.3s; }
.chapter-chevron.collapsed { transform:rotate(-90deg); }

/* Rules */
.rules-list { display:flex; flex-direction:column; gap:4px; }
.rule-item  { display:flex; gap:0.9rem; padding:9px 12px; border-radius:2px; border-left:2px solid transparent; transition:all 0.2s; background:rgba(0,0,0,0.12); }
.rule-item:hover { background:rgba(184,134,11,0.06); border-left-color:rgba(184,134,11,0.35); }
.rule-item.highlighted { background:rgba(184,134,11,0.09); border-left-color:var(--gold); }
.rule-num   { font-family:'Cinzel',serif; font-size:0.68rem; color:var(--gold); opacity:0.65; min-width:54px; padding-top:2px; letter-spacing:1px; flex-shrink:0; }
.rule-text  { font-size:0.87rem; line-height:1.65; color:var(--parchment-dk); }

.chapter-slide-enter-active, .chapter-slide-leave-active { transition:all 0.3s ease; overflow:hidden; }
.chapter-slide-enter-from, .chapter-slide-leave-to { opacity:0; max-height:0; }
.chapter-slide-enter-to, .chapter-slide-leave-from { opacity:1; max-height:9999px; }

mark { background:rgba(212,160,23,0.28); color:var(--gold-shine); border-radius:2px; padding:0 2px; }

.no-results { text-align:center; padding:4rem 2rem; }
.no-results-title { font-family:'Cinzel Decorative',serif; font-size:1.3rem; color:var(--gold); margin-bottom:1rem; }
.no-results-sub   { font-style:italic; color:var(--parchment-xdk); }

@media (max-width:900px) {
  .rules-layout { grid-template-columns:1fr; }
  .toc-sidebar  { display:none; }
}
</style>
