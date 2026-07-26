import axios from 'axios'

/**
 * Cliente HTTP único da aplicação.
 *
 * Antes existiam dois caminhos: esta instância (sem token) e o axios global
 * configurado no store de auth. Como axios.create() copia os defaults no
 * momento da criação, o header Authorization definido depois nunca chegava
 * aqui — as chamadas autenticadas iam sem token. Agora um interceptor lê o
 * token a cada request.
 */
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('mtg_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Token expirado/inválido: limpa a sessão para a UI refletir o estado real
    if (error.response?.status === 401 && localStorage.getItem('mtg_token')) {
      localStorage.removeItem('mtg_token')
      localStorage.removeItem('mtg_username')
      localStorage.removeItem('mtg_uid')
      window.dispatchEvent(new CustomEvent('mtg:unauthorized'))
    }
    return Promise.reject(error)
  },
)

export default api

// ── Grimório ────────────────────────────────────────────────────────────────
export const getCards       = (params = {}) => api.get('/cards/', { params })
export const getCardImages  = (name)        => api.get('/cards/images/', { params: { name } })
export const getCardPrices  = (name, id)    => api.get('/cards/prices/', { params: { name, id } })
export const getRules       = (params = {}) => api.get('/rules/', { params })
export const getManaSymbols = ()            => api.get('/symbols/')
export const getSets        = ()            => api.get('/sets/')
export const getCardTypes   = ()            => api.get('/types/')

// ── Coleções (sets do jogo) ─────────────────────────────────────────────────
export const getCollections = (params = {}) => api.get('/collections/', { params })
export const getSetDetail   = (code)        => api.get(`/collections/${code}/`)

// ── Import/export de listas ─────────────────────────────────────────────────
export const importDeck        = (text) => api.post('/deck/import/', { text })
export const exportDeck        = (body) => api.post('/deck/export/', body)
export const importCollection  = (text) => api.post('/collection/import/', { text })
export const exportCollection  = (body) => api.post('/collection/export/', body)

// ── Biblioteca do usuário ───────────────────────────────────────────────────
export const apiListDecks       = ()        => api.get('/auth/decks/')
export const apiGetDeck         = (id)      => api.get(`/auth/decks/${id}/`)
export const apiSaveDeck        = (body)    => api.post('/auth/decks/save/', body)
export const apiDeleteDeck      = (id)      => api.delete(`/auth/decks/${id}/delete/`)
export const apiListCollections = ()        => api.get('/auth/collections/')
export const apiGetCollection   = (id)      => api.get(`/auth/collections/${id}/`)
export const apiSaveCollection  = (body)    => api.post('/auth/collections/save/', body)
export const apiDeleteCollection = (id)     => api.delete(`/auth/collections/${id}/delete/`)
export const apiRenameCollection = (id, name) => api.patch(`/auth/collections/${id}/rename/`, { name })
