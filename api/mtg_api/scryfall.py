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
    data = fetch_scryfall('https://api.scryfall.com/sets', 'sets_cache.json')
    return {
        s['code']: {
            'name': s['name'],
            'released_at': s.get('released_at', ''),
            'icon_svg_uri': s.get('icon_svg_uri', ''),
        }
        for s in data.get('data', [])
    }


def get_mana_map() -> dict:
    data = fetch_scryfall('https://api.scryfall.com/symbology', 'symbology_cache.json')
    return {s['symbol']: s['svg_uri'] for s in data.get('data', [])}
