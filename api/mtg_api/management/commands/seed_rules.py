"""
Importa as Regras Abrangentes (Comprehensive Rules) para a tabela `rules`.

Uso:
    python manage.py seed_rules --file /caminho/MagicCompRules.txt
    python manage.py seed_rules --url https://media.wizards.com/.../MagicCompRules.txt

O arquivo oficial em texto está em https://magic.wizards.com/en/rules
"""
import re
import urllib.request

from django.core.management.base import BaseCommand
from django.db import connection

RULE_RE = re.compile(r'^(\d{3}\.\d+[a-z]?)\.?\s+(.*)$')


class Command(BaseCommand):
    help = 'Importa as regras abrangentes a partir de um arquivo ou URL.'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, default='')
        parser.add_argument('--url', type=str, default='')

    def handle(self, *args, **options):
        if options['file']:
            text = open(options['file'], encoding='utf-8-sig', errors='ignore').read()
        elif options['url']:
            request = urllib.request.Request(options['url'], headers={'User-Agent': 'MTGNexus/1.0'})
            with urllib.request.urlopen(request, timeout=60) as response:
                text = response.read().decode('utf-8-sig', errors='ignore')
        else:
            self.stderr.write('Informe --file ou --url.')
            return

        rows, seen = [], set()
        for line in text.splitlines():
            match = RULE_RE.match(line.strip())
            if not match:
                continue
            number, body = match.group(1), match.group(2).strip()
            if not body or number in seen:
                continue
            seen.add(number)
            rows.append((number, body, number.split('.')[0][0]))

        if not rows:
            self.stderr.write('Nenhuma regra reconhecida no arquivo.')
            return

        with connection.cursor() as cursor:
            cursor.executemany(
                'REPLACE INTO rules (rule_number, rule_text, chapter_id) VALUES (%s, %s, %s)',
                rows,
            )
        self.stdout.write(self.style.SUCCESS(f'{len(rows)} regras importadas.'))
