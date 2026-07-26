<template>
  <Transition name="modal-fade">
    <div v-if="store.pendingCard" class="modal-backdrop" @click.self="close">
      <div class="modal-box">
        <button class="modal-close" @click="close">×</button>

        <div class="modal-head">
          <span class="modal-eyebrow">Adicionar à coleção</span>
          <h3 class="modal-card-name">{{ store.pendingCard.name }}</h3>
        </div>

        <div v-if="erro" class="modal-msg err">{{ erro }}</div>

        <!-- Coleções existentes -->
        <div v-if="store.list.length" class="modal-section">
          <span class="section-label">Suas coleções</span>
          <button
            v-for="col in store.list"
            :key="col.id"
            class="col-option"
            :disabled="salvando"
            @click="adicionarEm(col)"
          >
            <span class="col-icon">📦</span>
            <span class="col-info">
              <span class="col-name">{{ col.name }}</span>
              <span class="col-meta">{{ col.total_copies }} cópias · {{ col.total_unique }} únicas</span>
            </span>
            <span class="col-plus">+</span>
          </button>
        </div>

        <div v-else-if="!store.loading" class="modal-empty">
          Você ainda não tem coleções. Crie a primeira abaixo.
        </div>

        <!-- Nova coleção -->
        <div class="modal-section">
          <span class="section-label">Nova coleção</span>
          <div class="nova-linha">
            <input
              v-model="novoNome"
              class="medieval-input"
              placeholder="Nome da coleção..."
              :disabled="salvando"
              @keyup.enter="criarNova"
            />
            <button class="btn-primary" :disabled="salvando || !novoNome.trim()" @click="criarNova">
              {{ salvando ? '⏳' : '✦ Criar' }}
            </button>
          </div>
        </div>

        <p v-if="!auth.isLoggedIn" class="modal-hint">
          Você não está logado — as coleções ficam salvas apenas neste navegador.
        </p>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useCollectionsStore } from '@/stores/collections'
import { useAuthStore } from '@/stores/auth'

const store = useCollectionsStore()
const auth  = useAuthStore()

const novoNome = ref('')
const salvando = ref(false)
const erro     = ref('')

// Ao abrir, atualiza a lista e sugere um nome
watch(() => store.pendingCard, (card) => {
  if (!card) return
  erro.value = ''
  novoNome.value = ''
  store.loadList()
})

function close() {
  store.pendingCard = null
}

async function adicionarEm(col) {
  salvando.value = true
  erro.value = ''
  const resultado = await store.addCardToCollection(col.id, store.pendingCard)
  salvando.value = false
  if (resultado.error) erro.value = resultado.error
  else close()
}

async function criarNova() {
  const nome = novoNome.value.trim()
  if (!nome) return
  salvando.value = true
  erro.value = ''
  const resultado = await store.createCollectionWithCard(nome, store.pendingCard)
  salvando.value = false
  if (resultado.error) erro.value = resultado.error
  else close()
}
</script>

<style scoped>
.modal-backdrop {
  position: fixed; inset: 0; z-index: 1000;
  background: rgba(0, 0, 0, 0.72);
  display: flex; align-items: center; justify-content: center;
  padding: 1.5rem;
}

.modal-box {
  position: relative; width: 100%; max-width: 420px;
  max-height: 85vh; overflow-y: auto;
  background: linear-gradient(155deg, #1c1409 0%, #0d0906 100%);
  border: 1px solid var(--gold); border-radius: 4px;
  padding: 22px 20px;
  box-shadow: 0 22px 60px rgba(0,0,0,0.7), 0 0 30px rgba(184,134,11,0.12);
}

.modal-close {
  position: absolute; top: 10px; right: 12px;
  background: none; border: none; color: var(--parchment-xdk);
  font-size: 1.3rem; cursor: pointer; line-height: 1;
}
.modal-close:hover { color: var(--gold-shine); }

.modal-head { margin-bottom: 1.2rem; padding-right: 20px; }
.modal-eyebrow {
  font-family: 'Cinzel', serif; font-size: 0.58rem; letter-spacing: 2px;
  color: var(--parchment-xdk); text-transform: uppercase;
}
.modal-card-name {
  font-family: 'Cinzel', serif; font-size: 1.02rem;
  color: var(--gold-shine); margin-top: 4px; line-height: 1.3;
}

.modal-msg.err {
  background: rgba(120,40,40,0.16); border: 1px solid rgba(200,90,90,0.35);
  color: #e8b0b0; padding: 8px 11px; border-radius: 3px;
  font-size: 0.75rem; margin-bottom: 1rem;
}

.modal-section { margin-bottom: 1.3rem; }
.section-label {
  display: block; margin-bottom: 8px;
  font-family: 'Cinzel', serif; font-size: 0.58rem; letter-spacing: 2px;
  color: var(--gold); text-transform: uppercase;
}

.col-option {
  display: flex; align-items: center; gap: 10px; width: 100%;
  background: rgba(0,0,0,0.28); border: 1px solid rgba(184,134,11,0.2);
  border-radius: 3px; padding: 10px 12px; margin-bottom: 6px;
  cursor: pointer; text-align: left; transition: all 0.18s;
}
.col-option:hover:not(:disabled) {
  border-color: var(--gold); background: rgba(184,134,11,0.12);
}
.col-option:disabled { opacity: 0.5; cursor: wait; }

.col-icon { font-size: 1rem; }
.col-info { flex: 1; min-width: 0; }
.col-name {
  display: block; font-family: 'Cinzel', serif; font-size: 0.8rem;
  color: var(--aged-white); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.col-meta { display: block; font-size: 0.64rem; color: var(--parchment-xdk); margin-top: 2px; }
.col-plus { color: var(--gold); font-size: 1.1rem; }

.modal-empty {
  font-size: 0.76rem; color: var(--parchment-xdk); font-style: italic;
  padding: 0.4rem 0 1rem;
}

.nova-linha { display: flex; gap: 8px; }
.nova-linha .medieval-input { flex: 1; min-width: 0; }

.modal-hint {
  font-size: 0.68rem; color: var(--parchment-xdk); font-style: italic;
  border-top: 1px solid rgba(184,134,11,0.15); padding-top: 10px;
}

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.2s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }
</style>
