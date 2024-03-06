from django.contrib import admin
from .models import CustomUser, Appeals, Goods, ManagersReports
from analytics.models import RequestsForLogisticsRate, RequestsForLogisticsGoods, RequestsForLogisticFiles, RoadsList, CarriersList, CargoFiles, CargoArticle, PaymentDocumentsForArticles, RequestsForLogisticsCalculations


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'patronymic', 'phone', 'role', 'time_create', 'status')
    list_display_links = ('id', 'phone')
    search_fields = ('role', 'phone')
    list_editable = ('status',)


class CustomCargoArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'responsible_manager', 'status', 'total_cost', 'weight', 'volume', 'cargo_id', 'time_create')
    list_display_links = ('id', 'article')
    search_fields = ('article', 'responsible_manager')
    list_editable = ('responsible_manager', 'status', )
    list_filter = ('status', 'responsible_manager')


class CustomPaymentDocumentsForArticles(admin.ModelAdmin):
    list_display = ('id', 'article', 'file_path', 'balance', 'time_create')
    list_display_links = ('id', )
    search_fields = ('article', 'time_create')
    list_editable = ('balance',)


class CustomRequestsForLogisticsCalculations(admin.ModelAdmin):
    list_display = ('name', 'status', 'initiator', 'logist', 'bid', 'time_create', 'time_update')
    list_display_links = ('name', )
    search_fields = ('name', 'initiator')
    list_editable = ('initiator',)


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
    list_display = ('request', 'photo_path_logistic_goods', 'time_create')
    list_display_links = ('request', )
    search_fields = ('request', )


class CustomRequestsForLogisticsRate(admin.ModelAdmin):
    list_display = ('request', 'road', 'bid', 'active', 'time_create')
    search_fields = ('request', )


admin.site.register(CustomUser, CustomUserAdmin)

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
