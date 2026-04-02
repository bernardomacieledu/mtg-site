from django.urls import path
from .views import (CardListView, CardImagesView, CollectionsView,
                    RulesView, mana_symbols, sets_filter_list,
                    card_types_list, card_prices)
from .game_views import create_game, get_game, game_action, list_decks
from .deck_views import import_deck, export_deck, import_collection, export_collection, import_collection, export_collection

urlpatterns = [
    # ── Grimório ──
    path('cards/',                     CardListView.as_view(),   name='card-list'),
    path('cards/images/',              CardImagesView.as_view(), name='card-images'),
    path('cards/prices/',              card_prices,              name='card-prices'),
    path('collections/',               CollectionsView.as_view(),name='collections'),
    path('rules/',                     RulesView.as_view(),      name='rules'),
    path('symbols/',                   mana_symbols,             name='symbols'),
    path('sets/',                      sets_filter_list,         name='sets'),
    path('types/',                     card_types_list,          name='types'),
    # ── Arena ──
    path('game/decks/',                list_decks,               name='game-decks'),
    path('game/create/',               create_game,              name='game-create'),
    path('game/<str:game_id>/',        get_game,                 name='game-get'),
    path('collection/import/', import_collection, name='collection-import'),
    path('collection/export/', export_collection, name='collection-export'),
    path('game/<str:game_id>/action/', game_action,              name='game-action'),
    # ── Deck Builder ──
    path('deck/import/',               import_deck,              name='deck-import'),
    path('deck/export/',               export_deck,              name='deck-export'),
    path('collection/import/', import_collection, name='collection-import'),
    path('collection/export/', export_collection, name='collection-export'),
]
