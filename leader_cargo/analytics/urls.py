from django.conf import settings
from django.urls import path
from django.conf.urls.static import static

from . import views

app_name = 'analytics'

urlpatterns = [
    path('logistic-requests/', views.LogisticRequestsView.as_view(), name='logistic_requests'),
    path('logistic-requests/htmx-auto-update', views.LogisticRequestsViewAutoUpdate, name='logistic_requests_auto_update'),
    path('logistic-requests/add', views.LogisticRequestsAddView.as_view(), name='add_logistic_requests'),
    path('logistic-requests/edit/<int:request_id>', views.LogisticRequestsEditView.as_view(), name='edit_logistic_requests'),
    path('logistic-requests/edit/htmx/<int:request_id>', views.editLogisticRequest, name='edit_htmx_logistic_requests'),
    path('logistic-requests/status-new/<int:request_id>', views.NewStatusRequest.as_view(), name='request_status_new'),
    path('logistic-requests/status-new-to-draft/<int:request_id>', views.LogisticRequestsBackToManagerView.as_view(), name='request_status_new_to_draft'),
    path('logistic-requests/status-for-edit/<int:request_id>', views.LogisticRequestsForEditView.as_view(), name='request_status_for_edit'),
    path('logistic-requests/status-in-work/<int:request_id>', views.work_status_request, name='request_status_in_work'),
    path('logistic-requests/status-in-calculation/<int:request_id>', views.calculation_status_request, name='request_status_in_calculation'),
    path('logistic-requests/status-in-progress/<int:request_id>', views.progress_status_request, name='request_status_in_progress'),
    path('logistic-requests/status-close/<int:request_id>', views.LogisticRequestsCloseStatusView.as_view(), name='request_status_in_close'),
    path('logistic-requests/edit/<int:request_id>/delete-file/<int:file_id>', views.DeleteFileInRequest.as_view(), name='delete_file_logistic_requests'),
    path('logistic-requests/delete/<int:request_id>', views.DeleteLogisticRequestsView.as_view(), name='delete_logistic_requests'),
    path('logistic-requests/edit/<int:request_id>/add-goods', views.AddGoodsLogisticRequestsView.as_view(), name='add_goods_logistic_requests'),
    path('logistic-requests/edit-goods/<int:goods_id>', views.editGoodsLogisticRequests, name='edit_goods_logistic_requests'),
    path('logistic-requests/edit/<int:request_id>/delete-goods/<int:goods_id>', views.DeleteGoodsLogisticRequestsView.as_view(), name='delete_goods_logistic_requests'),
    path('logistic-requests/edit/<int:bid_id>/add-bid', views.editBidLogisticRequestsView, name='add_bid'),


    path('calculator/', views.LogisticCalculatorView.as_view(), name='calculator'),

    path('carriers-list/', views.LogisticCarriersList.as_view(), name='carriers_list'),
    path('carriers-list/add', views.AddLogisticCarriersList.as_view(), name='add_carrier'),
    path('carriers-list/edit/<int:carrier_id>', views.EditLogisticCarriersList.as_view(), name='edit_carrier'),
    path('carriers-list/delete/<int:carrier_id>', views.DeleteLogisticCarriersList.as_view(), name='delete_carrier'),
    path('carriers-list/add-road', views.AddRoad.as_view(), name='add_road'),
    path('carriers-list/edit-road/<int:road_id>', views.EditRoad.as_view(), name='edit_road'),
    path('carriers-list/delete-road/<int:road_id>', views.DeleteRoad.as_view(), name='delete_road'),
    path('carriers-list/add-road-to-carrier/<int:carrier_id>', views.addRoadToCarriers, name='add_road_to_carrier'),
    path('carriers-list/edit-road-to-carrier/<int:carrier_id>/<int:road_id>', views.editRoadToCarriers, name='edit_road_to_carrier'),
    path('carriers-list/delete-road-to-carrier/<int:carrier_id>/<int:road_id>', views.deleteRoadToCarriers, name='delete_road_to_carrier'),
    path('carriers-list/price-list-to-carrier-road/<int:carrier_id>/<int:road_id>', views.priceListToCarrierRoad, name='price_list'),
    path('carriers-list/add-price-list-to-carrier-road/<int:carrier_id>/<int:road_id>', views.addPriceListToCarrierRoad, name='add_price_list'),
    path('carriers-list/edit-price-list-to-carrier-road/<int:density_id>', views.editPriceListToCarrierRoad, name='edit_price_list'),

    path('download/<int:file_id>', views.download, name='download_client_payment'),

    path('carrier-files/', views.LogisticMainView.as_view(), name='carrier'),
    path('carrier-files/update-article-status/<int:article_id>', views.change_article_status, name='update_article'),
    path('carrier-files/edit-transport-tariff/<int:article_id>', views.EditTransportTariff.as_view(), name='edit_transportation_tariff_for_clients'),
    path('carrier-files/edit-article/<int:article_id>', views.EditTableArticleView.as_view(), name='edit_table_article'),
    path('carrier-files/delete-article/<int:article_id>', views.DeleteArticleView.as_view(), name='delete_table_article'),
    path('carrier-files/edit-article-manager/<int:article_id>', views.paid_by_the_client_status, name='edit_table_manager_article'),
    path('carrier-files/add-payment-file/<int:article_id>', views.add_payment_file, name='add_payment_file'),
    path('carrier-files/delete-payment-file/<int:article_id>/<int:file_id>', views.delete_payment_file, name='delete_payment_file'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

htmx_patterns = [
    path('carrier-files/amount-fund', views.amountOfFund, name='amount_fund'),
    path('carrier-files/edit/<int:article_id>', views.edit_article_in_table, name='edit_article'),
    path('carrier-files/delete/<int:article_id>', views.delete_article_in_table, name='delete_article'),
]

urlpatterns += htmx_patterns
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
