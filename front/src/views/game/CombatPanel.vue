<template>
  <div class="combat-panel">
    <!-- Declare Attackers -->
    <div v-if="phase === 'combat_attackers'" class="combat-section">
      <div class="combat-label">⚔ Declare Atacantes</div>
      <div class="combat-creatures">
        <div
          v-for="perm in availableAttackers"
          :key="perm.uid"
          class="combat-creature"
          :class="{ selected: attackers.includes(perm.uid) }"
          @click="$emit('toggle-attacker', perm.uid)"
        >
          {{ perm.name }} ({{ perm.power }}/{{ perm.toughness }})
          <span v-if="attackers.includes(perm.uid)">⚔</span>
        </div>
      </div>
      <button class="btn-primary" style="margin-top:8px;font-size:0.65rem;" @click="$emit('confirm-attackers')">
        Confirmar Ataque ({{ attackers.length }} atacantes)
      </button>
    </div>

    <!-- Declare Blockers -->
    <div v-if="phase === 'combat_blockers'" class="combat-section">
      <div class="combat-label">🛡 Declare Bloqueadores</div>
      <div v-if="combatAttackers.length" class="attackers-list">
        <div class="combat-sub">Atacantes adversários:</div>
        <div
          v-for="uid in combatAttackers"
          :key="uid"
          class="attacker-entry"
        >
          <span class="att-name">⚔ {{ permName(uid) }}</span>
        </div>
      </div>
      <div class="blockers-list">
        <div class="combat-sub">Seus bloqueadores:</div>
        <div
          v-for="perm in myCreatures"
          :key="perm.uid"
          class="blocker-entry"
        >
          <span class="blk-name">{{ perm.name }}</span>
          <select
            class="blk-select"
            @change="onBlockerChange(perm.uid, $event.target.value)"
          >
            <option value="">Não bloqueia</option>
            <option v-for="aUid in combatAttackers" :key="aUid" :value="aUid">
              Bloqueia {{ permName(aUid) }}
            </option>
          </select>
        </div>
      </div>
      <button class="btn-primary" style="margin-top:8px;font-size:0.65rem;" @click="$emit('confirm-blockers')">
        Confirmar Bloqueio
      </button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  phase:             String,
  attackers:         { type: Array, default: () => [] },
  availableAttackers:{ type: Array, default: () => [] },
  combatAttackers:   { type: Array, default: () => [] },
  myCreatures:       { type: Array, default: () => [] },
  manaMap:           Object,
})
const emit = defineEmits(['toggle-attacker','confirm-attackers','toggle-blocker','confirm-blockers'])

function permName(uid) {
  const all = [...props.availableAttackers, ...props.myCreatures]
  return all.find(p => p.uid === uid)?.name || uid.slice(0,6)
}

function onBlockerChange(blockerUid, attackerUid) {
  emit('toggle-blocker', { blocker: blockerUid, attacker: attackerUid })
}
</script>

<style scoped>
.combat-panel {
  background: rgba(224,120,32,0.06);
  border: 1px solid rgba(224,120,32,0.3);
  border-radius: 3px; padding: 10px;
}
.combat-label { font-family:'Cinzel',serif; font-size:0.7rem; color:#e07820; letter-spacing:2px; margin-bottom:8px; }
.combat-sub   { font-family:'Cinzel',serif; font-size:0.58rem; color:var(--parchment-xdk); margin-bottom:4px; }
.combat-creatures, .blockers-list, .attackers-list { display:flex; flex-direction:column; gap:4px; }
.combat-creature {
  padding: 5px 8px; border:1px solid rgba(224,120,32,0.2); border-radius:2px;
  font-family:'Cinzel',serif; font-size:0.62rem; color:var(--parchment-dk);
  cursor:pointer; transition:all 0.2s; display:flex; justify-content:space-between;
}
.combat-creature:hover { border-color:#e07820; color:var(--aged-white); }
.combat-creature.selected { border-color:#e07820; background:rgba(224,120,32,0.15); color:var(--gold-shine); }
.attacker-entry { padding:4px 8px; background:rgba(139,26,26,0.15); border-radius:2px; font-family:'Cinzel',serif; font-size:0.6rem; color:var(--crimson-lt); }
.blocker-entry { display:flex; align-items:center; gap:6px; padding:4px 0; }
.blk-name { font-family:'Cinzel',serif; font-size:0.6rem; color:var(--parchment-dk); flex:1; }
.blk-select {
  background:#0d0a06; border:1px solid rgba(184,134,11,0.3); border-radius:2px;
  color:var(--parchment); font-size:0.58rem; padding:3px 5px; outline:none;
}
</style>
