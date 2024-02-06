import datetime
import os
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404, FileResponse
from django.utils.timezone import make_aware
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView, ListView
from .forms import AddCarrierFilesForm, EditTableArticleForm, EditTransportationTariffForClients, AddCarriersListForm, EditCarriersListForm, DeleteCarriersListForm, AddRoadForm, EditRoadForm, DeleteRoadForm, AddRoadToCarriersForm, \
    DeleteRoadToCarriersForm, AddRequestsForLogisticsCalculationsForm, EditRequestsForLogisticsCalculationsForm, AddGoodsRequestLogisticsForm, NewStatusRequestForm, EditGoodsRequestLogisticsForm, EditRoadToCarriersForm, \
    EditPaidByTheClientArticleForm
from .models import CargoFiles, CargoArticle, RequestsForLogisticsCalculations, CarriersList, RoadsList, RequestsForLogisticsGoods, RequestsForLogisticFiles, CarriersRoadParameters, PriceListsOfCarriers, PaymentDocumentsForArticles
from django.shortcuts import get_object_or_404
# FROM MAIN
from main.models import CustomUser
from main.utils import DataMixin, MyLoginMixin
# EXTERNAL LIBRARIES
import openpyxl
import xlrd


def download(request, file_id):
    obj = PaymentDocumentsForArticles.objects.get(pk=file_id)
    if obj:
        return FileResponse(obj.file_path)
    raise Http404


class LogisticRequestsView(MyLoginMixin, DataMixin, TemplateView):
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    template_name = 'analytics/logistics_requests.html'
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = RequestsForLogisticsCalculations.objects.filter(initiator=self.request.user.pk)
        context['reports_work'] = context['reports'].exclude(status='Черновик')
        context['reports_draft'] = context['reports'].filter(status='Черновик')
        context['table_paginator'] = Paginator(context['reports_work'], 20)
        page_number = self.request.GET.get('page')
        context['table_paginator_obj'] = context['table_paginator'].get_page(page_number)
        context['reports'] = context['table_paginator_obj']

        if self.request.user.role == 'Логист':
            c_def = self.get_user_context(title="Запросы логисту")
        else:
            c_def = self.get_user_context(title="Запросы на просчет")
        return dict(list(context.items()) + list(c_def.items()))


class LogisticRequestsAddView(MyLoginMixin, DataMixin, CreateView):
    model = RequestsForLogisticsCalculations
    form_class = AddRequestsForLogisticsCalculationsForm
    template_name = 'analytics/logistics_requests_add.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Создание запроса")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.initiator = self.request.user
        new_data.status = 'Черновик'
        new_data.save()
        return redirect('analytics:edit_logistic_requests', new_data.pk)


class LogisticRequestsEditView(MyLoginMixin, DataMixin, UpdateView):
    model = RequestsForLogisticsCalculations
    form_class = EditRequestsForLogisticsCalculationsForm
    pk_url_kwarg = 'request_id'
    template_name = 'analytics/logistics_requests_edit.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:logistic_requests')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['my_request'] = self.get_object()
        context['carriers'] = CarriersList.objects.all()
        context['roads'] = RoadsList.objects.all()
        context['goods'] = RequestsForLogisticsGoods.objects.filter(request=context['my_request'])
        if context['my_request'].description:
            context['my_request_description'] = context['my_request'].description
            context['my_request_description_carriers'] = context['my_request_description'].split('\n')[0]
            context['my_request_description_roads'] = context['my_request_description'].split('\n')[1]
        context['all_documents'] = context['my_request'].requestsforlogisticfiles_set.values("id", "name")
        c_def = self.get_user_context(title="Редактирование запроса на просчет")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        if new_data.status == 'Черновик':
            carriers = ''
            roads = ''
            for req in self.request.POST:
                if 'road' in req:
                    roads += ' ' + req.split('-')[1]
                elif 'carrier' in req:
                    carriers += ' ' + req.split('-')[1]
            new_data.description = carriers + '\n' + roads
            new_data.save()
            for f in self.request.FILES.getlist('files_for_request'):
                new_data.requestsforlogisticfiles_set.create(name=f, file_path_request=f)
        return redirect('analytics:edit_logistic_requests', new_data.pk)


class NewStatusRequest(MyLoginMixin, DataMixin, UpdateView):
    model = RequestsForLogisticsCalculations
    form_class = NewStatusRequestForm
    pk_url_kwarg = 'request_id'
    context_object_name = 'my_request'
    template_name = 'analytics/request_status_new.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:logistic_requests')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Отправление запроса логисту")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        if new_data.status == 'Черновик':
            new_data.status = 'Новый'
            new_data.save()
            return redirect('analytics:logistic_requests')
        return redirect('analytics:edit_logistic_requests', new_data.pk)


class AddGoodsLogisticRequestsView(MyLoginMixin, DataMixin, CreateView):
    model = RequestsForLogisticsGoods
    form_class = AddGoodsRequestLogisticsForm
    pk_url_kwarg = 'request_id'
    template_name = 'analytics/add_goods_for_requests_logistic.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['good'] = RequestsForLogisticsGoods.objects.last()
        context['my_request'] = context['good'].request
        context['count_goods'] = RequestsForLogisticsGoods.objects.filter(request=self.kwargs['request_id']).count()
        c_def = self.get_user_context(title="Создание товара к запросу")
        return dict(list(context.items()) + list(c_def.items()))

    def get(self, request, *args, **kwargs):
        my_request = get_object_or_404(RequestsForLogisticsCalculations, pk=self.kwargs['request_id'])
        my_request.requestsforlogisticsgoods_set.create()
        return super().get(request, *args, **kwargs)


def editGoodsLogisticRequests(request, goods_id):
    good = RequestsForLogisticsGoods.objects.get(pk=goods_id)
    if request.FILES:
        good.photo_path_logistic_goods = request.FILES["photo_path_logistic_goods"]
        good.save()
    elif request.POST:
        if request.htmx.trigger == 'description':
            good.description = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'material':
            good.material = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'number_of_packages':
            good.number_of_packages = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'quantity_in_each_package':
            good.quantity_in_each_package = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'size_of_packaging':
            good.size_of_packaging = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'gross_weight_of_packaging':
            good.gross_weight_of_packaging = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'total_volume':
            good.total_volume = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'total_gross_weight':
            good.total_gross_weight = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'total_quantity':
            good.total_quantity = request.POST[request.htmx.trigger]
        elif request.htmx.trigger == 'trademark':
            good.trademark = request.POST[request.htmx.trigger]
        good.save()
    return render(request, 'analytics/edit_goods_for_requests_logistic.html',
                  {'good': good})


class DeleteGoodsLogisticRequestsView(MyLoginMixin, DataMixin, DeleteView):
    model = RequestsForLogisticsGoods
    pk_url_kwarg = 'goods_id'
    template_name = 'analytics/delete_goods_for_requests_logistic.html'
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    login_url = reverse_lazy('main:login')

    def get(self, request, *args, **kwargs):
        good = self.get_object()
        good.delete()
        goods = RequestsForLogisticsGoods.objects.filter(request=self.kwargs['request_id'])
        my_request = RequestsForLogisticsCalculations.objects.get(pk=self.kwargs['request_id'])
        return render(request, self.template_name, {'goods': goods, 'my_request': my_request})


class DeleteFileInRequest(MyLoginMixin, DataMixin, DeleteView):
    model = RequestsForLogisticFiles
    pk_url_kwarg = 'file_id'
    context_object_name = 'my_file'
    template_name = 'analytics/delete_file_in_request.html'
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    success_url = reverse_lazy('analytics:edit_logistic_requests')
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Удаление файла к запросу")
        return dict(list(context.items()) + list(c_def.items()))

    def delete(self, request, *args, **kwargs):
        file = self.get_object()
        file.delete()
        return redirect('analytics:edit_logistic_requests', file.request.pk)


class DeleteLogisticRequestsView(MyLoginMixin, DataMixin, DeleteView):
    model = RequestsForLogisticsCalculations
    pk_url_kwarg = 'request_id'
    context_object_name = 'my_request'
    template_name = 'analytics/delete_request.html'
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    success_url = reverse_lazy('analytics:logistic_requests')
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Удаление файла к запросу")
        return dict(list(context.items()) + list(c_def.items()))


class LogisticCarriersList(MyLoginMixin, DataMixin, ListView):
    model = CarriersList
    context_object_name = 'carriers'
    template_name = 'analytics/carriers_list.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["roads"] = RoadsList.objects.all()
        c_def = self.get_user_context(title="Список перевозчиков")
        return dict(list(context.items()) + list(c_def.items()))


class AddLogisticCarriersList(MyLoginMixin, DataMixin, CreateView):
    model = CarriersList
    form_class = AddCarriersListForm
    template_name = 'analytics/create_carriers_list.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Добавление перевозчика")
        return dict(list(context.items()) + list(c_def.items()))


class EditLogisticCarriersList(MyLoginMixin, DataMixin, UpdateView):
    model = CarriersList
    form_class = EditCarriersListForm
    pk_url_kwarg = 'carrier_id'
    template_name = 'analytics/edit_carriers_list.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["carrier"] = self.get_object()
        c_def = self.get_user_context(title="Изменение данных перевозчика")
        return dict(list(context.items()) + list(c_def.items()))


class DeleteLogisticCarriersList(MyLoginMixin, DataMixin, UpdateView):
    model = CarriersList
    form_class = DeleteCarriersListForm
    template_name = 'analytics/delete_carriers_list.html'
    pk_url_kwarg = 'carrier_id'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["carrier"] = self.get_object()
        c_def = self.get_user_context(title="Удаление перевозчика")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        carrier = self.get_object()
        if carrier.status:
            carrier.status = False
        carrier.save()
        return super().post(request, *args, **kwargs)


class AddRoad(MyLoginMixin, DataMixin, CreateView):
    model = RoadsList
    form_class = AddRoadForm
    template_name = 'analytics/create_road.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Добавление дороги")
        return dict(list(context.items()) + list(c_def.items()))


class EditRoad(MyLoginMixin, DataMixin, UpdateView):
    model = RoadsList
    form_class = EditRoadForm
    pk_url_kwarg = 'road_id'
    template_name = 'analytics/edit_road.html'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["road"] = self.get_object()
        c_def = self.get_user_context(title="Изменение данных дороги")
        return dict(list(context.items()) + list(c_def.items()))


class DeleteRoad(MyLoginMixin, DataMixin, UpdateView):
    model = RoadsList
    form_class = DeleteRoadForm
    template_name = 'analytics/delete_road.html'
    pk_url_kwarg = 'road_id'
    login_url = reverse_lazy('main:login')
    success_url = reverse_lazy('analytics:carriers_list')
    role_have_perm = ['Супер Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["road"] = self.get_object()
        c_def = self.get_user_context(title="Удаление дороги")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        road = self.get_object()
        if road.status:
            road.status = False
        road.save()
        return super().post(request, *args, **kwargs)


def addRoadToCarriers(request, carrier_id):
    carrier = CarriersList.objects.get(pk=carrier_id)
    form = AddRoadToCarriersForm
    template_name = 'analytics/add_road_to_carrier.html'
    success_url = reverse_lazy('analytics:carriers_list')
    if request.POST:
        road = RoadsList.objects.get(pk=request.POST['road'])
        min_transportation_time = request.POST.get('min_transportation_time', 0)
        if len(min_transportation_time) == 0:
            min_transportation_time = 0
        max_transportation_time = request.POST.get('max_transportation_time', 0)
        if len(max_transportation_time) == 0:
            max_transportation_time = 0
        carrier.roads.add(road, through_defaults={
            "min_transportation_time": min_transportation_time,
            "max_transportation_time": max_transportation_time
        })
        return redirect(success_url)
    return render(request, template_name, {'carrier': carrier, 'form': form})


def editRoadToCarriers(request, carrier_id, road_id):
    carrier = CarriersList.objects.get(pk=carrier_id)
    road = RoadsList.objects.get(pk=road_id)
    roads_parameters = CarriersRoadParameters.objects.get(carrier=carrier, road=road)
    form = EditRoadToCarriersForm(instance=roads_parameters)
    template_name = 'analytics/edit_road_to_carrier.html'
    success_url = reverse_lazy('analytics:carriers_list')
    if request.POST:
        form = EditRoadToCarriersForm(request.POST)
        if form.is_valid():
            min_transportation_time = request.POST.get('min_transportation_time', 0)
            if len(min_transportation_time) == 0:
                min_transportation_time = 0
            max_transportation_time = request.POST.get('max_transportation_time', 0)
            if len(max_transportation_time) == 0:
                max_transportation_time = 0
            roads_parameters.min_transportation_time = min_transportation_time
            roads_parameters.max_transportation_time = max_transportation_time
            roads_parameters.save()
            return redirect(success_url)
    return render(request, template_name, {'carrier': carrier,
                                           'road': road,
                                           'form': form,
                                           'roads_parameters': roads_parameters})


def deleteRoadToCarriers(request, carrier_id, road_id):
    carrier = CarriersList.objects.get(pk=carrier_id)
    road = RoadsList.objects.get(pk=road_id)
    roads_parameters = CarriersRoadParameters.objects.get(carrier=carrier, road=road)
    form = DeleteRoadToCarriersForm
    template_name = 'analytics/delete_road_to_carrier.html'
    success_url = reverse_lazy('analytics:carriers_list')
    if request.POST:
        carrier.roads.remove(road)
        return redirect(success_url)
    return render(request, template_name, {'carrier': carrier,
                                           'road': road,
                                           'form': form,
                                           'roads_parameters': roads_parameters})


def priceListToCarrierRoad(request, carrier_id, road_id):
    carrier = CarriersList.objects.get(pk=carrier_id)
    road = RoadsList.objects.get(pk=road_id)
    roads_parameters = CarriersRoadParameters.objects.get(carrier=carrier, road=road)
    form = DeleteRoadToCarriersForm
    template_name = 'analytics/price_list.html'
    return render(request, template_name, {'carrier': carrier,
                                           'road': road,
                                           'form': form,
                                           'roads_parameters': roads_parameters})


def addPriceListToCarrierRoad(request, carrier_id, road_id):
    template_name = 'analytics/add_price_list.html'
    carrier = CarriersList.objects.get(pk=carrier_id)
    road = RoadsList.objects.get(pk=road_id)
    roads_parameters = CarriersRoadParameters.objects.get(carrier=carrier, road=road)
    density = roads_parameters.density.create()
    count = roads_parameters.density.count()
    return render(request, template_name, {'carrier': carrier,
                                           'road': road,
                                           'count': count,
                                           'density': density,
                                           'roads_parameters': roads_parameters})


def editPriceListToCarrierRoad(request, density_id):
    density = PriceListsOfCarriers.objects.get(pk=density_id)
    if request.POST:
        if request.POST.get('min_density'):
            density.min_density = request.POST.get('min_density')
        elif request.POST.get('max_density'):
            density.max_density = request.POST.get('max_density')
        elif request.POST.get('price'):
            density.price = request.POST.get('price')
        density.save()
    return render(request, 'analytics/edit_price_list.html',
                  {'density': density})


class LogisticCalculatorView(MyLoginMixin, DataMixin, TemplateView):
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    template_name = 'analytics/calculator.html'
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Калькулятор логистики")
        return dict(list(context.items()) + list(c_def.items()))


class LogisticMainView(MyLoginMixin, DataMixin, CreateView):
    model = CargoFiles
    form_class = AddCarrierFilesForm
    template_name = 'analytics/logistic_main/logistic_main.html'
    context_object_name = 'all_articles'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП', 'Логист', 'Менеджер']
    success_url = reverse_lazy('analytics:carrier')
    message = dict()
    message['update'] = False
    factor_kg_01 = 0.1
    factor_kg_02 = 0.2
    factor_volume_10 = 10
    factor_volume_20 = 20

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_pk_string'] = str(self.request.user.pk)
        context['all_articles'] = CargoArticle.objects.all()
        if self.request.user.role == 'Логист' or self.request.user.role == 'Супер Администратор':
            context['count_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).count()
            if 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100) == 100 and context['count_empty_responsible_manager'] != 0:
                context['pb_count_empty_responsible_manager'] = 99
            else:
                context['pb_count_empty_responsible_manager'] = 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100)
            context['count_empty_path_format'] = context['all_articles'].filter(path_format=None).count()
            if 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100) == 100 and context['count_empty_path_format'] != 0:
                context['pb_count_empty_path_format'] = 99
            else:
                context['pb_count_empty_path_format'] = 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100)
            context['all_article_with_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).values('article')
            context['all_article_with_empty_path_format'] = context['all_articles'].filter(path_format=None).values('article')
            context['all_articles_without_insurance'] = context['all_articles'].filter(insurance_cost__in=[None, '']).filter(time_create__year=datetime.datetime.now().year, time_create__month=datetime.datetime.now().month, time_create__day=datetime.datetime.now().day).values('article', 'weight', 'time_from_china')
            context['new_all_articles_without_insurance'] = []
            for art in context['all_articles_without_insurance']:
                if float(art['weight'].replace(" ", "").replace(",", ".")) > 10:
                    context['new_all_articles_without_insurance'].append(art)
            context['all_articles_without_insurance'] = context['new_all_articles_without_insurance']
            context['count_articles_without_insurance'] = len(context['all_articles_without_insurance'])

        context['count_notifications'] = context['all_articles'].filter(status='Прибыл в РФ').filter(time_cargo_release=None).count()
        context['all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None)
        context['count_all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None).count()

        if self.request.user.role == 'Менеджер':
            context['all_articles'] = context['all_articles'].filter(responsible_manager=f'{self.request.user.pk}')

        if self.request.user.role == 'РОП':
            managers_pk = [self.request.user.pk]
            context['managers'] = [{
                "pk": f"{self.request.user.pk}",
                "fi": f"{self.request.user.last_name} {self.request.user.first_name}"
            }]
            for user in CustomUser.objects.filter(role='Менеджер').filter(town=self.request.user.town).values('pk', 'last_name', 'first_name'):
                context['managers'].append({
                    "pk": f"{user['pk']}",
                    "fi": f"{user['last_name']} {user['first_name']}"
                })
                managers_pk.append(user['pk'])
            context['all_articles'] = context['all_articles'].filter(responsible_manager__in=managers_pk)
        elif self.request.user.role == 'Логист':
            context['managers'] = []
            for user in CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], status=True).values('pk', 'last_name', 'first_name').order_by('last_name'):
                context['managers'].append({
                    "pk": f"{user['pk']}",
                    "fi": f"{user['last_name']} {user['first_name']}"
                })

        context['count_notifications'] = context['all_articles'].filter(status='Прибыл в РФ').filter(time_cargo_release=None).count()

        if self.request.htmx:
            if self.request.htmx.trigger == 'article_search':
                q = self.request.GET.get('q') if self.request.GET.get('q') is not None else ''
                context['q'] = q
                context['all_articles'] = context['all_articles'].filter(article__iregex=q.replace(' ', ''))

        if self.request.GET.get('status') and self.request.GET.get('status') != 'Статус прибытия':
            context['status_now'] = self.request.GET.get('status')
            context['all_articles'] = context['all_articles'].filter(status=self.request.GET.get('status'))
        else:
            context['status_now'] = 'Статус прибытия'

        if self.request.GET.get('responsible_manager') and self.request.GET.get('responsible_manager') != 'Все менеджеры':
            context['responsible_manager_current'] = self.request.GET.get('responsible_manager')
            context['all_articles'] = context['all_articles'].filter(responsible_manager=context['responsible_manager_current'])
        else:
            context['responsible_manager_current'] = 'Все менеджеры'

        if self.request.GET.get('date'):
            context['date_current'] = self.request.GET.get('date')
            context['all_articles'] = context['all_articles'].filter(time_from_china__gte=make_aware(datetime.datetime.strptime(context['date_current'], '%Y-%m-%d')))
        else:
            if not self.request.htmx:
                if self.request.user.role == 'Логист':
                    first_day = (datetime.datetime.now() - datetime.timedelta(days=28)).replace(day=1)
                    context['date_current'] = first_day.strftime('%Y-%m-%d')
                    context['all_articles'] = context['all_articles'].filter(time_from_china__gte=make_aware(first_day))

        if self.request.GET.get('end_date'):
            context['end_date_current'] = self.request.GET.get('end_date')
            context['all_articles'] = context['all_articles'].filter(time_from_china__lte=make_aware(datetime.datetime.strptime(context['end_date_current'], '%Y-%m-%d')))

        if self.request.GET.get('paid_by_the_client') and self.request.GET.get('paid_by_the_client') != 'Оплата клиентом':
            context['paid_by_the_client_current'] = self.request.GET.get('paid_by_the_client')
            context['all_articles'] = context['all_articles'].filter(paid_by_the_client_status=context['paid_by_the_client_current'])
        else:
            context['paid_by_the_client_current'] = 'Оплата клиентом'

        if self.request.GET.get('paid_to_the_carrier') and self.request.GET.get('paid_to_the_carrier') != 'Оплата перевозчику':
            context['paid_to_the_carrier_current'] = self.request.GET.get('paid_to_the_carrier')
            context['all_articles'] = context['all_articles'].filter(payment_to_the_carrier_status=context['paid_to_the_carrier_current'])
        else:
            context['paid_to_the_carrier_current'] = 'Оплата перевозчику'

        if self.request.GET.get('carrier') and self.request.GET.get('carrier') != 'Все перевозчики':
            context['carrier_now'] = self.request.GET.get('carrier')
            context['all_articles'] = context['all_articles'].filter(carrier=self.request.GET.get('carrier'))
        else:
            context['carrier_now'] = 'Все перевозчики'

        context['form_article'] = []
        context['all_weight'] = 0
        context['all_volume'] = 0
        context['all_prr'] = 0
        context['all_tat'] = 0
        for article in context['all_articles']:
            if article.status:
                context['all_weight'] = context['all_weight'] + float(article.weight.replace(" ", "").replace(",", "."))
                context['all_volume'] = context['all_volume'] + float(article.volume.replace(" ", "").replace(",", "."))
                if article.prr:
                    context['all_prr'] = context['all_prr'] + float(article.prr.replace(" ", "").replace(",", "."))
                if article.tat_cost:
                    context['all_tat'] = context['all_tat'] + float(article.tat_cost.replace(" ", "").replace(",", "."))
        context['table_paginator'] = Paginator(context['all_articles'], 50)
        page_number = self.request.GET.get('page', 1)
        context['table_paginator_obj'] = context['table_paginator'].get_page(page_number)
        context['all_articles'] = context['table_paginator_obj']
        context['set_query'] = ''
        for req in self.request.GET:
            if req != 'page':
                context['set_query'] += f'&{req}={self.request.GET.get(req)}'
        context['vputi'] = 'В пути'
        context['pribil'] = 'Прибыл в РФ'
        if self.message['update']:
            context['message'] = self.message
        else:
            context['message'] = []
        self.message['update'] = False
        c_def = self.get_user_context(title="Учет грузов")
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx:
            return "analytics/logistic_main/table.html"
        else:
            return 'analytics/logistic_main/logistic_main.html'

    def form_valid(self, form, **kwargs):
        file_carrier = form.save(commit=False)
        file_carrier.save()
        self.message['success_articles'] = []
        self.message['warning_articles'] = []
        self.message['info_articles'] = []
        self.message['error'] = []

        try:
            if file_carrier.name_carrier == 'Ян':
                carrier = 'Ян'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'media', str(file_carrier.file_path)), data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'leader_cargo/media', str(file_carrier.file_path)), data_only=True)
                sheet = dataframe.get_sheet_by_name('运单')
                address_transportation_cost = ""
                for row in range(6, sheet.max_row):
                    if sheet[row][0].value == '送货费':
                        address_transportation_cost = float(sheet[row][13].value) / (row - 6)
                for row in range(6, sheet.max_row):
                    if sheet[row][0].value and sheet[row][0].value != '送货费':
                        article = str(sheet[row][0].value).replace(' ', '')
                        name_goods = str(sheet[row][1].value) if sheet[row][1].value else ""
                        number_of_seats = str(sheet[row][2].value)
                        weight = str(sheet[row][4].value) if sheet[row][4].value else ""
                        volume = str(sheet[row][5].value) if sheet[row][5].value else ""
                        transportation_tariff = str(sheet[row][6].value) if sheet[row][6].value else ""
                        cost_goods = str(sheet[row][7].value) if sheet[row][7].value else ""
                        insurance_cost = str(sheet[row][8].value) if sheet[row][8].value else ""
                        packaging_cost = str(sheet[row][9].value) if sheet[row][9].value else ""
                        if sheet[row][11].value:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][11].value, 0) if sheet[row][11].value else ""
                        else:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[3][6].value, 0) if sheet[3][6].value else ""
                            except TypeError:
                                time_from_china = sheet[3][6].value
                        total_cost = str(sheet[row][13].value) if sheet[row][13].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if sheet[row][6].value > 60:
                                    transportation_tariff_with_factor = float(sheet[row][6].value + self.factor_volume_10)
                                else:
                                    transportation_tariff_with_factor = float(sheet[row][6].value + self.factor_kg_01)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if sheet[row][6].value > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_10 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_01 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.weight == weight and old.time_from_china == make_aware(time_from_china):
                                check = True
                                old.carrier = carrier
                                old.number_of_seats = number_of_seats
                                old.volume = volume
                                old.transportation_tariff = transportation_tariff
                                if old.transportation_tariff_with_factor:
                                    old.transportation_tariff_with_factor = transportation_tariff_with_factor
                                    old.total_cost_with_factor = total_cost_with_factor
                                old.cost_goods = cost_goods
                                old.insurance_cost = insurance_cost
                                old.packaging_cost = packaging_cost
                                old.total_cost = total_cost
                                old.cargo_id = file_carrier
                                old.address_transportation_cost = address_transportation_cost
                                old.save()
                                self.message['info_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' "
                                                                     f"и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}'")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                                address_transportation_cost=address_transportation_cost,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
            elif file_carrier.name_carrier == 'Ян (полная машина)':
                carrier = 'Ян'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'media', str(file_carrier.file_path)), data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'leader_cargo/media', str(file_carrier.file_path)), data_only=True)
                sheet = dataframe.active
                article = str(sheet[3][3].value).replace(' ', '')
                number_of_seats = str(sheet[3][4].value)
                weight = str(sheet[3][5].value) if sheet[3][5].value else ""
                volume = str(sheet[3][6].value) if sheet[3][6].value else ""
                address_transportation_cost = float(sheet[3][9].value)
                try:
                    time_from_china = xlrd.xldate.xldate_as_datetime(sheet[3][0].value, 0) if sheet[3][0].value else ""
                except TypeError:
                    time_from_china = sheet[3][0].value
                try:
                    make_aware(time_from_china)
                except:
                    time_from_china = datetime.datetime.strptime(time_from_china, '%Y.%m.%d')
                total_cost = str(sheet[3][10].value) if sheet[3][10].value else ""
                check = False
                old_articles = CargoArticle.objects.filter(article=article)
                for old in old_articles:
                    if old.article == article and old.status == 'В пути':
                        check = True
                        self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                        break
                if not check:
                    CargoArticle.objects.create(
                        article=article,
                        carrier=carrier,
                        number_of_seats=number_of_seats,
                        weight=weight,
                        volume=volume,
                        time_from_china=make_aware(time_from_china),
                        total_cost=total_cost,
                        cargo_id=file_carrier,
                        address_transportation_cost=address_transportation_cost,
                    )
                    self.message['success_articles'].append(article)
            elif file_carrier.name_carrier == 'Валька':
                carrier = 'Валька'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}", data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}", data_only=True)
                sheet = dataframe.active
                for row in range(790, sheet.max_row):
                    if sheet[row][4].value and sheet[row][3].value and sheet[row][2].value:
                        article = str(sheet[row][4].value).replace(' ', '')
                        name_goods = str(sheet[row][6].value) if sheet[row][6].value else ""
                        number_of_seats = str(sheet[row][7].value)
                        weight = str(sheet[row][8].value) if sheet[row][8].value else ""
                        volume = str(sheet[row][9].value) if sheet[row][9].value else ""
                        transportation_tariff = str(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2))
                        cost_goods = str(sheet[row][13].value) if sheet[row][13].value else ""
                        insurance_cost = str(sheet[row][14].value) if sheet[row][14].value else ""
                        packaging_cost = str(sheet[row][15].value) if sheet[row][15].value else ""
                        try:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][3].value, 0) if sheet[row][3].value else ""
                        except TypeError:
                            time_from_china = sheet[row][3].value
                        total_cost = str(sheet[row][16].value) if sheet[row][16].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) > 60:
                                    transportation_tariff_with_factor = float(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) + self.factor_volume_20)
                                else:
                                    transportation_tariff_with_factor = float(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) + self.factor_kg_02)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_20 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_02 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.number_of_seats == number_of_seats and old.cost_goods == cost_goods and old.insurance_cost == insurance_cost \
                                    and old.weight == weight and old.volume == volume and old.transportation_tariff == transportation_tariff and old.packaging_cost == packaging_cost \
                                    and old.time_from_china == make_aware(time_from_china) and old.total_cost == total_cost:
                                check = True
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
            elif file_carrier.name_carrier == 'Мурад':
                carrier = 'Мурад'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}", data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}", data_only=True)
                sheet = dataframe.active
                for row in range(2, sheet.max_row + 1):
                    if sheet[row][5].value:
                        if sheet[row][5].value.find("（") != -1:
                            article = str(sheet[row][5].value.split("（")[0].replace(" ", "")) + '\n' + str(sheet[row][3].value)
                            if sheet[row][5].value.find("）") != -1:
                                name_goods = str(sheet[row][5].value.split("（")[1].replace(" ", "").replace("）", ""))
                            else:
                                name_goods = str(sheet[row][5].value.split("（")[1].replace(" ", "").replace(")", ""))
                        else:
                            article = str(sheet[row][5].value.split("(")[0].replace(" ", "")) + '\n' + str(sheet[row][3].value)
                            if sheet[row][5].value.find("）") != -1:
                                name_goods = str(sheet[row][5].value.split("(")[1].replace(" ", "").replace("）", ""))
                            else:
                                name_goods = str(sheet[row][5].value.split("(")[1].replace(" ", "").replace(")", ""))
                        number_of_seats = str(sheet[row][4].value)
                        weight = str(sheet[row][6].value) if sheet[row][4].value else ""
                        volume = str(sheet[row][7].value) if sheet[row][5].value else ""
                        transportation_tariff = str(sheet[row][15].value) if sheet[row][15].value else ""
                        cost_goods = str(sheet[row][12].value) if sheet[row][12].value else ""
                        insurance_cost = str(sheet[row][13].value) if sheet[row][13].value else ""
                        packaging_cost = str(sheet[row][14].value) if sheet[row][14].value else ""
                        try:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][1].value, 0) if sheet[row][1].value else ""
                        except TypeError:
                            time_from_china = sheet[row][1].value if sheet[row][1].value else ""
                        total_cost = str(sheet[row][18].value) if sheet[row][18].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if sheet[row][15].value > 60:
                                    transportation_tariff_with_factor = float(sheet[row][15].value + self.factor_volume_20)
                                else:
                                    transportation_tariff_with_factor = float(sheet[row][15].value + self.factor_kg_02)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if sheet[row][15].value > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_20 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_02 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.status == 'В пути':
                                check = True
                                self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
            elif file_carrier.name_carrier == 'Гелик':
                carrier = 'Гелик'
                if settings.DEBUG:
                    workbook = xlrd.open_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}")
                else:
                    workbook = xlrd.open_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}")
                sheet = workbook.sheet_by_index(0)
                for row in range(7, sheet.nrows):
                    if sheet[row][1].value:
                        if sheet[2][1].value.find(":") != -1:
                            article = str(sheet[2][1].value.split(":")[1].replace(" ", ""))
                        else:
                            article = str(sheet[2][1].value.split("：")[1].replace(" ", ""))
                        name_goods = str(sheet[row][1].value) if sheet[row][1].value else ""
                        number_of_seats = str(sheet[row][2].value)
                        weight = str(sheet[row][3].value) if sheet[row][3].value else ""
                        volume = str(sheet[row][4].value) if sheet[row][4].value else ""
                        transportation_tariff = str(sheet[row][5].value) if sheet[row][5].value else ""
                        cost_goods = str(sheet[row][8].value) if sheet[row][8].value else ""
                        insurance_cost = str(sheet[row][9].value) if sheet[row][9].value else ""
                        packaging_cost = str(sheet[row][6].value) if sheet[row][6].value else ""
                        if sheet[4][7].value.find(":") != -1:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[4][7].value.split(":")[1].replace(" ", ""), 0)
                            except TypeError:
                                time_from_china = datetime.datetime.strptime(sheet[4][7].value.split(":")[1].replace(" ", ""), '%Y/%m/%d')
                        else:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[4][7].value.split("：")[1].replace(" ", ""), 0)
                            except TypeError:
                                time_from_china = datetime.datetime.strptime(sheet[4][7].value.split("：")[1].replace(" ", ""), '%Y/%m/%d')
                        total_cost = str(sheet[row][11].value) if sheet[row][11].value else ""
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.status == 'В пути':
                                check = True
                                self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
        except Exception as e:
            self.message['error'].append(e)
        self.message['update'] = True
        return redirect('{}?{}'.format(reverse('analytics:carrier'), self.request.META['QUERY_STRING']))


class CarrierFilesView(MyLoginMixin, DataMixin, CreateView):
    model = CargoFiles
    form_class = AddCarrierFilesForm
    template_name = 'analytics/carrier_files.html'
    context_object_name = 'all_articles'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП', 'Логист', 'Менеджер']
    success_url = reverse_lazy('analytics:carrier')
    message = dict()
    message['update'] = False
    factor_kg_01 = 0.1
    factor_kg_02 = 0.2
    factor_volume_10 = 10
    factor_volume_20 = 20

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_pk_string'] = str(self.request.user.pk)
        context['all_articles'] = CargoArticle.objects.all()
        if self.request.user.role == 'Логист' or self.request.user.role == 'Супер Администратор':
            context['count_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).count()
            if 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100) == 100 and context['count_empty_responsible_manager'] != 0:
                context['pb_count_empty_responsible_manager'] = 99
            else:
                context['pb_count_empty_responsible_manager'] = 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100)
            context['count_empty_path_format'] = context['all_articles'].filter(path_format=None).count()
            if 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100) == 100 and context['count_empty_path_format'] != 0:
                context['pb_count_empty_path_format'] = 99
            else:
                context['pb_count_empty_path_format'] = 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100)
            context['all_article_with_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).values('article')
            context['all_article_with_empty_path_format'] = context['all_articles'].filter(path_format=None).values('article')
            context['all_articles_without_insurance'] = context['all_articles'].filter(insurance_cost__in=[None, '']).filter(time_from_china__gte=make_aware(datetime.datetime.now() - datetime.timedelta(days=11))).values('article', 'weight',
                                                                                                                                                                                                                            'time_from_china')
            context['new_all_articles_without_insurance'] = []
            for art in context['all_articles_without_insurance']:
                if float(art['weight'].replace(" ", "").replace(",", ".")) > 10:
                    context['new_all_articles_without_insurance'].append(art)
            context['all_articles_without_insurance'] = context['new_all_articles_without_insurance']
            context['count_articles_without_insurance'] = len(context['all_articles_without_insurance'])

        context['count_notifications'] = context['all_articles'].filter(status='Прибыл в РФ').filter(time_cargo_release=None).count()
        context['all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None)
        context['count_all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None).count()

        if self.request.user.role == 'Менеджер':
            context['all_articles'] = context['all_articles'].filter(responsible_manager=f'{self.request.user.pk}')

        if self.request.user.role == 'РОП':
            managers_pk = [self.request.user.pk]
            context['managers'] = [{
                "pk": f"{self.request.user.pk}",
                "fi": f"{self.request.user.last_name} {self.request.user.first_name}"
            }]
            for user in CustomUser.objects.filter(role='Менеджер').filter(town=self.request.user.town).values('pk', 'last_name', 'first_name'):
                context['managers'].append({
                    "pk": f"{user['pk']}",
                    "fi": f"{user['last_name']} {user['first_name']}"
                })
                managers_pk.append(user['pk'])
            context['all_articles'] = context['all_articles'].filter(responsible_manager__in=managers_pk)
        elif self.request.user.role == 'Логист':
            context['managers'] = []
            for user in CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], status=True).values('pk', 'last_name', 'first_name').order_by('last_name'):
                context['managers'].append({
                    "pk": f"{user['pk']}",
                    "fi": f"{user['last_name']} {user['first_name']}"
                })

        context['count_notifications'] = context['all_articles'].filter(status='Прибыл в РФ').filter(time_cargo_release=None).count()

        if self.request.htmx:
            if self.request.htmx.trigger == 'article_search':
                q = self.request.GET.get('q') if self.request.GET.get('q') is not None else ''
                context['q'] = q
                context['all_articles'] = context['all_articles'].filter(article__iregex=q)

        if self.request.GET.get('status') and self.request.GET.get('status') != 'Статус прибытия':
            context['status_now'] = self.request.GET.get('status')
            context['all_articles'] = context['all_articles'].filter(status=self.request.GET.get('status'))
        else:
            context['status_now'] = 'Статус прибытия'

        if self.request.GET.get('responsible_manager') and self.request.GET.get('responsible_manager') != 'Все менеджеры':
            context['responsible_manager_current'] = self.request.GET.get('responsible_manager')
            context['all_articles'] = context['all_articles'].filter(responsible_manager=context['responsible_manager_current'])
        else:
            context['responsible_manager_current'] = 'Все менеджеры'

        if self.request.GET.get('date'):
            context['date_current'] = self.request.GET.get('date')
            context['all_articles'] = context['all_articles'].filter(time_from_china__gte=make_aware(datetime.datetime.strptime(context['date_current'], '%Y-%m-%d')))
        else:
            if not self.request.htmx:
                if self.request.user.role == 'Логист':
                    first_day = (datetime.datetime.now() - datetime.timedelta(days=28)).replace(day=1)
                    context['date_current'] = first_day.strftime('%Y-%m-%d')
                    context['all_articles'] = context['all_articles'].filter(time_from_china__gte=make_aware(first_day))

        if self.request.GET.get('end_date'):
            context['end_date_current'] = self.request.GET.get('end_date')
            context['all_articles'] = context['all_articles'].filter(time_from_china__lte=make_aware(datetime.datetime.strptime(context['end_date_current'], '%Y-%m-%d')))

        if self.request.GET.get('paid_by_the_client') and self.request.GET.get('paid_by_the_client') != 'Оплата клиентом':
            context['paid_by_the_client_current'] = self.request.GET.get('paid_by_the_client')
            context['all_articles'] = context['all_articles'].filter(paid_by_the_client_status=context['paid_by_the_client_current'])
        else:
            context['paid_by_the_client_current'] = 'Оплата клиентом'

        if self.request.GET.get('paid_to_the_carrier') and self.request.GET.get('paid_to_the_carrier') != 'Оплата перевозчику':
            context['paid_to_the_carrier_current'] = self.request.GET.get('paid_to_the_carrier')
            context['all_articles'] = context['all_articles'].filter(payment_to_the_carrier_status=context['paid_to_the_carrier_current'])
        else:
            context['paid_to_the_carrier_current'] = 'Оплата перевозчику'

        if self.request.GET.get('carrier') and self.request.GET.get('carrier') != 'Все перевозчики':
            context['carrier_now'] = self.request.GET.get('carrier')
            context['all_articles'] = context['all_articles'].filter(carrier=self.request.GET.get('carrier'))
        else:
            context['carrier_now'] = 'Все перевозчики'

        context['form_article'] = []
        context['all_weight'] = 0
        context['all_volume'] = 0
        context['all_prr'] = 0
        context['all_tat'] = 0
        for article in context['all_articles']:
            if article.status:
                context['all_weight'] = context['all_weight'] + float(article.weight.replace(" ", "").replace(",", "."))
                context['all_volume'] = context['all_volume'] + float(article.volume.replace(" ", "").replace(",", "."))
                if article.prr:
                    context['all_prr'] = context['all_prr'] + float(article.prr.replace(" ", "").replace(",", "."))
                if article.tat_cost:
                    context['all_tat'] = context['all_tat'] + float(article.tat_cost.replace(" ", "").replace(",", "."))
        context['table_paginator'] = Paginator(context['all_articles'], 50)
        page_number = self.request.GET.get('page', 1)
        context['table_paginator_obj'] = context['table_paginator'].get_page(page_number)
        context['all_articles'] = context['table_paginator_obj']
        context['set_query'] = ''
        for req in self.request.GET:
            if req != 'page':
                context['set_query'] += f'&{req}={self.request.GET.get(req)}'
        context['vputi'] = 'В пути'
        context['pribil'] = 'Прибыл в РФ'
        if self.message['update']:
            context['message'] = self.message
        else:
            context['message'] = []
        self.message['update'] = False
        c_def = self.get_user_context(title="Учет грузов")
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx:
            return "analytics/components/table_for_carrier_files.html"
        else:
            return 'analytics/carrier_files.html'

    def form_valid(self, form, **kwargs):
        file_carrier = form.save(commit=False)
        file_carrier.save()
        self.message['success_articles'] = []
        self.message['warning_articles'] = []
        self.message['info_articles'] = []
        self.message['error'] = []

        try:
            if file_carrier.name_carrier == 'Ян':
                carrier = 'Ян'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'media', str(file_carrier.file_path)), data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'leader_cargo/media', str(file_carrier.file_path)), data_only=True)
                sheet = dataframe.get_sheet_by_name('运单')
                address_transportation_cost = ""
                for row in range(6, sheet.max_row):
                    if sheet[row][0].value == '送货费':
                        address_transportation_cost = float(sheet[row][13].value) / (row - 6)
                for row in range(6, sheet.max_row):
                    if sheet[row][0].value and sheet[row][0].value != '送货费':
                        article = str(sheet[row][0].value)
                        name_goods = str(sheet[row][1].value) if sheet[row][1].value else ""
                        number_of_seats = str(sheet[row][2].value)
                        weight = str(sheet[row][4].value) if sheet[row][4].value else ""
                        volume = str(sheet[row][5].value) if sheet[row][5].value else ""
                        transportation_tariff = str(sheet[row][6].value) if sheet[row][6].value else ""
                        cost_goods = str(sheet[row][7].value) if sheet[row][7].value else ""
                        insurance_cost = str(sheet[row][8].value) if sheet[row][8].value else ""
                        packaging_cost = str(sheet[row][9].value) if sheet[row][9].value else ""
                        if sheet[row][11].value:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][11].value, 0) if sheet[row][11].value else ""
                        else:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[3][6].value, 0) if sheet[3][6].value else ""
                            except TypeError:
                                time_from_china = sheet[3][6].value
                        total_cost = str(sheet[row][13].value) if sheet[row][13].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if sheet[row][6].value > 60:
                                    transportation_tariff_with_factor = float(sheet[row][6].value + self.factor_volume_10)
                                else:
                                    transportation_tariff_with_factor = float(sheet[row][6].value + self.factor_kg_01)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if sheet[row][6].value > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_10 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_01 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.weight == weight and old.time_from_china == make_aware(time_from_china):
                                check = True
                                old.carrier = carrier
                                old.number_of_seats = number_of_seats
                                old.volume = volume
                                old.transportation_tariff = transportation_tariff
                                if old.transportation_tariff_with_factor:
                                    old.transportation_tariff_with_factor = transportation_tariff_with_factor
                                    old.total_cost_with_factor = total_cost_with_factor
                                old.cost_goods = cost_goods
                                old.insurance_cost = insurance_cost
                                old.packaging_cost = packaging_cost
                                old.total_cost = total_cost
                                old.cargo_id = file_carrier
                                old.address_transportation_cost = address_transportation_cost
                                old.save()
                                self.message['info_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' "
                                                                     f"и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}'")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                                address_transportation_cost=address_transportation_cost,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
            elif file_carrier.name_carrier == 'Ян (полная машина)':
                carrier = 'Ян'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'media', str(file_carrier.file_path)), data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'leader_cargo/media', str(file_carrier.file_path)), data_only=True)
                sheet = dataframe.active
                article = str(sheet[3][3].value)
                number_of_seats = str(sheet[3][4].value)
                weight = str(sheet[3][5].value) if sheet[3][5].value else ""
                volume = str(sheet[3][6].value) if sheet[3][6].value else ""
                address_transportation_cost = float(sheet[3][9].value)
                try:
                    time_from_china = xlrd.xldate.xldate_as_datetime(sheet[3][0].value, 0) if sheet[3][0].value else ""
                except TypeError:
                    time_from_china = sheet[3][0].value
                try:
                    make_aware(time_from_china)
                except:
                    time_from_china = datetime.datetime.strptime(time_from_china, '%Y.%m.%d')
                total_cost = str(sheet[3][10].value) if sheet[3][10].value else ""
                check = False
                old_articles = CargoArticle.objects.filter(article=article)
                for old in old_articles:
                    if old.article == article and old.status == 'В пути':
                        check = True
                        self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                        break
                if not check:
                    CargoArticle.objects.create(
                        article=article,
                        carrier=carrier,
                        number_of_seats=number_of_seats,
                        weight=weight,
                        volume=volume,
                        time_from_china=make_aware(time_from_china),
                        total_cost=total_cost,
                        cargo_id=file_carrier,
                        address_transportation_cost=address_transportation_cost,
                    )
                    self.message['success_articles'].append(article)
            elif file_carrier.name_carrier == 'Валька':
                carrier = 'Валька'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}", data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}", data_only=True)
                sheet = dataframe.active
                for row in range(790, sheet.max_row):
                    if sheet[row][4].value and sheet[row][3].value and sheet[row][2].value:
                        article = str(sheet[row][4].value)
                        name_goods = str(sheet[row][6].value) if sheet[row][6].value else ""
                        number_of_seats = str(sheet[row][7].value)
                        weight = str(sheet[row][8].value) if sheet[row][8].value else ""
                        volume = str(sheet[row][9].value) if sheet[row][9].value else ""
                        transportation_tariff = str(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2))
                        cost_goods = str(sheet[row][13].value) if sheet[row][13].value else ""
                        insurance_cost = str(sheet[row][14].value) if sheet[row][14].value else ""
                        packaging_cost = str(sheet[row][15].value) if sheet[row][15].value else ""
                        try:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][3].value, 0) if sheet[row][3].value else ""
                        except TypeError:
                            time_from_china = sheet[row][3].value
                        total_cost = str(sheet[row][16].value) if sheet[row][16].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) > 60:
                                    transportation_tariff_with_factor = float(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) + self.factor_volume_20)
                                else:
                                    transportation_tariff_with_factor = float(round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) + self.factor_kg_02)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if round(float(sheet[row][12].value) / float(sheet[row][8].value), 2) > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_20 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_02 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.number_of_seats == number_of_seats and old.cost_goods == cost_goods and old.insurance_cost == insurance_cost \
                                    and old.weight == weight and old.volume == volume and old.transportation_tariff == transportation_tariff and old.packaging_cost == packaging_cost \
                                    and old.time_from_china == make_aware(time_from_china) and old.total_cost == total_cost:
                                check = True
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
            elif file_carrier.name_carrier == 'Мурад':
                carrier = 'Мурад'
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}", data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}", data_only=True)
                sheet = dataframe.active
                for row in range(2, sheet.max_row + 1):
                    if sheet[row][5].value:
                        if sheet[row][5].value.find("（") != -1:
                            article = str(sheet[row][5].value.split("（")[0].replace(" ", "")) + '\n' + str(sheet[row][3].value)
                            if sheet[row][5].value.find("）") != -1:
                                name_goods = str(sheet[row][5].value.split("（")[1].replace(" ", "").replace("）", ""))
                            else:
                                name_goods = str(sheet[row][5].value.split("（")[1].replace(" ", "").replace(")", ""))
                        else:
                            article = str(sheet[row][5].value.split("(")[0].replace(" ", "")) + '\n' + str(sheet[row][3].value)
                            if sheet[row][5].value.find("）") != -1:
                                name_goods = str(sheet[row][5].value.split("(")[1].replace(" ", "").replace("）", ""))
                            else:
                                name_goods = str(sheet[row][5].value.split("(")[1].replace(" ", "").replace(")", ""))
                        number_of_seats = str(sheet[row][4].value)
                        weight = str(sheet[row][6].value) if sheet[row][4].value else ""
                        volume = str(sheet[row][7].value) if sheet[row][5].value else ""
                        transportation_tariff = str(sheet[row][15].value) if sheet[row][15].value else ""
                        cost_goods = str(sheet[row][12].value) if sheet[row][12].value else ""
                        insurance_cost = str(sheet[row][13].value) if sheet[row][13].value else ""
                        packaging_cost = str(sheet[row][14].value) if sheet[row][14].value else ""
                        try:
                            time_from_china = xlrd.xldate.xldate_as_datetime(sheet[row][1].value, 0) if sheet[row][1].value else ""
                        except TypeError:
                            time_from_china = sheet[row][1].value if sheet[row][1].value else ""
                        total_cost = str(sheet[row][18].value) if sheet[row][18].value else ""
                        try:
                            if time_from_china >= datetime.datetime.strptime('21.11.2023', '%d.%m.%Y'):
                                if sheet[row][15].value > 60:
                                    transportation_tariff_with_factor = float(sheet[row][15].value + self.factor_volume_20)
                                else:
                                    transportation_tariff_with_factor = float(sheet[row][15].value + self.factor_kg_02)
                            else:
                                transportation_tariff_with_factor = None
                        except TypeError:
                            transportation_tariff_with_factor = None
                        if transportation_tariff_with_factor:
                            if sheet[row][15].value > 60:
                                total_cost_with_factor = float(total_cost) + self.factor_volume_20 * float(volume)
                            else:
                                total_cost_with_factor = float(total_cost) + self.factor_kg_02 * float(weight)
                        else:
                            total_cost_with_factor = None
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.status == 'В пути':
                                check = True
                                self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                transportation_tariff_with_factor=transportation_tariff_with_factor,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                total_cost_with_factor=total_cost_with_factor,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
            elif file_carrier.name_carrier == 'Гелик':
                carrier = 'Гелик'
                if settings.DEBUG:
                    workbook = xlrd.open_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}")
                else:
                    workbook = xlrd.open_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}")
                sheet = workbook.sheet_by_index(0)
                for row in range(7, sheet.nrows):
                    if sheet[row][1].value:
                        if sheet[2][1].value.find(":") != -1:
                            article = str(sheet[2][1].value.split(":")[1].replace(" ", ""))
                        else:
                            article = str(sheet[2][1].value.split("：")[1].replace(" ", ""))
                        name_goods = str(sheet[row][1].value) if sheet[row][1].value else ""
                        number_of_seats = str(sheet[row][2].value)
                        weight = str(sheet[row][3].value) if sheet[row][3].value else ""
                        volume = str(sheet[row][4].value) if sheet[row][4].value else ""
                        transportation_tariff = str(sheet[row][5].value) if sheet[row][5].value else ""
                        cost_goods = str(sheet[row][8].value) if sheet[row][8].value else ""
                        insurance_cost = str(sheet[row][9].value) if sheet[row][9].value else ""
                        packaging_cost = str(sheet[row][6].value) if sheet[row][6].value else ""
                        if sheet[4][7].value.find(":") != -1:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[4][7].value.split(":")[1].replace(" ", ""), 0)
                            except TypeError:
                                time_from_china = datetime.datetime.strptime(sheet[4][7].value.split(":")[1].replace(" ", ""), '%Y/%m/%d')
                        else:
                            try:
                                time_from_china = xlrd.xldate.xldate_as_datetime(sheet[4][7].value.split("：")[1].replace(" ", ""), 0)
                            except TypeError:
                                time_from_china = datetime.datetime.strptime(sheet[4][7].value.split("：")[1].replace(" ", ""), '%Y/%m/%d')
                        total_cost = str(sheet[row][11].value) if sheet[row][11].value else ""
                        check = False
                        old_articles = CargoArticle.objects.filter(article=article)
                        for old in old_articles:
                            if old.article == article and old.name_goods == name_goods and old.status == 'В пути':
                                check = True
                                self.message['warning_articles'].append(f"Артикул '{old.article}' со статусом '{old.status}' и датой '{(old.time_from_china + datetime.timedelta(hours=3)).strftime('%d-%m-%Y')}' - уже существует")
                                break
                        if not check:
                            CargoArticle.objects.create(
                                article=article,
                                carrier=carrier,
                                name_goods=name_goods,
                                number_of_seats=number_of_seats,
                                weight=weight,
                                volume=volume,
                                transportation_tariff=transportation_tariff,
                                cost_goods=cost_goods,
                                insurance_cost=insurance_cost,
                                packaging_cost=packaging_cost,
                                time_from_china=make_aware(time_from_china),
                                total_cost=total_cost,
                                cargo_id=file_carrier,
                            )
                            self.message['success_articles'].append(article)
                    else:
                        break
        except Exception as e:
            self.message['error'].append(e)
        self.message['update'] = True
        return redirect('{}?{}'.format(reverse('analytics:carrier'), self.request.META['QUERY_STRING']))


def change_article_status(request, article_id):
    role_have_perm = ['Супер Администратор', 'Логист']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.update_status_article()
    return redirect(request.META.get('HTTP_REFERER') + f'#article-{article_id}')


class EditTableArticleView(MyLoginMixin, DataMixin, UpdateView):
    model = CargoArticle
    form_class = EditTableArticleForm
    pk_url_kwarg = 'article_id'
    role_have_perm = ['Супер Администратор', 'Логист']
    success_url = reverse_lazy('analytics:carrier')
    login_url = reverse_lazy('main:login')

    def form_valid(self, form):
        file_carrier = form.save(commit=False)
        if form.cleaned_data['time_cargo_arrival_to_RF']:
            file_carrier.status = 'Прибыл в РФ'
        if form.cleaned_data['time_cargo_release']:
            file_carrier.status = 'Выдан'
        file_carrier.save()
        return redirect(self.request.META.get('HTTP_REFERER') + f'#article-{self.object.pk}')


class EditTransportTariff(MyLoginMixin, DataMixin, UpdateView):
    model = CargoArticle
    form_class = EditTransportationTariffForClients
    pk_url_kwarg = 'article_id'
    context_object_name = 'article'
    role_have_perm = ['Супер Администратор', 'РОП', 'Менеджер']
    success_url = reverse_lazy('analytics:carrier')
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Изменение транспортного тарифа клиента")
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'hx-modal-main':
            return 'analytics/logistic_main/modal/modalEditClientsTariff.html'
        else:
            return 'analytics/logistic_main/modal/modalEditClientsTariff.html'

    def form_valid(self, form):
        article = form.save(commit=False)
        article.save()
        return redirect(self.request.META.get('HTTP_REFERER') + f'#article-{self.object.pk}')


def amountOfFund(request):
    months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    years = [2023, 2024, 2025, 2026, 2027, 2028]
    now = datetime.datetime.now()
    month = request.GET.get('month', months[now.month - 1])
    year = request.GET.get('year', now.year)
    articles = CargoArticle.objects.filter(total_cost_with_factor__isnull=False)
    if request.htmx:
        if request.htmx.target == 'amountOfFundContent':
            if month != 'Все месяца':
                for index, m in enumerate(months):
                    if m == month:
                        month = index + 1
                        break
                articles = articles.filter(time_from_china__month=month)
            if year != 'Все года':
                articles = articles.filter(time_from_china__year=year)
            amount_of_fund = 0
            count_articles_with_factor = articles.count()
            for art in articles:
                amount_of_fund = amount_of_fund + (art.total_cost_with_factor - float(art.total_cost.replace(" ", "").replace(",", ".")))
            return render(request, 'analytics/components/modal/htmxAmountFundResults.html', {'amount_of_fund': amount_of_fund,
                                                                                             'count_articles_with_factor': count_articles_with_factor,
                                                                                             'month': month,
                                                                                             'year': year,
                                                                                             'months': months,
                                                                                             'years': years})
    amount_of_fund = 0
    month_number = 0
    for index, m in enumerate(months):
        if m == month:
            month_number = index + 1
            break
    articles = articles.filter(time_from_china__month=month_number, time_from_china__year=year)
    count_articles_with_factor = articles.count()
    for art in articles:
        amount_of_fund = amount_of_fund + (art.total_cost_with_factor - float(art.total_cost.replace(" ", "").replace(",", ".")))
    return render(request, 'analytics/components/modal/htmxModalAmountFund.html', {'amount_of_fund': amount_of_fund,
                                                                                   'count_articles_with_factor': count_articles_with_factor,
                                                                                   'month': month,
                                                                                   'year': year,
                                                                                   'months': months,
                                                                                   'years': years})


def edit_article_in_table(request, article_id):
    article = CargoArticle.objects.get(pk=article_id)
    form_article = EditTableArticleForm(instance=article,
                                        initial={
                                            'time_cargo_arrival_to_RF': (article.time_cargo_arrival_to_RF + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
                                            if article.time_cargo_arrival_to_RF else article.time_cargo_arrival_to_RF,
                                            'time_cargo_release': (article.time_cargo_release + datetime.timedelta(hours=3)).strftime("%Y-%m-%d")
                                            if article.time_cargo_release else article.time_cargo_release,
                                        })
    return render(request, 'analytics/components/modal/htmxModalEditArticleForLogist.html', {'article': article, 'form_article': form_article})


def delete_article_in_table(request, article_id):
    article = CargoArticle.objects.get(pk=article_id)
    return render(request, 'analytics/components/modal/htmxModalDeleteArticleForLogist.html', {'article': article})


def paid_by_the_client_status(request, article_id):
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП', 'Логист']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        if request.user.pk == int(article.responsible_manager):
            if request.POST:
                if article.file_payment_by_client.all():
                    article.paid_by_the_client_status = request.POST.get('paid_by_the_client_status')
                    article.time_paid_by_the_client_status = make_aware(datetime.datetime.now())
                    article.save()
                    return render(request, 'analytics/logistic_main/edit_Td_PaidByTheClientStatus.html',
                                  {'article': article})
            if article.file_payment_by_client.all() and article.paid_by_the_client_status == 'Оплачено полностью':
                return render(request, 'analytics/logistic_main/modal/modalViewArticlePaidByClientStatus.html',
                              {'article': article})
            form = EditPaidByTheClientArticleForm(instance=article)
            message = False
            if request.htmx.target == 'modal-alert-message':
                message = True
                if article.file_payment_by_client.all():
                    message = False
                return render(request, 'analytics/logistic_main/partial/modal_error_message.html',
                              {'message': message})

            return render(request, 'analytics/logistic_main/modal/modalEditArticlePaidByClientStatus.html',
                          {'article': article,
                           'form': form,
                           'message': message})
        else:
            return render(request, 'analytics/logistic_main/modal/modalViewArticlePaidByClientStatus.html',
                          {'article': article})
    else:
        return redirect('analytics:carrier')


def add_payment_file(request, article_id):
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП']
    article = CargoArticle.objects.get(pk=article_id)
    form = EditPaidByTheClientArticleForm(instance=article)
    if request.user.role in role_have_perm:
        for f in request.FILES.getlist('files'):
            article.file_payment_by_client.create(name=f, file_path=f)
        return render(request,
                      'analytics/logistic_main/create_payment_file.html',
                      {'article': article,
                       'form': form})
    else:
        return render(request,
                      'analytics/logistic_main/create_payment_file.html',
                      {'article': article,
                       'form': form})


def delete_payment_file(request, article_id, file_id):
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП']
    article = CargoArticle.objects.get(pk=article_id)
    file = PaymentDocumentsForArticles.objects.get(pk=file_id)
    form = EditPaidByTheClientArticleForm(instance=article)
    if request.user.role in role_have_perm:
        file.delete()
        return render(request,
                      'analytics/logistic_main/create_payment_file.html',
                      {'article': article,
                       'form': form})
    else:
        return render(request,
                      'analytics/logistic_main/create_payment_file.html',
                      {'article': article,
                       'form': form})


def change_article_for_manager(request, article_id):
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.paid_by_the_client_status = request.GET.get('paid_by_the_client_status')
        article.save()
        return redirect(request.META.get('HTTP_REFERER') + f'#article-{article.pk}')
    return redirect(request.META.get('HTTP_REFERER'))


class DeleteArticleView(MyLoginMixin, DataMixin, DeleteView):
    model = CargoArticle
    pk_url_kwarg = 'article_id'
    role_have_perm = ['Супер Администратор', 'Логист']
    success_url = reverse_lazy('analytics:carrier')
    login_url = reverse_lazy('main:login')

    def delete(self, request, *args, **kwargs):
        article = self.get_object()
        article.delete()
        return redirect(request.META.get('HTTP_REFERER'))
