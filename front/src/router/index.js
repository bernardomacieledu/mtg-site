import { createRouter, createWebHistory } from 'vue-router'

import CardsView              from '@/views/CardsView.vue'
import SetsView               from '@/views/SetsView.vue'
import RulesView              from '@/views/RulesView.vue'
import CardDetailView         from '@/views/CardDetailView.vue'
import LibraryView            from '@/views/LibraryView.vue'
import DeckDetailView         from '@/views/DeckDetailView.vue'
import CollectionDetailView   from '@/views/CollectionDetailView.vue'
import CollectionBuilderView  from '@/views/CollectionBuilderView.vue'
import CollectionsView        from '@/views/CollectionsView.vue'
import AdminView              from '@/views/AdminView.vue'
import LoginView              from '@/views/auth/LoginView.vue'

const routes = [
  { path: '/',                    name: 'cards',              component: CardsView },
  { path: '/colecoes',            name: 'sets',               component: SetsView },
  { path: '/colecao/montar',      name: 'collection-builder', component: CollectionBuilderView,
    meta: { requiresAuth: true } },
  { path: '/colecao/importar',    name: 'collection-import',  component: CollectionsView,
    meta: { requiresAuth: true } },
  { path: '/regras',              name: 'rules',              component: RulesView },
  { path: '/carta/:name',         name: 'card-detail',        component: CardDetailView },
  { path: '/biblioteca',          name: 'library',            component: LibraryView,
    meta: { requiresAuth: true } },
  { path: '/biblioteca/deck/:id', name: 'deck-detail',        component: DeckDetailView },
  { path: '/biblioteca/colecao',  name: 'collection-detail',  component: CollectionDetailView },
  { path: '/biblioteca/colecao/:id', name: 'collection-detail-id', component: CollectionDetailView },
  { path: '/login',               name: 'login',              component: LoginView },
  { path: '/administracao',       name: 'admin',              component: AdminView,
    meta: { requiresAuth: true, requiresAdmin: true } },

  // rotas antigas
  { path: '/colecao',             redirect: '/colecao/montar' },
  { path: '/:pathMatch(.*)*',     redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior: (to, from, saved) => saved || { top: 0, behavior: 'smooth' },
})

// Decks e coleções vivem no banco, vinculados ao usuário: sem conta, manda
// para o login guardando o destino para voltar depois.
router.beforeEach((to) => {
  if (to.meta.requiresAuth && !localStorage.getItem('mtg_token')) {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  // O servidor também valida: aqui é só para não exibir a tela em vão
  if (to.meta.requiresAdmin && localStorage.getItem('mtg_is_admin') !== '1') {
    return { name: 'cards' }
  }
  return true
})

export default router
