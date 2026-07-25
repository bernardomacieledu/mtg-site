<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Montar Coleção</h1>
      <p class="page-hero-sub">
        <router-link to="/biblioteca" class="back-link">📚 Biblioteca</router-link>
        <span class="crumb-sep">›</span> montando uma coleção
      </p>
      <div class="hero-divider"><span class="hero-divider-gem">📦</span></div>
    </div>

    <div class="page-wrap builder-layout">
      <!-- ── Rascunho ── -->
      <main class="builder-main">
        <div class="builder-head">
          <input
            :value="store.draft.name"
            class="medieval-input name-input"
            placeholder="Nome da coleção..."
            @input="store.renameDraft($event.target.value)"
          />
          <div class="head-actions">
            <button class="btn-primary" :disabled="store.isEmpty || store.saving" @click="save">
              {{ store.saving ? '⏳ Salvando...' : (store.draft.id ? '✔ Atualizar' : '✦ Salvar') }}
            </button>
            <button class="btn-ghost" :disabled="store.isEmpty" @click="confirmClear">🗑 Limpar</button>
          </div>
        </div>

        <div v-if="message" class="builder-msg" :class="message.startsWith('❌') ? 'err' : 'ok'">
          {{ message }}
        </div>

        <div v-if="!auth.isLoggedIn" class="local-warning">
          ⚠ Você não está logado — a coleção fica salva apenas neste navegador.
          <router-link to="/login">Entrar</router-link>
        </div>

        <!-- Vazio -->
        <div v-if="store.isEmpty" class="empty-builder">
          <div class="empty-title">✦ Coleção Vazia ✦</div>
          <p class="empty-sub">
            Navegue pelo <router-link to="/">Grimório</router-link> ou pelas
            <router-link to="/colecoes">Coleções</router-link> e use o botão
            <strong>+</strong> nas cartas para montar a sua.
          </p>
          <router-link to="/colecao/importar" class="btn-ghost import-link">
            ⬆ Ou importe uma lista pronta
          </router-link>
        </div>

        <template v-else>
          <!-- Resumo -->
          <div class="stats-bar">
            <div class="stat-chip">📦 <strong>{{ store.draftCount }}</strong> cópias</div>
            <div class="stat-chip">🃏 <strong>{{ store.draftUnique }}</strong> únicas</div>
            <div class="stat-chip">📚 <strong>{{ setCount }}</strong> sets</div>
            <div class="stat-chip">⚖ CMC médio <strong>{{ avgCmc }}</strong></div>
            <input v-model="filter" class="medieval-input filter-input" placeholder="Filtrar..." />
          </div>

          <!-- Lista por categoria -->
          <section v-for="group in groupedCards" :key="group.category" class="cat-group">
            <div class="cat-head">
              <span class="cat-name">{{ categoryLabel(group.category) }}</span>
              <span class="cat-count">{{ group.total }}</span>
              <div class="cat-rule"></div>
            </div>

            <div class="draft-grid">
              <article v-for="card in group.cards" :key="card.name" class="draft-card">
                <img
                  v-if="card.image_url"
                  :src="card.image_url"
                  :alt="card.name"
                  class="draft-img"
                  loading="lazy"
                  @click="openCard(card)"
                />
                <div class="draft-body">
                  <div class="draft-name" @click="openCard(card)">{{ card.name }}</div>
                  <div class="draft-type">{{ card.type_line }}</div>
                  <div class="draft-controls">
                    <button class="qty-btn" title="Remover uma" @click="store.removeCard(card.name)">−</button>
                    <input
                      class="qty-input"
                      type="number"
                      min="0"
                      :value="card.qty"
                      @change="store.setQty(card.name, Number($event.target.value))"
                    />
                    <button class="qty-btn" title="Adicionar uma" @click="store.addCard(card)">+</button>
                    <span :class="['rarity-badge', `rarity-${card.rarity}`]">{{ card.rarity }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </template>
      </main>

      <!-- ── Coleções salvas ── -->
      <aside class="builder-side">
        <div class="side-head">
          <span class="field-label">📚 Minhas Coleções</span>
          <button class="btn-ghost tiny" @click="store.loadList()">↻</button>
        </div>

        <div v-if="store.loading" class="side-empty">Carregando...</div>
        <div v-else-if="!store.list.length" class="side-empty">
          Nenhuma coleção salva ainda.
        </div>
        <div v-else class="side-empty">
          Você tem {{ store.list.length }} coleção(ões) salva(s).
          <router-link to="/biblioteca">Ver na Biblioteca ▸</router-link>
        </div>

        <router-link to="/colecao/importar" class="btn-ghost side-import">
          ⬆ Importar lista
        </router-link>
      </aside>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCollectionsStore } from '@/stores/collections'
import { useAuthStore } from '@/stores/auth'

const store   = useCollectionsStore()
const auth    = useAuthStore()
const router  = useRouter()
const filter  = ref('')
const message = ref('')

const CATEGORY_LABELS = {
  creature: 'Criaturas', planeswalker: 'Planeswalkers', instant: 'Mágicas Instantâneas',
  sorcery: 'Feitiços', artifact: 'Artefatos', enchantment: 'Encantamentos',
  land: 'Terrenos', other: 'Outros',
}
const CATEGORY_ORDER = Object.keys(CATEGORY_LABELS)

function categoryLabel(category) {
  return CATEGORY_LABELS[category] || category
}

const visibleCards = computed(() => {
  const term = filter.value.trim().toLowerCase()
  if (!term) return store.draft.cards
  return store.draft.cards.filter(card =>
    card.name.toLowerCase().includes(term) ||
    (card.type_line || '').toLowerCase().includes(term))
})

const groupedCards = computed(() => {
  const groups = {}
  for (const card of visibleCards.value) {
    const category = card.category || 'other'
    ;(groups[category] ||= []).push(card)
  }
  return CATEGORY_ORDER
    .filter(category => groups[category]?.length)
    .map(category => ({
      category,
      cards: groups[category].slice().sort((a, b) => a.name.localeCompare(b.name)),
      total: groups[category].reduce((sum, card) => sum + card.qty, 0),
    }))
})

const setCount = computed(() => new Set(store.draft.cards.map(card => card.set)).size)

const avgCmc = computed(() => {
  const nonLand = store.draft.cards.filter(card => card.category !== 'land')
  const copies = nonLand.reduce((sum, card) => sum + card.qty, 0)
  if (!copies) return '0.00'
  return (nonLand.reduce((sum, card) => sum + (card.cmc || 0) * card.qty, 0) / copies).toFixed(2)
})

function openCard(card) {
  router.push({ name: 'card-detail', params: { name: card.name } })
}

async function save() {
  message.value = ''
  const result = await store.saveDraft()
  message.value = result.error ? `❌ ${result.error}` : '✔ Coleção salva!'
  setTimeout(() => { message.value = '' }, 4000)
}

function confirmClear() {
  if (confirm('Limpar a coleção em montagem? As coleções já salvas não são afetadas.')) {
    store.clearDraft()
  }
}

async function edit(id) {
  const ok = await store.editCollection(id)
  message.value = ok ? '✔ Coleção carregada para edição.' : '❌ Não foi possível abrir a coleção.'
  setTimeout(() => { message.value = '' }, 4000)
}

async function remove(item) {
  if (!confirm(`Excluir a coleção "${item.name}"?`)) return
  await store.removeCollection(item.id)
}

onMounted(() => store.loadList())
</script>

<style scoped>
.back-link { color: var(--gold-shine); text-decoration: none; }
.back-link:hover { text-decoration: underline; }
.crumb-sep { color: var(--parchment-xdk); margin: 0 6px; }

.builder-layout { display: grid; grid-template-columns: 1fr 300px; gap: 1.8rem; align-items: start; }

.builder-head { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 1rem; }
.name-input { flex: 1 1 240px; }
.head-actions { display: flex; gap: 8px; }

.builder-msg { padding: 9px 12px; border-radius: 3px; font-size: 0.78rem; margin-bottom: 1rem; }
.builder-msg.ok  { background: rgba(60,120,60,0.16); border: 1px solid rgba(120,200,120,0.35); color: #b6e0b6; }
.builder-msg.err { background: rgba(120,40,40,0.16); border: 1px solid rgba(200,90,90,0.35); color: #e8b0b0; }

.local-warning {
  padding: 9px 12px; margin-bottom: 1.2rem; font-size: 0.75rem;
  background: rgba(120,90,20,0.14); border: 1px solid rgba(184,134,11,0.3);
  border-radius: 3px; color: var(--parchment-dk);
}
.local-warning a { color: var(--gold-shine); }

.empty-builder { text-align: center; padding: 4rem 1.5rem; }
.empty-title { font-family: 'Cinzel Decorative', serif; font-size: 1.3rem; color: var(--gold); margin-bottom: 0.8rem; }
.empty-sub { color: var(--parchment-xdk); font-style: italic; line-height: 1.9; }
.empty-sub a { color: var(--gold-shine); }
.import-link { display: inline-block; margin-top: 1.6rem; }

.stats-bar { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; margin-bottom: 1.8rem; }
.stat-chip {
  background: rgba(0,0,0,0.25); border: 1px solid rgba(184,134,11,0.18);
  border-radius: 3px; padding: 7px 11px; font-size: 0.72rem; color: var(--parchment-dk);
}
.stat-chip strong { color: var(--gold); }
.filter-input { flex: 1 1 160px; font-size: 0.78rem; padding: 7px 12px; }

.cat-group { margin-bottom: 2rem; }
.cat-head { display: flex; align-items: center; gap: 10px; margin-bottom: 0.8rem; }
.cat-name { font-family: 'Cinzel', serif; font-size: 0.78rem; letter-spacing: 2px; text-transform: uppercase; color: var(--gold); }
.cat-count { font-size: 0.68rem; color: var(--parchment-xdk); }
.cat-rule { flex: 1; height: 1px; background: linear-gradient(90deg, rgba(184,134,11,0.3), transparent); }

.draft-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); gap: 0.8rem; }
.draft-card {
  display: flex; gap: 10px; padding: 9px;
  background: linear-gradient(150deg, #1a130a 0%, #0f0b06 100%);
  border: 1px solid rgba(184,134,11,0.18); border-radius: 4px;
  transition: border-color 0.25s;
}
.draft-card:hover { border-color: rgba(184,134,11,0.5); }
.draft-img { width: 58px; border-radius: 3px; cursor: pointer; align-self: flex-start; }
.draft-body { flex: 1; min-width: 0; }
.draft-name {
  font-family: 'Cinzel', serif; font-size: 0.78rem; color: var(--aged-white);
  cursor: pointer; line-height: 1.3;
}
.draft-name:hover { color: var(--gold-shine); }
.draft-type {
  font-size: 0.62rem; color: var(--parchment-xdk); margin: 4px 0 8px;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.draft-controls { display: flex; align-items: center; gap: 5px; }
.qty-btn {
  width: 22px; height: 22px; line-height: 1;
  background: rgba(0,0,0,0.35); border: 1px solid rgba(184,134,11,0.35);
  color: var(--gold); border-radius: 2px; cursor: pointer; font-size: 0.85rem;
}
.qty-btn:hover { background: var(--gold); color: var(--obsidian); }
.qty-input {
  width: 42px; text-align: center; background: rgba(0,0,0,0.4);
  border: 1px solid rgba(184,134,11,0.25); color: var(--aged-white);
  border-radius: 2px; padding: 3px; font-size: 0.75rem;
}

.builder-side {
  background: rgba(0,0,0,0.22); border: 1px solid rgba(184,134,11,0.16);
  border-radius: 4px; padding: 15px; position: sticky; top: 90px;
}
.side-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; }
.btn-ghost.tiny { padding: 2px 8px; font-size: 0.7rem; }
.side-empty { font-size: 0.75rem; color: var(--parchment-xdk); font-style: italic; padding: 0.6rem 0; }

.saved-item {
  display: flex; align-items: center; gap: 8px; padding: 9px 0;
  border-bottom: 1px solid rgba(184,134,11,0.1);
}
.saved-info { flex: 1; min-width: 0; }
.saved-name {
  font-family: 'Cinzel', serif; font-size: 0.76rem; color: var(--aged-white);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.saved-meta { font-size: 0.64rem; color: var(--parchment-xdk); margin-top: 2px; }
.saved-actions { display: flex; gap: 4px; }
.icon-btn {
  background: none; border: 1px solid rgba(184,134,11,0.25); color: var(--parchment-dk);
  border-radius: 2px; width: 24px; height: 24px; cursor: pointer; font-size: 0.72rem;
}
.icon-btn:hover { border-color: var(--gold); color: var(--gold-shine); }
.icon-btn.danger:hover { border-color: var(--crimson-lt, #c85a5a); color: #e8b0b0; }

.side-import { display: block; text-align: center; margin-top: 1.2rem; font-size: 0.68rem; }

@media (max-width: 900px) {
  .builder-layout { grid-template-columns: 1fr; }
  .builder-side { position: static; }
}
</style>
