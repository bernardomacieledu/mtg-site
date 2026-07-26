<template>
  <div>
    <div class="page-hero">
      <h1 class="page-hero-title">Administração</h1>
      <p class="page-hero-sub">Atualização automática do acervo</p>
      <div class="hero-divider"><span class="hero-divider-gem">⚙</span></div>
    </div>

    <div class="page-wrap">
      <div v-if="mensagem" class="painel-msg" :class="mensagem.tipo">{{ mensagem.texto }}</div>

      <!-- Números gerais -->
      <section class="stats-grid">
        <div v-for="item in indicadores" :key="item.label" class="stat-box">
          <span class="stat-num">{{ item.valor.toLocaleString('pt-BR') }}</span>
          <span class="stat-label">{{ item.label }}</span>
        </div>
      </section>

      <!-- Cotação do dólar -->
      <section class="cambio">
        <div class="cambio-topo">
          <h3 class="cambio-titulo">💱 Cotação do dólar</h3>
          <span class="cambio-atual">
            1 US$ = R$ {{ cambio.effective ? cambio.effective.toFixed(2) : '—' }}
          </span>
        </div>
        <p class="cambio-nota">
          Usada para exibir os preços em real. É uma conversão do dólar, não o preço
          praticado no mercado brasileiro.
        </p>
        <div class="cambio-controles">
          <label class="controle">
            <input type="radio" value="auto" :checked="cambio.mode === 'auto'" @change="salvarCambio('auto')" />
            <span>Automática (consulta diária)</span>
          </label>
          <label class="controle">
            <input type="radio" value="manual" :checked="cambio.mode === 'manual'" @change="salvarCambio('manual')" />
            <span>Fixar valor</span>
          </label>
          <input
            v-model="cotacaoManual"
            class="input-cotacao"
            :disabled="cambio.mode !== 'manual'"
            placeholder="5,42"
            @keyup.enter="salvarCambio('manual')"
          />
          <button
            class="btn-primary btn-cambio"
            :disabled="cambio.mode !== 'manual' || salvando"
            @click="salvarCambio('manual')"
          >Salvar</button>
        </div>
      </section>

      <div class="section-head">
        <h2 class="section-title">✦ Tarefas Agendadas ✦</h2>
        <span class="section-sub">
          O worker verifica a cada minuto · horário do servidor:
          {{ horaServidor }}
        </span>
      </div>

      <div v-if="carregando" class="spinner-wrap">
        <div class="spinner"></div>
        <span class="spinner-text">Consultando o agendador...</span>
      </div>

      <div v-else class="tarefas">
        <article v-for="t in tarefas" :key="t.id" class="tarefa" :class="t.status">
          <div class="tarefa-topo">
            <div>
              <h3 class="tarefa-nome">{{ t.label }}</h3>
              <code class="tarefa-cmd">manage.py {{ t.key }} {{ t.options }}</code>
            </div>
            <span class="badge" :class="t.status">{{ t.status_label }}</span>
          </div>

          <div class="tarefa-tempos">
            <div>
              <span class="tempo-rotulo">Última execução</span>
              <span class="tempo-valor">{{ formatar(t.last_run) }}</span>
            </div>
            <div>
              <span class="tempo-rotulo">Próxima execução</span>
              <span class="tempo-valor destaque">
                {{ formatar(t.next_run) }}
                <em v-if="t.next_run && t.enabled" class="faltam">({{ faltam(t.next_run) }})</em>
                <em v-else-if="!t.enabled" class="faltam">— desativada</em>
              </span>
            </div>
          </div>

          <div class="tarefa-controles">
            <label class="controle">
              <input type="checkbox" :checked="t.enabled" @change="alternar(t, $event.target.checked)" />
              <span>Ativa</span>
            </label>

            <label class="controle">
              <span>A cada</span>
              <input
                type="number" min="1" max="8760" class="input-horas"
                :value="t.interval_hours"
                @change="mudarIntervalo(t, $event.target.value)"
              />
              <span>horas</span>
            </label>

            <button class="btn-primary btn-rodar" :disabled="t.force_now || salvando" @click="rodar(t)">
              {{ t.force_now ? '⏳ Na fila...' : '▶ Executar agora' }}
            </button>
          </div>

          <details v-if="t.last_message" class="tarefa-log">
            <summary>Resultado da última execução</summary>
            <pre>{{ t.last_message }}</pre>
          </details>
        </article>
      </div>

      <p class="rodape-nota">
        Para tornar outro usuário administrador:
        <code>docker compose exec api python manage.py set_admin &lt;usuário&gt;</code>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { adminStatus, adminTasks, adminUpdateTask, adminRunTask,
         adminExchange, adminSetExchange } from '@/composables/api'

const tarefas    = ref([])
const status     = ref({})
const carregando = ref(true)
const salvando   = ref(false)
const mensagem   = ref(null)
const horaServidor = ref('')
const cambio        = ref({ mode: 'auto', manual: '', effective: null })
const cotacaoManual = ref('')

let atualizacao = null

const indicadores = computed(() => [
  { label: 'Cartas',           valor: status.value.cards ?? 0 },
  { label: 'Preços',           valor: status.value.prices ?? 0 },
  { label: 'Coleções no banco', valor: status.value.sets_in_db ?? 0 },
  { label: 'Catálogo de sets',  valor: status.value.set_catalog ?? 0 },
  { label: 'Regras',           valor: status.value.rules ?? 0 },
  { label: 'Usuários',         valor: status.value.users ?? 0 },
])

function avisar(texto, tipo = 'ok') {
  mensagem.value = { texto, tipo }
  setTimeout(() => { mensagem.value = null }, 5000)
}

async function carregar(silencioso = false) {
  if (!silencioso) carregando.value = true
  try {
    const [{ data: tarefasData }, { data: statusData }] = await Promise.all([
      adminTasks(), adminStatus(),
    ])
    tarefas.value = tarefasData.tasks
    try {
      const { data: cambioData } = await adminExchange()
      cambio.value = cambioData
      if (!cotacaoManual.value) cotacaoManual.value = cambioData.manual || ''
    } catch { /* mantém o valor atual */ }
    horaServidor.value = new Date(tarefasData.server_time).toLocaleString('pt-BR')
    status.value = statusData
  } catch (erro) {
    if (!silencioso) avisar('Não foi possível carregar o painel.', 'err')
  } finally {
    carregando.value = false
  }
}

async function aplicar(tarefa, mudancas, textoOk) {
  salvando.value = true
  try {
    const { data } = await adminUpdateTask(tarefa.id, mudancas)
    Object.assign(tarefa, data)
    avisar(textoOk)
  } catch (erro) {
    avisar(erro.response?.data?.error || 'Não foi possível salvar.', 'err')
    await carregar(true)
  } finally {
    salvando.value = false
  }
}

const alternar = (t, ativa) =>
  aplicar(t, { enabled: ativa }, ativa ? `${t.label}: ativada.` : `${t.label}: desativada.`)

const mudarIntervalo = (t, horas) =>
  aplicar(t, { interval_hours: horas }, `${t.label}: agora a cada ${horas}h.`)

async function rodar(tarefa) {
  salvando.value = true
  try {
    const { data } = await adminRunTask(tarefa.id)
    Object.assign(tarefa, data)
    avisar(`${tarefa.label} entrou na fila. O worker executa em até 1 minuto.`)
  } catch (erro) {
    avisar(erro.response?.data?.error || 'Não foi possível agendar.', 'err')
  } finally {
    salvando.value = false
  }
}

async function salvarCambio(modo) {
  salvando.value = true
  try {
    const corpo = modo === 'manual'
      ? { mode: 'manual', rate: cotacaoManual.value }
      : { mode: 'auto' }
    const { data } = await adminSetExchange(corpo)
    cambio.value = data
    avisar(modo === 'manual'
      ? `Cotação fixada em R$ ${Number(data.effective).toFixed(2)}.`
      : 'Cotação automática reativada.')
  } catch (erro) {
    avisar(erro.response?.data?.error || 'Não foi possível salvar a cotação.', 'err')
    await carregar(true)
  } finally {
    salvando.value = false
  }
}

function formatar(iso) {
  if (!iso) return 'nunca'
  return new Date(iso).toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

function faltam(iso) {
  const diff = new Date(iso) - new Date()
  if (diff <= 0) return 'a qualquer momento'
  const horas = Math.floor(diff / 3600000)
  const minutos = Math.floor((diff % 3600000) / 60000)
  if (horas >= 24) return `em ${Math.floor(horas / 24)} dia(s)`
  if (horas >= 1) return `em ${horas}h ${minutos}min`
  return `em ${minutos}min`
}

onMounted(() => {
  carregar()
  // Atualiza sozinho para acompanhar a execução disparada pelo worker
  atualizacao = setInterval(() => carregar(true), 20000)
})
onBeforeUnmount(() => clearInterval(atualizacao))
</script>

<style scoped>
.painel-msg { padding: 9px 12px; border-radius: 3px; font-size: 0.78rem; margin-bottom: 1.4rem; }
.painel-msg.ok  { background: rgba(60,120,60,0.16); border: 1px solid rgba(120,200,120,0.35); color: #b6e0b6; }
.painel-msg.err { background: rgba(120,40,40,0.16); border: 1px solid rgba(200,90,90,0.35); color: #e8b0b0; }

.stats-grid {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 0.7rem; margin-bottom: 2.6rem;
}
.stat-box {
  background: rgba(0,0,0,0.25); border: 1px solid rgba(184,134,11,0.18);
  border-radius: 4px; padding: 14px; text-align: center;
}
.stat-num {
  display: block; font-family: 'Cinzel', serif; font-size: 1.3rem; color: var(--gold-shine);
}
.stat-label {
  display: block; margin-top: 4px; font-size: 0.62rem; letter-spacing: 1px;
  text-transform: uppercase; color: var(--parchment-xdk);
}

.cambio {
  background: rgba(0,0,0,0.25); border: 1px solid rgba(184,134,11,0.2);
  border-radius: 4px; padding: 16px 18px; margin-bottom: 2.4rem;
}
.cambio-topo { display: flex; justify-content: space-between; align-items: baseline; gap: 10px; flex-wrap: wrap; }
.cambio-titulo { font-family: 'Cinzel', serif; font-size: 0.9rem; color: var(--aged-white); }
.cambio-atual { font-family: 'Cinzel', serif; font-size: 1rem; color: var(--gold-shine); }
.cambio-nota { font-size: 0.66rem; color: var(--parchment-xdk); font-style: italic; margin: 6px 0 12px; }
.cambio-controles { display: flex; align-items: center; gap: 1.2rem; flex-wrap: wrap; }
.cambio-controles .controle input[type="radio"] { accent-color: var(--gold); cursor: pointer; }
.input-cotacao {
  width: 90px; padding: 5px 8px; text-align: center;
  background: rgba(0,0,0,0.4); border: 1px solid rgba(184,134,11,0.3);
  color: var(--aged-white); border-radius: 2px; font-size: 0.8rem;
}
.input-cotacao:disabled { opacity: 0.4; }
.btn-cambio { padding: 6px 14px; font-size: 0.64rem; }

.section-head { text-align: center; margin-bottom: 1.6rem; }
.section-title {
  font-family: 'Cinzel Decorative', serif; font-size: 1.15rem; color: var(--gold-shine);
  letter-spacing: 2px;
}
.section-sub { font-size: 0.7rem; color: var(--parchment-xdk); font-style: italic; }

.tarefas { display: flex; flex-direction: column; gap: 1rem; }
.tarefa {
  background: linear-gradient(150deg, #1a130a 0%, #0f0b06 100%);
  border: 1px solid rgba(184,134,11,0.2); border-left-width: 3px;
  border-radius: 4px; padding: 16px 18px;
}
.tarefa.ok      { border-left-color: rgba(120,200,120,0.6); }
.tarefa.error   { border-left-color: rgba(200,90,90,0.7); }
.tarefa.running { border-left-color: var(--gold); }

.tarefa-topo { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; }
.tarefa-nome { font-family: 'Cinzel', serif; font-size: 0.95rem; color: var(--aged-white); }
.tarefa-cmd { display: block; margin-top: 4px; font-size: 0.64rem; color: var(--parchment-xdk); }

.badge {
  font-family: 'Cinzel', serif; font-size: 0.55rem; letter-spacing: 1px;
  padding: 3px 8px; border-radius: 2px; white-space: nowrap;
  border: 1px solid rgba(184,134,11,0.35); color: var(--parchment-dk);
}
.badge.ok      { border-color: rgba(120,200,120,0.5); color: #b6e0b6; }
.badge.error   { border-color: rgba(200,90,90,0.5); color: #e8b0b0; }
.badge.running { background: var(--gold); color: var(--obsidian); border-color: var(--gold); }

.tarefa-tempos {
  display: flex; gap: 2.4rem; flex-wrap: wrap;
  margin: 14px 0; padding: 10px 0;
  border-top: 1px solid rgba(184,134,11,0.1);
  border-bottom: 1px solid rgba(184,134,11,0.1);
}
.tempo-rotulo {
  display: block; font-size: 0.58rem; letter-spacing: 1px; text-transform: uppercase;
  color: var(--parchment-xdk);
}
.tempo-valor { font-size: 0.82rem; color: var(--parchment-dk); }
.tempo-valor.destaque { color: var(--gold-shine); }
.faltam { font-size: 0.68rem; color: var(--parchment-xdk); font-style: italic; }

.tarefa-controles { display: flex; align-items: center; gap: 1.4rem; flex-wrap: wrap; }
.controle {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.74rem; color: var(--parchment-dk); cursor: pointer;
}
.controle input[type="checkbox"] { accent-color: var(--gold); cursor: pointer; }
.input-horas {
  width: 68px; text-align: center; padding: 4px 6px;
  background: rgba(0,0,0,0.4); border: 1px solid rgba(184,134,11,0.3);
  color: var(--aged-white); border-radius: 2px; font-size: 0.76rem;
}
.btn-rodar { margin-left: auto; padding: 7px 14px; font-size: 0.66rem; }

.tarefa-log { margin-top: 12px; }
.tarefa-log summary {
  cursor: pointer; font-size: 0.68rem; color: var(--parchment-xdk);
  font-family: 'Cinzel', serif; letter-spacing: 1px;
}
.tarefa-log pre {
  margin-top: 8px; padding: 10px; max-height: 200px; overflow: auto;
  background: rgba(0,0,0,0.4); border: 1px solid rgba(184,134,11,0.12);
  border-radius: 3px; font-size: 0.68rem; color: var(--parchment-dk);
  white-space: pre-wrap; word-break: break-word;
}

.rodape-nota {
  margin-top: 2.4rem; padding-top: 1.2rem; font-size: 0.68rem;
  color: var(--parchment-xdk); border-top: 1px solid rgba(184,134,11,0.12);
}
.rodape-nota code { color: var(--gold); }

@media (max-width: 640px) {
  .btn-rodar { margin-left: 0; width: 100%; }
}
</style>
