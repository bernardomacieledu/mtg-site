import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  apiListCollections, apiGetCollection, apiSaveCollection,
  apiDeleteCollection, apiRenameCollection,
} from '@/composables/api'
import { useAuthStore } from '@/stores/auth'

const DRAFT_KEY = 'mtg_collection_draft'

// Coleções são sempre gravadas no banco, vinculadas ao usuário. O rascunho em
// andamento segue no localStorage por conveniência (é um buffer de trabalho),
// mas salvar exige conta.
const ERRO_LOGIN = 'Entre na sua conta para salvar coleções.'

const CATEGORY_OF = [
  ['Creature', 'creature'], ['Planeswalker', 'planeswalker'], ['Land', 'land'],
  ['Artifact', 'artifact'], ['Enchantment', 'enchantment'],
  ['Instant', 'instant'], ['Sorcery', 'sorcery'],
]

function classify(typeLine = '') {
  for (const [needle, category] of CATEGORY_OF) {
    if (typeLine.includes(needle)) return category
  }
  return 'other'
}

function readLocal(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback }
  catch { return fallback }
}

/**
 * Monta os agrupamentos e estatísticas no mesmo formato que o backend devolve
 * em /api/collection/import/, para que as telas de detalhe funcionem igual
 * vindo de um import de lista ou da montagem carta a carta.
 */
export function buildCollectionPayload(name, cards) {
  const bySetMap = {}
  const byRarity = {}
  const byCategory = {}
  const rarityCounts = {}

  for (const card of cards) {
    const setCode = card.set || ''
    if (!bySetMap[setCode]) {
      bySetMap[setCode] = { set_code: setCode, set_name: card.set_name || setCode, cards: [] }
    }
    bySetMap[setCode].cards.push(card)

    const rarity = card.rarity || 'common'
    ;(byRarity[rarity] ||= []).push(card)
    rarityCounts[rarity] = (rarityCounts[rarity] || 0) + card.qty

    const category = card.category || classify(card.type_line)
    ;(byCategory[category] ||= []).push(card)
  }

  const totalCopies = cards.reduce((sum, c) => sum + c.qty, 0)
  const nonLand = cards.filter(c => (c.category || classify(c.type_line)) !== 'land')
  const nonLandCopies = nonLand.reduce((sum, c) => sum + c.qty, 0)
  const avgCmc = nonLandCopies
    ? Number((nonLand.reduce((sum, c) => sum + (c.cmc || 0) * c.qty, 0) / nonLandCopies).toFixed(2))
    : 0

  return {
    name,
    cards,
    bySet: Object.values(bySetMap),
    byRarity,
    byCategory,
    stats: {
      total_copies: totalCopies,
      total_cards: totalCopies,
      total_unique: cards.length,
      unique_cards: cards.length,
      total_sets: Object.keys(bySetMap).length,
      avg_cmc: avgCmc,
      rarity_counts: rarityCounts,
      by_category: Object.fromEntries(
        Object.entries(byCategory).map(([k, v]) => [k, v.reduce((s, c) => s + c.qty, 0)]),
      ),
      estimated_value: 0,
      estimated_value_foil: 0,
    },
  }
}

export const useCollectionsStore = defineStore('collections', () => {
  const auth = useAuthStore()

  const list    = ref([])
  const pendingCard = ref(null)          // carta aguardando escolha de coleção                                   // resumos das coleções salvas
  const draft   = ref(readLocal(DRAFT_KEY, { name: 'Nova Coleção', cards: [] }))
  const loading = ref(false)
  const saving  = ref(false)

  const draftCount  = computed(() => draft.value.cards.reduce((sum, c) => sum + c.qty, 0))
  const draftUnique = computed(() => draft.value.cards.length)
  const isEmpty     = computed(() => draft.value.cards.length === 0)

  function persistDraft() {
    localStorage.setItem(DRAFT_KEY, JSON.stringify(draft.value))
  }

  function qtyOf(name) {
    return draft.value.cards.find(c => c.name === name)?.qty || 0
  }

  /** Adiciona (ou incrementa) uma carta na coleção em montagem. */
  function addCard(card, qty = 1) {
    const existing = draft.value.cards.find(c => c.name === card.name)
    if (existing) {
      existing.qty += qty
    } else {
      const firstSet = card.sets?.[0]
      draft.value.cards.push({
        name:        card.name,
        qty,
        mana_cost:   card.mana_cost || '',
        cmc:         card.cmc ?? 0,
        type_line:   card.type_line || '',
        oracle_text: card.oracle_text || '',
        rarity:      card.rarity || 'common',
        colors:      card.colors || [],
        set:         card.set || firstSet?.code || '',
        set_name:    card.set_name || firstSet?.name || '',
        image_url:   card.image_url || card.image_url_normal || '',
        category:    card.category || classify(card.type_line || ''),
        prints:      card.prints || [],
      })
    }
    persistDraft()
  }

  function removeCard(name, qty = 1) {
    const index = draft.value.cards.findIndex(c => c.name === name)
    if (index === -1) return
    draft.value.cards[index].qty -= qty
    if (draft.value.cards[index].qty <= 0) draft.value.cards.splice(index, 1)
    persistDraft()
  }

  function setQty(name, qty) {
    const card = draft.value.cards.find(c => c.name === name)
    if (!card) return
    if (qty <= 0) removeCard(name, card.qty)
    else { card.qty = qty; persistDraft() }
  }

  function clearDraft() {
    draft.value = { name: 'Nova Coleção', cards: [] }
    persistDraft()
  }

  function renameDraft(name) {
    draft.value.name = name
    persistDraft()
  }

  /** Carrega uma coleção salva de volta para edição. */
  async function editCollection(id) {
    const data = await getCollection(id)
    if (!data) return false
    draft.value = { id, name: data.name, cards: data.cards || [] }
    persistDraft()
    return true
  }

  // ── Persistência ──────────────────────────────────────────────────────────

  async function loadList() {
    if (!auth.isLoggedIn) { list.value = []; return }
    loading.value = true
    try {
      const { data } = await apiListCollections()
      list.value = data
    } catch {
      list.value = []
    } finally {
      loading.value = false
    }
  }

  async function getCollection(id) {
    if (!auth.isLoggedIn) return null
    try {
      const { data } = await apiGetCollection(id)
      return data
    } catch { return null }
  }

  /** Salva o rascunho atual como coleção (nova ou atualizando a existente). */
  async function saveDraft() {
    if (!auth.isLoggedIn) return { error: ERRO_LOGIN, requiresAuth: true }
    if (isEmpty.value) return { error: 'A coleção está vazia.' }
    saving.value = true
    try {
      const payload = buildCollectionPayload(draft.value.name || 'Nova Coleção', draft.value.cards)
      const { data } = await apiSaveCollection({
        id: draft.value.id, name: payload.name, cards: payload.cards,
        by_set: payload.bySet, by_rarity: payload.byRarity,
        by_category: payload.byCategory, stats: payload.stats,
      })
      draft.value.id = data.id
      persistDraft()
      await loadList()
      return { id: draft.value.id }
    } catch (error) {
      return { error: error.response?.data?.error || 'Não foi possível salvar a coleção.' }
    } finally {
      saving.value = false
    }
  }

  async function removeCollection(id) {
    if (!auth.isLoggedIn) return { error: ERRO_LOGIN, requiresAuth: true }
    await apiDeleteCollection(id)
    if (String(draft.value.id) === String(id)) delete draft.value.id
    await loadList()
    return { ok: true }
  }

  async function rename(id, name) {
    if (!auth.isLoggedIn) return { error: ERRO_LOGIN, requiresAuth: true }
    await apiRenameCollection(id, name)
    await loadList()
    return { ok: true }
  }

  /** Abre o modal de escolha de coleção para esta carta. */
  function requestAdd(card) {
    pendingCard.value = card
  }

  function _normaliza(card, firstSet) {
    return {
      name: card.name, qty: 1,
      mana_cost: card.mana_cost || '', cmc: card.cmc ?? 0,
      type_line: card.type_line || '', oracle_text: card.oracle_text || '',
      rarity: card.rarity || 'common', colors: card.colors || [],
      set: card.set || firstSet?.code || '',
      set_name: card.set_name || firstSet?.name || '',
      image_url: card.image_url || card.image_url_normal || '',
      category: card.category || classify(card.type_line || ''),
      prints: card.prints || [],
    }
  }

  /** Adiciona a carta a uma coleção existente e grava no banco. */
  async function addCardToCollection(id, card) {
    if (!auth.isLoggedIn) return { error: ERRO_LOGIN, requiresAuth: true }
    try {
      const dados = await getCollection(id)
      if (!dados) return { error: 'Coleção não encontrada.' }

      const cartas = [...(dados.cards || [])]
      const existente = cartas.find(c => c.name === card.name)
      if (existente) existente.qty += 1
      else cartas.push(_normaliza(card, card.sets?.[0]))

      const payload = buildCollectionPayload(dados.name, cartas)
      await apiSaveCollection({
        id, name: payload.name, cards: payload.cards, by_set: payload.bySet,
        by_rarity: payload.byRarity, by_category: payload.byCategory, stats: payload.stats,
      })
      await loadList()
      return { id }
    } catch (error) {
      return { error: error.response?.data?.error || 'Não foi possível salvar.' }
    }
  }

  /** Cria uma coleção nova já com a carta dentro. */
  async function createCollectionWithCard(nome, card) {
    if (!auth.isLoggedIn) return { error: ERRO_LOGIN, requiresAuth: true }
    const payload = buildCollectionPayload(nome, [_normaliza(card, card.sets?.[0])])
    try {
      await apiSaveCollection({
        name: payload.name, cards: payload.cards, by_set: payload.bySet,
        by_rarity: payload.byRarity, by_category: payload.byCategory, stats: payload.stats,
      })
      await loadList()
      return { ok: true }
    } catch (error) {
      return { error: error.response?.data?.error || 'Não foi possível criar a coleção.' }
    }
  }

  return {
    list, draft, loading, saving, pendingCard,
    requestAdd, addCardToCollection, createCollectionWithCard,
    draftCount, draftUnique, isEmpty,
    qtyOf, addCard, removeCard, setQty, clearDraft, renameDraft,
    loadList, getCollection, editCollection, saveDraft, removeCollection, rename,
  }
})
