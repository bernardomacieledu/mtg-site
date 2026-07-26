<template>
  <div>
    <div class="back-bar">
      <button class="btn-ghost" @click="$router.back()">◂ Voltar</button>
    </div>

    <div v-if="loading" class="spinner-wrap">
      <div class="spinner"></div>
      <span class="spinner-text">Consultando os Arquivos...</span>
    </div>

    <div v-else-if="prints.length" class="detail-wrap">

      <!-- ── Esquerda: imagem + impressões ── -->
      <div class="detail-left">
        <div class="art-frame">
          <Transition name="img-fade" mode="out-in">
            <img :key="activeImg" :src="activeImg" :alt="cardName" class="detail-img" />
          </Transition>
        </div>

        <div class="prints-label cinzel-caps">✦ Impressões Disponíveis</div>
        <div class="prints-grid">
          <button
            v-for="p in prints"
            :key="p.set_code"
            class="print-btn"
            :class="{ active: activePrint?.set_code === p.set_code }"
            @click="activePrint = p"
            :title="p.set_name"
          >
            <img
              :src="`https://svgs.scryfall.io/sets/${p.set_code.toLowerCase()}.svg`"
              :alt="p.set_code"
              @error="e => e.target.style.display='none'"
            />
            <div class="print-info">
              <span class="print-set-name">{{ p.set_name }}</span>
              <span class="print-date">{{ p.released_at }}</span>
            </div>
            <span v-if="activePrint?.set_code === p.set_code" class="print-active-dot">●</span>
          </button>
        </div>
      </div>

      <!-- ── Direita: informações ── -->
      <div class="detail-right">
        <div class="detail-header">
          <h1 class="detail-name">{{ cardName }}</h1>
          <div class="detail-mana" v-html="renderMana(currentCard?.mana_cost)" />
        </div>

        <div class="hero-divider" style="margin:1rem 0">
          <span class="hero-divider-gem">❖</span>
        </div>

        <div class="detail-section">
          <div class="detail-section-label">Tipo</div>
          <div class="detail-section-value">{{ currentCard?.type_line }}</div>
        </div>

        <div class="detail-section">
          <div class="detail-section-label">Texto</div>
          <div class="detail-oracle" v-html="renderMana(currentCard?.oracle_text)" />
        </div>

        <div class="detail-section">
          <div class="detail-section-label">Raridade · CMC</div>
          <div style="display:flex;align-items:center;gap:12px;">
            <span :class="['rarity-badge', `rarity-${currentCard?.rarity}`]">{{ currentCard?.rarity }}</span>
            <span class="detail-section-value" style="font-size:0.9rem;">
              {{ currentCard?.cmc !== null ? currentCard?.cmc : '—' }}
            </span>
          </div>
        </div>

        <div class="detail-section" v-if="activePrint">
          <div class="detail-section-label">Coleção</div>
          <div class="detail-set-row">
            <img
              :src="`https://svgs.scryfall.io/sets/${activePrint.set_code.toLowerCase()}.svg`"
              class="detail-set-icon"
              @error="e => e.target.style.display='none'"
            />
            <span class="detail-section-value">
              {{ activePrint.set_name }}
              <em style="color:var(--parchment-xdk)"> · {{ activePrint.released_at }}</em>
            </span>
          </div>
        </div>

        <!-- ── Preços ── -->
        <div class="detail-section">
          <div class="detail-section-label">💰 Preços de Mercado</div>

          <div v-if="pricesLoading" style="display:flex;align-items:center;gap:10px;padding:8px 0;">
            <div class="spinner" style="width:20px;height:20px;border-width:2px;"></div>
            <span class="cinzel-caps" style="font-size:0.6rem;">Consultando mercado...</span>
          </div>

          <div v-else-if="prices && hasPrices" class="prices-grid">
            <div v-if="prices.usd" class="price-item">
              <span class="price-label">Normal</span>
              <span class="price-value">US$ {{ prices.usd }}</span>
            </div>
            <div v-if="prices.usd_foil" class="price-item price-foil">
              <span class="price-label">✨ Foil</span>
              <span class="price-value">US$ {{ prices.usd_foil }}</span>
            </div>
            <div v-if="prices.usd_etched" class="price-item price-foil">
              <span class="price-label">Etched</span>
              <span class="price-value">US$ {{ prices.usd_etched }}</span>
            </div>
            <div v-if="prices.eur" class="price-item">
              <span class="price-label">EUR</span>
              <span class="price-value">€ {{ prices.eur }}</span>
            </div>
            <div v-if="prices.eur_foil" class="price-item price-foil">
              <span class="price-label">EUR Foil</span>
              <span class="price-value">€ {{ prices.eur_foil }}</span>
            </div>
            <div v-if="prices.tix" class="price-item">
              <span class="price-label">MTGO</span>
              <span class="price-value">{{ prices.tix }} tix</span>
            </div>
          </div>

          <div v-else class="price-unavailable">
            Preços não disponíveis para esta impressão.
          </div>
        </div>

        <!-- ── Ações ── -->
        <div class="detail-actions">
          <a
            :href="`https://scryfall.com/search?q=%21%22${encodeURIComponent(cardName)}%22`"
            target="_blank"
            class="btn-ghost"
          >🔍 Scryfall</a>
          <router-link :to="{ name: 'cards', query: { set: activePrint?.set_code } }" class="btn-ghost">
            📜 Ver Coleção
          </router-link>
          <a
            :href="ligaMagicUrl(cardName)"
            target="_blank"
            rel="noopener noreferrer"
            class="btn-ghost"
            title="Abre a busca desta carta no site da Liga Magic"
          >💰 Preço (R$)</a>
        </div>
      </div>

    </div>

    <div v-else-if="!loading" class="no-results" style="padding:6rem;text-align:center">
      <div class="no-results-title">✦ Carta Não Encontrada ✦</div>
      <p class="no-results-sub">Os arquivos do Nexus não contêm registros desta carta.</p>
      <button class="btn-ghost" style="margin-top:2rem" @click="$router.back()">◂ Voltar</button>
    </div>
  </div>

</template>

<script setup>
import { ligaMagicUrl } from '@/composables/useLigaMagic'
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getCardImages, getCardPrices } from '@/composables/api'
import { useMana } from '@/composables/useMana'

const route          = useRoute()
const { renderMana } = useMana()

const prints        = ref([])
const activePrint   = ref(null)
const loading       = ref(false)
const prices        = ref(null)
const pricesLoading = ref(false)

const cardName    = computed(() => decodeURIComponent(route.params.name))
const activeImg   = computed(() => activePrint.value?.image_url || '')
const currentCard = computed(() => activePrint.value)
const hasPrices   = computed(() =>
  prices.value && Object.values(prices.value).some(v => v !== null && v !== undefined)
)

async function load() {
  loading.value       = true
  pricesLoading.value = true
  prints.value        = []
  prices.value        = null

  try {
    const { data } = await getCardImages(cardName.value)
    prints.value      = data.images || []
    activePrint.value = prints.value[0] || null
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }

  // Busca preços em paralelo (não bloqueia a UI)
  try {
    const { data } = await getCardPrices(cardName.value, activePrint.value?.scryfall_id)
    prices.value = data.prices
  } catch {
    prices.value = null
  } finally {
    pricesLoading.value = false
  }
}

onMounted(load)
watch(cardName, load)
</script>

<style scoped>
.preco-externo { margin: 1.4rem 0; display: flex; flex-direction: column; gap: 6px; align-items: flex-start; }
.liga-btn { display: inline-block; text-decoration: none; }
.preco-nota { font-size: 0.64rem; color: var(--parchment-xdk); font-style: italic; }

.back-bar { max-width:1400px; margin:0 auto; padding:1.5rem 1.5rem 0; }

.detail-wrap {
  max-width: 1200px; margin: 0 auto;
  padding: 2rem 1.5rem 6rem;
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 3rem;
  align-items: start;
}

/* ── Esquerda ── */
.art-frame {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(184,134,11,0.25);
  border-radius: 8px; padding: 12px;
  margin-bottom: 1.5rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.6);
}
.detail-img { width:100%; border-radius:6px; display:block; }

.img-fade-enter-active, .img-fade-leave-active { transition: opacity 0.25s; }
.img-fade-enter-from, .img-fade-leave-to { opacity: 0; }

.prints-label { font-size:0.6rem; letter-spacing:3px; color:var(--gold); margin-bottom:0.8rem; }
.prints-grid  { display:flex; flex-direction:column; gap:6px; max-height:340px; overflow-y:auto; }

.print-btn {
  display:flex; align-items:center; gap:10px;
  background:rgba(0,0,0,0.2); border:1px solid rgba(184,134,11,0.18);
  border-radius:3px; padding:8px 12px; cursor:pointer; transition:all 0.2s;
  text-align:left; width:100%;
}
.print-btn:hover, .print-btn.active { background:rgba(184,134,11,0.1); border-color:var(--gold); }
.print-btn img      { width:24px; height:24px; filter:invert(0.85) sepia(0.3); opacity:0.8; flex-shrink:0; }
.print-info         { flex:1; min-width:0; }
.print-set-name     { display:block; font-family:'Cinzel',serif; font-size:0.75rem; color:var(--aged-white); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.print-date         { display:block; font-size:0.68rem; color:var(--parchment-xdk); font-style:italic; }
.print-active-dot   { color:var(--gold); font-size:0.7rem; }

/* ── Direita ── */
.detail-header { display:flex; align-items:flex-start; justify-content:space-between; gap:1rem; flex-wrap:wrap; }
.detail-name   { font-family:'Cinzel Decorative',serif; font-size:clamp(1.4rem,3vw,2.2rem); color:var(--gold-shine); text-shadow:0 0 30px rgba(212,160,23,0.3); line-height:1.2; }
.detail-mana   { display:flex; flex-wrap:wrap; gap:2px; align-items:center; flex-shrink:0; }

.detail-section       { margin-bottom:1.4rem; }
.detail-section-label { font-family:'Cinzel',serif; font-size:0.6rem; letter-spacing:3px; text-transform:uppercase; color:var(--gold); opacity:0.7; margin-bottom:8px; }
.detail-section-value { font-size:1rem; color:var(--parchment); line-height:1.5; }

.detail-oracle {
  background:rgba(0,0,0,0.3); border-left:3px solid rgba(184,134,11,0.3);
  border-radius:0 3px 3px 0; padding:14px 16px;
  font-size:0.95rem; line-height:1.7; color:var(--parchment-dk); font-style:italic;
}

.detail-set-row  { display:flex; align-items:center; gap:10px; }
.detail-set-icon { width:28px; height:28px; filter:invert(0.85) sepia(0.3); opacity:0.8; }

/* ── Preços ── */
.prices-grid {
  display: flex; gap: 10px; flex-wrap: wrap;
}
.price-item {
  background: rgba(0,0,0,0.35);
  border: 1px solid rgba(184,134,11,0.22);
  border-radius: 3px; padding: 10px 18px;
  text-align: center; min-width: 90px;
  transition: border-color 0.2s;
}
.price-item:hover { border-color: var(--gold); }
.price-foil {
  border-color: rgba(160,200,255,0.25);
  background: rgba(120,160,220,0.06);
}
.price-label {
  display:block; font-family:'Cinzel',serif;
  font-size:0.55rem; letter-spacing:2px;
  color:var(--gold); margin-bottom:5px;
}
.price-value {
  display:block; font-size:1.1rem;
  color:var(--aged-white); font-weight:bold;
  font-family:'Cinzel',serif;
}
.price-unavailable {
  font-style:italic; color:var(--parchment-xdk); font-size:0.88rem;
}

/* ── Ações ── */
.detail-actions { display:flex; gap:10px; flex-wrap:wrap; margin-top:2rem; padding-top:1.5rem; border-top:1px solid rgba(184,134,11,0.15); }

@media (max-width: 800px) {
  .detail-wrap { grid-template-columns:1fr; }
}
</style>
