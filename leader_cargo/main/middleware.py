from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponseForbidden
from django.urls import reverse

from .models import MaintenanceMode

class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Проверяем, есть ли активный режим обслуживания
        maintenance_mode = MaintenanceMode.objects.first()
        if maintenance_mode and maintenance_mode.is_enabled:
            # Исключение для администраторов (superusers)
            if not request.path.startswith(reverse('admin:index')):
                return render(request, 'main/maintenance.html', {
                    'message': maintenance_mode.message
                }, status=503)

        response = self.get_response(request)
        return response