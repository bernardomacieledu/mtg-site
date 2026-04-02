<template>
  <div class="lobby">
    <div class="page-hero">
      <h1 class="page-hero-title">⚔ Arena Mágica ⚔</h1>
      <p class="page-hero-sub">Escolha seu deck e entre em batalha</p>
      <div class="hero-divider"><span class="hero-divider-gem">❖</span></div>
    </div>

    <div class="lobby-wrap">
      <div class="lobby-card">

        <div class="section-label cinzel-caps">✦ Seu Nome</div>
        <input v-model="playerName" class="medieval-input" placeholder="Seu nome de jogador..." style="margin-bottom:1.5rem;" />

        <div class="section-label cinzel-caps">✦ Escolha seu Deck</div>
        <div class="deck-grid">
          <div
            v-for="deck in decks"
            :key="deck.id"
            class="deck-option"
            :class="{ selected: selectedDeck === deck.id }"
            @click="selectedDeck = deck.id"
          >
            <div class="deck-colors">
              <span v-for="c in deck.colors" :key="c" class="color-pip" :class="`pip-${c.toLowerCase()}`">
                {{ c }}
              </span>
            </div>
            <div class="deck-name">{{ deck.name }}</div>
            <div class="deck-count cinzel-caps">{{ deck.card_count }} cartas</div>
            <div v-if="selectedDeck === deck.id" class="deck-selected-badge">✦ Selecionado</div>
          </div>
        </div>

        <div class="section-label cinzel-caps" style="margin-top:1.5rem;">✦ Deck do Oponente (IA)</div>
        <select v-model="opponentDeck" class="medieval-input" style="margin-bottom:1.5rem;">
          <option v-for="deck in decks" :key="deck.id" :value="deck.id">{{ deck.name }}</option>
        </select>

        <button
          class="btn-primary"
          style="width:100%;padding:14px;font-size:0.9rem;letter-spacing:4px;"
          :disabled="!selectedDeck || loading"
          @click="startGame"
        >
          {{ loading ? 'Conjurando a Partida...' : '⚔ INICIAR BATALHA ⚔' }}
        </button>

      </div>

      <!-- Rules summary -->
      <div class="rules-summary">
        <div class="section-label cinzel-caps">📜 Como Jogar</div>
        <div class="rules-list">
          <div class="rule-item-mini">🌲 Clique em terrenos ou criaturas com habilidade de toque para gerar mana</div>
          <div class="rule-item-mini">✨ Cartas destacadas em dourado podem ser jogadas (clique para lançar)</div>
          <div class="rule-item-mini">⚔ Na fase de ataque, selecione suas criaturas e confirme</div>
          <div class="rule-item-mini">🛡 Na fase de bloqueio, atribua bloqueadores aos atacantes inimigos</div>
          <div class="rule-item-mini">Space = Passar Prioridade | Enter = Próxima Fase</div>
          <div class="rule-item-mini">❤ Reduza a vida do oponente a 0 para vencer!</div>
        </div>

        <div class="section-label cinzel-caps" style="margin-top:1rem;">⚔ Keywords</div>
        <div class="rules-list">
          <div class="rule-item-mini">🦅 <strong>Flying</strong> — Só pode ser bloqueado por voadores ou reach</div>
          <div class="rule-item-mini">👁 <strong>Vigilance</strong> — Não vira ao atacar</div>
          <div class="rule-item-mini">⚡ <strong>Haste</strong> — Pode atacar imediatamente</div>
          <div class="rule-item-mini">💪 <strong>Trample</strong> — Excesso de dano vai ao jogador</div>
          <div class="rule-item-mini">⚔ <strong>First Strike</strong> — Causa dano antes</div>
          <div class="rule-item-mini">☠ <strong>Deathtouch</strong> — Qualquer dano é letal</div>
          <div class="rule-item-mini">❤ <strong>Lifelink</strong> — Dano causado = vida ganha</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'


const decks        = ref([])
const selectedDeck = ref('')
const opponentDeck = ref('red_aggro')
const playerName   = ref('Jogador')
const loading = ref(false)
const router  = useRouter()

onMounted(async () => {
  const { data } = await axios.get('/api/game/decks/')
  decks.value = data.decks
  if (decks.value.length) selectedDeck.value = decks.value[0].id
})

async function startGame() {
  if (!selectedDeck.value || loading.value) return
  loading.value = true
  try {
    const { data } = await axios.post('/api/game/create/', {
      p1_deck: selectedDeck.value,
      p2_deck: opponentDeck.value,
      p1_name: playerName.value || 'Jogador',
      p2_name: 'Oponente IA',
    })
    router.push({ name: 'game', params: { gameId: data.game_id } })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.lobby { min-height: 100vh; }

.lobby-wrap {
  max-width: 900px; margin: 0 auto;
  padding: 0 1.5rem 4rem;
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 2rem;
  align-items: start;
}

.lobby-card {
  background: linear-gradient(135deg, rgba(26,19,10,0.95), rgba(13,10,6,0.95));
  border: 1px solid rgba(184,134,11,0.3);
  border-radius: 4px;
  padding: 2rem;
}

.section-label { font-size:0.6rem; letter-spacing:3px; color:var(--gold); margin-bottom:0.8rem; }

.deck-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 0.5rem; }

.deck-option {
  border: 1px solid rgba(184,134,11,0.2);
  border-radius: 3px; padding: 14px;
  cursor: pointer; transition: all 0.2s;
  position: relative; background: rgba(0,0,0,0.2);
}
.deck-option:hover { border-color: var(--gold); background: rgba(184,134,11,0.06); }
.deck-option.selected { border-color: var(--gold-shine); background: rgba(184,134,11,0.12); }

.deck-colors { display: flex; gap: 5px; margin-bottom: 6px; }
.color-pip {
  width: 20px; height: 20px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.55rem; font-weight: bold;
}
.pip-w { background: #c8b896; color: #1a0f00; }
.pip-u { background: #1a3a6b; color: #a8d4f5; }
.pip-b { background: #2a1a3e; color: #c8a8f5; }
.pip-r { background: #6b1a1a; color: #f5a8a8; }
.pip-g { background: #1a3a1a; color: #a8f5a8; }

.deck-name { font-family: 'Cinzel', serif; font-size: 0.85rem; color: var(--aged-white); margin-bottom: 4px; }
.deck-count { font-size: 0.55rem; color: var(--parchment-xdk); }
.deck-selected-badge {
  position: absolute; top: 6px; right: 8px;
  font-family: 'Cinzel', serif; font-size: 0.5rem;
  color: var(--gold); letter-spacing: 1px;
}

/* Rules */
.rules-summary {
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(184,134,11,0.15);
  border-radius: 3px; padding: 1.5rem;
}
.rules-list { display: flex; flex-direction: column; gap: 8px; }
.rule-item-mini {
  font-size: 0.78rem; color: var(--parchment-dk);
  line-height: 1.4; padding: 4px 0;
  border-bottom: 1px solid rgba(184,134,11,0.08);
}
.rule-item-mini strong { color: var(--gold); }
</style>
