from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, UserCollection, UserDeck


@admin.register(User)
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_staff', 'is_superuser', 'created_at')
    readonly_fields = ('created_at',)


@admin.register(UserDeck)
class DeckAdmin(admin.ModelAdmin):
    list_display  = ('name', 'user', 'total_cards', 'updated_at')
    search_fields = ('name', 'user__username')


@admin.register(UserCollection)
class ColecaoAdmin(admin.ModelAdmin):
    list_display  = ('name', 'user', 'updated_at')
    search_fields = ('name', 'user__username')
