<template>
  <div class="stack-panel">
    <div class="stack-label cinzel-caps">⚡ Stack ({{ stack.length }})</div>
    <div class="stack-items">
      <div v-for="item in [...stack].reverse()" :key="item.uid" class="stack-item">
        <span class="stack-controller">{{ item.controller === 'p1' ? '👤' : '🤖' }}</span>
        <span class="stack-name">{{ item.name }}</span>
        <span class="stack-type">{{ item.item_type }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({ stack: { type: Array, default: () => [] }, manaMap: Object })
</script>

<style scoped>
.stack-panel {
  background: rgba(0,0,0,0.3);
  border: 1px solid rgba(59,130,246,0.3);
  border-radius: 3px; padding: 8px;
}
.stack-label { font-size:0.55rem; letter-spacing:3px; color:#3b82f6; margin-bottom:6px; }
.stack-items { display:flex; flex-direction:column; gap:4px; }
.stack-item {
  display:flex; align-items:center; gap:6px;
  background: rgba(59,130,246,0.1);
  border: 1px solid rgba(59,130,246,0.2);
  border-radius:2px; padding:4px 8px;
}
.stack-controller { font-size:0.8rem; }
.stack-name { font-family:'Cinzel',serif; font-size:0.65rem; color:var(--aged-white); flex:1; }
.stack-type { font-size:0.5rem; color:rgba(59,130,246,0.7); letter-spacing:1px; }
</style>
