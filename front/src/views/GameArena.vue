<template>
  <GameView
    v-if="gameId"
    :game-id="gameId"
    :mana-map="manaMap"
    @exit="router.push({ name: 'game-lobby' })"
  />
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import GameView from './GameView.vue'
import { useMana } from '@/composables/useMana'

const route  = useRoute()
const router = useRouter()
const { symbols: manaMap } = useMana()

const gameId = computed(() => route.params.gameId)
</script>
