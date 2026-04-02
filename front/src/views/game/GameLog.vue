<template>
  <div class="game-log" ref="logEl">
    <div class="log-label cinzel-caps">📜 Log</div>
    <div class="log-entries">
      <div
        v-for="(entry, i) in log"
        :key="i"
        class="log-entry"
        :class="entryClass(entry)"
      >
        {{ entry }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'
const props = defineProps({ log: { type: Array, default: () => [] } })
const logEl = ref(null)

watch(() => props.log, async () => {
  await nextTick()
  if (logEl.value) {
    const entries = logEl.value.querySelector('.log-entries')
    if (entries) entries.scrollTop = entries.scrollHeight
  }
})

function entryClass(entry) {
  if (entry.includes('══')) return 'log-turn'
  if (entry.includes('perdeu') || entry.includes('derrota')) return 'log-loss'
  if (entry.includes('dano') || entry.includes('causa')) return 'log-damage'
  if (entry.includes('Fase:')) return 'log-phase'
  if (entry.includes('cemitério') || entry.includes('vai ao')) return 'log-death'
  if (entry.includes('Trigger')) return 'log-trigger'
  return 'log-normal'
}
</script>

<style scoped>
.game-log {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  background: rgba(0,0,0,0.2);
  border: 1px solid rgba(184,134,11,0.1);
  border-radius: 3px;
  overflow: hidden;
}
.log-label { font-size:0.5rem; letter-spacing:3px; color:rgba(184,134,11,0.4); padding:4px 8px; border-bottom:1px solid rgba(184,134,11,0.1); }
.log-entries {
  flex:1; overflow-y:auto; padding:6px 8px;
  display:flex; flex-direction:column; gap:2px;
}
.log-entry { font-size:0.6rem; line-height:1.4; padding:1px 0; }
.log-turn    { color:var(--gold); font-family:'Cinzel',serif; letter-spacing:1px; margin:4px 0 2px; }
.log-phase   { color:rgba(184,134,11,0.5); font-style:italic; font-size:0.55rem; }
.log-damage  { color:#f5a8a8; }
.log-death   { color:var(--parchment-xdk); font-style:italic; }
.log-loss    { color:var(--crimson-lt); font-weight:bold; }
.log-trigger { color:#a8d4f5; }
.log-normal  { color:var(--parchment-dk); }
</style>
