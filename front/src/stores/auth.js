import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(localStorage.getItem('mtg_token') || '')
  const username = ref(localStorage.getItem('mtg_username') || '')
  const uid      = ref(localStorage.getItem('mtg_uid') || '')

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(data) {
    token.value    = data.token
    username.value = data.username
    uid.value      = String(data.uid)
    localStorage.setItem('mtg_token',    data.token)
    localStorage.setItem('mtg_username', data.username)
    localStorage.setItem('mtg_uid',      String(data.uid))
    axios.defaults.headers.common['Authorization'] = `Bearer ${data.token}`
  }

  function clearAuth() {
    token.value    = ''
    username.value = ''
    uid.value      = ''
    localStorage.removeItem('mtg_token')
    localStorage.removeItem('mtg_username')
    localStorage.removeItem('mtg_uid')
    delete axios.defaults.headers.common['Authorization']
  }

  function initAuth() {
    if (token.value) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token.value}`
    }
  }

  async function register(usernameVal, email, password) {
    const { data } = await axios.post('/api/auth/register/', {
      username: usernameVal, email, password
    })
    setAuth(data)
    return data
  }

  async function login(usernameVal, password) {
    const { data } = await axios.post('/api/auth/login/', {
      username: usernameVal, password
    })
    setAuth(data)
    return data
  }

  function logout() {
    clearAuth()
  }

  return { token, username, uid, isLoggedIn, setAuth, clearAuth, initAuth, register, login, logout }
})
