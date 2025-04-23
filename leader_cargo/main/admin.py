from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from telegram_bot.models import TelegramProfile
from .models import CustomUser, Appeals, Goods, ManagersReports, ManagerPlans, ExchangeRates, Calls, CallsFile, Leads, MaintenanceMode
from analytics.models import RequestsForLogisticsRate, RequestsForLogisticsGoods, RequestsForLogisticFiles, RoadsList, CarriersList, CargoFiles, CargoArticle, PaymentDocumentsForArticles, RequestsForLogisticsCalculations
from bills.models import Clients, RequisitesClients, Entity, RequisitesEntity, Bills, BillsFiles

@admin.register(MaintenanceMode)
class MaintenanceModeAdmin(admin.ModelAdmin):
    list_display = ('id', 'is_enabled', 'message')
    list_editable = ('is_enabled', 'message' )
    fields = ('is_enabled', 'message')

@admin.register(TelegramProfile)
class TelegramProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_verified', 'chat_id', 'token')
    list_editable = ('is_verified', 'chat_id', )


@admin.register(Leads)
class LeadsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'call', 'manager', 'status_manager', 'client_name', 'client_phone', 'client_location',
                    'date_next_call_manager',  'description_manager',
                    'time_new', 'time_in_work', 'time_approve_no_other', 'time_create')
    list_display_links = ('pk',)
    list_filter = ('manager', )
    actions = ['delete_empty_manager', 'save_current_state_to_history', 'save_all_leads_to_history']
    search_fields = ('pk', 'client_phone')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('call', 'manager')

    def delete_empty_manager(self, request, queryset):
        # Проверка на наличие разрешения (если требуется)
        if not request.user.is_superuser:
            self.message_user(request, "У вас нет прав для выполнения этого действия.", level=messages.ERROR)
            return

        # Вызов метода clear_all
        Leads.delete_empty_manager()
        self.message_user(request, "Все лиды с пустым значение менеджера были удалены.", level=messages.SUCCESS)

    delete_empty_manager.short_description = "Удалить лиды с пустым значение менеджера"

    def save_current_state_to_history(self, request, queryset):
        """
        Сохраняет текущее состояние выбранных лидов в историю.
        """
        if not request.user.is_superuser:
            self.message_user(request, "У вас нет прав для выполнения этого действия.", level=messages.ERROR)
            return

        # Сохраняем текущее состояние выбранных лидов
        updated_count = 0
        for lead in queryset:
            lead.save()  # Это создаст запись в истории благодаря HistoricalRecords
            updated_count += 1

        self.message_user(
            request,
            f"Текущее состояние {updated_count} лидов сохранено в историю.",
            level=messages.SUCCESS
        )

    save_current_state_to_history.short_description = _("Сохранить текущее состояние лидов в историю")

    def save_all_leads_to_history(self, request, queryset):
        """
        Сохраняет текущее состояние всех лидов в историю.
        """
        if not request.user.is_superuser:
            self.message_user(request, _("У вас нет прав для выполнения этого действия."), level=messages.ERROR)
            return

        # Сохраняем текущее состояние всех лидов
        updated_count = 0
        for lead in Leads.objects.all():
            lead.save()
            updated_count += 1

        self.message_user(
            request,
            _(f"Текущее состояние {updated_count} лидов сохранено в историю."),
            level=messages.SUCCESS
        )

    save_all_leads_to_history.short_description = _("Сохранить текущее состояние ВСЕХ лидов в историю")
@admin.register(Calls)
class CallsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'operator', 'status_call', 'client_name', 'client_phone', 'client_location', 'date_next_call', 'time_create',
                    'manager', 'date_to_manager', 'status_manager', 'date_next_call_manager')
    list_display_links = ('pk',)
    actions = ['clear_all_records', 'create_old_leads']
    search_fields = ('pk', 'client_phone')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('operator', 'manager')

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('clear-all/', self.admin_site.admin_view(self.clear_all_view), name='calls-clear-all'),
        ]
        return custom_urls + urls

    def clear_all_records(self, request, queryset):
        # Проверка на наличие разрешения (если требуется)
        if not request.user.is_superuser:
            self.message_user(request, "У вас нет прав для выполнения этого действия.", level=messages.ERROR)
            return

        # Вызов метода clear_all
        Calls.clear_all()
        self.message_user(request, "Все звонки были удалены.", level=messages.SUCCESS)

    clear_all_records.short_description = "Удалить все звонки"

    def create_old_leads(self, request, queryset):
        # Проверка на наличие разрешения (если требуется)
        if not request.user.is_superuser:
            self.message_user(request, "У вас нет прав для выполнения этого действия.", level=messages.ERROR)
            return

        # Вызов метода clear_all
        Calls.create_old_leads()
        self.message_user(request, "Все звонки перенесены в лиды", level=messages.SUCCESS)

    create_old_leads.short_description = "Перенос старых звонков в лиды"

    def clear_all_view(self, request):
        # Вызов метода clear_all
        Calls.clear_all()
        self.message_user(request, "Все звонки были удалены.", level=messages.SUCCESS)
        return HttpResponseRedirect("../")

@admin.register(CallsFile)
class CallsFileAdmin(admin.ModelAdmin):
    list_display = ('pk', 'crm', 'user', 'file', 'uploaded_at')
    list_display_links = ('pk',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')


@admin.register(ExchangeRates)
class ExchangeRatesAdmin(admin.ModelAdmin):
    list_display = ('id', 'yuan_cash_M', 'yuan_cash_K', 'yuan', 'yuan_non_cash', 'dollar', 'time_create')
    list_display_links = ('id',)


@admin.register(ManagerPlans)
class ManagerPlansAdmin(admin.ModelAdmin):
    list_display = ('id', 'manager_monthly_net_profit_plan', 'month', 'year', 'manager_id', 'time_create')
    list_display_links = ('id',)
    list_editable = ('month', 'year', )
    search_fields = ('manager_id__first_name', 'manager_id__phone')


class BillsFilesAdmin(admin.ModelAdmin):
    list_display = ('id', 'bill', 'name', 'file_path_request', 'time_create')
    list_display_links = ('id', )
    list_editable = ('name',)
    search_fields = ('bill', 'name')


class BillsAdmin(admin.ModelAdmin):
    list_display = ('id', 'manager', 'status', 'client', 'nds_status', 'entity', 'summa')
    list_display_links = ('id', )
    search_fields = ('manager', 'entity', 'client')
    list_filter = ('status', 'manager', 'entity', 'client')


class RequisitesEntityAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity', 'name', 'rs', 'bic', 'ks', 'name_bank')
    list_display_links = ('id', 'name')
    search_fields = ('entity', 'name', 'rs', 'bic', 'ks')
    list_filter = ('name_bank', 'entity')


class EntityAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'type', 'inn', 'nds_status', 'phone')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'inn')
    list_editable = ('nds_status',)
    list_filter = ('type', 'nds_status')


class RequisitesClientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'client', 'name', 'rs', 'bic', 'ks', 'name_bank')
    list_display_links = ('id', 'name')
    search_fields = ('client', 'name', 'rs', 'bic', 'ks')
    list_filter = ('name_bank', 'client')


class ClientsAdmin(admin.ModelAdmin):
    list_display = ('id', 'manager', 'name', 'type', 'inn',  'nds_status', 'phone')
    list_display_links = ('id', 'name')
    search_fields = ('manager', 'name', 'inn')
    list_editable = ('nds_status',)
    list_filter = ('type', 'nds_status', 'manager')


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'patronymic', 'phone', 'role', 'time_create', 'status')
    list_display_links = ('id', 'phone')
    search_fields = ('role', 'phone')
    list_editable = ('status', 'role')


class CustomCargoArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'responsible_manager', 'time_from_china', 'status', 'total_cost', 'weight', 'volume', 'cargo_id', 'time_create')
    list_display_links = ('id', 'article')
    search_fields = ('article', 'responsible_manager')
    list_editable = ('responsible_manager', 'status', )
    list_filter = ('status', 'time_from_china', 'responsible_manager')


class CustomPaymentDocumentsForArticles(admin.ModelAdmin):
    list_display = ('id', 'article', 'file_path', 'balance', 'time_create')
    list_display_links = ('id', )
    search_fields = ('article', 'time_create')
    list_editable = ('balance',)


class CustomRequestsForLogisticsCalculations(admin.ModelAdmin):
    list_display = ('name', 'status', 'initiator', 'logist', 'bid', 'time_create', 'time_update')
    list_display_links = ('name', )
    search_fields = ('name', 'initiator')
    list_editable = ('initiator', 'status')


class CustomRoadsList(admin.ModelAdmin):
    list_display = ('name', 'activity', 'status', 'time_create')
    list_display_links = ('name', )
    search_fields = ('name', )
    list_editable = ('activity', 'status')


class CustomCarriersList(admin.ModelAdmin):
    list_display = ('name', 'activity', 'status', 'time_create')
    list_display_links = ('name', )
    search_fields = ('name', )
    list_editable = ('activity', 'status')


class CustomRequestsForLogisticFiles(admin.ModelAdmin):
    list_display = ('request', 'name', 'file_path_request', 'time_create')
    list_display_links = ('name', )
    search_fields = ('request', 'name', )


class CustomRequestsForLogisticsGoods(admin.ModelAdmin):
    list_display = ('request', 'description', 'bid', 'photo_path_logistic_goods', 'time_create')
    list_display_links = ('request', )
    search_fields = ('request', )
    list_editable = ('bid', )


class CustomRequestsForLogisticsRate(admin.ModelAdmin):
    list_display = ('good', 'carrier', 'road', 'bid', 'active', 'time_create')
    search_fields = ('good', )
    list_editable = ('bid', 'active',)
    list_filter = ('road', 'carrier', 'active', 'time_create')


admin.site.register(Bills, BillsAdmin)
admin.site.register(BillsFiles, BillsFilesAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(RequisitesEntity, RequisitesEntityAdmin)
admin.site.register(Clients, ClientsAdmin)
admin.site.register(RequisitesClients, RequisitesClientsAdmin)

admin.site.register(CargoArticle, CustomCargoArticleAdmin)
admin.site.register(CargoFiles)
admin.site.register(PaymentDocumentsForArticles, CustomPaymentDocumentsForArticles)

admin.site.register(RoadsList, CustomRoadsList)
admin.site.register(CarriersList, CustomCarriersList)

admin.site.register(RequestsForLogisticsCalculations, CustomRequestsForLogisticsCalculations)
admin.site.register(RequestsForLogisticFiles, CustomRequestsForLogisticFiles)
admin.site.register(RequestsForLogisticsGoods, CustomRequestsForLogisticsGoods)
admin.site.register(RequestsForLogisticsRate, CustomRequestsForLogisticsRate)

admin.site.register(ManagersReports)

admin.site.register(Appeals)
admin.site.register(Goods)
