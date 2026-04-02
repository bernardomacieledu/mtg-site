import { createRouter, createWebHistory } from 'vue-router'
import CardsView            from '@/views/CardsView.vue'
import CollectionsView      from '@/views/CollectionsView.vue'
import RulesView            from '@/views/RulesView.vue'
import CardDetailView       from '@/views/CardDetailView.vue'
import LibraryView          from '@/views/LibraryView.vue'
import DeckDetailView       from '@/views/DeckDetailView.vue'
import CollectionDetailView from '@/views/CollectionDetailView.vue'

import LoginView from '@/views/auth/LoginView.vue'

const routes = [
  { path: '/',                   name: 'cards',             component: CardsView },
  { path: '/colecoes',           name: 'collections',       component: CollectionsView },
  { path: '/regras',             name: 'rules',             component: RulesView },
  { path: '/carta/:name',        name: 'card-detail',       component: CardDetailView },
  { path: '/biblioteca',         name: 'library',           component: LibraryView },
  { path: '/biblioteca/deck/:id',name: 'deck-detail',       component: DeckDetailView },
  { path: '/biblioteca/colecao', name: 'collection-detail', component: CollectionDetailView },
  { path: '/login', name: 'login', component: LoginView },
  { path: '/:pathMatch(.*)*',    redirect: '/' },
]

export default createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: () => ({ top: 0, behavior: 'smooth' }),
})