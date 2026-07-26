<template>
  <div class="tome-card" @mouseenter="hovering = true" @mouseleave="hovering = false">

    <!-- Art -->
    <div class="card-art" @click="goToDetail">
      <Transition name="img-fade" mode="out-in">
        <img :key="currentImage" :src="currentImage" :alt="card.name" class="card-img" loading="lazy" />
      </Transition>

      <!-- Set switcher overlay -->
      <Transition name="fade">
        <div v-if="hovering && (card.sets?.length || 0) > 1" class="set-overlay">
          <button
            v-for="s in (card.sets || [])"
            :key="s.code"
            class="set-btn"
            :class="{ active: activeSet === s.code }"
            :title="`${s.name} · ${s.released_at}`"
            @click.stop="switchSet(s)"
          >
            <img
              :src="`https://svgs.scryfall.io/sets/${s.code.toLowerCase()}.svg`"
              :alt="s.code"
              @error="e => e.target.style.display='none'"
            />
            <span>{{ s.code.toUpperCase() }}</span>
          </button>
        </div>
      </Transition>

      <!-- Click hint -->
      <div v-if="hovering" class="detail-hint">Ver detalhes ▸</div>

      <!-- Quantidade já na coleção em montagem -->
      <div v-if="inCollection > 0" class="qty-badge" title="Cópias na coleção em montagem">
        {{ inCollection }}×
      </div>
    </div>

    <!-- Body -->
    <div class="card-body" @click="goToDetail" style="cursor:pointer">
      <div class="card-name-row">
        <span class="card-name">{{ card.name }}</span>
        <span class="mana-cost" v-html="renderMana(card.mana_cost)" />
      </div>
      <div class="card-type">{{ card.type_line }}</div>
      <div class="card-oracle" v-html="renderMana(card.oracle_text)" />
    </div>

    <!-- Footer -->
    <div class="card-footer">
      <div class="footer-sets">
        <img
          v-for="s in (card.sets || []).slice(0,6)"
          :key="s.code"
          :src="`https://svgs.scryfall.io/sets/${s.code.toLowerCase()}.svg`"
          :title="`${s.name} · ${s.released_at}`"
          class="footer-set-icon"
          @click.stop="switchSet(s)"
          @error="e => e.target.style.display='none'"
        />
      </div>
      <div v-if="precoAtual" class="preco-tag" :title="tituloPreco">
        <span class="preco-brl">R$ {{ precoAtual.brl?.toFixed(2) ?? '—' }}</span>
        <span v-if="precoAtual.usd" class="preco-usd">US$ {{ precoAtual.usd.toFixed(2) }}</span>
      </div>

      <div class="footer-right">
        <span :class="['rarity-badge', `rarity-${card.rarity}`]">{{ card.rarity }}</span>
        <div class="collect-actions">
          <button
            v-if="inCollection > 0"
            class="collect-btn"
            title="Remover uma cópia da coleção"
            @click.stop="collections.removeCard(card.name)"
          >−</button>
          <button
            class="collect-btn add"
            :title="`Adicionar ${card.name} à coleção`"
            @click.stop="addToCollection"
          >+</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useMana } from '@/composables/useMana'
import { getCardImages } from '@/composables/api'
import { useCollectionsStore } from '@/stores/collections'

const props  = defineProps({ card: { type: Object, required: true } })
const router = useRouter()
const { renderMana } = useMana()

const collections = useCollectionsStore()

const hovering   = ref(false)
const activeSet  = ref(props.card.sets?.[0]?.code || '')
const imageCache = ref({ [activeSet.value]: props.card.image_url_normal })

const currentImage  = computed(() => imageCache.value[activeSet.value] || props.card.image_url_normal)
const inCollection  = computed(() => collections.qtyOf(props.card.name))

// O preço acompanha a impressão selecionada: versões diferentes da mesma carta
// têm valores bem distintos.
const precoAtual = computed(() => {
  const impressao = props.card.sets?.find(s => s.code === activeSet.value)
  return impressao?.prices || props.card.prices || null
})

const tituloPreco = computed(() => {
  const cotacao = props.card.usd_brl
  const base = `Impressão ${activeSet.value?.toUpperCase() || ''}`
  return cotacao
    ? `${base} — estimativa convertida de US$ (câmbio ${cotacao.toFixed(2)})`
    : `${base} — valor em dólar`
})

function addToCollection() {
  // Abre o modal para o usuário escolher (ou criar) a coleção de destino
  collections.requestAdd({
    ...props.card,
    set:       activeSet.value,
    set_name:  props.card.sets?.find(s => s.code === activeSet.value)?.name || activeSet.value,
    image_url: currentImage.value,
  })
}

function goToDetail() {
  router.push({ name: 'card-detail', params: { name: props.card.name } })
}

async function switchSet(s) {
  if (activeSet.value === s.code) return
  activeSet.value = s.code
  if (!imageCache.value[s.code]) {
    try {
      const { data } = await getCardImages(props.card.name)
      data.images.forEach(img => { imageCache.value[img.set_code] = img.image_url })
    } catch { /* mantém atual */ }
  }
}
</script>

<style scoped>
.tome-card {
  background: linear-gradient(160deg, #1a130a 0%, #0f0b06 100%);
  border: 1px solid rgba(184,134,11,0.22); border-radius: 4px; overflow: hidden;
  display: flex; flex-direction: column;
  transition: transform 0.35s cubic-bezier(.23,1,.32,1), border-color 0.3s, box-shadow 0.3s;
  position: relative; height: 100%;
}
.tome-card:hover {
  transform: translateY(-6px) scale(1.01);
  border-color: var(--gold);
  box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 30px rgba(184,134,11,0.14);
}

.card-art { position: relative; background: #080604; padding: 12px 12px 0; cursor: pointer; }
.card-img  { width: 100%; border-radius: 3px; display: block; }

.detail-hint {
  position: absolute; bottom: 8px; right: 12px;
  font-family: 'Cinzel', serif; font-size: 0.6rem; letter-spacing: 2px;
  color: var(--gold-shine); background: rgba(0,0,0,0.75);
  padding: 3px 8px; border-radius: 2px; border: 1px solid rgba(184,134,11,0.4);
}

.img-fade-enter-active, .img-fade-leave-active { transition: opacity 0.2s; }
.img-fade-enter-from, .img-fade-leave-to { opacity: 0; }

.set-overlay {
  position: absolute; bottom: 30px; left: 12px; right: 12px;
  display: flex; gap: 5px; flex-wrap: wrap;
}
.set-btn {
  display: flex; align-items: center; gap: 4px;
  background: rgba(10,7,3,0.92); border: 1px solid rgba(184,134,11,0.4);
  border-radius: 2px; padding: 3px 7px; cursor: pointer; transition: all 0.2s;
}
.set-btn img { width: 15px; height: 15px; filter: invert(0.9) sepia(0.2); opacity: 0.8; }
.set-btn span { font-family:'Cinzel',serif; font-size:0.5rem; letter-spacing:1px; color:var(--parchment-dk); }
.set-btn:hover, .set-btn.active { background: rgba(184,134,11,0.2); border-color: var(--gold); }

.card-body { padding: 15px; flex-grow: 1; display: flex; flex-direction: column; gap: 7px; }
.card-name-row { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
.card-name     { font-family:'Cinzel',serif; font-weight:700; font-size:0.92rem; color:var(--aged-white); line-height:1.3; }
.mana-cost     { display:flex; flex-wrap:wrap; gap:1px; flex-shrink:0; }
.card-type     { font-family:'Cinzel',serif; font-size:0.62rem; letter-spacing:2px; text-transform:uppercase; color:var(--gold); opacity:0.8; border-bottom:1px solid rgba(184,134,11,0.2); padding-bottom:6px; }
.card-oracle   { background:rgba(0,0,0,0.3); border-left:2px solid rgba(184,134,11,0.25); border-radius:0 2px 2px 0; padding:9px 11px; font-size:0.83rem; line-height:1.6; color:var(--parchment-dk); font-style:italic; flex-grow:1; min-height:60px; }

.card-footer   { background:rgba(0,0,0,0.22); border-top:1px solid rgba(184,134,11,0.12); padding:9px 15px; display:flex; align-items:center; justify-content:space-between; }
.footer-sets   { display:flex; gap:4px; }
.footer-right  { display:flex; align-items:center; gap:8px; }
.preco-tag {
  display:flex; flex-direction:column; align-items:flex-start; line-height:1.2;
  margin-right:auto;
}
.preco-brl {
  font-family:'Cinzel',serif; font-size:0.76rem; color:var(--gold-shine); font-weight:600;
}
.preco-usd { font-size:0.58rem; color:var(--parchment-xdk); }
.collect-actions { display:flex; gap:3px; }
.collect-btn {
  width:22px; height:22px; line-height:1;
  background:rgba(0,0,0,0.4); border:1px solid rgba(184,134,11,0.4);
  color:var(--gold); border-radius:2px; cursor:pointer; font-size:0.9rem;
  transition:all 0.2s;
}
.collect-btn:hover { background:var(--gold); color:var(--obsidian); }
.collect-btn.add   { border-color:var(--gold); }

.qty-badge {
  position:absolute; top:20px; left:20px;
  background:var(--gold); color:var(--obsidian);
  font-family:'Cinzel',serif; font-size:0.66rem; font-weight:700;
  padding:2px 7px; border-radius:2px;
  box-shadow:0 2px 8px rgba(0,0,0,0.6);
}
.footer-set-icon { width:18px; height:18px; filter:invert(0.8) sepia(0.2); opacity:0.5; cursor:pointer; transition:all 0.2s; }
.footer-set-icon:hover { opacity:1; transform:scale(1.2); }
</style>
