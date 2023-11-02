from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

urlpatterns = [
    path('carrier-files/', views.CarrierFilesView.as_view(), name='carrier'),
    path('carrier-files/delete-article/<int:article_id>', views.DeleteArticleView.as_view(), name='delete_article'),
    path('carrier-files/update-article-status/<int:article_id>', views.change_article_status, name='update_article'),
    path('carrier-files/edit-article/<int:article_id>', views.EditTableArticleView.as_view(), name='edit_table_article'),
    path('carrier-files/edit-article-manager/<int:article_id>', views.change_article_for_manager, name='edit_table_manager_article'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

htmx_patterns = [
    # path('filter-table/', views.index_x, name='filter_table')
]

urlpatterns += htmx_patterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)