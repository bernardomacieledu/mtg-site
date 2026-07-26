from django.contrib import admin, messages

from .models import CardPrice, CardSet, ManaSymbol, ScheduledTask


@admin.register(ScheduledTask)
class ScheduledTaskAdmin(admin.ModelAdmin):
    list_display  = ('get_key_display', 'enabled', 'interval_hours',
                     'last_run', 'next_run', 'status')
    list_editable = ('enabled', 'interval_hours')
    list_filter   = ('enabled', 'status')
    readonly_fields = ('last_run', 'next_run', 'status', 'last_message', 'updated_at')
    actions = ['executar_agora', 'reagendar']

    @admin.action(description='Executar agora (na próxima verificação)')
    def executar_agora(self, request, queryset):
        total = queryset.update(force_now=True)
        self.message_user(
            request,
            f'{total} tarefa(s) marcada(s). O agendador verifica a cada minuto.',
            messages.SUCCESS)

    @admin.action(description='Reagendar a partir de agora')
    def reagendar(self, request, queryset):
        for tarefa in queryset:
            tarefa.agendar_proxima()
            tarefa.save(update_fields=['next_run'])
        self.message_user(request, 'Próxima execução recalculada.', messages.SUCCESS)


@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display  = ('code', 'name', 'set_type', 'released_at', 'card_count')
    search_fields = ('code', 'name')
    list_filter   = ('set_type', 'digital')


@admin.register(CardPrice)
class CardPriceAdmin(admin.ModelAdmin):
    list_display  = ('scryfall_id', 'usd', 'usd_foil', 'eur', 'price_date')
    search_fields = ('scryfall_id',)


@admin.register(ManaSymbol)
class ManaSymbolAdmin(admin.ModelAdmin):
    list_display  = ('symbol', 'english')
    search_fields = ('symbol', 'english')
