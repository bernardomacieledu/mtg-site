import math
from django.db import connection
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Card, Rule
from .scryfall import get_set_names, get_mana_map, get_usd_brl_rate


# Habilidades reconhecidas no filtro -> termo procurado no texto da carta.
#
# Nada de REGEXP aqui: o MySQL 8 trocou o motor de expressões regulares para
# ICU e deixou de aceitar [[:<:]]/[[:>:]], que o MariaDB ainda aceita. Em vez de
# depender da engine, a busca normaliza a pontuação e procura o termo cercado
# de espaços — comportamento idêntico nos dois bancos.
KEYWORDS = {
    'flying':         'flying',
    'first strike':   'first strike',
    'double strike':  'double strike',
    'deathtouch':     'deathtouch',
    'lifelink':       'lifelink',
    'trample':        'trample',
    'haste':          'haste',
    'vigilance':      'vigilance',
    'reach':          'reach',
    'menace':         'menace',
    'hexproof':       'hexproof',
    'shroud':         'shroud',
    'indestructible': 'indestructible',
    'defender':       'defender',
    'flash':          'flash',
    'ward':           'ward',
    'prowess':        'prowess',
}

# Troca quebras de linha e pontuação por espaço e cerca o texto de espaços,
# para "Flying" casar em "Flying, vigilance" e "Reach, deathtouch." sem casar
# com palavras que apenas contenham o termo.
TEXTO_NORMALIZADO = (
    "CONCAT(' ', REPLACE(REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
    "COALESCE(oracle_text,''), '\\n', ' '), ',', ' '), '.', ' '), ';', ' '), "
    "':', ' '), '—', ' '), ' ')"
)


def _safe_int(value, default, minimum=None, maximum=None):
    """Converte para int sem estourar 500 quando o usuário manda lixo na query string."""
    try:
        result = int(value)
    except (TypeError, ValueError):
        return default
    if minimum is not None:
        result = max(minimum, result)
    if maximum is not None:
        result = min(maximum, result)
    return result


def _is_iso_date(value):
    import datetime
    if not value:
        return False
    try:
        datetime.date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def _safe_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _build_where(search='', set_code='', rarity='', card_type='', cmc='', cmc_op='=',
                 date_from='', date_to='', colors='', extra=None):
    where  = ['image_url_normal IS NOT NULL']
    params = []

    if search:
        where.append('(name LIKE %s OR oracle_text LIKE %s)')
        params += [f'%{search}%', f'%{search}%']
    if set_code:
        where.append('set_code = %s')
        params.append(set_code)
    if rarity:
        where.append('rarity = %s')
        params.append(rarity)
    if card_type:
        where.append('type_line LIKE %s')
        params.append(f'%{card_type}%')
    cmc_value = _safe_float(cmc) if cmc not in ('', None) else None
    if cmc_value is not None:
        op = cmc_op if cmc_op in ('=', '<=', '>=', '<', '>') else '='
        where.append(f'cmc {op} %s')
        params.append(cmc_value)
    if _is_iso_date(date_from):
        where.append('release_date >= %s')
        params.append(date_from)
    if _is_iso_date(date_to):
        where.append('release_date <= %s')
        params.append(date_to)

    opcoes = extra or {}

    if colors:
        # 'and' = precisa ter todas as cores marcadas (padrão); 'or' = qualquer uma
        juncao = ' OR ' if opcoes.get('color_mode', 'and').lower() == 'or' else ' AND '
        clausulas, valores = [], []
        for col in colors.split(','):
            # O front envia "{W},{U}"; aceita também "W,U" para uso direto da API.
            col = col.strip().upper().strip('{}')
            if col in ('W', 'U', 'B', 'R', 'G'):
                # Casa o símbolo exato ({W}) e híbridos ({W/U}, {2/W})
                clausulas.append('(mana_cost LIKE %s OR mana_cost LIKE %s OR mana_cost LIKE %s)')
                valores += [f'%{{{col}}}%', f'%{{{col}/%', f'%/{col}}}%']
            elif col == 'C':
                clausulas.append("(mana_cost IS NULL OR mana_cost = '' OR "
                                 "mana_cost NOT REGEXP '\\{(W|U|B|R|G)')")
        if clausulas:
            where.append('(' + juncao.join(clausulas) + ')')
            params += valores

    if opcoes.get('legendary') in ('1', 'true', 'True'):
        where.append('type_line LIKE %s')
        params.append('%Legendary%')

    if opcoes.get('nonlegendary') in ('1', 'true', 'True'):
        where.append('(type_line IS NULL OR type_line NOT LIKE %s)')
        params.append('%Legendary%')

    # Habilidades de palavra-chave, buscadas no texto de regras da carta
    palavras = [k.strip().lower() for k in (opcoes.get('keywords') or '').split(',') if k.strip()]
    if palavras:
        juncao_kw = ' OR ' if opcoes.get('keyword_mode', 'and').lower() == 'or' else ' AND '
        partes = []
        for palavra in palavras[:8]:
            termo = KEYWORDS.get(palavra)
            if termo:
                partes.append(f'{TEXTO_NORMALIZADO} LIKE %s')
                params.append(f'% {termo} %')
        if partes:
            where.append('(' + juncao_kw.join(partes) + ')')

    return ' AND '.join(where), params


def _fetch_grouped(where_sql, params, limit, offset, order_by='MAX(release_date) DESC'):
    sql = f"""
        SELECT name,
               MAX(mana_cost)        AS mana_cost,
               MAX(cmc)              AS cmc,
               MAX(type_line)        AS type_line,
               MAX(oracle_text)      AS oracle_text,
               MAX(rarity)           AS rarity,
               SUBSTRING_INDEX(GROUP_CONCAT(image_url_normal ORDER BY release_date DESC), ',', 1) AS image_url_normal,
               GROUP_CONCAT(DISTINCT set_code ORDER BY release_date DESC) AS set_codes,
               GROUP_CONCAT(CONCAT(set_code, '|', scryfall_id)
                            ORDER BY release_date DESC) AS impressoes,
               MAX(release_date)     AS latest_release,
               MIN(release_date)     AS first_release
        FROM cards WHERE {where_sql}
        GROUP BY name ORDER BY {order_by}
        LIMIT %s OFFSET %s
    """
    with connection.cursor() as cur:
        cur.execute(sql, params + [limit, offset])
        cols = [c[0] for c in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def _count_grouped(where_sql, params):
    with connection.cursor() as cur:
        cur.execute(f'SELECT COUNT(DISTINCT name) FROM cards WHERE {where_sql}', params)
        return cur.fetchone()[0]


def _precos_por_impressao(raw_cards):
    """Uma única consulta para os preços de todas as impressões da página."""
    ids = set()
    for c in raw_cards:
        for par in (c.get('impressoes') or '').split(','):
            if '|' in par:
                ids.add(par.split('|', 1)[1])
    if not ids:
        return {}

    from .models import CardPrice
    return {
        registro['scryfall_id']: registro
        for registro in CardPrice.objects.filter(scryfall_id__in=ids)
                                         .values('scryfall_id', 'usd', 'usd_foil', 'eur')
    }


def _enrich(raw_cards, set_names):
    precos = _precos_por_impressao(raw_cards)
    cotacao = get_usd_brl_rate()

    def valores(scryfall_id):
        registro = precos.get(scryfall_id)
        if not registro:
            return None
        usd = float(registro['usd']) if registro['usd'] is not None else None
        saida = {
            'usd':      usd,
            'usd_foil': float(registro['usd_foil']) if registro['usd_foil'] is not None else None,
            'eur':      float(registro['eur']) if registro['eur'] is not None else None,
        }
        # Estimativa: convertida da cotação do dia, não é preço de mercado local
        saida['brl'] = round(usd * cotacao, 2) if (usd is not None and cotacao) else None
        return saida

    cards = []
    for c in raw_cards:
        # set_code -> scryfall_id da impressão daquele set
        ids_por_set = {}
        for par in (c.get('impressoes') or '').split(','):
            if '|' in par:
                codigo, scryfall_id = par.split('|', 1)
                ids_por_set.setdefault(codigo, scryfall_id)

        set_codes = (c['set_codes'] or '').split(',')
        sets = []
        for code in set_codes:
            info = set_names.get(code, {})
            scryfall_id = ids_por_set.get(code)
            sets.append({
                'code':         code,
                'name':         info.get('name', code),
                'released_at':  info.get('released_at', ''),
                'icon_svg_uri': info.get('icon_svg_uri',
                    f'https://svgs.scryfall.io/sets/{code.lower()}.svg'),
                'scryfall_id':  scryfall_id,
                'prices':       valores(scryfall_id) if scryfall_id else None,
            })
        cards.append({
            'name':             c['name'],
            'mana_cost':        c['mana_cost'] or '',
            'cmc':              float(c['cmc']) if c['cmc'] is not None else None,
            'type_line':        c['type_line'] or '',
            'oracle_text':      c['oracle_text'] or '',
            'rarity':           c['rarity'] or 'common',
            'image_url_normal': c['image_url_normal'],
            'sets':             sets,
            # preço da impressão mais recente, exibido antes de trocar de versão
            'prices':           sets[0]['prices'] if sets else None,
            'usd_brl':          cotacao,
            'latest_release':   str(c['latest_release']) if c['latest_release'] else None,
            'first_release':    str(c['first_release']) if c['first_release'] else None,
        })
    return cards


class CardListView(APIView):
    def get(self, request):
        p         = request.query_params
        search    = p.get('q', '').strip()
        set_code  = p.get('set', '').strip()
        rarity    = p.get('rarity', '').strip()
        card_type = p.get('type', '').strip()
        cmc       = p.get('cmc', '').strip()
        cmc_op    = p.get('cmc_op', '=').strip()
        date_from = p.get('date_from', '').strip()
        date_to   = p.get('date_to', '').strip()
        page      = _safe_int(p.get('page', 1), 1, minimum=1)
        page_size = _safe_int(p.get('page_size', 24), 24, minimum=1, maximum=48)

        colors    = p.get('colors', '').strip()
        sort = p.get('sort', 'release_desc')
        ordem = {
            'name':         'name ASC',
            'name_desc':    'name DESC',
            'cmc_desc':     'MAX(cmc) DESC, name ASC',
            'cmc_asc':      'MAX(cmc) ASC, name ASC',
            'rarity_desc':  "MIN(FIELD(rarity,'mythic','rare','uncommon','common')) ASC, name ASC",
            'rarity_asc':   "MIN(FIELD(rarity,'common','uncommon','rare','mythic')) ASC, name ASC",
            'release_desc': 'MAX(release_date) DESC',
            'release_asc':  'MIN(release_date) ASC',
        }.get(sort, 'MAX(release_date) DESC')

        where_sql, params = _build_where(
            search, set_code, rarity, card_type, cmc, cmc_op, date_from, date_to, colors,
            extra=p,
        )
        total  = _count_grouped(where_sql, params)
        offset = (page - 1) * page_size

        set_names = get_set_names()
        raw   = _fetch_grouped(where_sql, params, page_size, offset, ordem)
        cards = _enrich(raw, set_names)

        return Response({
            'count':       total,
            'total_pages': math.ceil(total / page_size) if total else 1,
            'page':        page,
            'page_size':   page_size,
            'results':     cards,
        })


class CardImagesView(APIView):
    def get(self, request):
        name = request.query_params.get('name', '').strip()
        if not name:
            return Response({'images': []})

        rows = Card.objects.filter(name=name, image_url_normal__isnull=False) \
            .values('scryfall_id', 'set_code', 'image_url_normal', 'release_date',
                    'mana_cost', 'cmc', 'type_line', 'oracle_text', 'rarity') \
            .order_by('-release_date')

        set_names = get_set_names()
        images = []
        for c in rows:
            info = set_names.get(c['set_code'], {})
            images.append({
                # necessário para consultar o preço desta impressão específica
                'scryfall_id': c['scryfall_id'],
                'set_code':    c['set_code'],
                'set_name':    info.get('name', c['set_code']),
                'released_at': info.get('released_at', str(c['release_date']) if c['release_date'] else ''),
                'icon_svg_uri': info.get('icon_svg_uri',
                    f"https://svgs.scryfall.io/sets/{c['set_code'].lower()}.svg"),
                'image_url':   c['image_url_normal'],
                'mana_cost':   c['mana_cost'] or '',
                'cmc':         float(c['cmc']) if c['cmc'] is not None else None,
                'type_line':   c['type_line'] or '',
                'oracle_text': c['oracle_text'] or '',
                'rarity':      c['rarity'] or 'common',
            })

        return Response({'name': name, 'images': images})


class CollectionsView(APIView):
    """
    GET /api/collections/
    Lista as coleções (sets) disponíveis no banco.

    Query params:
      q       — busca por nome ou código do set
      limit   — nº de sets no bloco "latest" (padrão 12)
      year    — filtra por ano de lançamento
    """

    def get(self, request):
        q     = request.query_params.get('q', '').strip().lower()
        year  = request.query_params.get('year', '').strip()
        limit = _safe_int(request.query_params.get('limit', 12), 12, minimum=1, maximum=60)

        with connection.cursor() as cur:
            cur.execute("""
                SELECT set_code,
                       COUNT(*)                AS total,
                       COUNT(DISTINCT name)    AS uniques,
                       MIN(release_date)       AS release_date
                FROM cards
                WHERE image_url_normal IS NOT NULL
                GROUP BY set_code
                ORDER BY release_date DESC
            """)
            rows = cur.fetchall()

        set_names = get_set_names()
        sets = []
        for set_code, count, uniques, release_date in rows:
            info = set_names.get(set_code, {})
            name = info.get('name', set_code)
            released = info.get('released_at') or (str(release_date) if release_date else '')
            if q and q not in name.lower() and q not in (set_code or '').lower():
                continue
            if year and not released.startswith(year):
                continue
            sets.append({
                'code':         set_code,
                'name':         name,
                'set_type':     info.get('set_type', ''),
                'released_at':  released,
                'icon_svg_uri': info.get('icon_svg_uri',
                    f'https://svgs.scryfall.io/sets/{(set_code or "").lower()}.svg'),
                'card_count':   count,
                'unique_count': uniques,
            })

        # Ordena por data de lançamento (mais recentes primeiro), sem depender do MIN do banco
        sets.sort(key=lambda item: item['released_at'] or '', reverse=True)

        import datetime
        hoje = datetime.date.today().isoformat()
        for item in sets:
            item['is_upcoming'] = bool(item['released_at']) and item['released_at'] > hoje

        upcoming = [item for item in sets if item['is_upcoming']]
        lancadas = [item for item in sets if not item['is_upcoming']]
        # As futuras vão em ordem cronológica: a que chega primeiro no topo
        upcoming.reverse()

        by_year = {}
        for item in sets:
            key = item['released_at'][:4] if item['released_at'] else 'Desconhecido'
            by_year.setdefault(key, []).append(item)

        years = [{'year': y, 'sets': sl} for y, sl in sorted(by_year.items(), reverse=True)]

        return Response({
            'total_sets':     len(sets),
            'total_cards':    sum(item['card_count'] for item in sets),
            'upcoming':       upcoming,
            'latest':         lancadas[:limit],
            'available_years': [y['year'] for y in years],
            'years':          years,
        })


class SetDetailView(APIView):
    """GET /api/collections/<code>/ — resumo de uma coleção específica."""

    def get(self, request, code):
        code = (code or '').strip()
        with connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*)             AS total,
                       COUNT(DISTINCT name) AS uniques,
                       MIN(release_date)    AS released,
                       AVG(cmc)             AS avg_cmc
                FROM cards
                WHERE set_code = %s AND image_url_normal IS NOT NULL
            """, [code])
            total, uniques, released, avg_cmc = cur.fetchone()

            cur.execute("""
                SELECT rarity, COUNT(*) FROM cards
                WHERE set_code = %s AND image_url_normal IS NOT NULL
                GROUP BY rarity
            """, [code])
            rarities = {row[0] or 'common': row[1] for row in cur.fetchall()}

        if not total:
            return Response({'error': 'Coleção não encontrada.'}, status=404)

        import datetime
        info = get_set_names().get(code, {})
        released_at = info.get('released_at') or (str(released) if released else '')
        return Response({
            'is_upcoming':  bool(released_at) and released_at > datetime.date.today().isoformat(),
            'code':         code,
            'name':         info.get('name', code),
            'released_at':  info.get('released_at') or (str(released) if released else ''),
            'icon_svg_uri': info.get('icon_svg_uri',
                f'https://svgs.scryfall.io/sets/{code.lower()}.svg'),
            'card_count':   total,
            'unique_count': uniques,
            'avg_cmc':      round(float(avg_cmc), 2) if avg_cmc is not None else 0,
            'rarities':     rarities,
        })


class RulesView(APIView):
    CHAPTER_NAMES = {
        '1': 'Game Concepts',        '2': 'Parts of a Card',
        '3': 'Card Types',           '4': 'Zones',
        '5': 'Turn Structure',       '6': 'Spells, Abilities & Effects',
        '7': 'Additional Rules',     '8': 'Multiplayer Rules',
        '9': 'Casual Variants',
    }

    def get(self, request):
        search  = request.query_params.get('q', '').strip()
        chapter = request.query_params.get('chapter', '').strip()
        qs = Rule.objects.all()
        if search:
            qs = qs.filter(Q(rule_text__icontains=search) | Q(rule_number__icontains=search))
        if chapter:
            qs = qs.filter(chapter_id=chapter)

        chapters = {}
        for rule in qs:
            ch = rule.chapter_id or rule.rule_number.split('.')[0]
            if ch not in chapters:
                chapters[ch] = {'number': ch, 'title': self.CHAPTER_NAMES.get(ch, f'Capítulo {ch}'), 'rules': []}
            chapters[ch]['rules'].append({'id': rule.id, 'rule_number': rule.rule_number, 'rule_text': rule.rule_text})

        chapters_list = sorted(chapters.values(), key=lambda x: int(x['number']) if x['number'].isdigit() else 999)
        return Response({'total': qs.count(), 'search': search, 'chapters': chapters_list})


@api_view(['GET'])
def mana_symbols(request):
    return Response({'symbols': get_mana_map()})


@api_view(['GET'])
def sets_filter_list(request):
    set_names = get_set_names()
    db_codes  = Card.objects.filter(image_url_normal__isnull=False) \
        .values_list('set_code', flat=True).distinct()
    sets = []
    for code in db_codes:
        info = set_names.get(code, {})
        sets.append({'code': code, 'name': info.get('name', code), 'released_at': info.get('released_at', '')})
    sets.sort(key=lambda x: x['released_at'], reverse=True)
    return Response({'sets': sets})


@api_view(['GET'])
def card_types_list(request):
    """Retorna os tipos únicos disponíveis no banco."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT DISTINCT
                CASE
                    WHEN type_line LIKE '%Creature%'     THEN 'Creature'
                    WHEN type_line LIKE '%Planeswalker%' THEN 'Planeswalker'
                    WHEN type_line LIKE '%Instant%'      THEN 'Instant'
                    WHEN type_line LIKE '%Sorcery%'      THEN 'Sorcery'
                    WHEN type_line LIKE '%Enchantment%'  THEN 'Enchantment'
                    WHEN type_line LIKE '%Artifact%'     THEN 'Artifact'
                    WHEN type_line LIKE '%Land%'         THEN 'Land'
                    WHEN type_line LIKE '%Battle%'       THEN 'Battle'
                    ELSE 'Other'
                END as main_type
            FROM cards
            WHERE image_url_normal IS NOT NULL
            ORDER BY main_type
        """)
        types = [row[0] for row in cur.fetchall() if row[0] != 'Other']
    return Response({'types': types})


@api_view(['GET'])
def card_prices(request):
    """
    GET /api/cards/prices/?id=<scryfall_id>&name=<nome>

    Com `id`, devolve o preço daquela impressão específica, lido da tabela
    alimentada pelo MTGJSON (`manage.py seed_prices`). Antes a consulta era
    sempre por nome e trazia o preço da impressão padrão, ignorando qual
    versão o usuário estava vendo.
    """
    import json as _json, urllib.request as _req, urllib.parse as _parse

    scryfall_id = request.query_params.get('id', '').strip()
    if scryfall_id:
        from .models import CardPrice
        registro = CardPrice.objects.filter(scryfall_id=scryfall_id).first()
        if registro:
            precos = {}
            if registro.usd is not None:      precos['usd'] = str(registro.usd)
            if registro.usd_foil is not None: precos['usd_foil'] = str(registro.usd_foil)
            if registro.eur is not None:      precos['eur'] = str(registro.eur)
            if registro.eur_foil is not None: precos['eur_foil'] = str(registro.eur_foil)
            if precos:
                return Response({'prices': precos, 'source': 'mtgjson',
                                 'price_date': registro.price_date})

    name = request.query_params.get('name', '').strip()
    if not name:
        return Response({'prices': None})
    try:
        encoded = _parse.urlencode({'exact': name}).replace('+', '%20')
        url = f"https://api.scryfall.com/cards/named?{encoded}"
        req = _req.Request(url, headers={'User-Agent': 'MTGNexus/1.0'})
        with _req.urlopen(req, timeout=8) as resp:
            data = _json.loads(resp.read())
        prices = {k: v for k, v in data.get('prices', {}).items() if v is not None}
        return Response({'prices': prices, 'name': name, 'source': 'scryfall'})
    except Exception as e:
        return Response({'prices': None, 'error': str(e)})


@api_view(['GET'])
def health(request):
    """
    GET /api/health/ — estado do serviço e progresso da carga inicial.

    Serve para acompanhar o seed sem ficar lendo o log do container.
    """
    import os

    payload = {'status': 'ok', 'database': 'ok'}
    try:
        with connection.cursor() as cur:
            cur.execute('SELECT COUNT(*) FROM cards')
            payload['cards'] = cur.fetchone()[0]
            cur.execute('SELECT COUNT(DISTINCT set_code) FROM cards')
            payload['sets'] = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM rules')
            payload['rules'] = cur.fetchone()[0]
    except Exception as exc:
        payload['status'] = 'degraded'
        payload['database'] = f'erro: {exc}'
        return Response(payload, status=503)

    expected = int(os.environ.get('SEED_RECENT_SETS', 8))
    if payload['cards'] == 0:
        payload['seed'] = 'sem cartas — a importação pode estar em andamento ou ter falhado'
    elif payload['sets'] < expected:
        payload['seed'] = f"em andamento: {payload['sets']} de ~{expected} coleções importadas"
    else:
        payload['seed'] = 'concluído'

    return Response(payload)
