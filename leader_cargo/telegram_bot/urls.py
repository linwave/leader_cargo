from django.urls import path
from . import views

urlpatterns = [
    path('unlink-telegram/', views.unlink_telegram, name='unlink_telegram'),
    path('webhook/', views.telegram_webhook, name='telegram_webhook'),
]