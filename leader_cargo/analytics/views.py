import datetime
import os
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.timezone import make_aware
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, DeleteView, UpdateView

from .forms import AddCarrierFilesForm, EditTableArticleForm
from .utils import DataMixinAll
from .models import CargoFiles, CargoArticle

import openpyxl
import xlrd


class CarrierFilesView(LoginRequiredMixin, DataMixinAll, CreateView):
    model = CargoFiles
    form_class = AddCarrierFilesForm
    template_name = 'analytics/carrier_files.html'
    context_object_name = 'all_articles'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'РОП', 'Логист', 'Менеджер']
    success_url = reverse_lazy('carrier')
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
        if self.request.GET.getlist('date'):
            context['date_current'] = self.request.GET.getlist('date')[0]
        else:
            context['date_current'] = datetime.datetime.now().replace(day=1).strftime("%Y-%m-%d")
        if self.request.GET.getlist('status') and self.request.GET.getlist('status')[0] != 'Все статусы':
            context['status_now'] = self.request.GET.getlist('status')
            if self.request.GET.getlist('date'):
                context['all_articles'] = CargoArticle.objects.filter(status__in=self.request.GET.getlist('status'),
                                                                      time_from_china__gte=make_aware(datetime.datetime.strptime(context['date_current'], '%Y-%m-%d'))).order_by('-time_from_china')
            else:
                context['all_articles'] = CargoArticle.objects.filter(status__in=self.request.GET.getlist('status')).order_by('-time_from_china')
        else:
            context['status_now'] = 'Все статусы'
            context['all_articles'] = CargoArticle.objects.filter(time_from_china__gte=make_aware(datetime.datetime.strptime(context['date_current'], '%Y-%m-%d'))).order_by('-time_from_china')
        context['form_article'] = []
        for article in context['all_articles']:
            context['form_article'].append({
                'art': article.pk,
                'f': EditTableArticleForm(instance=article,
                                          initial={
                                              'time_cargo_arrival_to_RF': (article.time_cargo_arrival_to_RF+datetime.timedelta(hours=3)).strftime("%Y-%m-%d") if article.time_cargo_arrival_to_RF else article.time_cargo_arrival_to_RF,
                                              'time_cargo_release': (article.time_cargo_release+datetime.timedelta(hours=3)).strftime("%Y-%m-%d") if article.time_cargo_release else article.time_cargo_release,
                                          })
            })
        context['all_weight'] = 0
        context['all_volume'] = 0
        if self.message['update']:
            context['message'] = self.message
        else:
            context['message'] = []
        self.message['update'] = False
        for art in context['all_articles']:
            if art.status:
                context['all_weight'] = context['all_weight'] + float(art.weight)
                context['all_volume'] = context['all_volume'] + float(art.volume)
        context['vputi'] = 'В пути'
        context['pribil'] = 'Прибыл в РФ'
        c_def = self.get_user_context(title="Учет грузов")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form, **kwargs):
        file_carrier = form.save(commit=False)
        file_carrier.save()
        self.message['success_articles'] = []
        self.message['warning_articles'] = []
        self.message['error'] = []

        try:
            if file_carrier.name_carrier == 'Ян':
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'media', str(file_carrier.file_path)), data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(os.path.join(str(os.getcwd()), 'leader_cargo/media', str(file_carrier.file_path)), data_only=True)
                sheet = dataframe.active
                for row in range(6, sheet.max_row):
                    if sheet[row][0].value:
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

                        total_cost = str(sheet[row][13].value) if sheet[row][13].value else ""
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
            elif file_carrier.name_carrier == 'Валька':
                if settings.DEBUG:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/media/{file_carrier.file_path}", data_only=True)
                else:
                    dataframe = openpyxl.load_workbook(f"{os.getcwd()}/leader_cargo/media/{file_carrier.file_path}", data_only=True)
                sheet = dataframe.active
                for row in range(792, sheet.max_row):
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
            elif file_carrier.name_carrier == 'Мурад':
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
            elif file_carrier.name_carrier == 'Гелик':
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
        return redirect('{}?{}'.format(reverse('carrier'), self.request.META['QUERY_STRING']))


def change_article_status(request, article_id):
    role_have_perm = ['Супер Администратор', 'Логист']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.update_status_article()
    return redirect(request.META.get('HTTP_REFERER'))


class EditTableArticleView(LoginRequiredMixin, DataMixinAll, UpdateView):
    model = CargoArticle
    form_class = EditTableArticleForm
    pk_url_kwarg = 'article_id'
    role_have_perm = ['Супер Администратор', 'Логист']
    success_url = reverse_lazy('carrier')
    login_url = reverse_lazy('login')
    
    def form_valid(self, form):
        file_carrier = form.save(commit=False)
        file_carrier.save()
        return redirect(self.request.META.get('HTTP_REFERER')+f'#article-{self.object.pk}')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


def change_article_for_manager(request, article_id):
    role_have_perm = ['Супер Администратор', 'Менеджер']
    if request.user.role in role_have_perm:
        article = CargoArticle.objects.get(pk=article_id)
        article.paid_by_the_client_status = request.GET.get('paid_by_the_client_status')
        article.save()
        return redirect(request.META.get('HTTP_REFERER') + f'#article-{article.pk}')
    return redirect(request.META.get('HTTP_REFERER'))


class DeleteArticleView(LoginRequiredMixin, DataMixinAll, DeleteView):
    model = CargoArticle
    pk_url_kwarg = 'article_id'
    role_have_perm = ['Супер Администратор', 'Логист']
    success_url = reverse_lazy('carrier')
    login_url = reverse_lazy('login')

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
