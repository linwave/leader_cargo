from django.contrib import admin, messages
from django.http import HttpResponseRedirect
from django.urls import path
from django.utils.html import format_html

from .models import CustomUser, Appeals, Goods, ManagersReports, ManagerPlans, ExchangeRates, Calls, CallsFile
from analytics.models import RequestsForLogisticsRate, RequestsForLogisticsGoods, RequestsForLogisticFiles, RoadsList, CarriersList, CargoFiles, CargoArticle, PaymentDocumentsForArticles, RequestsForLogisticsCalculations
from bills.models import Clients, RequisitesClients, Entity, RequisitesEntity, Bills, BillsFiles


@admin.register(Calls)
class CallsAdmin(admin.ModelAdmin):
    list_display = ('pk', 'operator', 'status_call', 'client_name', 'client_phone', 'client_location', 'date_next_call', 'time_create',
                    'manager', 'date_to_manager', 'status_manager', 'date_next_call_manager')
    list_display_links = ('pk',)
    actions = ['clear_all_records']

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
