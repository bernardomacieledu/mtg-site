<template>
  <!-- Loading -->
  <div v-if="!state" class="spinner-wrap" style="height:100vh">
    <div class="spinner"></div>
    <span class="spinner-text">Conjurando a Partida...</span>
  </div>

  <!-- Game -->
  <div v-else class="game-root" :class="{ 'combat-mode': isCombat }">

    <div class="battlefield">

      <!-- OPPONENT -->
      <div class="player-side opponent-side">
        <PlayerInfo :player="state.players.p2" side="opponent" />
        <ManaPool :mana="state.players.p2.mana_pool" />
        <Hand :cards="state.players.p2.hand" :hidden="true" :count="state.players.p2.hand_count" />
        <BattlefieldZone
          :permanents="opponentBattlefield"
          :mana-map="manaMap"
          side="opponent"
          :selectable-uids="selectableTargets"
          @select="onSelectTarget"
        />
      </div>

      <!-- CENTER -->
      <div class="center-panel">
        <PhaseTracker :phase="state.phase" :active-player="state.active_player" />
        <StackDisplay v-if="state.stack.length" :stack="state.stack" :mana-map="manaMap" />
        <CombatPanel
          v-if="isCombat"
          :phase="state.phase"
          :attackers="selectedAttackers"
          :available-attackers="myCreatures.filter(p => p.can_attack)"
          :combat-attackers="state.combat_attackers"
          :my-creatures="myCreatures"
          :mana-map="manaMap"
          @toggle-attacker="toggleAttacker"
          @confirm-attackers="confirmAttackers"
          @toggle-blocker="toggleBlocker"
          @confirm-blockers="confirmBlockers"
        />
        <GameLog :log="state.log" />
      </div>

      <!-- PLAYER -->
      <div class="player-side player-side-me">
        <BattlefieldZone
          :permanents="myBattlefield"
          :mana-map="manaMap"
          side="player"
          :selectable-uids="selectableTargets"
          @select="onSelectTarget"
          @tap="onTapPermanent"
        />
        <ManaPool :mana="state.players.p1.mana_pool" />
        <Hand
          :cards="state.players.p1.hand"
          :hidden="false"
          :cards-db="state.cards_db"
          :mana-map="manaMap"
          :playable="getPlayableCards()"
          :phase="state.phase"
          @play="onPlayCard"
        />
        <PlayerInfo :player="state.players.p1" side="player" />
      </div>
    </div>

    <!-- ACTION BAR -->
    <div class="action-bar">
      <button class="action-btn btn-primary" @click="passPriority" :disabled="isLoading">
        Passar Prioridade <span class="key-hint">Space</span>
      </button>
      <button class="action-btn btn-ghost" @click="endPhase"
              :disabled="isLoading || state.active_player !== 'p1'">
        {{ phaseLabel }} →
      </button>
      <div v-if="pendingSpell" class="target-prompt">
        Selecione um alvo para <strong>{{ pendingSpell.name }}</strong>
        <button class="btn-ghost" style="margin-left:8px" @click="cancelSpell">✕</button>
      </div>
    </div>

    <!-- GAME OVER -->
    <Transition name="fade">
      <div v-if="state.game_over" class="game-over-overlay">
        <div class="game-over-box">
          <div class="game-over-title">
            {{ state.winner === 'p1' ? '⚔ VITÓRIA ⚔' : '☠ DERROTA ☠' }}
          </div>
          <div class="game-over-sub">
            {{ state.players[state.winner]?.name }} venceu!
          </div>
          <button class="btn-primary" @click="$emit('exit')">Voltar ao Menu</button>
        </div>
      </div>
    </Transition>

    <!-- TARGET SELECTION -->
    <Transition name="fade">
      <div v-if="selectingTargets" class="target-overlay" @click.self="cancelSpell">
        <div class="target-panel">
          <div class="target-title">Selecione o alvo para {{ pendingSpell?.name }}</div>
          <div class="target-options">
            <button class="target-opt" @click="addTarget('p1')">
              {{ state.players.p1.name }} ({{ state.players.p1.life }} ❤)
            </button>
            <button class="target-opt" @click="addTarget('p2')">
              {{ state.players.p2.name }} ({{ state.players.p2.life }} ❤)
            </button>
            <div class="target-creatures">
              <button
                v-for="perm in allCreatures"
                :key="perm.uid"
                class="target-opt"
                @click="addTarget(perm.uid)"
              >
                {{ perm.name }} ({{ perm.power }}/{{ perm.toughness }})
                <span class="target-owner">{{ perm.controller === 'p1' ? '👤' : '🤖' }}</span>
              </button>
            </div>
          </div>
          <button class="btn-ghost" @click="cancelSpell">Cancelar</button>
        </div>
      </div>
    </Transition>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import PlayerInfo      from './game/PlayerInfo.vue'
import ManaPool        from './game/ManaPool.vue'
import Hand            from './game/Hand.vue'
import BattlefieldZone from './game/BattlefieldZone.vue'
import PhaseTracker    from './game/PhaseTracker.vue'
import StackDisplay    from './game/StackDisplay.vue'
import CombatPanel     from './game/CombatPanel.vue'
import GameLog         from './game/GameLog.vue'

const props = defineProps({
  gameId:  { type: String, required: true },
  manaMap: { type: Object, default: () => ({}) },
})
const emit = defineEmits(['exit'])

const state              = ref(null)
const isLoading          = ref(false)
const pendingSpell       = ref(null)
const pendingCardId      = ref(null)
const selectingTargets   = ref(false)
const selectedTargets    = ref([])
const selectedAttackers  = ref([])
const blockerAssignments = ref({})
const selectableTargets  = ref([])

const myBattlefield = computed(() =>
  (state.value?.battlefield || []).filter(p => p.controller === 'p1')
)
const opponentBattlefield = computed(() =>
  (state.value?.battlefield || []).filter(p => p.controller === 'p2')
)
const myCreatures = computed(() =>
  myBattlefield.value.filter(p => p.type === 'Creature')
)
const allCreatures = computed(() =>
  (state.value?.battlefield || []).filter(p => p.type === 'Creature')
)
const isCombat = computed(() =>
  state.value?.phase?.startsWith('combat')
)
const phaseLabel = computed(() => {
  const labels = {
    main1: 'Ir para Combate', combat_begin: 'Atacantes',
    combat_attackers: 'Confirmar Ataque', combat_blockers: 'Confirmar Bloqueio',
    combat_damage: 'Dano', combat_end: 'Pós-Combate',
    main2: 'Encerrar Turno', end: 'Encerrar',
  }
  return labels[state.value?.phase] || 'Próxima Fase'
})

async function loadGame() {
  const { data } = await axios.get(`/api/game/${props.gameId}/`)
  state.value = data
}

async function action(type, payload = {}) {
  if (isLoading.value) return
  isLoading.value = true
  try {
    const { data } = await axios.post(`/api/game/${props.gameId}/action/`, {
      action: type, pid: 'p1', payload,
    })
    if (data.state) state.value = data.state
    if (!data.ok && data.error) console.warn('Game error:', data.error)
  } catch (e) {
    console.error(e)
  } finally {
    isLoading.value = false
  }
}

function onPlayCard(cardId) {
  const card = state.value?.cards_db?.[cardId]
  if (!card) return
  if (card.type === 'Land') { action('play_land', { card_id: cardId }); return }
  const needsTarget = card.oracle_text?.toLowerCase().includes('target')
  if (needsTarget) {
    pendingSpell.value  = card
    pendingCardId.value = cardId
    selectingTargets.value = true
    selectedTargets.value  = []
  } else {
    action('cast_spell', { card_id: cardId, targets: [] })
  }
}

function addTarget(targetId) {
  selectedTargets.value.push(targetId)
  selectingTargets.value = false
  action('cast_spell', { card_id: pendingCardId.value, targets: selectedTargets.value })
  pendingSpell.value = null; pendingCardId.value = null; selectedTargets.value = []
}

function cancelSpell() {
  pendingSpell.value = null; pendingCardId.value = null
  selectingTargets.value = false; selectedTargets.value = []
}

function onTapPermanent(permUid) {
  action('activate_ability', { perm_uid: permUid, ability_index: 0, targets: [] })
}

function onSelectTarget(uid) { if (selectingTargets.value) addTarget(uid) }
function passPriority()      { action('pass_priority') }

function endPhase() {
  if (state.value?.phase === 'combat_attackers') confirmAttackers()
  else if (state.value?.phase === 'combat_blockers') confirmBlockers()
  else action('end_phase')
}

function toggleAttacker(uid) {
  const i = selectedAttackers.value.indexOf(uid)
  i === -1 ? selectedAttackers.value.push(uid) : selectedAttackers.value.splice(i, 1)
}
function confirmAttackers() {
  action('declare_attackers', { attacker_uids: selectedAttackers.value })
  selectedAttackers.value = []
}
function toggleBlocker({ blocker, attacker }) {
  if (blockerAssignments.value[blocker] === attacker) delete blockerAssignments.value[blocker]
  else blockerAssignments.value[blocker] = attacker
}
function confirmBlockers() {
  action('declare_blockers', { block_assignments: blockerAssignments.value })
  blockerAssignments.value = {}
}

function getPlayableCards() {
  if (!state.value) return []
  const p     = state.value.players.p1
  const pool  = p.mana_pool
  const phase = state.value.phase
  const isMyTurn = state.value.active_player === 'p1'

  return p.hand.filter(cardId => {
    const card = state.value.cards_db?.[cardId]
    if (!card) return false
    if (card.type === 'Land') {
      return isMyTurn && !p.land_played &&
             (phase === 'main1' || phase === 'main2') && !state.value.stack.length
    }
    let tempPool = { ...pool }; let canCast = true; let generic = 0
    for (const [sym, amt] of Object.entries(card.mana_cost)) {
      if (['W','U','B','R','G'].includes(sym)) {
        if ((tempPool[sym] || 0) < amt) { canCast = false; break }
        tempPool[sym] -= amt
      } else generic += parseInt(amt)
    }
    if (canCast && generic > Object.values(tempPool).reduce((a,b)=>a+b,0)) canCast = false
    return canCast
  })
}

function onKeydown(e) {
  if (e.target.matches('input,textarea,select')) return
  if (e.code === 'Space')  { e.preventDefault(); passPriority() }
  if (e.code === 'Enter')  { e.preventDefault(); endPhase() }
}

onMounted(() => { loadGame(); window.addEventListener('keydown', onKeydown) })
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.game-root {
  display: flex; flex-direction: column; height: 100vh;
  background: var(--obsidian); overflow: hidden; position: relative;
}
.battlefield {
  flex: 1; display: grid; grid-template-columns: 1fr 280px 1fr;
  gap: 0; min-height: 0; overflow: hidden;
}
.player-side {
  display: flex; flex-direction: column; padding: 8px; gap: 6px; overflow: hidden;
}
.opponent-side  { flex-direction: column-reverse; background: rgba(139,26,26,0.04); }
.player-side-me { background: rgba(59,130,246,0.04); }
.center-panel {
  display: flex; flex-direction: column; gap: 6px; padding: 8px 4px;
  border-left: 1px solid rgba(184,134,11,0.15);
  border-right: 1px solid rgba(184,134,11,0.15);
  overflow-y: auto;
}
.action-bar {
  display: flex; align-items: center; gap: 8px; padding: 8px 16px;
  background: linear-gradient(180deg, transparent, rgba(0,0,0,0.6));
  border-top: 1px solid rgba(184,134,11,0.2); flex-shrink: 0;
}
.action-btn { font-size: 0.75rem; letter-spacing: 1px; }
.key-hint {
  font-size: 0.55rem; opacity: 0.6; margin-left: 4px;
  border: 1px solid currentColor; padding: 1px 4px; border-radius: 2px;
}
.target-prompt {
  font-family: 'Cinzel', serif; font-size: 0.72rem; color: var(--gold-shine);
  padding: 6px 12px; background: rgba(184,134,11,0.15);
  border: 1px solid rgba(184,134,11,0.4); border-radius: 2px;
  display: flex; align-items: center;
}
.target-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.75);
  display: flex; align-items: center; justify-content: center; z-index: 100;
}
.target-panel {
  background: linear-gradient(135deg, #1a130a, #0d0a06);
  border: 1px solid var(--gold); border-radius: 4px;
  padding: 2rem; min-width: 320px; max-width: 500px;
}
.target-title {
  font-family: 'Cinzel Decorative', serif; font-size: 1rem;
  color: var(--gold-shine); margin-bottom: 1.5rem; text-align: center;
}
.target-options  { display: flex; flex-direction: column; gap: 8px; margin-bottom: 1rem; }
.target-opt {
  display: flex; align-items: center; justify-content: space-between;
  background: rgba(0,0,0,0.3); border: 1px solid rgba(184,134,11,0.25);
  border-radius: 2px; padding: 10px 14px; cursor: pointer;
  font-family: 'Cinzel', serif; font-size: 0.78rem; color: var(--parchment);
  transition: all 0.2s;
}
.target-opt:hover { border-color: var(--gold); color: var(--gold-shine); background: rgba(184,134,11,0.1); }
.target-creatures { display: flex; flex-direction: column; gap: 6px; margin-top: 8px; }
.target-owner { opacity: 0.6; }
.game-over-overlay {
  position: fixed; inset: 0; background: rgba(0,0,0,0.85);
  display: flex; align-items: center; justify-content: center; z-index: 200;
}
.game-over-box {
  text-align: center; background: linear-gradient(135deg, #1a130a, #0d0a06);
  border: 2px solid var(--gold); border-radius: 6px; padding: 3rem 4rem;
}
.game-over-title {
  font-family: 'Cinzel Decorative', serif; font-size: 2.5rem;
  color: var(--gold-shine); text-shadow: 0 0 40px rgba(212,160,23,0.6); margin-bottom: 1rem;
}
.game-over-sub {
  font-family: 'Cinzel', serif; font-size: 1rem; color: var(--parchment-dk);
  margin-bottom: 2rem; letter-spacing: 2px;
}
.fade-enter-active, .fade-leave-active { transition: opacity 0.3s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
