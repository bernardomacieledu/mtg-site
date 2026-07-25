import math
from django.db import connection
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Card, Rule
from .scryfall import get_set_names, get_mana_map


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


def _build_where(search='', set_code='', rarity='', card_type='', cmc='', cmc_op='=', date_from='', date_to='', colors=''):
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

    if colors:
        for col in colors.split(','):
            col = col.strip().upper()
            if col in ('W', 'U', 'B', 'R', 'G'):
                # Casa o símbolo exato ({W}) e híbridos ({W/U}, {2/W}) — antes um
                # LIKE '%W%' solto casava com qualquer texto que tivesse a letra.
                where.append("(mana_cost LIKE %s OR mana_cost LIKE %s OR mana_cost LIKE %s)")
                params += [f'%{{{col}}}%', f'%{{{col}/%', f'%/{col}}}%']
            elif col == 'C':
                where.append("(mana_cost IS NULL OR mana_cost = '' OR "
                             "mana_cost NOT REGEXP '\\{(W|U|B|R|G)')")
    return ' AND '.join(where), params


def _fetch_grouped(where_sql, params, limit, offset):
    sql = f"""
        SELECT name,
               MAX(mana_cost)        AS mana_cost,
               MAX(cmc)              AS cmc,
               MAX(type_line)        AS type_line,
               MAX(oracle_text)      AS oracle_text,
               MAX(rarity)           AS rarity,
               SUBSTRING_INDEX(GROUP_CONCAT(image_url_normal ORDER BY release_date DESC), ',', 1) AS image_url_normal,
               GROUP_CONCAT(DISTINCT set_code ORDER BY release_date DESC) AS set_codes,
               MAX(release_date)     AS latest_release,
               MIN(release_date)     AS first_release
        FROM cards WHERE {where_sql}
        GROUP BY name ORDER BY MAX(release_date) DESC
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


def _enrich(raw_cards, set_names):
    cards = []
    for c in raw_cards:
        set_codes = (c['set_codes'] or '').split(',')
        sets = []
        for code in set_codes:
            info = set_names.get(code, {})
            sets.append({
                'code':         code,
                'name':         info.get('name', code),
                'released_at':  info.get('released_at', ''),
                'icon_svg_uri': info.get('icon_svg_uri',
                    f'https://svgs.scryfall.io/sets/{code.lower()}.svg'),
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
        where_sql, params = _build_where(search, set_code, rarity, card_type, cmc, cmc_op, date_from, date_to, colors)
        total  = _count_grouped(where_sql, params)
        offset = (page - 1) * page_size

        set_names = get_set_names()
        raw   = _fetch_grouped(where_sql, params, page_size, offset)
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
            .values('set_code', 'image_url_normal', 'release_date',
                    'mana_cost', 'cmc', 'type_line', 'oracle_text', 'rarity') \
            .order_by('-release_date')

        set_names = get_set_names()
        images = []
        for c in rows:
            info = set_names.get(c['set_code'], {})
            images.append({
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

        by_year = {}
        for item in sets:
            key = item['released_at'][:4] if item['released_at'] else 'Desconhecido'
            by_year.setdefault(key, []).append(item)

        years = [{'year': y, 'sets': sl} for y, sl in sorted(by_year.items(), reverse=True)]

        return Response({
            'total_sets':     len(sets),
            'total_cards':    sum(item['card_count'] for item in sets),
            'latest':         sets[:limit],
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

        info = get_set_names().get(code, {})
        return Response({
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
    import json as _json, urllib.request as _req, urllib.parse as _parse
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
        return Response({'prices': prices, 'name': name})
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
