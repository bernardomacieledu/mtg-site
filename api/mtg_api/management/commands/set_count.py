"""Imprime quantas coleções há no catálogo (usado pelo entrypoint)."""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Imprime o total de coleções no catálogo.'

    def handle(self, *args, **options):
        try:
            from mtg_api.models import CardSet
            self.stdout.write(str(CardSet.objects.count()))
        except Exception:
            self.stdout.write('0')
