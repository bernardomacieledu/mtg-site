<!-- PlayerInfo.vue -->
<template>
  <div class="player-info" :class="side">
    <div class="player-name cinzel-caps">{{ player?.name }}</div>
    <div class="player-life" :class="{ danger: player?.life <= 5 }">
      ❤ {{ player?.life }}
    </div>
    <div class="player-lib cinzel-caps">📚 {{ player?.library_count }}</div>
  </div>
</template>

<script setup>
defineProps({ player: Object, side: String })
</script>

<style scoped>
.player-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 6px 10px;
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(184,134,11,0.2);
  border-radius: 3px;
  flex-shrink: 0;
}
.player-name { font-size: 0.65rem; letter-spacing: 2px; color: var(--parchment-dk); }
.player-life { font-family:'Cinzel Decorative',serif; font-size: 1.2rem; color: var(--gold-shine); }
.player-life.danger { color: var(--crimson-lt); animation: pulse-life 0.8s ease-in-out infinite; }
@keyframes pulse-life { 0%,100%{opacity:1} 50%{opacity:0.5} }
.player-lib { font-size: 0.58rem; color: var(--parchment-xdk); }
</style>
