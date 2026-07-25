"""
Popula a tabela `cards` a partir da API pública do Scryfall.

Exemplos:
    python manage.py seed_cards --recent 8
    python manage.py seed_cards --sets blb,dsk,fdn
    python manage.py seed_cards --recent 20 --max-per-set 400
"""
import json
import time
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand
from django.db import connection

SCRYFALL = 'https://api.scryfall.com'
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0', 'Accept': 'application/json'}

# Tipos de set que não interessam para o grimório
SKIP_SET_TYPES = {'token', 'memorabilia', 'minigame', 'funny', 'alchemy', 'treasure_chest'}

INSERT_SQL = """
    REPLACE INTO cards
        (scryfall_id, name, mana_cost, cmc, type_line, oracle_text, rarity,
         image_url_normal, local_image_path, set_code, release_date, lang)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
"""


def get_json(url, retries=3):
    for attempt in range(retries):
        try:
            request = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.loads(response.read())
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    return {}


def card_row(card):
    """Converte um objeto do Scryfall em uma linha da tabela `cards`."""
    image = (card.get('image_uris') or {}).get('normal')
    faces = card.get('card_faces') or []
    if not image and faces:
        image = (faces[0].get('image_uris') or {}).get('normal')

    mana_cost = card.get('mana_cost') or (faces[0].get('mana_cost') if faces else '')
    oracle = card.get('oracle_text')
    if not oracle and faces:
        oracle = '\n//\n'.join(f.get('oracle_text', '') for f in faces)

    if not image:
        return None

    return (
        card['id'],
        card.get('name'),
        (mana_cost or '')[:50],
        card.get('cmc'),
        (card.get('type_line') or '')[:255],
        oracle or '',
        (card.get('rarity') or '')[:20],
        image[:512],
        None,
        (card.get('set') or '')[:10],
        card.get('released_at'),
        (card.get('lang') or 'en')[:10],
    )


class Command(BaseCommand):
    help = 'Importa cartas do Scryfall para a tabela cards.'

    def add_arguments(self, parser):
        parser.add_argument('--recent', type=int, default=0,
                            help='Importa as N coleções mais recentes.')
        parser.add_argument('--sets', type=str, default='',
                            help='Lista de códigos de set separados por vírgula.')
        parser.add_argument('--max-per-set', type=int, default=0,
                            help='Limite de cartas por coleção (0 = sem limite).')
        parser.add_argument('--delay', type=float, default=0.12,
                            help='Intervalo entre requisições, em segundos.')

    def handle(self, *args, **options):
        codes = [c.strip().lower() for c in options['sets'].split(',') if c.strip()]

        if not codes:
            recent = options['recent'] or 8
            self.stdout.write(f'Buscando lista de coleções no Scryfall...')
            data = get_json(f'{SCRYFALL}/sets')
            sets = [
                s for s in data.get('data', [])
                if s.get('set_type') not in SKIP_SET_TYPES
                and s.get('card_count', 0) > 0
                and s.get('released_at')
                and s['released_at'] <= time.strftime('%Y-%m-%d')
                and not s.get('digital')
            ]
            sets.sort(key=lambda s: s['released_at'], reverse=True)
            codes = [s['code'] for s in sets[:recent]]
            self.stdout.write(f'Coleções selecionadas: {", ".join(codes)}')

        total = 0
        for code in codes:
            total += self.import_set(code, options['max_per_set'], options['delay'])

        self.stdout.write(self.style.SUCCESS(f'\nConcluído: {total} cartas gravadas.'))

    def import_set(self, code, max_per_set, delay):
        query = urllib.parse.urlencode({
            'q': f'set:{code}',
            'unique': 'prints',
            'order': 'set',
        })
        url = f'{SCRYFALL}/cards/search?{query}'
        imported = 0

        while url:
            try:
                payload = get_json(url)
            except Exception as exc:
                self.stderr.write(self.style.WARNING(f'  {code}: falha ao buscar ({exc})'))
                break

            rows = [row for row in (card_row(c) for c in payload.get('data', [])) if row]
            if max_per_set:
                rows = rows[:max(0, max_per_set - imported)]

            if rows:
                with connection.cursor() as cursor:
                    cursor.executemany(INSERT_SQL, rows)
                imported += len(rows)

            if max_per_set and imported >= max_per_set:
                break

            url = payload.get('next_page') if payload.get('has_more') else None
            time.sleep(delay)

        self.stdout.write(f'  {code.upper():<6} {imported:>5} cartas')
        return imported
