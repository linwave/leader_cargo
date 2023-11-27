from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = 'analytics'

urlpatterns = [
    path('logistic-requests/', views.LogisticRequestsView.as_view(), name='logistic-requests'),
    path('logistic-requests/add', views.LogisticRequestsAddView.as_view(), name='add_logistic-requests'),
    path('logistic-requests/edit/<int:request_id>', views.LogisticRequestsView.as_view(), name='edit_logistic-requests'),

    path('calculator/', views.LogisticCalculatorView.as_view(), name='calculator'),

    path('carrier-files/', views.CarrierFilesView.as_view(), name='carrier'),
    path('carrier-files/update-article-status/<int:article_id>', views.change_article_status, name='update_article'),
    path('carrier-files/edit-article-manager/<int:article_id>', views.change_article_for_manager, name='edit_table_manager_article'),
    path('carrier-files/edit-article/<int:article_id>', views.EditTableArticleView.as_view(), name='edit_table_article'),
    path('carrier-files/delete-article/<int:article_id>', views.DeleteArticleView.as_view(), name='delete_table_article'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

htmx_patterns = [
    path('carrier-files/edit/<int:article_id>', views.edit_article_in_table, name='edit_article'),
    path('carrier-files/delete/<int:article_id>', views.delete_article_in_table, name='delete_article'),
]

urlpatterns += htmx_patterns

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)