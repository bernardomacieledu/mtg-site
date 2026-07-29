<template>
  <div>
    <nav class="navbar">
      <div class="nav-inner">
        <router-link to="/" class="nav-logo">
          <div class="nav-logo-emblem">
            <svg viewBox="0 0 64 64" class="nav-logo-svg" aria-hidden="true">
              <defs>
                <linearGradient id="nav-gold" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#f0d78c"/>
                  <stop offset="55%" stop-color="#b8860b"/>
                  <stop offset="100%" stop-color="#8a640a"/>
                </linearGradient>
                <linearGradient id="nav-ale" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="#e8a83c"/>
                  <stop offset="100%" stop-color="#b3701f"/>
                </linearGradient>
              </defs>
              <path d="M44 22 h5 a7 7 0 0 1 7 7 v6 a7 7 0 0 1 -7 7 h-5"
                    fill="none" stroke="url(#nav-gold)" stroke-width="4"/>
              <path d="M14 20 h30 v26 a4 4 0 0 1 -4 4 H18 a4 4 0 0 1 -4 -4 Z"
                    fill="#1c1409" stroke="url(#nav-gold)" stroke-width="2.5"/>
              <path d="M17 26 h24 v18 a3 3 0 0 1 -3 3 H20 a3 3 0 0 1 -3 -3 Z" fill="url(#nav-ale)"/>
              <circle cx="24" cy="34" r="1.3" fill="#f7dca0" opacity="0.8"/>
              <circle cx="31" cy="39" r="1" fill="#f7dca0" opacity="0.7"/>
              <circle cx="36" cy="31" r="1.2" fill="#f7dca0" opacity="0.75"/>
              <path d="M15 26 q2 -6 6 -3 q2 -5 6.5 -2 q2.5 -4 6.5 -1 q3 -3.5 6.5 0 q3.5 -2 5.5 3
                       q1.5 3 -1 4.5 H16 q-2.5 -1.2 -1 -4.5 Z" fill="#f4ead0"/>
            </svg>
          </div>
          <div class="nav-title">
            MTG BEERnas
            <span>Grimório das Terras</span>
          </div>
        </router-link>

        <ul class="nav-links">
          <li>
            <router-link to="/" :class="{ active: $route.name === 'cards' }">
              ⚔ Cartas
            </router-link>
          </li>
          <li>
            <router-link to="/colecoes" :class="{ active: $route.name === 'sets' }">
              ❖ Coleções
            </router-link>
          </li>
          <li>
            <router-link to="/regras" :class="{ active: $route.name === 'rules' }">
              🏛 Regras
            </router-link>
          </li>
          <li v-if="auth.isAdmin">
            <router-link to="/administracao" :class="{ active: $route.name === 'admin' }">
              ⚙ Admin
            </router-link>
          </li>
          <li>
            <router-link to="/biblioteca"
              :class="{ active: ['library','deck-detail','collection-detail'].includes($route.name) }">
              📚 Biblioteca
            </router-link>
          </li>
        </ul>

        <div class="nav-right">
          <UserMenu />
        </div>

        <button class="mobile-toggle" @click="mobileOpen = !mobileOpen">
          <span></span><span></span><span></span>
        </button>
      </div>

      <Transition name="drawer">
        <div v-if="mobileOpen" class="mobile-drawer">
          <router-link to="/"           @click="mobileOpen=false">⚔ Cartas</router-link>
          <router-link to="/colecoes"   @click="mobileOpen=false">❖ Coleções</router-link>
          <router-link to="/regras"     @click="mobileOpen=false">🏛 Regras</router-link>
          <router-link v-if="auth.isAdmin" to="/administracao" @click="mobileOpen=false">⚙ Admin</router-link>
          <router-link to="/biblioteca" @click="mobileOpen=false">📚 Biblioteca</router-link>
          <router-link v-if="!auth.isLoggedIn" to="/login" @click="mobileOpen=false">⚔ Entrar</router-link>
          <button v-else class="mobile-logout" @click="auth.logout(); mobileOpen=false">🚪 Sair ({{ auth.username }})</button>
        </div>
      </Transition>
    </nav>

    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>

    <CollectionDock />
    <AddToCollectionModal />

    <Transition name="fade">
      <button v-if="showScrollTop" class="scroll-top-btn" @click="scrollTop" title="Voltar ao topo">▲</button>
    </Transition>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import UserMenu from '@/components/UserMenu.vue'
import CollectionDock from '@/components/CollectionDock.vue'
import AddToCollectionModal from '@/components/AddToCollectionModal.vue'

const auth         = useAuthStore()
const mobileOpen   = ref(false)
const showScrollTop = ref(false)

function scrollTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }
function onScroll()  { showScrollTop.value = window.scrollY > 400 }

const route = useRoute()
watch(() => route.fullPath, () => { mobileOpen.value = false })

onMounted(() => {
  auth.initAuth()
  window.addEventListener('scroll', onScroll, { passive: true })
})
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
.navbar {
  position: sticky; top: 0; z-index: 1000;
  background: linear-gradient(180deg, #0a0602 0%, #150f08 70%, transparent 100%);
  border-bottom: 1px solid rgba(184,134,11,0.3);
}
.navbar::after {
  content: ''; display: block; height: 2px;
  background: linear-gradient(90deg, transparent, var(--gold), var(--gold-shine), var(--gold), transparent);
}
.nav-inner {
  max-width: 1400px; margin: 0 auto;
  padding: 0 2rem;
  display: flex; align-items: center; gap: 1rem;
  height: 70px;
}
.nav-logo {
  display: flex; align-items: center; gap: 12px;
  text-decoration: none; flex-shrink: 0;
}
.nav-logo-emblem {
  width: 46px; height: 46px;
  border: 2px solid var(--gold); border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: radial-gradient(circle, rgba(184,134,11,0.2), transparent);
  box-shadow: 0 0 12px var(--glow-gold), inset 0 0 8px rgba(0,0,0,0.5);
  animation: pulse-glow 3s ease-in-out infinite;
  overflow: hidden;
}
.nav-logo-svg {
  width: 30px; height: 30px;
}
@keyframes pulse-glow {
  0%,100% { box-shadow: 0 0 12px var(--glow-gold), inset 0 0 8px rgba(0,0,0,.5); }
  50%      { box-shadow: 0 0 26px rgba(212,160,23,.5), inset 0 0 8px rgba(0,0,0,.5); }
}
.nav-title {
  font-family: 'Cinzel Decorative', serif;
  font-size: 1.3rem; color: var(--gold-shine);
  text-shadow: 0 0 20px var(--glow-gold), 0 2px 4px rgba(0,0,0,0.8);
  letter-spacing: 2px; line-height: 1;
}
.nav-title span {
  display: block; font-size: 0.5rem; font-family: 'Cinzel', serif;
  color: var(--parchment-xdk); letter-spacing: 5px;
  text-transform: uppercase; margin-top: 3px;
}
.nav-links { display: flex; gap: 0; list-style: none; flex: 1; }
.nav-links a {
  display: block; padding: 0 1.2rem; height: 70px; line-height: 70px;
  font-family: 'Cinzel', serif; font-size: 0.78rem;
  font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
  color: var(--parchment-dk); text-decoration: none;
  transition: color 0.3s, background 0.3s; position: relative;
}
.nav-links a::after {
  content: ''; position: absolute; bottom: 0; left: 50%;
  width: 0; height: 2px; background: var(--gold);
  transform: translateX(-50%); transition: width 0.3s;
}
.nav-links a:hover,
.nav-links a.active { color: var(--gold-shine); background: rgba(184,134,11,0.06); }
.nav-links a:hover::after,
.nav-links a.active::after { width: 60%; }

.nav-right { margin-left: auto; flex-shrink: 0; }

.mobile-toggle {
  display: none; flex-direction: column; gap: 5px;
  background: none; border: none; cursor: pointer; padding: 6px;
}
.mobile-toggle span { display: block; width: 24px; height: 2px; background: var(--gold); border-radius: 2px; }

.mobile-drawer {
  display: flex; flex-direction: column;
  background: #0d0a06; border-top: 1px solid rgba(184,134,11,0.2); padding: 0.5rem 0;
}
.mobile-drawer a,
.mobile-logout {
  padding: 14px 2rem; font-family: 'Cinzel', serif; font-size: 0.8rem;
  letter-spacing: 2px; text-transform: uppercase;
  color: var(--parchment-dk); text-decoration: none;
  border-left: 2px solid transparent; transition: 0.2s;
  background: none; border-right: none; border-top: none; border-bottom: none;
  cursor: pointer; text-align: left;
}
.mobile-drawer a:hover,
.mobile-logout:hover { color: var(--gold-shine); border-left-color: var(--gold); background: rgba(184,134,11,0.05); }

.drawer-enter-active, .drawer-leave-active { transition: all 0.25s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; transform: translateY(-8px); }

.scroll-top-btn {
  position: fixed; bottom: 2rem; right: 2rem;
  width: 46px; height: 46px;
  background: var(--obsidian-lt); border: 1px solid var(--gold);
  border-radius: 50%; color: var(--gold); cursor: pointer;
  font-size: 1rem; z-index: 999; transition: all 0.3s;
}
.scroll-top-btn:hover { background: var(--gold); color: var(--obsidian); }

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 768px) {
  .nav-links, .nav-right { display: none; }
  .mobile-toggle { display: flex; }
  .nav-inner { justify-content: space-between; }
}
</style>