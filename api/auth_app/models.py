from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Usuário customizado."""
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'auth_users'

    def __str__(self):
        return self.username


class UserDeck(models.Model):
    """Deck salvo no banco por usuário."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='decks')
    name        = models.CharField(max_length=255)
    raw_text    = models.TextField(blank=True)
    cards_json  = models.JSONField(default=list)        # lista completa de cartas
    categorized_json = models.JSONField(default=dict)   # por categoria
    commander_json   = models.JSONField(null=True, blank=True)  # comandante
    legendaries_json = models.JSONField(default=list)
    colors      = models.JSONField(default=list)
    total_cards = models.IntegerField(default=0)
    avg_cmc     = models.FloatField(default=0)
    not_found   = models.JSONField(default=list)
    active_imgs = models.JSONField(default=dict)  # name -> image_url escolhida
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_decks'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} / {self.name}"


class UserCollection(models.Model):
    """Coleção de cartas salva no banco por usuário."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='collections')
    name        = models.CharField(max_length=255, default='Minha Coleção')
    cards_json  = models.JSONField(default=list)
    by_set_json = models.JSONField(default=list)
    by_rarity_json  = models.JSONField(default=dict)
    by_category_json = models.JSONField(default=dict)
    stats_json  = models.JSONField(default=dict)
    active_imgs = models.JSONField(default=dict)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_collections'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} / {self.name}"
