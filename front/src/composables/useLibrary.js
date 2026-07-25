/**
 * useLibrary.js
 * Gerencia decks e coleções sincronizando com o backend quando logado,
 * ou usando localStorage quando não logado.
 */
import { ref, computed } from 'vue'
import api from '@/composables/api'
import { useAuthStore } from '@/stores/auth'

// Singleton state
const decks      = ref([])
const collection = ref(JSON.parse(localStorage.getItem('mtg_collection') ||
  '{"cards":[],"bySet":[],"byRarity":{},"byCategory":{},"stats":null,"name":"Minha Coleção"}'))
const activeImgs = ref(JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}'))
const loading    = ref(false)

export function useLibrary() {
  const auth = useAuthStore()

  // ── DECKS ───────────────────────────────────────────────────────────────

  async function loadDecks() {
    if (auth.isLoggedIn) {
      try {
        const { data } = await api.get('/auth/decks/')
        decks.value = data
      } catch { decks.value = [] }
    } else {
      decks.value = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
    }
  }

  async function getDeck(id) {
    if (auth.isLoggedIn) {
      const { data } = await api.get(`/auth/decks/${id}/`)
      return data
    } else {
      const all = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
      return all.find(d => d.id === id) || null
    }
  }

  async function saveDeck(deck) {
    if (auth.isLoggedIn) {
      const { data } = await api.post('/auth/decks/save/', {
        id:           deck.id || undefined,
        name:         deck.name,
        raw_text:     deck.raw_text,
        cards:        deck.cards,
        categorized:  deck.categorized,
        commander:    deck.commander,
        legendaries:  deck.legendaries,
        colors:       deck.colors,
        total_cards:  deck.total_cards,
        avg_cmc:      deck.avg_cmc,
        not_found:    deck.not_found,
        active_imgs:  activeImgs.value,
      })
      // Reload list
      await loadDecks()
      return data.id
    } else {
      const all = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
      if (deck.id) {
        const idx = all.findIndex(d => d.id === deck.id)
        if (idx >= 0) all[idx] = deck
      } else {
        deck.id = Date.now().toString()
        all.push(deck)
      }
      localStorage.setItem('mtg_decks', JSON.stringify(all))
      decks.value = all
      return deck.id
    }
  }

  async function deleteDeck(id) {
    if (auth.isLoggedIn) {
      await api.delete(`/auth/decks/${id}/delete/`)
    } else {
      const all = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
      localStorage.setItem('mtg_decks', JSON.stringify(all.filter(d => d.id !== String(id))))
    }
    await loadDecks()
  }

  // ── COLLECTION ──────────────────────────────────────────────────────────

  async function loadCollection() {
    if (auth.isLoggedIn) {
      try {
        const { data } = await api.get('/auth/collection/')
        if (data.exists) {
          collection.value = data
          activeImgs.value = data.active_imgs || {}
        }
      } catch {}
    } else {
      collection.value = JSON.parse(localStorage.getItem('mtg_collection') ||
        '{"cards":[],"bySet":[],"byRarity":{},"byCategory":{},"stats":null,"name":"Minha Coleção"}')
      activeImgs.value = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}')
    }
  }

  async function saveCollection(colData) {
    collection.value = colData
    if (auth.isLoggedIn) {
      await api.post('/auth/collection/save/', {
        name:        colData.name,
        cards:       colData.cards,
        by_set:      colData.bySet || colData.by_set,
        by_rarity:   colData.byRarity || colData.by_rarity,
        by_category: colData.byCategory || colData.by_category,
        stats:       colData.stats,
        active_imgs: activeImgs.value,
      })
    } else {
      localStorage.setItem('mtg_collection', JSON.stringify(colData))
    }
  }

  // ── ACTIVE IMAGES ───────────────────────────────────────────────────────

  async function changeImg(name, url, deckId = null) {
    activeImgs.value = { ...activeImgs.value, [name]: url }

    if (auth.isLoggedIn) {
      if (deckId) {
        await api.patch(`/auth/decks/${deckId}/imgs/`, { active_imgs: { [name]: url } })
      } else {
        await api.patch('/auth/collection/imgs/', { active_imgs: { [name]: url } })
      }
    } else {
      const saved = JSON.parse(localStorage.getItem('mtg_active_imgs') || '{}')
      saved[name] = url
      localStorage.setItem('mtg_active_imgs', JSON.stringify(saved))
    }
  }

  // ── MIGRATION: localStorage → backend ao fazer login ───────────────────

  async function migrateLocalToBackend() {
    if (!auth.isLoggedIn) return

    // Migrate decks
    const localDecks = JSON.parse(localStorage.getItem('mtg_decks') || '[]')
    for (const deck of localDecks) {
      await saveDeck({ ...deck, id: undefined }) // save sem id para criar novo
    }

    // Migrate collection
    const localCol = JSON.parse(localStorage.getItem('mtg_collection') ||
      '{"cards":[],"stats":null}')
    if (localCol.cards?.length) {
      await saveCollection(localCol)
    }

    // Clear localStorage after migration
    localStorage.removeItem('mtg_decks')
    localStorage.removeItem('mtg_collection')
    localStorage.removeItem('mtg_active_imgs')
  }

  return {
    decks, collection, activeImgs, loading,
    loadDecks, getDeck, saveDeck, deleteDeck,
    loadCollection, saveCollection,
    changeImg, migrateLocalToBackend,
  }
}
