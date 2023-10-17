from django.contrib import admin
from .models import CustomUser, Appeals, Goods


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'last_name', 'first_name', 'patronymic', 'phone', 'role', 'time_create', 'status')
    list_display_links = ('id', 'phone')
    search_fields = ('role', 'phone')
    list_editable = ('status',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Appeals)
admin.site.register(Goods)
