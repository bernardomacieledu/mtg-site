"""
Importa preços por impressão do MTGJSON.

Duas etapas, porque o MTGJSON indexa preços pelo seu próprio `uuid`:

  1. Para cada coleção presente no banco, baixa o arquivo da coleção
     (https://mtgjson.com/api/v5/<SET>.json) e monta o mapa uuid -> scryfall_id.
  2. Baixa AllPricesToday.json em streaming e grava apenas os uuids mapeados.

Uso:
    python manage.py seed_prices                # todas as coleções do banco
    python manage.py seed_prices --sets blb,dom  # apenas algumas
"""
import json
import time
import urllib.request

from django.core.management.base import BaseCommand, CommandError
from django.db import connection

from mtg_api.models import CardPrice

MTGJSON = 'https://mtgjson.com/api/v5'
HEADERS = {'User-Agent': 'MTGNexus-Seed/1.0', 'Accept': 'application/json'}


def stream_json_object_items(url, timeout=180):
    """
    Percorre os pares chave/valor de um objeto JSON gigante sem carregá-lo na
    memória. AllPricesToday.json passa de 100 MB e é um objeto, não uma lista.
    """
    import gzip
    import io

    decoder = json.JSONDecoder()
    pedido = urllib.request.Request(url, headers={**HEADERS, 'Accept-Encoding': 'gzip'})

    with urllib.request.urlopen(pedido, timeout=timeout) as resposta:
        fluxo = resposta
        if resposta.headers.get('Content-Encoding') == 'gzip' or url.endswith('.gz'):
            fluxo = gzip.GzipFile(fileobj=resposta)

        leitor = io.TextIOWrapper(fluxo, encoding='utf-8')
        buffer = ''
        dentro_de_data = False

        while True:
            pedaco = leitor.read(1 << 20)
            if not pedaco:
                break
            buffer += pedaco

            # Pula tudo até o início do objeto "data"
            if not dentro_de_data:
                marca = buffer.find('"data"')
                if marca == -1:
                    buffer = buffer[-32:]      # guarda o fim, a marca pode estar cortada
                    continue
                abre = buffer.find('{', marca)
                if abre == -1:
                    continue
                buffer = buffer[abre + 1:]
                dentro_de_data = True

            while True:
                buffer = buffer.lstrip()
                if buffer[:1] in (',', ''):
                    buffer = buffer[1:]
                    if not buffer:
                        break
                    continue
                if buffer[0] == '}':
                    return
                if buffer[0] != '"':
                    break
                try:
                    chave, fim = decoder.raw_decode(buffer)
                except ValueError:
                    break
                resto = buffer[fim:].lstrip()
                if not resto.startswith(':'):
                    break
                resto = resto[1:].lstrip()
                try:
                    valor, fim_valor = decoder.raw_decode(resto)
                except ValueError:
                    break                      # valor incompleto: espera mais dados
                buffer = resto[fim_valor:]
                yield chave, valor


def preco_mais_recente(bloco):
    """Extrai o preço mais recente de um bloco retail do MTGJSON."""
    if not isinstance(bloco, dict) or not bloco:
        return None
    data = max(bloco.keys())
    try:
        return round(float(bloco[data]), 2), data
    except (TypeError, ValueError):
        return None


class Command(BaseCommand):
    help = 'Importa preços por impressão a partir do MTGJSON.'

    def add_arguments(self, parser):
        parser.add_argument('--sets', type=str, default='',
                            help='Códigos de coleção separados por vírgula.')
        parser.add_argument('--delay', type=float, default=0.1)

    def handle(self, *args, **options):
        if options['sets']:
            codigos = [c.strip().lower() for c in options['sets'].split(',') if c.strip()]
        else:
            with connection.cursor() as cursor:
                cursor.execute('SELECT DISTINCT set_code FROM cards WHERE set_code IS NOT NULL')
                codigos = [linha[0].lower() for linha in cursor.fetchall() if linha[0]]

        if not codigos:
            raise CommandError('Nenhuma coleção no banco. Rode seed_cards primeiro.')

        self.stdout.write(f'[1/2] Montando mapa uuid -> scryfall_id de {len(codigos)} coleção(ões)...')
        mapa = {}
        ausentes = []
        for indice, codigo in enumerate(codigos, start=1):
            try:
                pedido = urllib.request.Request(f'{MTGJSON}/{codigo.upper()}.json', headers=HEADERS)
                with urllib.request.urlopen(pedido, timeout=60) as resposta:
                    dados = json.loads(resposta.read())
            except Exception:
                ausentes.append(codigo)
                continue

            for carta in dados.get('data', {}).get('cards', []):
                scryfall = (carta.get('identifiers') or {}).get('scryfallId')
                if scryfall and carta.get('uuid'):
                    mapa[carta['uuid']] = scryfall

            if indice % 10 == 0:
                self.stdout.write(f'   {indice}/{len(codigos)} coleções, {len(mapa)} cartas mapeadas')
            time.sleep(options['delay'])

        if ausentes:
            self.stdout.write(self.style.WARNING(
                f'   {len(ausentes)} coleção(ões) sem arquivo no MTGJSON: {", ".join(ausentes[:8])}'))
        if not mapa:
            raise CommandError('Nenhuma carta mapeada; não há como associar os preços.')

        self.stdout.write(f'[2/2] Lendo AllPricesToday.json ({len(mapa)} cartas de interesse)...')
        registros, lidos = [], 0
        try:
            for uuid, bloco in stream_json_object_items(f'{MTGJSON}/AllPricesToday.json'):
                lidos += 1
                scryfall = mapa.get(uuid)
                if not scryfall:
                    continue

                papel = (bloco or {}).get('paper', {})
                tcg = (papel.get('tcgplayer') or {}).get('retail', {})
                mkm = (papel.get('cardmarket') or {}).get('retail', {})

                usd      = preco_mais_recente(tcg.get('normal'))
                usd_foil = preco_mais_recente(tcg.get('foil'))
                eur      = preco_mais_recente(mkm.get('normal'))
                eur_foil = preco_mais_recente(mkm.get('foil'))

                if not any([usd, usd_foil, eur, eur_foil]):
                    continue

                registros.append(CardPrice(
                    scryfall_id=scryfall, mtgjson_uuid=uuid,
                    usd=usd[0] if usd else None,
                    usd_foil=usd_foil[0] if usd_foil else None,
                    eur=eur[0] if eur else None,
                    eur_foil=eur_foil[0] if eur_foil else None,
                    price_date=(usd or usd_foil or eur or eur_foil)[1],
                ))

                if len(registros) >= 1000:
                    self.gravar(registros)
                    self.stdout.write(f'   {lidos} lidas, gravando...')
                    registros = []
        except Exception as exc:
            raise CommandError(f'Falha ao ler os preços ({exc}).') from None

        self.gravar(registros)
        total = CardPrice.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'Concluído: {total} impressões com preço no banco (de {lidos} lidas no arquivo).'))

    def gravar(self, registros):
        if not registros:
            return
        CardPrice.objects.bulk_create(
            registros, update_conflicts=True,
            update_fields=['mtgjson_uuid', 'usd', 'usd_foil', 'eur', 'eur_foil', 'price_date'],
        )
