"""
Concede ou remove privilégio de administrador de um usuário já cadastrado.

    python manage.py set_admin bernardo
    python manage.py set_admin bernardo --remove
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Torna administrador um usuário existente.'

    def add_arguments(self, parser):
        parser.add_argument('username')
        parser.add_argument('--remove', action='store_true',
                            help='Remove o privilégio em vez de conceder.')

    def handle(self, *args, **options):
        Usuario = get_user_model()
        try:
            usuario = Usuario.objects.get(username=options['username'])
        except Usuario.DoesNotExist:
            raise CommandError(f'Usuário "{options["username"]}" não encontrado.') from None

        conceder = not options['remove']
        usuario.is_staff = conceder
        usuario.is_superuser = conceder
        usuario.save(update_fields=['is_staff', 'is_superuser'])

        acao = 'agora é administrador' if conceder else 'não é mais administrador'
        self.stdout.write(self.style.SUCCESS(f'"{usuario.username}" {acao}.'))
        if conceder:
            self.stdout.write('Saia e entre de novo no site para o token refletir a mudança.')
