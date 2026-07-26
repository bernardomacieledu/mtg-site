import json
import time
import urllib.request
from django.conf import settings

HEADERS = {'User-Agent': 'MTGNexus-Vue/1.0'}


def fetch_scryfall(url: str, cache_file: str) -> dict:
    cache_path = settings.SCRYFALL_CACHE_DIR / cache_file
    now = time.time()
    if not cache_path.exists() or (now - cache_path.stat().st_mtime) > settings.SCRYFALL_CACHE_TIMEOUT:
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=10) as r:
                data = r.read()
            cache_path.write_bytes(data)
        except Exception:
            if not cache_path.exists():
                return {'data': []}
    try:
        return json.loads(cache_path.read_bytes())
    except Exception:
        return {'data': []}


def get_set_names() -> dict:
    """
    Catálogo de coleções: banco primeiro, Scryfall como complemento.

    O banco é preenchido por `manage.py seed_sets` e não depende de rede, então
    o nome completo e o ícone continuam corretos mesmo offline.
    """
    catalog = {}

    try:
        from .models import CardSet
        for item in CardSet.objects.all().values(
                'code', 'name', 'released_at', 'icon_svg_uri', 'set_type'):
            catalog[item['code']] = {
                'name':         item['name'],
                'released_at':  item['released_at'],
                'icon_svg_uri': item['icon_svg_uri'],
                'set_type':     item['set_type'],
            }
    except Exception:
        # Tabela ainda não migrada: segue só com o cache do Scryfall.
        pass

    data = fetch_scryfall('https://api.scryfall.com/sets', 'sets_cache.json')
    for s in data.get('data', []):
        # O banco tem prioridade; o cache só preenche o que faltar.
        catalog.setdefault(s['code'], {
            'name':         s['name'],
            'released_at':  s.get('released_at', ''),
            'icon_svg_uri': s.get('icon_svg_uri', ''),
            'set_type':     s.get('set_type', ''),
        })

    return catalog


def get_mana_map() -> dict:
    """
    Símbolos de mana: banco primeiro, Scryfall como complemento.

    Preenchido por `manage.py seed_symbols`, para não depender de rede a cada
    request (sem isso a interface mostra as letras no lugar dos símbolos).
    """
    mapa = {}

    try:
        from .models import ManaSymbol
        mapa = dict(ManaSymbol.objects.values_list('symbol', 'svg_uri'))
    except Exception:
        pass  # tabela ainda não migrada

    data = fetch_scryfall('https://api.scryfall.com/symbology', 'symbology_cache.json')
    for s in data.get('data', []):
        mapa.setdefault(s['symbol'], s['svg_uri'])

    return mapa


def get_usd_brl_rate():
    """
    Cotação USD -> BRL.

    Ordem: valor fixado pelo administrador > cotação do dia (cache de 24 h) >
    USD_BRL_FALLBACK do ambiente. É sempre uma ESTIMATIVA: o mercado brasileiro
    tem dinâmica própria e costuma divergir da conversão direta.
    """
    import os

    try:
        from .models import SystemSetting
        if SystemSetting.get('usd_brl_mode', 'auto') == 'manual':
            manual = SystemSetting.get('usd_brl_manual', '')
            if manual:
                return float(manual)
    except Exception:
        pass  # tabela ainda não migrada

    dados = fetch_scryfall('https://economia.awesomeapi.com.br/last/USD-BRL',
                           'usd_brl_cache.json')
    try:
        return float(dados['USDBRL']['bid'])
    except (KeyError, TypeError, ValueError):
        try:
            return float(os.environ.get('USD_BRL_FALLBACK', '0') or 0) or None
        except ValueError:
            return None
