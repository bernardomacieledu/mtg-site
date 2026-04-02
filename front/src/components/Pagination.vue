<template>
  <div v-if="totalPages > 1" class="scroll-nav">
    <button class="btn-ghost" :class="{ disabled: page <= 1 }" @click="go(page - 1)">◂ Anterior</button>
    <span class="scroll-info">{{ page }} · de · {{ totalPages }}</span>
    <button class="btn-ghost" :class="{ disabled: page >= totalPages }" @click="go(page + 1)">Próxima ▸</button>
  </div>
</template>

<script setup>
const props = defineProps({ page: Number, totalPages: Number })
const emit  = defineEmits(['change'])
function go(p) {
  if (p < 1 || p > props.totalPages) return
  emit('change', p)
  window.scrollTo({ top: 0, behavior: 'smooth' })
}
</script>

<style scoped>
.scroll-nav { display:flex; justify-content:center; align-items:center; gap:1rem; margin-top:4rem; }
.scroll-info { font-family:'Cinzel',serif; font-size:0.8rem; color:var(--gold); letter-spacing:2px; min-width:120px; text-align:center; }
</style>
