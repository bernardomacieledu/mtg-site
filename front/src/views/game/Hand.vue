<template>
  <div class="hand-zone">
    <div class="hand-label cinzel-caps">{{ hidden ? `Mão (${count})` : `Sua Mão (${cards.length})` }}</div>

    <!-- Hidden opponent hand -->
    <div v-if="hidden" class="hand-hidden">
      <div v-for="i in count" :key="i" class="card-back">
        <div class="card-back-pattern">⚜</div>
      </div>
    </div>

    <!-- Player hand -->
    <div v-else class="hand-cards">
      <div
        v-for="cardId in cards"
        :key="cardId"
        class="hand-card"
        :class="{
          playable: playable.includes(cardId),
          land: cardsDb[cardId]?.type === 'Land',
        }"
        @click="$emit('play', cardId)"
      >
        <!-- Mana cost -->
        <div class="card-cost">
          <template v-for="(amt, sym) in (cardsDb[cardId]?.mana_cost || {})" :key="sym">
            <img v-if="manaMap[`{${sym}}`]" :src="manaMap[`{${sym}}`]" class="mana-sym" />
            <span v-else class="mana-txt">{{ sym }}</span>
          </template>
        </div>

        <!-- Art -->
        <div class="card-art-mini" :style="cardStyle(cardId)">
          <span class="type-icon-mini">{{ typeIcon(cardId) }}</span>
        </div>

        <!-- Name -->
        <div class="card-name-mini">{{ cardsDb[cardId]?.name || cardId }}</div>

        <!-- P/T for creatures -->
        <div v-if="cardsDb[cardId]?.power != null" class="card-pt-mini">
          {{ cardsDb[cardId].power }}/{{ cardsDb[cardId].toughness }}
        </div>

        <!-- Playable glow -->
        <div v-if="playable.includes(cardId)" class="playable-glow" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  cards:   { type: Array, default: () => [] },
  hidden:  { type: Boolean, default: false },
  count:   { type: Number, default: 0 },
  cardsDb: { type: Object, default: () => ({}) },
  manaMap: { type: Object, default: () => ({}) },
  playable:{ type: Array, default: () => [] },
  phase:   { type: String, default: '' },
})
defineEmits(['play'])

const COLOR_BG = {
  W: '#c8b896', U: '#1a3a6b', B: '#1a0f2e',
  R: '#6b1a1a', G: '#1a3a1a', null: '#2a2016',
}

function cardStyle(cardId) {
  const card = {} // injected via cardsDb
  return {}
}

function typeIcon(cardId) {
  // We don't have cardsDb here directly, but we do via prop
  return '🃏'
}
</script>

<script>
export default {
  methods: {
    cardStyle(cardId) {
      const card = this.cardsDb[cardId]
      if (!card) return {}
      const colors = { W:'#c8b896',U:'#1a3a6b',B:'#1a0f2e',R:'#6b1a1a',G:'#1a3a1a' }
      const bg = colors[card.color] || '#2a2016'
      return { background: bg }
    },
    typeIcon(cardId) {
      const card = this.cardsDb[cardId]
      if (!card) return '🃏'
      const icons = { Creature:'🐉',Land:'🌲',Instant:'⚡',Sorcery:'📜',Enchantment:'✨',Artifact:'⚙' }
      return icons[card.type] || '🃏'
    }
  }
}
</script>

<style scoped>
.hand-zone {
  display: flex;
  flex-direction: column;
  gap: 4px;
  flex-shrink: 0;
}

.hand-label {
  font-size: 0.55rem;
  letter-spacing: 3px;
  color: rgba(184,134,11,0.5);
}

.hand-hidden {
  display: flex;
  gap: 4px;
  flex-wrap: wrap;
}

.card-back {
  width: 48px; height: 68px;
  background: linear-gradient(135deg, #1a0f2e, #0d0a06);
  border: 1px solid rgba(184,134,11,0.3);
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-back-pattern {
  color: rgba(184,134,11,0.3);
  font-size: 1.2rem;
}

.hand-cards {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  padding: 4px;
}

.hand-card {
  width: 64px;
  height: 90px;
  border: 1px solid rgba(184,134,11,0.25);
  border-radius: 4px;
  overflow: hidden;
  cursor: default;
  transition: all 0.2s;
  position: relative;
  background: #0d0a06;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.hand-card.playable {
  border-color: rgba(212,160,23,0.6);
  cursor: pointer;
}
.hand-card.playable:hover {
  transform: translateY(-8px);
  border-color: var(--gold-shine);
  box-shadow: 0 8px 20px rgba(0,0,0,0.6), 0 0 16px rgba(212,160,23,0.3);
  z-index: 10;
}

.card-cost {
  display: flex;
  justify-content: flex-end;
  padding: 2px 3px;
  gap: 1px;
  background: rgba(0,0,0,0.4);
  min-height: 14px;
}

.mana-sym { width: 10px; height: 10px; }
.mana-txt { font-size: 0.45rem; color: var(--gold); }

.card-art-mini {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #2a2016, #1a1510);
}

.type-icon-mini { font-size: 1.2rem; }

.card-name-mini {
  font-family: 'Cinzel', serif;
  font-size: 0.38rem;
  color: var(--parchment-dk);
  padding: 2px 3px;
  text-align: center;
  line-height: 1.2;
  background: rgba(0,0,0,0.5);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-pt-mini {
  font-family: 'Cinzel', serif;
  font-size: 0.5rem;
  color: var(--gold-shine);
  font-weight: 700;
  text-align: right;
  padding: 1px 3px;
  background: rgba(0,0,0,0.6);
}

.playable-glow {
  position: absolute;
  inset: -1px;
  border: 2px solid var(--gold-shine);
  border-radius: 4px;
  pointer-events: none;
  animation: glow-pulse 1.5s ease-in-out infinite;
}

@keyframes glow-pulse {
  0%,100% { opacity: 0.4; }
  50%      { opacity: 1; }
}
</style>
