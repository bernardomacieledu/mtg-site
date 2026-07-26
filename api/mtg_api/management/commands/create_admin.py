"""
Cria (ou atualiza) o usuário administrador a partir de variáveis de ambiente.

Idempotente: pode rodar a cada boot. Sem ADMIN_PASSWORD definido, não faz nada,
para nunca criar um superusuário com senha previsível.

    ADMIN_USERNAME=admin ADMIN_PASSWORD=segredo python manage.py create_admin
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Cria o superusuário a partir de ADMIN_USERNAME/ADMIN_PASSWORD/ADMIN_EMAIL.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default=os.environ.get('ADMIN_USERNAME', 'admin'))
        parser.add_argument('--password', default=os.environ.get('ADMIN_PASSWORD', ''))
        parser.add_argument('--email',    default=os.environ.get('ADMIN_EMAIL', 'admin@localhost'))

    def handle(self, *args, **options):
        senha = options['password']
        if not senha:
            self.stdout.write('ADMIN_PASSWORD não definida; superusuário não foi criado.')
            return

        Usuario = get_user_model()
        usuario, criado = Usuario.objects.get_or_create(
            username=options['username'],
            defaults={'email': options['email']},
        )
        usuario.is_staff = True
        usuario.is_superuser = True
        usuario.set_password(senha)
        usuario.save()

        acao = 'criado' if criado else 'atualizado'
        self.stdout.write(self.style.SUCCESS(
            f'Superusuário "{usuario.username}" {acao}. Acesse /admin/'))
