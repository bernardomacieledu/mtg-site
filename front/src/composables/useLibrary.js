/**
 * useLibrary.js
 *
 * Decks e coleções exigem conta: tudo é gravado no banco, vinculado ao usuário.
 * As funções devolvem { error, requiresAuth } quando não há sessão, para a tela
 * poder oferecer o login em vez de falhar em silêncio.
 *
 * `migrateLocalToBackend` existe para quem já tinha dados salvos apenas no
 * navegador antes desta mudança: ao entrar na conta, sobe o que havia e limpa.
 */
import { ref } from 'vue'
import api from '@/composables/api'
import { useAuthStore } from '@/stores/auth'

const ERRO_LOGIN = 'Entre na sua conta para salvar decks e coleções.'
const SEM_SESSAO = { error: ERRO_LOGIN, requiresAuth: true }

const COLECAO_VAZIA = {
  cards: [], bySet: [], byRarity: {}, byCategory: {},
  stats: null, name: 'Minha Coleção',
}

// Estado compartilhado entre as telas
const decks      = ref([])
const collection = ref({ ...COLECAO_VAZIA })
const activeImgs = ref({})
const loading    = ref(false)

export function useLibrary() {
  const auth = useAuthStore()

  // ── Decks ───────────────────────────────────────────────────────────────

  async function loadDecks() {
    if (!auth.isLoggedIn) { decks.value = []; return SEM_SESSAO }
    loading.value = true
    try {
      const { data } = await api.get('/auth/decks/')
      decks.value = data
    } catch {
      decks.value = []
    } finally {
      loading.value = false
    }
  }

  async function getDeck(id) {
    if (!auth.isLoggedIn) return null
    try {
      const { data } = await api.get(`/auth/decks/${id}/`)
      return data
    } catch {
      return null
    }
  }

  async function saveDeck(deck) {
    if (!auth.isLoggedIn) return SEM_SESSAO
    const { data } = await api.post('/auth/decks/save/', {
      id:          deck.id || undefined,
      name:        deck.name,
      raw_text:    deck.raw_text,
      cards:       deck.cards,
      categorized: deck.categorized,
      commander:   deck.commander,
      legendaries: deck.legendaries,
      colors:      deck.colors,
      total_cards: deck.total_cards,
      avg_cmc:     deck.avg_cmc,
      not_found:   deck.not_found,
      active_imgs: activeImgs.value,
    })
    await loadDecks()
    return data.id
  }

  async function deleteDeck(id) {
    if (!auth.isLoggedIn) return SEM_SESSAO
    await api.delete(`/auth/decks/${id}/delete/`)
    await loadDecks()
  }

  // ── Coleção (endpoint de compatibilidade, coleção única) ────────────────

  async function loadCollection() {
    if (!auth.isLoggedIn) { collection.value = { ...COLECAO_VAZIA }; return SEM_SESSAO }
    try {
      const { data } = await api.get('/auth/collection/')
      if (data.exists) {
        collection.value = data
        activeImgs.value = data.active_imgs || {}
      }
    } catch { /* mantém o estado atual */ }
  }

  async function saveCollection(colData) {
    if (!auth.isLoggedIn) return SEM_SESSAO
    collection.value = colData
    await api.post('/auth/collection/save/', {
      name:        colData.name,
      cards:       colData.cards,
      by_set:      colData.bySet || colData.by_set,
      by_rarity:   colData.byRarity || colData.by_rarity,
      by_category: colData.byCategory || colData.by_category,
      stats:       colData.stats,
      active_imgs: activeImgs.value,
    })
  }

  // ── Imagem ativa de cada carta ──────────────────────────────────────────

  async function changeImg(name, url, deckId = null) {
    activeImgs.value = { ...activeImgs.value, [name]: url }
    if (!auth.isLoggedIn) return SEM_SESSAO

    if (deckId) {
      await api.patch(`/auth/decks/${deckId}/imgs/`, { active_imgs: { [name]: url } })
    } else {
      await api.patch('/auth/collection/imgs/', { active_imgs: { [name]: url } })
    }
  }

  // ── Migração dos dados que ficaram só no navegador ──────────────────────

  async function migrateLocalToBackend() {
    if (!auth.isLoggedIn) return { migrados: 0 }

    let migrados = 0

    const lerLocal = (chave, padrao) => {
      try { return JSON.parse(localStorage.getItem(chave)) ?? padrao }
      catch { return padrao }
    }

    for (const deck of lerLocal('mtg_decks', [])) {
      try {
        await saveDeck({ ...deck, id: undefined })   // sem id: cria novo
        migrados += 1
      } catch { /* segue com os demais */ }
    }

    // Coleções que ficaram no navegador (formato antigo e o multi-coleção)
    const antiga = lerLocal('mtg_collection', null)
    if (antiga?.cards?.length) {
      try { await saveCollection(antiga); migrados += 1 } catch { /* ignora */ }
    }

    for (const col of lerLocal('mtg_collections', [])) {
      if (!col?.cards?.length) continue
      try {
        await api.post('/auth/collections/save/', {
          name:        col.name || 'Coleção importada',
          cards:       col.cards,
          by_set:      col.bySet || col.by_set,
          by_rarity:   col.byRarity || col.by_rarity,
          by_category: col.byCategory || col.by_category,
          stats:       col.stats,
        })
        migrados += 1
      } catch { /* ignora */ }
    }

    localStorage.removeItem('mtg_decks')
    localStorage.removeItem('mtg_collection')
    localStorage.removeItem('mtg_collections')
    localStorage.removeItem('mtg_active_imgs')

    return { migrados }
  }

  return {
    decks, collection, activeImgs, loading,
    loadDecks, getDeck, saveDeck, deleteDeck,
    loadCollection, saveCollection,
    changeImg, migrateLocalToBackend,
  }
}
