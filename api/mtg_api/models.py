from django.db import models


class Card(models.Model):
    scryfall_id = models.CharField(max_length=36, primary_key=True)
    name = models.CharField(max_length=255, null=True, blank=True, db_index=True)
    mana_cost = models.CharField(max_length=50, null=True, blank=True)
    cmc = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    type_line = models.CharField(max_length=255, null=True, blank=True)
    oracle_text = models.TextField(null=True, blank=True)
    rarity = models.CharField(max_length=20, null=True, blank=True)
    image_url_normal = models.CharField(max_length=512, null=True, blank=True)
    local_image_path = models.CharField(max_length=512, null=True, blank=True)
    set_code = models.CharField(max_length=10, null=True, blank=True, db_index=True)
    release_date = models.DateField(null=True, blank=True)
    lang = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'cards'

    def __str__(self):
        return self.name or self.scryfall_id


class Rule(models.Model):
    rule_number = models.CharField(max_length=20, unique=True)
    rule_text = models.TextField()
    chapter_id = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'rules'
        ordering = ['rule_number']

    def __str__(self):
        return f"{self.rule_number}: {self.rule_text[:60]}"
