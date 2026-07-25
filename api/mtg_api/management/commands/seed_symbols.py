"""
Importa os símbolos de mana do Scryfall para a tabela `mtg_symbols`.

Uma requisição, poucos segundos. Sem isso a interface exibe as letras (W, U, B)
no lugar dos símbolos coloridos.
"""
import json
import urllib.request

from django.core.management.base import BaseCommand, CommandError

from mtg_api.models import ManaSymbol

SYMBOLOGY = 'https://api.scryfall.com/symbology'
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0', 'Accept': 'application/json'}


class Command(BaseCommand):
    help = 'Atualiza a tabela de símbolos de mana.'

    def handle(self, *args, **options):
        self.stdout.write('Buscando símbolos de mana no Scryfall...')
        try:
            request = urllib.request.Request(SYMBOLOGY, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.loads(response.read())
        except Exception as exc:
            raise CommandError(
                f'Não foi possível obter os símbolos ({exc}). '
                'A interface exibirá as letras no lugar dos ícones.'
            ) from None

        registros = [
            ManaSymbol(
                symbol=item['symbol'][:20],
                svg_uri=(item.get('svg_uri') or '')[:512],
                english=(item.get('english') or '')[:255],
            )
            for item in data.get('data', [])
            if item.get('symbol') and item.get('svg_uri')
        ]

        if not registros:
            raise CommandError('O Scryfall não retornou símbolos.')

        ManaSymbol.objects.bulk_create(
            registros,
            update_conflicts=True,
            update_fields=['svg_uri', 'english'],
        )
        self.stdout.write(self.style.SUCCESS(f'{len(registros)} símbolos gravados.'))
