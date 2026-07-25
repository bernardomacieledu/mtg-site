from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register, name='auth-register'),
    path('login/',    views.login,    name='auth-login'),
    path('me/',       views.me,       name='auth-me'),

    # Decks
    path('decks/',                      views.list_decks,       name='deck-list'),
    path('decks/save/',                 views.create_deck,      name='deck-create'),
    path('decks/<int:deck_id>/',        views.get_deck,         name='deck-get'),
    path('decks/<int:deck_id>/delete/', views.delete_deck,      name='deck-delete'),
    path('decks/<int:deck_id>/imgs/',   views.update_deck_imgs, name='deck-imgs'),

    # Coleções (múltiplas)
    path('collections/',                             views.list_collections,     name='collections-list'),
    path('collections/save/',                        views.save_collection_multi, name='collections-save'),
    path('collections/<int:collection_id>/',         views.get_collection_by_id, name='collections-get'),
    path('collections/<int:collection_id>/delete/',  views.delete_collection,    name='collections-delete'),
    path('collections/<int:collection_id>/rename/',  views.rename_collection,    name='collections-rename'),
    path('collections/<int:collection_id>/imgs/',    views.update_collection_imgs, name='collections-imgs'),

    # Compatibilidade (coleção única)
    path('collection/',      views.get_collection,         name='collection-get'),
    path('collection/save/', views.save_collection,        name='collection-save'),
    path('collection/imgs/', views.update_collection_imgs, name='collection-imgs'),
]
