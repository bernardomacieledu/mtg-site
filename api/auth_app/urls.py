from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('register/', views.register,    name='auth-register'),
    path('login/',    views.login,       name='auth-login'),
    path('me/',       views.me,          name='auth-me'),

    # Decks
    path('decks/',              views.list_decks,       name='deck-list'),
    path('decks/save/',         views.create_deck,      name='deck-create'),
    path('decks/<int:deck_id>/',        views.get_deck,  name='deck-get'),
    path('decks/<int:deck_id>/delete/', views.delete_deck, name='deck-delete'),
    path('decks/<int:deck_id>/imgs/',   views.update_deck_imgs, name='deck-imgs'),

    # Collection
    path('collection/',       views.get_collection,      name='collection-get'),
    path('collection/save/',  views.save_collection,     name='collection-save'),
    path('collection/imgs/',  views.update_collection_imgs, name='collection-imgs'),
]
