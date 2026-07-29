<template>
  <div class="auth-page">
    <div class="auth-box">
      <div class="auth-emblem">🍺</div>
      <h1 class="auth-title">MTG BEERnas</h1>
      <p class="auth-sub">Grimório das Terras</p>

      <div class="auth-tabs">
        <button class="auth-tab" :class="{ active: mode === 'login' }" @click="mode = 'login'">
          Entrar
        </button>
        <button class="auth-tab" :class="{ active: mode === 'register' }" @click="mode = 'register'">
          Criar Conta
        </button>
      </div>

      <form class="auth-form" @submit.prevent="submit">
        <div class="field-wrap">
          <label class="field-label">⚔ Username</label>
          <input v-model="form.username" class="medieval-input" placeholder="seu_nome"
            autocomplete="username" required />
        </div>

        <div v-if="mode === 'register'" class="field-wrap">
          <label class="field-label">📜 Email (opcional)</label>
          <input v-model="form.email" class="medieval-input" type="email" placeholder="seu@email.com"
            autocomplete="email" />
        </div>

        <div class="field-wrap">
          <label class="field-label">🔒 Senha</label>
          <input v-model="form.password" class="medieval-input" type="password"
            placeholder="mínimo 6 caracteres" autocomplete="current-password" required />
        </div>

        <div v-if="mode === 'register'" class="field-wrap">
          <label class="field-label">🔒 Confirmar Senha</label>
          <input v-model="form.confirm" class="medieval-input" type="password"
            placeholder="repita a senha" autocomplete="new-password" />
        </div>

        <div v-if="error" class="auth-error">⚠ {{ error }}</div>

        <button type="submit" class="btn-primary" style="width:100%;padding:12px;font-size:0.85rem;letter-spacing:3px;margin-top:8px"
          :disabled="loading">
          {{ loading ? '⏳ Aguarde...' : (mode === 'login' ? '✦ ENTRAR' : '✦ CRIAR CONTA') }}
        </button>
      </form>

      <div class="auth-divider">
        <span>ou</span>
      </div>

      <button class="btn-ghost" style="width:100%;font-size:0.72rem" @click="continueAsGuest">
        Continuar sem conta
      </button>

      <p class="auth-note">
        Sem conta, decks e coleções ficam apenas neste navegador.
        Com conta, ficam salvos no servidor.
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLibrary } from '@/composables/useLibrary'

const router  = useRouter()
const auth    = useAuthStore()
const library = useLibrary()

const mode    = ref('login')
const loading = ref(false)
const error   = ref('')

const form = reactive({ username: '', email: '', password: '', confirm: '' })

async function submit() {
  error.value = ''
  if (mode.value === 'register' && form.password !== form.confirm) {
    error.value = 'As senhas não coincidem.'
    return
  }

  // Etapa 1 — autenticação. Só o que acontece AQUI pode virar erro de login.
  // Antes, um único try cobria login, migração de dados e navegação: qualquer
  // falha depois do 200 aparecia como "Erro ao autenticar" com o usuário já
  // autenticado.
  loading.value = true
  let autenticado = false
  try {
    if (mode.value === 'login') {
      await auth.login(form.username, form.password)
    } else {
      await auth.register(form.username, form.email, form.password)
    }
    autenticado = true
  } catch (e) {
    const doServidor = e.response?.data?.error
    error.value = doServidor || (mode.value === 'login'
      ? 'Não foi possível entrar. Confira usuário e senha.'
      : 'Não foi possível criar a conta.')
  } finally {
    loading.value = false
  }

  if (!autenticado) return

  // Etapa 2 — sobe o que estava salvo só neste navegador. Se falhar, não
  // invalida o login: o usuário está dentro e os dados seguem no navegador.
  try {
    await library.migrateLocalToBackend()
  } catch (e) {
    console.warn('Não foi possível migrar os dados locais:', e)
  }

  // Etapa 3 — navegação. Uma falha aqui também não é erro de autenticação.
  try {
    await router.push(route.query.redirect || { name: 'library' })
  } catch (e) {
    console.warn('Falha ao navegar após o login:', e)
    router.push({ name: 'cards' })
  }
}

function continueAsGuest() {
  router.push({ name: 'cards' })
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: radial-gradient(ellipse at 50% 30%, rgba(139,26,26,0.12) 0%, transparent 60%),
              radial-gradient(ellipse at 50% 70%, rgba(184,134,11,0.08) 0%, transparent 60%);
}

.auth-box {
  background: linear-gradient(135deg, rgba(26,19,10,0.97), rgba(13,10,6,0.97));
  border: 1px solid rgba(184,134,11,0.35);
  border-radius: 6px;
  padding: 2.5rem 2rem;
  width: 100%;
  max-width: 400px;
  text-align: center;
  box-shadow: 0 30px 60px rgba(0,0,0,0.6);
}

.auth-emblem {
  font-size: 2.5rem;
  color: var(--gold);
  text-shadow: 0 0 20px var(--glow-gold);
  margin-bottom: 8px;
  animation: pulse-glow 3s ease-in-out infinite;
}
@keyframes pulse-glow {
  0%,100% { text-shadow: 0 0 20px var(--glow-gold); }
  50%      { text-shadow: 0 0 40px rgba(212,160,23,0.6); }
}

.auth-title { font-family:'Cinzel Decorative',serif; font-size:1.6rem; color:var(--gold-shine); margin-bottom:4px; }
.auth-sub   { font-size:0.75rem; letter-spacing:4px; color:var(--parchment-xdk); font-family:'Cinzel',serif; text-transform:uppercase; margin-bottom:1.5rem; }

.auth-tabs { display:flex; gap:0; margin-bottom:1.5rem; border:1px solid rgba(184,134,11,0.25); border-radius:3px; overflow:hidden; }
.auth-tab  { flex:1; padding:8px; font-family:'Cinzel',serif; font-size:0.72rem; letter-spacing:2px; text-transform:uppercase; background:transparent; border:none; color:var(--parchment-xdk); cursor:pointer; transition:all 0.2s; }
.auth-tab.active { background:rgba(184,134,11,0.15); color:var(--gold-shine); }

.auth-form  { text-align:left; display:flex; flex-direction:column; gap:0.8rem; margin-bottom:1rem; }
.field-wrap { display:flex; flex-direction:column; gap:5px; }

.auth-error { font-family:'Cinzel',serif; font-size:0.65rem; color:var(--crimson-lt); background:rgba(139,26,26,0.15); border:1px solid rgba(139,26,26,0.3); border-radius:2px; padding:8px 12px; text-align:center; }

.auth-divider { display:flex; align-items:center; gap:1rem; margin:1rem 0; }
.auth-divider::before, .auth-divider::after { content:''; flex:1; height:1px; background:rgba(184,134,11,0.2); }
.auth-divider span { font-size:0.65rem; color:var(--parchment-xdk); font-family:'Cinzel',serif; }

.auth-note { font-size:0.62rem; color:rgba(184,134,11,0.4); font-style:italic; margin-top:1rem; line-height:1.5; }
</style>
