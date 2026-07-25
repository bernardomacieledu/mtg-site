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

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

SCRYFALL = 'https://api.scryfall.com'
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0', 'Accept': 'application/json'}

# Tipos de set que não interessam para o grimório
SKIP_SET_TYPES = {'token', 'memorabilia', 'minigame', 'funny', 'alchemy', 'treasure_chest'}

# Layouts que não são cartas de baralho (fichas, emblemas, séries de arte)
SKIP_LAYOUTS = {'token', 'double_faced_token', 'emblem', 'art_series', 'vanguard'}

# Teto do DECIMAL(5,1) da coluna cmc. Cartas de brincadeira (Gleemax custa
# {1000000}) estouram a coluna e derrubavam a importação inteira.
MAX_CMC = 9999.9

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


def stream_bulk_cards(url):
    """
    Percorre o array JSON gigante do bulk sem carregá-lo inteiro na memória.

    Usa raw_decode sobre um buffer deslizante, então não depende do arquivo
    estar formatado com um objeto por linha.
    """
    import gzip
    import io

    decoder = json.JSONDecoder()
    request = urllib.request.Request(url, headers={**HEADERS, 'Accept-Encoding': 'gzip'})

    with urllib.request.urlopen(request, timeout=120) as response:
        stream = response
        if response.headers.get('Content-Encoding') == 'gzip' or url.endswith('.gz'):
            stream = gzip.GzipFile(fileobj=response)

        reader = io.TextIOWrapper(stream, encoding='utf-8')
        buffer = ''
        started = False

        while True:
            chunk = reader.read(1 << 20)  # 1 MB
            if not chunk:
                break
            buffer += chunk

            if not started:
                start = buffer.find('[')
                if start == -1:
                    continue
                buffer = buffer[start + 1:]
                started = True

            while True:
                buffer = buffer.lstrip()
                if buffer[:1] in (',', ''):
                    buffer = buffer[1:]
                    if not buffer:
                        break
                    continue
                if buffer[0] == ']':
                    return
                try:
                    obj, end = decoder.raw_decode(buffer)
                except ValueError:
                    break  # objeto incompleto: espera o próximo chunk
                buffer = buffer[end:]
                yield obj


def card_row(card, apply_filters=True):
    """
    Converte um objeto do Scryfall em uma linha da tabela `cards`.

    Devolve None quando a carta não deve entrar no grimório (sem imagem, ficha,
    emblema, coleção de brincadeira ou carta digital).
    """
    if apply_filters:
        if card.get('layout') in SKIP_LAYOUTS:
            return None
        if card.get('set_type') in SKIP_SET_TYPES:
            return None
        if card.get('digital'):
            return None

    image = (card.get('image_uris') or {}).get('normal')
    faces = card.get('card_faces') or []
    if not image and faces:
        image = (faces[0].get('image_uris') or {}).get('normal')

    if not image:
        return None

    mana_cost = card.get('mana_cost') or (faces[0].get('mana_cost') if faces else '')
    oracle = card.get('oracle_text')
    if not oracle and faces:
        oracle = '\n//\n'.join(f.get('oracle_text', '') for f in faces)

    # cmc fora da faixa da coluna é limitado em vez de abortar a carga
    cmc = card.get('cmc')
    try:
        cmc = None if cmc is None else max(0.0, min(float(cmc), MAX_CMC))
    except (TypeError, ValueError):
        cmc = None

    return (
        card['id'],
        (card.get('name') or '')[:255],
        (mana_cost or '')[:50],
        cmc,
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
        parser.add_argument('--all', action='store_true',
                            help='Importa TODAS as coleções (demorado; use --bulk se possível).')
        parser.add_argument('--since', type=str, default='',
                            help='Só coleções lançadas a partir deste ano (ex: 2015).')
        parser.add_argument('--skip-existing', action='store_true',
                            help='Pula coleções que já têm cartas no banco (permite retomar).')
        parser.add_argument('--released-only', action='store_true',
                            help='Ignora coleções ainda não lançadas (por padrão elas entram).')
        parser.add_argument('--fresh', action='store_true',
                            help='Esvazia a tabela cards antes de importar (limpa cargas antigas).')
        parser.add_argument('--bulk', action='store_true',
                            help='Baixa o arquivo bulk do Scryfall: bem mais rápido para pegar tudo.')
        parser.add_argument('--sets', type=str, default='',
                            help='Lista de códigos de set separados por vírgula.')
        parser.add_argument('--max-per-set', type=int, default=0,
                            help='Limite de cartas por coleção (0 = sem limite).')
        parser.add_argument('--delay', type=float, default=0.12,
                            help='Intervalo entre requisições, em segundos.')

    rejeitadas = 0
    explicit_sets = False

    def handle(self, *args, **options):
        if options['fresh']:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM cards')
                antes = cursor.fetchone()[0]
                cursor.execute('TRUNCATE TABLE cards')
            self.stdout.write(self.style.WARNING(f'Tabela cards esvaziada ({antes} linhas removidas).'))

        if options['bulk']:
            return self.import_bulk(options)

        codes = [c.strip().lower() for c in options['sets'].split(',') if c.strip()]
        # Se o usuário pediu coleções nominalmente, respeita o pedido: não faz
        # sentido filtrar por tipo quando alguém pede explicitamente um Un-set.
        self.explicit_sets = bool(codes)

        if not codes:
            self.stdout.write('Buscando lista de coleções no Scryfall...')
            try:
                data = get_json(f'{SCRYFALL}/sets')
            except Exception as exc:
                # Sem stacktrace: em geral é rede/proxy do ambiente, não bug.
                raise CommandError(
                    f'Não foi possível falar com o Scryfall ({exc}). '
                    'Verifique a conexão do container e rode novamente: '
                    'python manage.py seed_cards --recent 8'
                ) from None

            hoje = time.strftime('%Y-%m-%d')
            sets = [
                s for s in data.get('data', [])
                if s.get('set_type') not in SKIP_SET_TYPES
                and s.get('card_count', 0) > 0
                and s.get('released_at')
                and not s.get('digital')
                # Coleções anunciadas (spoilers) entram por padrão: são o que
                # o público mais procura. --released-only volta ao antigo.
                and (not options['released_only'] or s['released_at'] <= hoje)
            ]

            futuras = [s for s in sets if s['released_at'] > hoje]
            if futuras:
                nomes = ', '.join(f"{s['code'].upper()} ({s['released_at']})" for s in futuras[:5])
                self.stdout.write(f'{len(futuras)} coleção(ões) futura(s) incluída(s): {nomes}')
            if options['since']:
                sets = [s for s in sets if s['released_at'][:4] >= options['since']]

            sets.sort(key=lambda s: s['released_at'], reverse=True)

            if options['all'] or options['since']:
                selected = sets
            else:
                selected = sets[:options['recent'] or 8]

            codes = [s['code'] for s in selected]
            self.stdout.write(f'{len(codes)} coleções selecionadas.')

        if options['skip_existing']:
            with connection.cursor() as cursor:
                cursor.execute('SELECT DISTINCT set_code FROM cards')
                existing = {row[0] for row in cursor.fetchall() if row[0]}
            antes = len(codes)
            codes = [c for c in codes if c not in existing]
            if antes != len(codes):
                self.stdout.write(f'{antes - len(codes)} coleções já no banco foram puladas.')

        total = 0
        for index, code in enumerate(codes, start=1):
            total += self.import_set(code, options['max_per_set'], options['delay'], index, len(codes))

        self.stdout.write(self.style.SUCCESS(f'\nConcluído: {total} cartas gravadas.'))

    def import_bulk(self, options):
        """
        Importa a partir do arquivo bulk do Scryfall (todas as impressões).

        É muito mais rápido do que percorrer set a set, mas o arquivo é grande
        (~2 GB descompactado), então é lido em streaming, sem carregar tudo na
        memória, e gravado em lotes.
        """
        self.stdout.write('Consultando os arquivos bulk do Scryfall...')
        try:
            catalog = get_json(f'{SCRYFALL}/bulk-data')
        except Exception as exc:
            raise CommandError(f'Não foi possível listar os arquivos bulk ({exc}).') from None

        entry = next((item for item in catalog.get('data', [])
                      if item.get('type') == 'default_cards'), None)
        if not entry:
            raise CommandError('Arquivo "default_cards" não encontrado no catálogo do Scryfall.')

        size_mb = entry.get('size', 0) / (1024 * 1024)
        self.stdout.write(f'Baixando {entry["download_uri"]} (~{size_mb:.0f} MB). '
                          'Isso leva alguns minutos.')

        batch, imported, seen = [], 0, 0
        for card in stream_bulk_cards(entry['download_uri']):
            seen += 1
            row = card_row(card)
            if row:
                batch.append(row)
            if len(batch) >= 1000:
                imported += self.flush(batch)
                batch = []
                self.stdout.write(f'  {imported} cartas gravadas ({seen} lidas)...')
        imported += self.flush(batch)

        resumo = f'\nConcluído: {imported} cartas gravadas de {seen} lidas.'
        if self.rejeitadas:
            resumo += f' {self.rejeitadas} ignoradas por dados inválidos.'
        self.stdout.write(self.style.SUCCESS(resumo))

    def flush(self, batch):
        """
        Grava o lote. Se alguma linha for rejeitada pelo MySQL, reprocessa o
        lote linha a linha para salvar o resto — antes, um único registro
        problemático abortava a importação inteira.
        """
        if not batch:
            return 0
        try:
            with connection.cursor() as cursor:
                cursor.executemany(INSERT_SQL, batch)
            return len(batch)
        except Exception as exc:
            self.stdout.write(self.style.WARNING(
                f'  lote rejeitado ({exc}); gravando linha a linha...'))
            gravadas = 0
            for row in batch:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(INSERT_SQL, row)
                    gravadas += 1
                except Exception as row_exc:
                    self.rejeitadas += 1
                    if self.rejeitadas <= 5:
                        self.stdout.write(self.style.WARNING(
                            f'    ignorada: {row[1]!r} ({row_exc})'))
            return gravadas

    def import_set(self, code, max_per_set, delay, index=1, total_sets=1):
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

            rows = [row for row in
                    (card_row(c, apply_filters=not self.explicit_sets)
                     for c in payload.get('data', []))
                    if row]
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

        self.stdout.write(f'  [{index}/{total_sets}] {code.upper():<6} {imported:>5} cartas')
        return imported
