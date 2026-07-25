"""Imprime a quantidade de cartas no banco (usado pelo entrypoint do Docker)."""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Imprime o total de linhas da tabela cards.'

    def handle(self, *args, **options):
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT COUNT(*) FROM cards')
                self.stdout.write(str(cursor.fetchone()[0]))
        except Exception:
            self.stdout.write('0')
