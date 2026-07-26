from django.urls import path

from .views import (CardListView, CardImagesView, CollectionsView, SetDetailView,
                    RulesView, mana_symbols, sets_filter_list,
                    card_types_list, card_prices, health)
from .game_views import create_game, get_game, game_action, list_decks
from .admin_api import (listar_tarefas, atualizar_tarefa, executar_tarefa,
                        status_sistema, cambio)
from .deck_views import (import_deck, export_deck,
                         import_collection, export_collection)

urlpatterns = [
    # ── Administração (exige usuário com privilégio) ──
    path('admin/status/',                 status_sistema,    name='admin-status'),
    path('admin/exchange/',               cambio,            name='admin-exchange'),
    path('admin/tasks/',                  listar_tarefas,    name='admin-tasks'),
    path('admin/tasks/<int:task_id>/',    atualizar_tarefa,  name='admin-task-update'),
    path('admin/tasks/<int:task_id>/run/', executar_tarefa,  name='admin-task-run'),

    # ── Diagnóstico ──
    path('health/',             health,                   name='health'),

    # ── Grimório ──
    path('cards/',              CardListView.as_view(),   name='card-list'),
    path('cards/images/',       CardImagesView.as_view(), name='card-images'),
    path('cards/prices/',       card_prices,              name='card-prices'),
    path('collections/',        CollectionsView.as_view(), name='collections'),
    path('collections/<str:code>/', SetDetailView.as_view(), name='collection-detail'),
    path('rules/',              RulesView.as_view(),      name='rules'),
    path('symbols/',            mana_symbols,             name='symbols'),
    path('sets/',               sets_filter_list,         name='sets'),
    path('types/',              card_types_list,          name='types'),

    # ── Deck Builder ──
    path('deck/import/',        import_deck,              name='deck-import'),
    path('deck/export/',        export_deck,              name='deck-export'),

    # ── Coleção (import/export de listas) ──
    path('collection/import/',  import_collection,        name='collection-import'),
    path('collection/export/',  export_collection,        name='collection-export'),

    # ── Arena ──
    path('game/decks/',                list_decks,        name='game-decks'),
    path('game/create/',               create_game,       name='game-create'),
    path('game/<str:game_id>/',        get_game,          name='game-get'),
    path('game/<str:game_id>/action/', game_action,       name='game-action'),
]
