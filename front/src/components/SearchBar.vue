<template>
  <div class="search-grimoire">
    <div class="grimoire-label">✦ BUSCAR NO GRIMÓRIO ✦</div>

    <!-- Linha 1: nome + coleção + buscar -->
    <div class="search-row">
      <div class="field-wrap field-lg">
        <label class="field-label">⚔ Nome / Texto</label>
        <input v-model="f.q" type="text" class="medieval-input"
          placeholder="Nome ou texto da carta..." @keyup.enter="doSearch" />
      </div>

      <div class="field-wrap field-md">
        <label class="field-label">📜 Coleção</label>
        <select v-model="f.set" class="medieval-input">
          <option value="">Todas as Coleções</option>
          <option v-for="s in sets" :key="s.code" :value="s.code">
            {{ s.name || s.code }}{{ s.released_at ? ` (${s.released_at.slice(0,4)})` : '' }}
          </option>
        </select>
      </div>

      <div class="field-wrap field-md">
        <label class="field-label">⇅ Ordenar</label>
        <select v-model="f.sort" class="medieval-input">
          <option v-for="o in SORT_OPTIONS" :key="o.id" :value="o.id">{{ o.label }}</option>
        </select>
      </div>

      <div class="field-wrap field-btn">
        <label class="field-label" style="opacity:0">.</label>
        <div style="display:flex;gap:8px;align-items:center;">
          <button class="btn-primary" @click="doSearch">✦ Conjurar</button>
          <button v-if="hasFilters" class="btn-ghost" @click="clear">✕ Limpar</button>
          <button class="toggle-advanced" @click="showAdvanced = !showAdvanced">
            {{ showAdvanced ? '▲' : '▼' }} Filtros
          </button>
        </div>
      </div>
    </div>

    <!-- Linha 2: filtros avançados (colapsável) -->
    <Transition name="advanced-slide">
      <div v-if="showAdvanced" class="advanced-row">

        <!-- Tipo -->
        <div class="field-wrap field-sm">
          <label class="field-label">🐉 Tipo</label>
          <select v-model="f.type" class="medieval-input">
            <option value="">Todos os Tipos</option>
            <option v-for="t in types" :key="t" :value="t">{{ typeLabel(t) }}</option>
          </select>
        </div>

        <!-- Raridade -->
        <div class="field-wrap field-sm">
          <label class="field-label">💎 Raridade</label>
          <select v-model="f.rarity" class="medieval-input">
            <option value="">Todas</option>
            <option value="common">Comum</option>
            <option value="uncommon">Incomum</option>
            <option value="rare">Rara</option>
            <option value="mythic">Mítica</option>
          </select>
        </div>

        <!-- CMC -->
        <div class="field-wrap field-cmc">
          <label class="field-label">💠 Custo de Mana (CMC)</label>
          <div style="display:flex;gap:6px;">
            <select v-model="f.cmc_op" class="medieval-input" style="width:60px;padding:10px 6px;">
              <option value="=">=</option>
              <option value="<=">≤</option>
              <option value=">=">≥</option>
              <option value="<">&lt;</option>
              <option value=">">&gt;</option>
            </select>
            <input v-model="f.cmc" type="number" min="0" max="20" class="medieval-input"
              style="width:70px;" placeholder="0–20" />
          </div>
        </div>

        <!-- Cores de mana -->
        <div class="field-wrap field-colors">
          <label class="field-label">
            🎨 Cor
            <button
              class="mode-toggle"
              :title="f.color_mode === 'and' ? 'Precisa ter todas as cores marcadas' : 'Basta ter qualquer uma'"
              @click="f.color_mode = f.color_mode === 'and' ? 'or' : 'and'"
            >{{ f.color_mode === 'and' ? 'TODAS' : 'QUALQUER' }}</button>
          </label>
          <div class="color-pips">
            <button
              v-for="c in manaColors"
              :key="c.sym"
              class="pip-btn"
              :class="{ active: f.colors.includes(c.sym) }"
              :title="c.name"
              @click="toggleColor(c.sym)"
            >
              <img
                v-if="!iconesQuebrados.includes(c.sym)"
                :src="manaMap[c.sym] || c.icon"
                :alt="c.name"
                class="ms"
                @error="iconesQuebrados.push(c.sym)"
              />
              <span v-else class="pip-letra">{{ letraDaCor[c.sym] }}</span>
            </button>
          </div>
        </div>

        <!-- Lendária -->
        <div class="field-wrap field-sm">
          <label class="field-label">👑 Supertipo</label>
          <label class="check-line">
            <input type="checkbox" v-model="f.legendary" @change="doSearch" />
            <span>Somente lendárias</span>
          </label>
        </div>

        <!-- Habilidades -->
        <div class="field-wrap field-keywords">
          <label class="field-label">
            ✦ Habilidades
            <button
              class="mode-toggle"
              :title="f.keyword_mode === 'and' ? 'Precisa ter todas' : 'Basta ter qualquer uma'"
              @click="f.keyword_mode = f.keyword_mode === 'and' ? 'or' : 'and'"
            >{{ f.keyword_mode === 'and' ? 'TODAS' : 'QUALQUER' }}</button>
          </label>
          <div class="kw-chips">
            <button
              v-for="kw in KEYWORDS"
              :key="kw.id"
              class="kw-chip"
              :class="{ active: (f.keywords || []).includes(kw.id) }"
              @click="toggleKeyword(kw.id); doSearch()"
            >{{ kw.label }}</button>
          </div>
        </div>

        <!-- Data de lançamento -->
        <div class="field-wrap field-date">
          <label class="field-label">📅 Lançamento</label>
          <div style="display:flex;gap:6px;align-items:center;">
            <input v-model="f.date_from" type="date" class="medieval-input" style="flex:1;" />
            <span style="color:var(--gold);font-size:0.8rem;">até</span>
            <input v-model="f.date_to" type="date" class="medieval-input" style="flex:1;" />
          </div>
        </div>

      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { getCardTypes } from '@/composables/api'
import { useMana } from '@/composables/useMana'

const props = defineProps({
  sets:       { type: Array,  default: () => [] },
  initialFilters: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['search'])

const { symbols: manaMap } = useMana()
const iconesQuebrados = ref([])
const types         = ref([])
const showAdvanced  = ref(false)

// Os ícones vêm direto do Scryfall (URLs públicas e estáveis, carregadas pelo
// navegador). Antes dependiam do mapa de símbolos servido pela API: quando ele
// vinha vazio, os pips exibiam "{W}" em texto.
const manaColors = [
  { sym: '{W}', name: 'Branco',   icon: 'https://svgs.scryfall.io/card-symbols/W.svg' },
  { sym: '{U}', name: 'Azul',     icon: 'https://svgs.scryfall.io/card-symbols/U.svg' },
  { sym: '{B}', name: 'Preto',    icon: 'https://svgs.scryfall.io/card-symbols/B.svg' },
  { sym: '{R}', name: 'Vermelho', icon: 'https://svgs.scryfall.io/card-symbols/R.svg' },
  { sym: '{G}', name: 'Verde',    icon: 'https://svgs.scryfall.io/card-symbols/G.svg' },
  { sym: '{C}', name: 'Incolor',  icon: 'https://svgs.scryfall.io/card-symbols/C.svg' },
]

const letraDaCor = { '{W}': 'W', '{U}': 'U', '{B}': 'B', '{R}': 'R', '{G}': 'G', '{C}': 'C' }

const KEYWORDS = [
  { id: 'flying',        label: 'Voar' },
  { id: 'deathtouch',    label: 'Toque mortífero' },
  { id: 'lifelink',      label: 'Vínculo com a vida' },
  { id: 'trample',       label: 'Atropelar' },
  { id: 'first strike',  label: 'Iniciativa' },
  { id: 'double strike', label: 'Golpe duplo' },
  { id: 'haste',         label: 'Ímpeto' },
  { id: 'vigilance',     label: 'Vigilância' },
  { id: 'reach',         label: 'Alcance' },
  { id: 'menace',        label: 'Ameaçar' },
  { id: 'hexproof',      label: 'Resistência a magia' },
  { id: 'indestructible',label: 'Indestrutível' },
  { id: 'flash',         label: 'Lampejo' },
  { id: 'defender',      label: 'Defensor' },
  { id: 'ward',          label: 'Proteção (ward)' },
  { id: 'prowess',       label: 'Ardil' },
]

const SORT_OPTIONS = [
  { id: 'release_desc', label: 'Lançamento (mais novas)' },
  { id: 'release_asc',  label: 'Lançamento (mais antigas)' },
  { id: 'cmc_desc',     label: 'Custo de mana (maior)' },
  { id: 'cmc_asc',      label: 'Custo de mana (menor)' },
  { id: 'rarity_desc',  label: 'Raridade (mítica → comum)' },
  { id: 'rarity_asc',   label: 'Raridade (comum → mítica)' },
  { id: 'name',         label: 'Nome (A–Z)' },
  { id: 'name_desc',    label: 'Nome (Z–A)' },
]

const typeLabels = {
  Creature: 'Criatura', Planeswalker: 'Planeswalker', Instant: 'Mágica Instantânea',
  Sorcery: 'Feitiço', Enchantment: 'Encantamento', Artifact: 'Artefato',
  Land: 'Terreno', Battle: 'Batalha',
}
const typeLabel = t => typeLabels[t] || t

function normalizaCores(valor) {
  // A URL devolve "{W},{U}" (string) e o componente trabalha com array.
  // O spread de initialFilters vinha DEPOIS e sobrescrevia o array pela string,
  // fazendo f.colors.push() estourar "is not a function" ao clicar num pip.
  if (Array.isArray(valor)) return [...valor]
  if (typeof valor === 'string' && valor) return valor.split(',').filter(Boolean)
  return []
}

const f = reactive({
  q: '', set: '', rarity: '', type: '',
  cmc: '', cmc_op: '=',
  date_from: '', date_to: '',
  sort: 'release_desc',
  color_mode: 'and',
  legendary: false,
  keywords: [],
  keyword_mode: 'and',
  ...props.initialFilters,
  // sempre por último: garante os tipos corretos independentemente do que veio
  colors: normalizaCores(props.initialFilters?.colors),
})

const hasFilters = computed(() =>
  f.q || f.set || f.rarity || f.type || f.cmc !== '' ||
  (f.colors?.length || 0) || f.date_from || f.date_to ||
  f.legendary || (f.keywords?.length || 0)
)

function toggleColor(sym) {
  if (!Array.isArray(f.colors)) f.colors = normalizaCores(f.colors)
  const i = f.colors.indexOf(sym)
  i === -1 ? f.colors.push(sym) : f.colors.splice(i, 1)
}

function toggleKeyword(kw) {
  if (!Array.isArray(f.keywords)) f.keywords = []
  const i = f.keywords.indexOf(kw)
  i === -1 ? f.keywords.push(kw) : f.keywords.splice(i, 1)
}

function buildColorQuery() {
    if (!Array.isArray(f.colors)) return String(f.colors || "")
  // Monta filtro de cor: ex {W} → mana_cost LIKE '%{W}%'
  return f.colors.join(',')
}

function doSearch() {
  emit('search', {
    q: f.q, set: f.set, rarity: f.rarity, type: f.type,
    cmc: f.cmc, cmc_op: f.cmc_op,
    colors: buildColorQuery(),
    color_mode: f.color_mode,
    legendary: f.legendary ? '1' : '',
    keywords: Array.isArray(f.keywords) ? f.keywords.join(',') : '',
    keyword_mode: f.keyword_mode,
    sort: f.sort,
    date_from: f.date_from, date_to: f.date_to,
  })
}

// Ordenação e modos aplicam na hora: são ajustes de visualização
watch(() => [f.sort, f.color_mode, f.keyword_mode], doSearch)

function clear() {
  Object.assign(f, { q:'', set:'', rarity:'', type:'', cmc:'', cmc_op:'=', colors:[],
                     date_from:'', date_to:'', legendary:false, keywords:[] })
  doSearch()
}

onMounted(async () => {
  try { const { data } = await getCardTypes(); types.value = data.types } catch {}
  // Abre filtros avançados se já tiver filtro ativo
  if (props.initialFilters?.type || props.initialFilters?.cmc || props.initialFilters?.date_from)
    showAdvanced.value = true
})
</script>

<style scoped>
.search-grimoire {
  background: linear-gradient(135deg, rgba(26,19,10,0.95), rgba(13,10,6,0.95));
  border: 1px solid rgba(184,134,11,0.35); border-radius: 4px;
  padding: 1.8rem 2rem 1.5rem; margin-bottom: 2rem; position: relative;
  box-shadow: 0 8px 32px rgba(0,0,0,0.5), inset 0 1px 0 rgba(212,160,23,0.08);
}
.grimoire-label {
  position: absolute; top: -11px; left: 50%; transform: translateX(-50%);
  background: var(--obsidian-lt); padding: 0 1rem;
  font-family: 'Cinzel', serif; font-size: 0.6rem;
  letter-spacing: 4px; color: var(--gold); white-space: nowrap;
}

.search-row   { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; }
.advanced-row { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; margin-top: 1.2rem; padding-top: 1.2rem; border-top: 1px solid rgba(184,134,11,0.15); }

.field-wrap   { display: flex; flex-direction: column; }
.field-lg     { flex: 2; min-width: 200px; }
.field-md     { flex: 1.5; min-width: 180px; }
.field-sm     { flex: 1; min-width: 140px; }
.field-cmc    { flex: 0 0 auto; }
.field-colors { flex: 0 0 auto; }
.field-date   { flex: 2; min-width: 260px; }
.field-btn    { flex: 0 0 auto; }

.toggle-advanced {
  font-family: 'Cinzel', serif; font-size: 0.65rem; letter-spacing: 2px;
  background: rgba(184,134,11,0.08); border: 1px solid rgba(184,134,11,0.25);
  color: var(--parchment-xdk); padding: 10px 14px; border-radius: 2px;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.toggle-advanced:hover { border-color: var(--gold); color: var(--gold-shine); }

/* Color pips */
.color-pips { display: flex; gap: 6px; padding-top: 2px; flex-wrap: wrap; }

.mode-toggle {
  margin-left: 8px; padding: 1px 6px; cursor: pointer;
  background: rgba(184,134,11,0.14); border: 1px solid rgba(184,134,11,0.4);
  color: var(--gold-shine); border-radius: 2px;
  font-family: 'Cinzel', serif; font-size: 0.5rem; letter-spacing: 1px;
}
.mode-toggle:hover { background: var(--gold); color: var(--obsidian); }

.check-line { display: flex; align-items: center; gap: 6px; padding-top: 8px;
  font-size: 0.75rem; color: var(--parchment-dk); cursor: pointer; }
.check-line input { accent-color: var(--gold); cursor: pointer; }

.field-keywords { flex: 1 1 100%; }
.kw-chips { display: flex; flex-wrap: wrap; gap: 5px; padding-top: 4px; }
.kw-chip {
  background: rgba(0,0,0,0.3); border: 1px solid rgba(184,134,11,0.22);
  color: var(--parchment-dk); border-radius: 2px; padding: 4px 9px;
  font-size: 0.66rem; cursor: pointer; transition: all 0.18s;
}
.kw-chip:hover { border-color: var(--gold); color: var(--gold-shine); }
.kw-chip.active { background: rgba(184,134,11,0.22); border-color: var(--gold); color: var(--gold-shine); }
.pip-btn {
  width: 34px; height: 34px; border-radius: 50%;
  border: 2px solid rgba(184,134,11,0.25);
  background: rgba(0,0,0,0.3); cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.pip-btn:hover { border-color: var(--gold); transform: scale(1.1); }
.pip-btn.active { border-color: var(--gold-shine); background: rgba(184,134,11,0.2); box-shadow: 0 0 10px rgba(212,160,23,0.3); }
.pip-btn .ms { width: 22px; height: 22px; }
.pip-letra { font-family: 'Cinzel', serif; font-size: 0.8rem; color: var(--gold); }

/* Transition */
.advanced-slide-enter-active, .advanced-slide-leave-active { transition: all 0.3s ease; overflow: hidden; }
.advanced-slide-enter-from, .advanced-slide-leave-to { opacity: 0; max-height: 0; margin-top: 0; padding-top: 0; }
.advanced-slide-enter-to, .advanced-slide-leave-from { opacity: 1; max-height: 200px; }
</style>
