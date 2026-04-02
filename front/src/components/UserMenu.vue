<template>
  <div class="user-menu" v-if="auth.isLoggedIn" ref="menuRef">
    <button class="user-btn" @click="open = !open">
      <span class="user-avatar">{{ auth.username[0].toUpperCase() }}</span>
      <span class="user-name">{{ auth.username }}</span>
      <span class="user-chevron">{{ open ? '▲' : '▼' }}</span>
    </button>
    <Transition name="dropdown">
      <div v-if="open" class="user-dropdown">
        <div class="dropdown-header">
          <span class="dropdown-username">{{ auth.username }}</span>
          <span class="dropdown-sub">Conta local</span>
        </div>
        <div class="dropdown-divider" />
        <button class="dropdown-item" @click="goLibrary">📚 Biblioteca</button>
        <div class="dropdown-divider" />
        <button class="dropdown-item danger" @click="logout">🚪 Sair</button>
      </div>
    </Transition>
  </div>

  <router-link v-else to="/login" class="login-btn">
    ⚔ Entrar
  </router-link>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth    = useAuthStore()
const router  = useRouter()
const open    = ref(false)
const menuRef = ref(null)

function goLibrary() {
  open.value = false
  router.push({ name: 'library' })
}

function logout() {
  auth.logout()
  open.value = false
  router.push({ name: 'cards' })
}

function onClickOutside(e) {
  if (menuRef.value && !menuRef.value.contains(e.target)) {
    open.value = false
  }
}

onMounted(() => document.addEventListener('click', onClickOutside))
onUnmounted(() => document.removeEventListener('click', onClickOutside))
</script>

<style scoped>
.user-menu { position:relative; }
.user-btn {
  display:flex; align-items:center; gap:8px;
  background:rgba(184,134,11,0.08); border:1px solid rgba(184,134,11,0.25);
  border-radius:3px; padding:6px 12px; cursor:pointer; transition:all 0.2s; height:40px;
}
.user-btn:hover { border-color:var(--gold); background:rgba(184,134,11,0.14); }
.user-avatar {
  width:26px; height:26px; border-radius:50%;
  background:var(--gold); color:var(--obsidian);
  font-family:'Cinzel',serif; font-size:0.72rem; font-weight:700;
  display:flex; align-items:center; justify-content:center; flex-shrink:0;
}
.user-name   { font-family:'Cinzel',serif; font-size:0.68rem; letter-spacing:1px; color:var(--parchment-dk); }
.user-chevron { font-size:0.5rem; color:var(--gold); }

.user-dropdown {
  position:absolute; top:calc(100% + 8px); right:0;
  background:linear-gradient(135deg,#1a130a,#0d0a06);
  border:1px solid rgba(184,134,11,0.35); border-radius:3px;
  min-width:190px; z-index:1000;
  box-shadow:0 8px 24px rgba(0,0,0,0.6);
}
.dropdown-header { padding:12px 16px; }
.dropdown-username { display:block; font-family:'Cinzel',serif; font-size:0.82rem; color:var(--aged-white); }
.dropdown-sub      { display:block; font-size:0.62rem; color:var(--parchment-xdk); font-style:italic; margin-top:2px; }
.dropdown-divider  { height:1px; background:rgba(184,134,11,0.15); }
.dropdown-item {
  display:block; width:100%; padding:11px 16px;
  font-family:'Cinzel',serif; font-size:0.7rem; letter-spacing:1px;
  color:var(--parchment-dk); background:transparent; border:none;
  cursor:pointer; text-align:left; transition:all 0.15s;
}
.dropdown-item:hover { background:rgba(184,134,11,0.08); color:var(--gold); }
.dropdown-item.danger:hover { background:rgba(139,26,26,0.15); color:var(--crimson-lt); }

.login-btn {
  font-family:'Cinzel',serif; font-size:0.72rem; letter-spacing:2px;
  padding:6px 16px; border:1px solid rgba(184,134,11,0.35); border-radius:3px;
  color:var(--parchment-dk); text-decoration:none; transition:all 0.2s;
  height:40px; display:flex; align-items:center;
}
.login-btn:hover { border-color:var(--gold); color:var(--gold-shine); background:rgba(184,134,11,0.08); }

.dropdown-enter-active,.dropdown-leave-active { transition:all 0.2s ease; }
.dropdown-enter-from,.dropdown-leave-to { opacity:0; transform:translateY(-6px); }
</style>
