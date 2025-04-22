from django.conf.urls import url
from django.contrib import admin
from django.http import HttpResponseNotFound
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('main.urls')),
    path('api/', include('api.urls')),
    path('logistic/', include('analytics.urls')),
    path('bills/', include('bills.urls')),
    path('telegram/', include('telegram_bot.urls')),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns = [
                      path("__debug__/", include("debug_toolbar.urls")),
                  ] + urlpatterns
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        url(f'^{settings.MEDIA_URL.lstrip("/")}(?P<path>.*)$',
            serve, {'document_root': settings.MEDIA_ROOT}),
        # url(f'^{settings.STATIC_URL.lstrip("/")}(?P<path>.*)$',
        #     serve, {'document_root': settings.STATIC_ROOT}),
    ]


def pageNotFound(request, exception):
    return HttpResponseNotFound('<h1>У нас такой страницы нет</h1>')


handler404 = pageNotFound
