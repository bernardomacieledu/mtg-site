import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/composables/api'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(localStorage.getItem('mtg_token') || '')
  const username = ref(localStorage.getItem('mtg_username') || '')
  const uid      = ref(localStorage.getItem('mtg_uid') || '')
  const isAdmin  = ref(localStorage.getItem('mtg_is_admin') === '1')

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(data) {
    token.value    = data.token
    username.value = data.username
    uid.value      = String(data.uid)
    localStorage.setItem('mtg_token',    data.token)
    localStorage.setItem('mtg_username', data.username)
    localStorage.setItem('mtg_uid',      String(data.uid))
    isAdmin.value = !!data.is_admin
    localStorage.setItem('mtg_is_admin', data.is_admin ? '1' : '0')
  }

  function clearAuth() {
    token.value    = ''
    username.value = ''
    uid.value      = ''
    localStorage.removeItem('mtg_token')
    localStorage.removeItem('mtg_username')
    localStorage.removeItem('mtg_uid')
    isAdmin.value = false
    localStorage.removeItem('mtg_is_admin')
  }

  // O token é injetado pelo interceptor de @/composables/api a cada request,
  // então aqui basta sincronizar o estado com o localStorage.
  function initAuth() {
    token.value    = localStorage.getItem('mtg_token') || ''
    username.value = localStorage.getItem('mtg_username') || ''
    uid.value      = localStorage.getItem('mtg_uid') || ''
    isAdmin.value  = localStorage.getItem('mtg_is_admin') === '1'
    window.addEventListener('mtg:unauthorized', clearAuth)
  }

  async function register(usernameVal, email, password) {
    const { data } = await api.post('/auth/register/', {
      username: usernameVal, email, password,
    })
    setAuth(data)
    return data
  }

  async function login(usernameVal, password) {
    const { data } = await api.post('/auth/login/', {
      username: usernameVal, password,
    })
    setAuth(data)
    return data
  }

  function logout() {
    clearAuth()
  }

  return { token, username, uid, isAdmin, isLoggedIn, setAuth, clearAuth, initAuth, register, login, logout }
})
