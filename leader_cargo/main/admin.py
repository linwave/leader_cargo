from django.contrib import admin
from .models import CustomUser, Appeals, Goods


class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'phone', 'role', 'time_create', 'status')
    list_display_links = ('id', 'phone')
    search_fields = ('role', 'phone')
    list_editable = ('status',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Appeals)
admin.site.register(Goods)
