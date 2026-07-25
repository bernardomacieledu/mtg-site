"""
Importa o catálogo de coleções do Scryfall para a tabela `mtg_sets`.

É uma única requisição e roda em segundos. Sem isso a interface mostra o código
da coleção no lugar do nome completo e os ícones quebram.
"""
import json
import time
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from mtg_api.models import CardSet

SCRYFALL_SETS = 'https://api.scryfall.com/sets'
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0', 'Accept': 'application/json'}


class Command(BaseCommand):
    help = 'Atualiza o catálogo de coleções (nome, ícone, data de lançamento).'

    def handle(self, *args, **options):
        self.stdout.write('Buscando catálogo de coleções no Scryfall...')
        try:
            request = urllib.request.Request(SCRYFALL_SETS, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read())
        except Exception as exc:
            raise CommandError(
                f'Não foi possível obter o catálogo ({exc}). '
                'Os nomes das coleções seguirão vindo do cache local.'
            ) from None

        registros = []
        for item in data.get('data', []):
            if not item.get('code'):
                continue
            registros.append(CardSet(
                code=item['code'][:10],
                name=(item.get('name') or item['code'])[:255],
                set_type=(item.get('set_type') or '')[:50],
                released_at=(item.get('released_at') or '')[:10],
                icon_svg_uri=(item.get('icon_svg_uri') or '')[:512],
                card_count=item.get('card_count') or 0,
                parent_code=(item.get('parent_set_code') or '')[:10],
                digital=bool(item.get('digital')),
            ))

        if not registros:
            raise CommandError('O Scryfall não retornou nenhuma coleção.')

        # MySQL nao aceita unique_fields no upsert (usa ON DUPLICATE KEY UPDATE)
        CardSet.objects.bulk_create(
            registros,
            update_conflicts=True,
            update_fields=['name', 'set_type', 'released_at', 'icon_svg_uri',
                           'card_count', 'parent_code', 'digital'],
        )
        self.stdout.write(self.style.SUCCESS(f'{len(registros)} coleções no catálogo.'))
