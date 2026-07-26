<template>
  <Transition name="dock">
    <div v-if="store.draftCount > 0 && !hidden" class="dock">
      <button class="dock-close" title="Ocultar" @click="hidden = true">×</button>

      <div class="dock-info" @click="goToBuilder" @mouseenter="clearTimeout(temporizador)">
        <span class="dock-icon">📦</span>
        <div>
          <div class="dock-name">{{ store.draft.name }}</div>
          <div class="dock-count">
            {{ store.draftCount }} cópias · {{ store.draftUnique }} únicas
          </div>
        </div>
      </div>

      <button class="dock-btn" @click="goToBuilder">Continuar ▸</button>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useCollectionsStore } from '@/stores/collections'

const store  = useCollectionsStore()
const router = useRouter()
const route  = useRoute()
const hidden = ref(false)

function goToBuilder() {
  router.push({ name: 'collection-builder' })
}

// Some na própria tela de montagem e reaparece ao adicionar carta em outra tela
watch(() => route.name, (name) => { hidden.value = name === 'collection-builder' }, { immediate: true })
let temporizador = null

function agendarOcultacao() {
  clearTimeout(temporizador)
  // Some sozinho: é um aviso de progresso, não um painel permanente
  temporizador = setTimeout(() => { hidden.value = true }, 6000)
}

watch(() => store.draftCount, (value, previous) => {
  if (value > previous && route.name !== 'collection-builder') {
    hidden.value = false
    agendarOcultacao()
  }
})

onMounted(() => { if (store.draftCount > 0) agendarOcultacao() })
onBeforeUnmount(() => clearTimeout(temporizador))
</script>

<style scoped>
.dock {
  position: fixed; bottom: 1.6rem; left: 1.6rem; z-index: 998;
  display: flex; align-items: center; gap: 14px;
  background: linear-gradient(150deg, #1c1409 0%, #0d0906 100%);
  border: 1px solid var(--gold); border-radius: 4px;
  padding: 11px 14px;
  box-shadow: 0 14px 34px rgba(0,0,0,0.65), 0 0 24px rgba(184,134,11,0.16);
  max-width: calc(100vw - 3.2rem);
}
.dock-close {
  position: absolute; top: -9px; right: -9px;
  width: 20px; height: 20px; line-height: 17px;
  background: var(--obsidian-lt); border: 1px solid rgba(184,134,11,0.5);
  color: var(--parchment-dk); border-radius: 50%; cursor: pointer;
  font-size: 0.85rem; padding: 0;
}
.dock-close:hover { color: var(--gold-shine); border-color: var(--gold); }

.dock-info { display: flex; align-items: center; gap: 10px; cursor: pointer; min-width: 0; }
.dock-icon { font-size: 1.2rem; }
.dock-name {
  font-family: 'Cinzel', serif; font-size: 0.78rem; color: var(--aged-white);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 190px;
}
.dock-count { font-size: 0.66rem; color: var(--parchment-xdk); margin-top: 2px; }

.dock-btn {
  background: rgba(184,134,11,0.18); border: 1px solid var(--gold);
  color: var(--gold-shine); border-radius: 2px; padding: 7px 12px;
  font-family: 'Cinzel', serif; font-size: 0.64rem; letter-spacing: 2px;
  cursor: pointer; transition: all 0.2s; white-space: nowrap;
}
.dock-btn:hover { background: var(--gold); color: var(--obsidian); }

.dock-enter-active, .dock-leave-active { transition: all 0.3s cubic-bezier(.23,1,.32,1); }
.dock-enter-from, .dock-leave-to { opacity: 0; transform: translateY(16px); }

@media (max-width: 768px) {
  .dock { left: 1rem; right: 1rem; bottom: 1rem; }
  .dock-name { max-width: 120px; }
}
</style>
