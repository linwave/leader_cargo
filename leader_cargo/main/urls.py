from django.conf import settings
from django.urls import path
from . import views
from django.conf.urls.static import static


urlpatterns = [
    path('', views.ExchangeRatesView.as_view(), name='home'),
    path('login/', views.LoginUser.as_view(), name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('employees/', views.EmployeesView.as_view(), name='employees'),
    path('employees/create-employees/', views.AddEmployeeView.as_view(), name='create_employees'),
    path('employees/card-employees/<int:employee_id>/', views.CardEmployeesView.as_view(), name='card_employees'),
    path('exchangerates/', views.ExchangeRatesView.as_view(), name='exchangerates'),
    path('exchangerates/create-exchangerates/', views.AddExchangeRatesView.as_view(), name='create_exchangerates'),
    path('clients/', views.ClientsView.as_view(), name='clients'),
    path('clients/create-client/', views.AddClientView.as_view(), name='create_client'),
    path('clients/card-client/<int:client_id>/', views.CardClientsView.as_view(), name='card_client'),
    path('appeals/', views.AppealsView.as_view(), name='appeals'),
    path('appeals/new-appeal/', views.AddAppealsView.as_view(), name='create_appeal'),
    path('appeals/card-appeal/<int:appeal_id>', views.CardAppealsView.as_view(), name='card_appeal'),
    path('appeals/card-appeal/<int:appeal_id>/create-goods', views.AddGoodsView.as_view(), name='create_goods'),
    path('appeals/card-appeal/<int:appeal_id>/card-goods/<int:goods_id>', views.CardGoodsView.as_view(), name='card_goods'),
    path('appeals/card-appeal/<int:appeal_id>/delete-goods/<int:goods_id>', views.DeleteGoodsView.as_view(), name='delete_goods'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
