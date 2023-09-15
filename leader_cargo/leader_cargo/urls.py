from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import path, include


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls'))
]


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>У нас такой страницы нет</h1>')


handler404 = pageNotFound
