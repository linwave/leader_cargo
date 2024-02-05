from django.contrib import admin
from .models import CustomUser, Appeals, Goods, ManagersReports
from analytics.models import CargoFiles, CargoArticle


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'patronymic', 'phone', 'role', 'time_create', 'status')
    list_display_links = ('id', 'phone')
    search_fields = ('role', 'phone')
    list_editable = ('status',)


class CustomCargoArticleAdmin(admin.ModelAdmin):
    list_display = ('id', 'article', 'responsible_manager', 'total_cost', 'weight', 'volume', 'cargo_id', 'time_create')
    list_display_links = ('id', 'article')
    search_fields = ('article', 'responsible_manager')
    list_editable = ('responsible_manager',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(CargoFiles)
admin.site.register(CargoArticle, CustomCargoArticleAdmin)
admin.site.register(ManagersReports)
admin.site.register(Appeals)
admin.site.register(Goods)
