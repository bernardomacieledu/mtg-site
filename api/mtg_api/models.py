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


class CardSet(models.Model):
    """
    Catálogo de coleções (nome, ícone, data), gravado no banco.

    Antes esses dados vinham de uma chamada ao Scryfall a cada request: quando
    ela falhava, a interface exibia o código da coleção no lugar do nome e o
    ícone quebrava. Persistir aqui torna a exibição independente de rede.
    """
    code         = models.CharField(max_length=10, primary_key=True)
    name         = models.CharField(max_length=255)
    set_type     = models.CharField(max_length=50, blank=True, default='')
    released_at  = models.CharField(max_length=10, blank=True, default='')
    icon_svg_uri = models.CharField(max_length=512, blank=True, default='')
    card_count   = models.IntegerField(default=0)
    parent_code  = models.CharField(max_length=10, blank=True, default='')
    digital      = models.BooleanField(default=False)
    updated_at   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mtg_sets'
        ordering = ['-released_at']

    def __str__(self):
        return f'{self.name} ({self.code.upper()})'


class ManaSymbol(models.Model):
    """
    Símbolos de mana ({W}, {2/U}, {T}...) com a URL do SVG.

    Ficavam só em cache de disco alimentado por uma chamada ao Scryfall em
    tempo de request; no container o cache nasce vazio e a interface exibia as
    letras em vez dos símbolos.
    """
    symbol   = models.CharField(max_length=20, primary_key=True)
    svg_uri  = models.CharField(max_length=512)
    english  = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'mtg_symbols'

    def __str__(self):
        return self.symbol


class CardPrice(models.Model):
    """
    Preços por impressão, vindos do MTGJSON (AllPricesToday).

    Fica em tabela própria em vez de colunas novas em `cards`: aquela tabela é
    legada (managed = False) e alterá-la exigiria ALTER TABLE em bancos que já
    existem. Aqui o Django cuida do schema via migration.

    A chave é o scryfall_id, que é o que `cards` usa. O uuid do MTGJSON fica
    guardado para conferência e para buscas de histórico depois.
    """
    scryfall_id   = models.CharField(max_length=36, primary_key=True)
    mtgjson_uuid  = models.CharField(max_length=36, blank=True, default='', db_index=True)
    usd           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    usd_foil      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    eur           = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    eur_foil      = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_date    = models.CharField(max_length=10, blank=True, default='')
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'mtg_prices'

    def __str__(self):
        return f'{self.scryfall_id}: US$ {self.usd}'
