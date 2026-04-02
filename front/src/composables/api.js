import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  timeout: 15000,
  headers: { 'Content-Type': 'application/json' },
})

export default api

export const getCards       = (params = {}) => api.get('/cards/',           { params })
export const getCardImages  = (name)        => api.get('/cards/images/',     { params: { name } })
export const getCollections = ()            => api.get('/collections/')
export const getRules       = (params = {}) => api.get('/rules/',            { params })
export const getManaSymbols = ()            => api.get('/symbols/')
export const getSets        = ()            => api.get('/sets/')

export const getCardTypes = () => api.get('/types/')

export const getCardPrices = (name) => api.get('/cards/prices/', { params: { name } })
