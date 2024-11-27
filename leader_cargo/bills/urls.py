from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = 'bills'

urlpatterns = [
    path('bills', views.BillsView.as_view(), name='bills'),
    path('bills/add', views.BillsAddView.as_view(), name='bills_add'),
    path('bills/add/row', views.add_row_to_bill, name='bills_add_row'),
    path('bills/edit/<int:bill_id>', views.BillsAddView.as_view(), name='bills_edit'),


    path('entity', views.EntityView.as_view(), name='entity'),
    path('entity/add', views.EntityAddView.as_view(), name='entity_add'),
    path('entity/edit/<int:entity_id>', views.EntityEditView.as_view(), name='entity_edit'),
    path('entity/edit/<int:entity_id>/requisites/add', views.RequisitesEntityAddView.as_view(), name='requisites_add_entity'),
    path('entity/edit/<int:entity_id>/requisites/edit/<int:requisite_id>', views.RequisitesEntityEditView.as_view(), name='requisites_edit_entity'),

    path('clients', views.ClientsView.as_view(), name='clients'),
    path('clients/add', views.ClientsAddView.as_view(), name='clients_add'),
    path('clients/edit/<int:client_id>', views.ClientsEditView.as_view(), name='clients_edit'),
    path('clients/edit/<int:client_id>/requisites/add', views.RequisitesClientsAddView.as_view(), name='requisites_add'),
    path('clients/edit/<int:client_id>/requisites/edit/<int:requisite_id>', views.RequisitesClientsEditView.as_view(), name='requisites_edit'),
]