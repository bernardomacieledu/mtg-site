"""
API de administração consumida pelo painel do próprio site.

Espelha o que o Django Admin faz com as tarefas agendadas, para o administrador
não precisar sair do MTG Nexus.
"""
from django.db import connection
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.response import Response

from auth_app.views import admin_required

from .models import CardPrice, CardSet, ManaSymbol, ScheduledTask


def _serializar(tarefa):
    return {
        'id':             tarefa.id,
        'key':            tarefa.key,
        'label':          tarefa.get_key_display(),
        'enabled':        tarefa.enabled,
        'interval_hours': tarefa.interval_hours,
        'options':        tarefa.options,
        'status':         tarefa.status,
        'status_label':   tarefa.get_status_display(),
        'last_run':       tarefa.last_run.isoformat() if tarefa.last_run else None,
        'next_run':       tarefa.next_run.isoformat() if tarefa.next_run else None,
        'last_message':   (tarefa.last_message or '')[-600:],
        'force_now':      tarefa.force_now,
    }


@api_view(['GET'])
@admin_required
def listar_tarefas(request):
    """GET /api/admin/tasks/"""
    return Response({
        'server_time': timezone.now().isoformat(),
        'tasks': [_serializar(t) for t in ScheduledTask.objects.all()],
    })


@api_view(['PATCH'])
@admin_required
def atualizar_tarefa(request, task_id):
    """PATCH /api/admin/tasks/<id>/ — intervalo, ativo/inativo e argumentos."""
    try:
        tarefa = ScheduledTask.objects.get(id=task_id)
    except ScheduledTask.DoesNotExist:
        return Response({'error': 'Tarefa não encontrada.'}, status=404)

    dados = request.data
    alterados = []

    if 'enabled' in dados:
        tarefa.enabled = bool(dados['enabled'])
        alterados.append('enabled')

    if 'interval_hours' in dados:
        try:
            horas = int(dados['interval_hours'])
        except (TypeError, ValueError):
            return Response({'error': 'Intervalo inválido.'}, status=400)
        if not 1 <= horas <= 8760:
            return Response({'error': 'Intervalo deve ficar entre 1 hora e 1 ano.'}, status=400)
        tarefa.interval_hours = horas
        alterados.append('interval_hours')
        # Reagenda a partir da última execução para o novo intervalo valer já
        tarefa.agendar_proxima(tarefa.last_run)
        alterados.append('next_run')

    if 'options' in dados:
        tarefa.options = str(dados['options'])[:255]
        alterados.append('options')

    if alterados:
        tarefa.save(update_fields=alterados + ['updated_at'])

    return Response(_serializar(tarefa))


@api_view(['POST'])
@admin_required
def executar_tarefa(request, task_id):
    """POST /api/admin/tasks/<id>/run/ — marca para rodar na próxima verificação."""
    try:
        tarefa = ScheduledTask.objects.get(id=task_id)
    except ScheduledTask.DoesNotExist:
        return Response({'error': 'Tarefa não encontrada.'}, status=404)

    tarefa.force_now = True
    tarefa.save(update_fields=['force_now', 'updated_at'])
    return Response({**_serializar(tarefa),
                     'message': 'Agendada para a próxima verificação do worker.'})


@api_view(['GET'])
@admin_required
def status_sistema(request):
    """GET /api/admin/status/ — números gerais para o painel."""
    from auth_app.models import User, UserCollection, UserDeck

    with connection.cursor() as cursor:
        cursor.execute('SELECT COUNT(*) FROM cards')
        cartas = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(DISTINCT set_code) FROM cards')
        colecoes_no_banco = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM rules')
        regras = cursor.fetchone()[0]

    return Response({
        'cards':        cartas,
        'sets_in_db':   colecoes_no_banco,
        'rules':        regras,
        'prices':       CardPrice.objects.count(),
        'set_catalog':  CardSet.objects.count(),
        'symbols':      ManaSymbol.objects.count(),
        'users':        User.objects.count(),
        'decks':        UserDeck.objects.count(),
        'collections':  UserCollection.objects.count(),
    })
