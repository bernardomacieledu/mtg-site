"""
Agendador das atualizações automáticas.

Roda num container próprio, em laço: a cada verificação executa as tarefas
vencidas e regrava no banco quando será a próxima. O agendamento fica no banco
para o administrador poder ajustar intervalo e forçar execução pela interface.

    python manage.py run_scheduler
    python manage.py run_scheduler --once     # uma passada só (útil em cron)
"""
import io
import time
import traceback

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.utils import timezone

from mtg_api.models import ScheduledTask

# Criadas na primeira execução, com intervalos que fazem sentido para cada uma
PADRAO = [
    # O MTGJSON/Scryfall publicam preços uma vez ao dia
    {'key': 'seed_prices',  'interval_hours': 24, 'options': ''},
    # Cartas novas só saem em lançamento, mas spoilers pingam na semana anterior
    {'key': 'seed_cards',   'interval_hours': 24, 'options': '--recent 3'},
    {'key': 'seed_sets',    'interval_hours': 168, 'options': ''},
    {'key': 'seed_symbols', 'interval_hours': 720, 'options': ''},
]


class Command(BaseCommand):
    help = 'Executa as atualizações agendadas.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true',
                            help='Faz uma única verificação e sai.')
        parser.add_argument('--interval', type=int, default=60,
                            help='Segundos entre verificações (padrão 60).')

    def handle(self, *args, **options):
        self.criar_padroes()

        if options['once']:
            self.verificar()
            return

        self.stdout.write(self.style.SUCCESS(
            f'Agendador ativo (verificando a cada {options["interval"]}s). Ctrl+C para sair.'))
        while True:
            try:
                self.verificar()
            except Exception:
                self.stderr.write(traceback.format_exc())
            time.sleep(options['interval'])

    def criar_padroes(self):
        for padrao in PADRAO:
            tarefa, criada = ScheduledTask.objects.get_or_create(
                key=padrao['key'],
                defaults={'interval_hours': padrao['interval_hours'],
                          'options': padrao['options'],
                          'enabled': True},
            )
            if criada:
                tarefa.agendar_proxima()
                tarefa.save(update_fields=['next_run'])
                self.stdout.write(f'  tarefa criada: {tarefa.get_key_display()}')

    def verificar(self):
        for tarefa in ScheduledTask.objects.all():
            if not tarefa.esta_vencida():
                continue
            self.executar(tarefa)

    def executar(self, tarefa):
        inicio = timezone.now()
        forcada = tarefa.force_now

        tarefa.status = 'running'
        tarefa.force_now = False
        tarefa.save(update_fields=['status', 'force_now'])

        rotulo = tarefa.get_key_display()
        self.stdout.write(f'[{inicio:%Y-%m-%d %H:%M}] executando {rotulo}'
                          f'{" (forçada)" if forcada else ""}...')

        saida = io.StringIO()
        try:
            call_command(tarefa.key, *tarefa.args, stdout=saida, stderr=saida)
            tarefa.status = 'ok'
            # Guarda só o fim da saída: o log completo fica no container
            tarefa.last_message = saida.getvalue()[-2000:]
            self.stdout.write(self.style.SUCCESS(f'  {rotulo}: concluída'))
        except Exception as exc:
            tarefa.status = 'error'
            tarefa.last_message = f'{exc}\n\n{saida.getvalue()[-1500:]}'
            self.stderr.write(self.style.ERROR(f'  {rotulo}: falhou — {exc}'))

        tarefa.last_run = inicio
        tarefa.agendar_proxima()
        tarefa.save(update_fields=['status', 'last_message', 'last_run', 'next_run'])
