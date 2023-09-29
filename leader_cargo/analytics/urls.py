from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('carrier-files/', views.CarrierFilesView.as_view(), name='carrier'),
    path('carrier-files/delete-article/<int:article_id>', views.DeleteArticleView.as_view(), name='delete_article'),
    path('carrier-files/update-article/<int:article_id>', views.UpdateArticleView.as_view(), name='update_article'),
    # path('carrier-files/add-file', views.AddCarrierFilesView.as_view(), name='add_carrier_files'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)