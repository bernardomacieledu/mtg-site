<template>
  <div class="phase-tracker">
    <div
      v-for="ph in phases"
      :key="ph.id"
      class="phase-pip"
      :class="{ active: phase === ph.id, past: isPast(ph.id) }"
      :title="ph.label"
    >
      <span class="pip-icon">{{ ph.icon }}</span>
      <span class="pip-label">{{ ph.short }}</span>
    </div>
    <div class="active-player-badge">
      {{ activePlayer === 'p1' ? '👤' : '🤖' }} Turno
    </div>
  </div>
</template>

<script setup>
const props = defineProps({ phase: String, activePlayer: String })

const phases = [
  { id: 'untap',             icon: '↺', short: 'Des', label: 'Destornar' },
  { id: 'upkeep',            icon: '⏰', short: 'Man', label: 'Manutenção' },
  { id: 'draw',              icon: '📤', short: 'Com', label: 'Comprar' },
  { id: 'main1',             icon: '🏠', short: 'P1',  label: 'Fase Principal 1' },
  { id: 'combat_attackers',  icon: '⚔', short: 'Atq', label: 'Atacantes' },
  { id: 'combat_blockers',   icon: '🛡', short: 'Blq', label: 'Bloqueadores' },
  { id: 'combat_damage',     icon: '💥', short: 'Dno', label: 'Dano' },
  { id: 'main2',             icon: '🏠', short: 'P2',  label: 'Fase Principal 2' },
  { id: 'end',               icon: '🌙', short: 'Fim', label: 'Encerramento' },
]

const ORDER = phases.map(p => p.id)

function isPast(phaseId) {
  return ORDER.indexOf(phaseId) < ORDER.indexOf(props.phase)
}
</script>

<style scoped>
.phase-tracker {
  display: flex; gap: 3px; align-items: center; flex-wrap: wrap;
  padding: 6px 8px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(184,134,11,0.15);
  border-radius: 3px;
  flex-shrink: 0;
}
.phase-pip {
  display: flex; flex-direction: column; align-items: center;
  padding: 3px 5px; border-radius: 2px;
  opacity: 0.35; transition: all 0.2s;
  min-width: 28px;
}
.phase-pip.past { opacity: 0.5; }
.phase-pip.active {
  opacity: 1;
  background: rgba(184,134,11,0.2);
  border: 1px solid var(--gold);
}
.pip-icon { font-size: 0.8rem; }
.pip-label { font-family:'Cinzel',serif; font-size:0.38rem; letter-spacing:1px; color:var(--parchment-xdk); margin-top:1px; }
.phase-pip.active .pip-label { color: var(--gold); }
.active-player-badge {
  margin-left: auto;
  font-family: 'Cinzel', serif;
  font-size: 0.6rem;
  color: var(--gold);
  padding: 3px 8px;
  background: rgba(184,134,11,0.1);
  border-radius: 2px;
}
</style>
