<template>
  <div class="mana-pool">
    <template v-for="(amt, color) in mana" :key="color">
      <div v-if="amt > 0" class="mana-pip" :class="`mana-${color.toLowerCase()}`">
        <span class="mana-color">{{ color }}</span>
        <span class="mana-amt">{{ amt }}</span>
      </div>
    </template>
    <div v-if="total === 0" class="mana-empty">— sem mana —</div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ mana: { type: Object, default: () => ({}) } })
const total = computed(() => Object.values(props.mana).reduce((a,b) => a+b, 0))
</script>

<style scoped>
.mana-pool {
  display: flex; gap: 4px; align-items: center; flex-wrap: wrap;
  padding: 4px 6px;
  background: rgba(0,0,0,0.2);
  border-radius: 2px;
  min-height: 28px;
  flex-shrink: 0;
}
.mana-pip {
  display: flex; align-items: center; gap: 2px;
  padding: 2px 6px; border-radius: 50px;
  font-family: 'Cinzel', serif; font-size: 0.6rem; font-weight: 700;
}
.mana-w { background: #c8b896; color: #1a0f00; }
.mana-u { background: #1a3a6b; color: #a8d4f5; border: 1px solid #2d5fa8; }
.mana-b { background: #2a1a3e; color: #c8a8f5; border: 1px solid #4a2d6b; }
.mana-r { background: #6b1a1a; color: #f5a8a8; border: 1px solid #a83030; }
.mana-g { background: #1a3a1a; color: #a8f5a8; border: 1px solid #2d6b2d; }
.mana-c { background: #3a3a3a; color: #c8c8c8; }
.mana-color { font-size: 0.5rem; }
.mana-amt { font-size: 0.7rem; }
.mana-empty { font-size: 0.55rem; color: rgba(184,134,11,0.3); font-style: italic; }
</style>
