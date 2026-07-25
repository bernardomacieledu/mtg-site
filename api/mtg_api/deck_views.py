"""
deck_views.py — Importação/exportação de decks e coleções usando o banco local
"""
import json
import re
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection


def fetch_card_local(name: str) -> dict | None:
    """Busca carta no banco local pelo nome exato (case-insensitive)."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT name, mana_cost, cmc, type_line, oracle_text, rarity,
                   image_url_normal, set_code, release_date, scryfall_id
            FROM cards
            WHERE LOWER(name) = LOWER(%s) AND image_url_normal IS NOT NULL
            ORDER BY release_date DESC
            LIMIT 1
        """, [name])
        row = cur.fetchone()
        if not row:
            return None
        cols = ['name','mana_cost','cmc','type_line','oracle_text','rarity',
                'image_url_normal','set_code','release_date','scryfall_id']
        return dict(zip(cols, row))


def fetch_all_prints_local(name: str) -> list:
    """Busca todas as impressões de uma carta no banco."""
    with connection.cursor() as cur:
        cur.execute("""
            SELECT name, mana_cost, cmc, type_line, oracle_text, rarity,
                   image_url_normal, set_code, release_date, scryfall_id
            FROM cards
            WHERE LOWER(name) = LOWER(%s) AND image_url_normal IS NOT NULL
            ORDER BY release_date DESC
        """, [name])
        cols = ['name','mana_cost','cmc','type_line','oracle_text','rarity',
                'image_url_normal','set_code','release_date','scryfall_id']
        return [dict(zip(cols, row)) for row in cur.fetchall()]


def classify_card(type_line: str) -> str:
    if not type_line: return 'other'
    if 'Creature'     in type_line: return 'creature'
    if 'Artifact'     in type_line: return 'artifact'
    if 'Land'         in type_line: return 'land'
    if 'Enchantment'  in type_line: return 'enchantment'
    if 'Planeswalker' in type_line: return 'planeswalker'
    if 'Instant'      in type_line: return 'instant'
    if 'Sorcery'      in type_line: return 'sorcery'
    return 'other'


def is_legendary(type_line: str) -> bool:
    """Qualquer permanente lendário pode ser comandante."""
    return bool(type_line and 'Legendary' in type_line)


QTY_RE = re.compile(r'^(?:(\d+)\s*[xX]?\s+)?(.+?)$')


def parse_deck_text(text: str) -> list:
    """
    Aceita os formatos mais comuns de decklist:
        4 Lightning Bolt
        4x Lightning Bolt
        Lightning Bolt              (sem quantidade -> 1)
        1 Sol Ring (LTR) 123        (código de set/número são ignorados)
        SB: 2 Duress                (sideboard)
        // comentário  ou  # comentário
    """
    entries = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith(('//', '#')):
            continue

        # remove marcadores de seção usados por sites de deck
        low = line.lower()
        if low in ('deck', 'sideboard', 'commander', 'maybeboard', 'companion'):
            continue
        for prefix in ('SB:', 'sb:', 'MB:', 'mb:'):
            if line.startswith(prefix):
                line = line[len(prefix):].strip()

        match = QTY_RE.match(line)
        if not match:
            continue

        qty  = int(match.group(1)) if match.group(1) else 1
        name = match.group(2).strip()

        # tira sufixos "(SET) 123", "[SET]" e números de coleção soltos no fim
        name = re.sub(r'\s*[\(\[][A-Za-z0-9]{2,6}[\)\]].*$', '', name).strip()
        name = re.sub(r'\s+\d+\s*$', '', name).strip()
        # cartas de dupla face: usa a primeira face
        name = name.split(' // ')[0].strip()

        if name and not name.isdigit():
            entries.append({'qty': max(1, min(qty, 999)), 'name': name})
    return entries


def fetch_prints_bulk(names: list) -> dict:
    """
    Busca TODAS as impressões de várias cartas em uma única query.

    O código original fazia 2 queries por carta (uma para achar a carta e outra
    para as impressões); uma lista de 100 cartas gerava 200 idas ao banco.
    """
    if not names:
        return {}

    placeholders = ', '.join(['%s'] * len(names))
    with connection.cursor() as cur:
        cur.execute(f"""
            SELECT name, mana_cost, cmc, type_line, oracle_text, rarity,
                   image_url_normal, set_code, release_date, scryfall_id
            FROM cards
            WHERE LOWER(name) IN ({placeholders}) AND image_url_normal IS NOT NULL
            ORDER BY release_date DESC
        """, [n.lower() for n in names])
        cols = ['name', 'mana_cost', 'cmc', 'type_line', 'oracle_text', 'rarity',
                'image_url_normal', 'set_code', 'release_date', 'scryfall_id']
        grouped = {}
        for row in cur.fetchall():
            item = dict(zip(cols, row))
            grouped.setdefault(item['name'].lower(), []).append(item)
        return grouped


def format_card(row: dict, qty: int, prints: list | None = None) -> dict:
    type_line = row.get('type_line') or ''
    mana_cost = row.get('mana_cost') or ''
    colors = sorted(set(re.findall(r'\{([WUBRG])\}', mana_cost)))

    if prints is None:
        prints = fetch_all_prints_local(row['name'])

    prints_list = [{
        'set_code':     p.get('set_code', ''),
        'image_url':    p.get('image_url_normal', ''),
        'release_date': str(p.get('release_date', '')) if p.get('release_date') else '',
        'scryfall_id':  p.get('scryfall_id', ''),
    } for p in prints]

    return {
        'name':        row['name'],
        'qty':         qty,
        'mana_cost':   mana_cost,
        'cmc':         float(row['cmc']) if row.get('cmc') is not None else 0,
        'type_line':   type_line,
        'oracle_text': row.get('oracle_text') or '',
        'rarity':      row.get('rarity') or 'common',
        'colors':      colors,
        'color_identity': colors,
        'power':       None,
        'toughness':   None,
        'set':         row.get('set_code') or '',
        'set_name':    row.get('set_code') or '',
        'image_url':   row.get('image_url_normal') or '',
        'selected_set': row.get('set_code') or '',  # set ativo (pode ser trocado pelo usuário)
        'prints':      prints_list,
        'category':    classify_card(type_line),
        'is_legendary': is_legendary(type_line),
        'is_legendary_creature': is_legendary(type_line),  # mantém compatibilidade
        'prices':      {},
    }


def process_entries(entries):
    """Resolve a lista inteira com 1 query, somando quantidades de nomes repetidos."""
    merged = {}
    order  = []
    for entry in entries:
        key = entry['name'].strip().lower()
        if not key:
            continue
        if key in merged:
            merged[key]['qty'] += entry['qty']
        else:
            merged[key] = {'name': entry['name'].strip(), 'qty': entry['qty']}
            order.append(key)

    grouped = fetch_prints_bulk([merged[k]['name'] for k in order])

    results, not_found = [], []
    for key in order:
        prints = grouped.get(key)
        if prints:
            results.append(format_card(prints[0], merged[key]['qty'], prints))
        else:
            not_found.append(merged[key]['name'])
    return results, not_found


def build_response(results, not_found):
    categories = {k: [] for k in ['creature','artifact','land','enchantment',
                                   'planeswalker','instant','sorcery','other']}
    legendary_cards = []
    by_set      = {}
    by_rarity   = {'mythic':[],'rare':[],'uncommon':[],'common':[],'special':[]}
    by_category = {}

    for card in results:
        cat = card['category']
        categories[cat].append(card)
        by_category.setdefault(cat, []).append(card)
        if card['is_legendary']:
            legendary_cards.append(card)

        key = card['set']
        if key not in by_set:
            by_set[key] = {'set_code': key, 'set_name': card['set_name'], 'cards': []}
        by_set[key]['cards'].append(card)

        r = card['rarity'] if card['rarity'] in by_rarity else 'special'
        by_rarity[r].append(card)

    total_copies = sum(c['qty'] for c in results)
    non_land     = [c for c in results if c['category'] != 'land']
    avg_cmc      = round(sum(c['cmc']*c['qty'] for c in non_land) /
                         max(sum(c['qty'] for c in non_land), 1), 2)
    color_counts = {}
    for c in results:
        for col in c.get('color_identity', []):
            color_counts[col] = color_counts.get(col, 0) + c['qty']

    return {
        'cards':            results,
        'categories':       categories,
        'by_set':           list(by_set.values()),
        'by_rarity':        by_rarity,
        'by_category':      by_category,
        'legendary_creatures': legendary_cards,  # todos os lendários
        'not_found':        not_found,
        'stats': {
            'total_cards':   total_copies,
            'total_copies':  total_copies,
            'unique_cards':  len(results),
            'total_unique':  len(results),
            'total_sets':    len(by_set),
            'avg_cmc':       avg_cmc,
            'color_identity': color_counts,
            'by_category':   {k: sum(c['qty'] for c in v) for k, v in categories.items() if v},
            'rarity_counts': {k: sum(c['qty'] for c in v) for k, v in by_rarity.items() if v},
            'set_counts':    {s['set_name']: sum(c['qty'] for c in s['cards']) for s in by_set.values()},
            'estimated_value':      0,
            'estimated_value_foil': 0,
        }
    }


@api_view(['POST'])
def import_deck(request):
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'Texto do deck vazio.'}, status=400)
    entries = parse_deck_text(text)
    if not entries:
        return Response({'error': 'Nenhuma carta encontrada.'}, status=400)
    results, not_found = process_entries(entries)
    return Response(build_response(results, not_found))


@api_view(['POST'])
def export_deck(request):
    import datetime
    name      = request.data.get('name', 'Meu Deck')
    commander = request.data.get('commander')
    cards     = request.data.get('cards', [])
    total     = sum(c.get('qty', 1) for c in cards)
    non_land  = [c for c in cards if c.get('category') != 'land']
    avg_cmc   = round(sum(c.get('cmc',0)*c.get('qty',1) for c in non_land) /
                      max(sum(c.get('qty',1) for c in non_land), 1), 2)
    return Response({
        'deck_name':   name,
        'format':      request.data.get('format','commander'),
        'commander':   commander,
        'total_cards': total,
        'avg_cmc':     avg_cmc,
        'cards':       cards,
        'exported_at': datetime.datetime.utcnow().isoformat() + 'Z',
    })


@api_view(['POST'])
def import_collection(request):
    text = request.data.get('text', '').strip()
    if not text:
        return Response({'error': 'Texto vazio.'}, status=400)
    entries = parse_deck_text(text)
    if not entries:
        return Response({'error': 'Nenhuma carta encontrada.'}, status=400)
    results, not_found = process_entries(entries)
    return Response(build_response(results, not_found))


@api_view(['POST'])
def export_collection(request):
    import datetime
    name  = request.data.get('name', 'Minha Coleção')
    cards = request.data.get('cards', [])
    total = sum(c.get('qty', 1) for c in cards)
    return Response({
        'collection_name': name,
        'total_copies':    total,
        'total_unique':    len(cards),
        'estimated_value_usd': 0,
        'exported_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'cards': cards,
    })