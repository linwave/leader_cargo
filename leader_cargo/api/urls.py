from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = 'api'

urlpatterns = [
    path('v1/articles/', views.WomenAPIView.as_view()),
    path('v1/calls/rosaccreditation/', views.create_call_from_rosaccreditation, name='create_rosacc_call'),
    path('v1/calls/rosaccreditation/bulk/', views.bulk_create_calls_from_rosaccreditation, name='bulk_rosacc_calls'),
]
