"""
Aguarda o banco ficar disponível usando a MESMA conexão do Django.

O loop anterior usava `mysqladmin` com o erro descartado: quando a conexão
falhava (cliente MariaDB x caching_sha2_password do MySQL 8, senha errada,
banco inexistente), o container ficava preso para sempre sem explicar nada.
Aqui cada tentativa informa o tempo decorrido e o motivo real da falha.
"""
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = 'Aguarda o banco de dados aceitar conexões.'

    def add_arguments(self, parser):
        parser.add_argument('--timeout', type=int, default=180,
                            help='Tempo máximo de espera, em segundos.')
        parser.add_argument('--interval', type=float, default=2,
                            help='Intervalo entre tentativas, em segundos.')

    def handle(self, *args, **options):
        timeout = options['timeout']
        interval = options['interval']
        connection = connections['default']

        started = time.time()
        attempt = 0
        last_error = None

        while True:
            attempt += 1
            elapsed = int(time.time() - started)
            try:
                connection.ensure_connection()
            except (OperationalError, Exception) as exc:  # noqa: B014
                last_error = exc
                connection.close()

                if elapsed >= timeout:
                    raise CommandError(
                        f'Banco indisponível após {elapsed}s. Último erro: {exc}'
                    ) from None

                # Mostra o motivo na 1ª tentativa e a cada 5 seguintes, para o
                # log não virar spam mas também não esconder a causa.
                if attempt == 1 or attempt % 5 == 0:
                    self.stdout.write(
                        f'    tentativa {attempt} ({elapsed}s de {timeout}s): {exc}'
                    )
                time.sleep(interval)
            else:
                self.stdout.write(self.style.SUCCESS(
                    f'    banco respondeu em {elapsed}s (tentativa {attempt}).'
                ))
                return
