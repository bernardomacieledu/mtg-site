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
          <label class="field-label">🎨 Cor</label>
          <div class="color-pips">
            <button
              v-for="c in manaColors"
              :key="c.sym"
              class="pip-btn"
              :class="{ active: f.colors.includes(c.sym) }"
              :title="c.name"
              @click="toggleColor(c.sym)"
            >
              <img v-if="manaMap[c.sym]" :src="manaMap[c.sym]" class="ms" />
              <span v-else>{{ c.sym }}</span>
            </button>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { getCardTypes } from '@/composables/api'
import { useMana } from '@/composables/useMana'

const props = defineProps({
  sets:       { type: Array,  default: () => [] },
  initialFilters: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['search'])

const { symbols: manaMap } = useMana()
const types         = ref([])
const showAdvanced  = ref(false)

const manaColors = [
  { sym: '{W}', name: 'Branco' },
  { sym: '{U}', name: 'Azul'   },
  { sym: '{B}', name: 'Preto'  },
  { sym: '{R}', name: 'Vermelho'},
  { sym: '{G}', name: 'Verde'  },
]

const typeLabels = {
  Creature: 'Criatura', Planeswalker: 'Planeswalker', Instant: 'Mágica Instantânea',
  Sorcery: 'Feitiço', Enchantment: 'Encantamento', Artifact: 'Artefato',
  Land: 'Terreno', Battle: 'Batalha',
}
const typeLabel = t => typeLabels[t] || t

const f = reactive({
  q: '', set: '', rarity: '', type: '',
  cmc: '', cmc_op: '=',
  colors: Array.isArray(props.initialFilters?.colors) ? props.initialFilters.colors : [],
  date_from: '', date_to: '',
  ...props.initialFilters,
})

const hasFilters = computed(() =>
  f.q || f.set || f.rarity || f.type || f.cmc !== '' ||
  f.colors.length || f.date_from || f.date_to
)

function toggleColor(sym) {
  const i = f.colors.indexOf(sym)
  i === -1 ? f.colors.push(sym) : f.colors.splice(i, 1)
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
    date_from: f.date_from, date_to: f.date_to,
  })
}

function clear() {
  Object.assign(f, { q:'', set:'', rarity:'', type:'', cmc:'', cmc_op:'=', colors:[], date_from:'', date_to:'' })
  emit('search', { q:'', set:'', rarity:'', type:'', cmc:'', cmc_op:'=', colors:'', date_from:'', date_to:'' })
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
.color-pips { display: flex; gap: 6px; padding-top: 2px; }
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

/* Transition */
.advanced-slide-enter-active, .advanced-slide-leave-active { transition: all 0.3s ease; overflow: hidden; }
.advanced-slide-enter-from, .advanced-slide-leave-to { opacity: 0; max-height: 0; margin-top: 0; padding-top: 0; }
.advanced-slide-enter-to, .advanced-slide-leave-from { opacity: 1; max-height: 200px; }
</style>
