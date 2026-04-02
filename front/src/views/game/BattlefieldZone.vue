<template>
  <div class="bf-zone" :class="side">
    <div class="zone-label cinzel-caps">{{ side === 'player' ? '⚔ Seu Campo' : '🤖 Campo Adversário' }}</div>
    <div class="permanents-grid">
      <div
        v-for="perm in permanents"
        :key="perm.uid"
        class="permanent"
        :class="{
          tapped:    perm.tapped,
          attacking: perm.attacking,
          blocking:  perm.blocking,
          selectable: selectableUids.includes(perm.uid),
          creature:  perm.type === 'Creature',
          land:      perm.type === 'Land',
        }"
        @click="onPermClick(perm)"
      >
        <!-- Card art placeholder with gradient by color -->
        <div class="perm-art" :style="artStyle(perm)">
          <span class="perm-type-icon">{{ typeIcon(perm) }}</span>
          <div v-if="perm.damage > 0" class="damage-counter">💥{{ perm.damage }}</div>
        </div>

        <div class="perm-body">
          <div class="perm-name">{{ perm.name }}</div>
          <div v-if="perm.type === 'Creature'" class="perm-pt">
            {{ perm.power }}/{{ perm.toughness }}
          </div>
        </div>

        <div class="perm-keywords" v-if="perm.keywords?.length">
          <span v-for="kw in perm.keywords" :key="kw" class="kw-badge">{{ kwIcon(kw) }}</span>
        </div>

        <!-- Tap button for player's permanents -->
        <button
          v-if="side === 'player' && !perm.tapped && hasActivatedAbility(perm)"
          class="tap-btn"
          @click.stop="$emit('tap', perm.uid)"
          title="Ativar habilidade"
        >T</button>
      </div>

      <div v-if="!permanents.length" class="empty-zone">
        <span>Vazio</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  permanents:     { type: Array, default: () => [] },
  side:           { type: String, default: 'player' },
  selectableUids: { type: Array, default: () => [] },
  manaMap:        { type: Object, default: () => ({}) },
})
const emit = defineEmits(['select', 'tap'])

const COLOR_GRADIENTS = {
  W: 'linear-gradient(135deg, #e8e0c8, #c8b896)',
  U: 'linear-gradient(135deg, #1a3a6b, #2d5fa8)',
  B: 'linear-gradient(135deg, #1a0f2e, #2d1a4a)',
  R: 'linear-gradient(135deg, #6b1a1a, #a83030)',
  G: 'linear-gradient(135deg, #1a3a1a, #2d6b2d)',
  GW:'linear-gradient(135deg, #2d6b2d, #c8b896)',
  null: 'linear-gradient(135deg, #2a2016, #1a1510)',
}

function artStyle(perm) {
  const color = perm.color || 'null'
  const grad = COLOR_GRADIENTS[color] || COLOR_GRADIENTS.null
  return { background: grad }
}

function typeIcon(perm) {
  const icons = {
    Creature: '🐉', Land: '🌲', Instant: '⚡', Sorcery: '📜',
    Enchantment: '✨', Artifact: '⚙',
  }
  return icons[perm.type] || '🃏'
}

function kwIcon(kw) {
  const icons = {
    flying: '🦅', vigilance: '👁', haste: '⚡', trample: '💪',
    'first strike': '⚔', deathtouch: '☠', lifelink: '❤', reach: '🎯',
  }
  return (icons[kw] || '') + ' ' + kw
}

function hasActivatedAbility(perm) {
  return perm.type !== 'Creature' ||
    (perm.type === 'Creature' && perm.oracle_text?.includes('{T}:'))
}

function onPermClick(perm) {
  emit('select', perm.uid)
}
</script>

<style scoped>
.bf-zone {
  flex: 1;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.zone-label {
  font-size: 0.55rem;
  letter-spacing: 3px;
  color: rgba(184,134,11,0.5);
  padding: 2px 0;
}

.permanents-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-content: flex-start;
  min-height: 100px;
  padding: 4px;
  border: 1px solid rgba(184,134,11,0.1);
  border-radius: 3px;
  background: rgba(0,0,0,0.1);
}

.permanent {
  width: 72px;
  border: 1px solid rgba(184,134,11,0.3);
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
  background: #0d0a06;
  flex-shrink: 0;
}

.permanent:hover { border-color: var(--gold); transform: translateY(-2px); }
.permanent.selectable { border-color: var(--crimson-lt); box-shadow: 0 0 8px rgba(192,57,43,0.5); }
.permanent.attacking  { border-color: #e07820; box-shadow: 0 0 8px rgba(224,120,32,0.4); }
.permanent.blocking   { border-color: #3b82f6; box-shadow: 0 0 8px rgba(59,130,246,0.4); }
.permanent.tapped     { transform: rotate(90deg); margin: 12px 4px; }
.permanent.tapped:hover { transform: rotate(90deg) translateY(-2px); }

.perm-art {
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.4rem;
  position: relative;
}

.damage-counter {
  position: absolute;
  top: 2px; right: 2px;
  font-size: 0.5rem;
  background: rgba(192,57,43,0.8);
  border-radius: 2px;
  padding: 1px 3px;
  color: #fff;
}

.perm-body {
  padding: 3px 4px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2px;
}

.perm-name {
  font-family: 'Cinzel', serif;
  font-size: 0.45rem;
  color: var(--parchment-dk);
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.perm-pt {
  font-family: 'Cinzel', serif;
  font-size: 0.6rem;
  font-weight: 700;
  color: var(--gold-shine);
  flex-shrink: 0;
}

.perm-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 2px;
  padding: 0 3px 3px;
}

.kw-badge {
  font-size: 0.38rem;
  background: rgba(184,134,11,0.15);
  border-radius: 2px;
  padding: 1px 3px;
  color: var(--gold);
  letter-spacing: 0.5px;
}

.tap-btn {
  position: absolute;
  top: 2px; left: 2px;
  width: 14px; height: 14px;
  background: rgba(184,134,11,0.3);
  border: 1px solid var(--gold);
  border-radius: 50%;
  font-size: 0.45rem;
  color: var(--gold);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-zone {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(184,134,11,0.2);
  font-style: italic;
  font-size: 0.7rem;
  padding: 20px;
}
</style>
