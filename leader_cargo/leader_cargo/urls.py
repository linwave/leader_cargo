from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('analytics/', include('analytics.urls'))
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>У нас такой страницы нет</h1>')


handler404 = pageNotFound
