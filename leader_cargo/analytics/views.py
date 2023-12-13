import datetime
import os
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.utils.timezone import make_aware
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, UpdateView, TemplateView
from .forms import AddCarrierFilesForm, EditTableArticleForm
from .models import CargoFiles, CargoArticle, RequestsForLogisticsCalculations
# FROM MAIN
from main.models import CustomUser
from main.utils import DataMixin
# EXTERNAL LIBRARIES
import openpyxl
import xlrd


class LogisticRequestsView(LoginRequiredMixin, DataMixin, TemplateView):
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    template_name = 'analytics/logistics_requests.html'
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = RequestsForLogisticsCalculations.objects.all()
        context['table_paginator'] = Paginator(context['reports'], 20)
        page_number = self.request.GET.get('page')
        context['table_paginator_obj'] = context['table_paginator'].get_page(page_number)
        context['reports'] = context['table_paginator_obj']

        if self.request.user.role == 'Логист':
            c_def = self.get_user_context(title="Запросы логисту")
        else:
            c_def = self.get_user_context(title="Запросы на просчет")
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'collapseDraft':
            return "analytics/components/collapse/collapseDraft.html"
        else:
            return self.template_name

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class LogisticRequestsAddView(LoginRequiredMixin, DataMixin, TemplateView):
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    template_name = 'analytics/logistics_requests_add.html'
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['reports'] = RequestsForLogisticsCalculations.objects.all()
        context['table_paginator'] = Paginator(context['reports'], 20)
        page_number = self.request.GET.get('page')
        context['table_paginator_obj'] = context['table_paginator'].get_page(page_number)
        context['reports'] = context['table_paginator_obj']
        context['goods'] = context['table_paginator_obj']

        if self.request.user.role == 'Логист':
            c_def = self.get_user_context(title="Запросы логисту")
        else:
            c_def = self.get_user_context(title="Запросы на просчет")
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        return self.template_name

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class LogisticCalculatorView(LoginRequiredMixin, DataMixin, TemplateView):
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']
    template_name = 'analytics/calculator.html'
    login_url = reverse_lazy('main:login')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Калькулятор логистики")
        return dict(list(context.items()) + list(c_def.items()))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class CarrierFilesView(LoginRequiredMixin, DataMixin, CreateView):
    model = CargoFiles
    form_class = AddCarrierFilesForm
    template_name = 'analytics/carrier_files.html'
    context_object_name = 'all_articles'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП', 'Логист', 'Менеджер']
    success_url = reverse_lazy('analytics:carrier')
    message = dict()
    message['update'] = False

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_articles'] = CargoArticle.objects.all()
        context['count_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).count()
        context['count_empty_path_format'] = context['all_articles'].filter(path_format=None).count()
        context['all_article_with_empty_responsible_manager'] = context['all_articles'].filter(responsible_manager=None).values('article')
        context['all_article_with_empty_path_format'] = context['all_articles'].filter(path_format=None).values('article')
        context['all_articles_without_insurance'] = context['all_articles'].filter(insurance_cost__in=[None, '']).filter(time_from_china__gte=make_aware(datetime.datetime.now() - datetime.timedelta(days=11))).values('article', 'time_from_china')
        context['new_all_articles_without_insurance'] = []
        for art in context['all_articles_without_insurance']:
            if float(art.weight.replace(" ", "").replace(",", ".")) > 10:
                context['new_all_articles_without_insurance'].append(art)
        context['all_articles_without_insurance'] = context['new_all_articles_without_insurance']
        context['count_articles_without_insurance'] = len(context['all_articles_without_insurance'])
        context['count_notifications'] = context['all_articles'].filter(status='Прибыл в РФ').filter(time_cargo_release=None).count()
        context['all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None)
        context['count_all_articles_not_issued'] = context['all_articles'].filter(paid_by_the_client_status='Оплачено полностью').filter(time_cargo_release=None).count()

        if 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100) == 100 and context['count_empty_responsible_manager'] != 0:
            context['pb_count_empty_responsible_manager'] = 99
        else:
            context['pb_count_empty_responsible_manager'] = 100 - int(context['count_empty_responsible_manager'] / context['all_articles'].count() * 100)
        if 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100) == 100 and context['count_empty_path_format'] != 0:
            context['pb_count_empty_path_format'] = 99
        else:
            context['pb_count_empty_path_format'] = 100 - int(context['count_empty_path_format'] / context['all_articles'].count() * 100)

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
        self.factor_kg_01 = 0.1
        self.factor_kg_02 = 0.2
        self.factor_volume_10 = 10
        self.factor_volume_20 = 20

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


# def search_article_in_table(request):
#     q = request.GET.get('q') if request.GET.get('q') is not None else ''
#     all_articles = CargoArticle.objects.filter(article__iregex=q)
#     return render(request, 'analytics/components/table_for_carrier_files.html', {'data': all_articles})


def change_article_status(request, article_id):
    role_have_perm = ['Супер Администратор', 'Логист']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.update_status_article()
    return redirect(request.META.get('HTTP_REFERER') + f'#article-{article_id}')


class EditTableArticleView(LoginRequiredMixin, DataMixin, UpdateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


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


def change_article_for_manager(request, article_id):
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.paid_by_the_client_status = request.GET.get('paid_by_the_client_status')
        article.save()
        return redirect(request.META.get('HTTP_REFERER') + f'#article-{article.pk}')
    return redirect(request.META.get('HTTP_REFERER'))


class DeleteArticleView(LoginRequiredMixin, DataMixin, DeleteView):
    model = CargoArticle
    pk_url_kwarg = 'article_id'
    role_have_perm = ['Супер Администратор', 'Логист']
    success_url = reverse_lazy('analytics:carrier')
    login_url = reverse_lazy('main:login')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect(request.META.get('HTTP_REFERER'))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()
