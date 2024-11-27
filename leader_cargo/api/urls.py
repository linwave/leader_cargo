from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = 'api'

urlpatterns = [
    path('v1/articles/', views.WomenAPIView.as_view()),
    ]
