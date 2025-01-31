import calendar
import datetime
import re
import pandas as pd
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import string
import random

from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import AddEmployeesForm, AddExchangeRatesForm, AddClientsForm, CardEmployeesForm, CardClientsForm, LoginUserForm, AddAppealsForm, AddGoodsForm, CardGoodsForm, UpdateStatusAppealsForm, UpdateAppealsClientForm, \
    UpdateAppealsManagerForm, RopReportForm, EditRopReportForm, EditManagerPlanForm, AddManagerPlanForm, EditCallsOperator, CallsFileForm, CallsFilterForm, EditCallsManager
from .models import *
from .utils import DataMixin, MyLoginMixin
from .tasks import process_excel_file

from analytics.models import CargoArticle

statuses = [
    'Черновик',
    'Новая',
    'В работе',
    'Просчёт',
    'Просчёт готов',
    'Выкуп и проверка',
    'Доставка',
    'Завершено',
]
logger = logging.getLogger(__name__)
User = get_user_model()


# Доп. функции
def generate_password(length):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


# Заглушки
def logout_user(request):
    logout(request)
    return redirect('main:login')


# ВЬЮХИИИИИИ КЛАССЫ
class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'main/login_new.html'
    message = False

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = self.message
        c_def = self.get_user_context(title="Авторизация")
        return dict(list(context.items()) + list(c_def.items()))

    def form_invalid(self, form):
        login_user = authenticate(self.request, username=''.join(re.findall(r'\d+', form.cleaned_data['phone'])), password=form.cleaned_data['password'])
        if login_user and login_user.status:
            login(self.request, login_user)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))
        else:
            self.message = True
            form.add_error(None, f'Ошибка авторизации')
            return super(LoginUser, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        else:
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class ProfileUser(MyLoginMixin, DataMixin, TemplateView):
    template_name = 'main/profile.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Профиль пользователя")
        return dict(list(context.items()) + list(c_def.items()))


class MonitoringSystemView(MyLoginMixin, DataMixin, ListView):
    paginate_by = 8
    model = CustomUser
    template_name = 'main/monitoring_system.html'
    context_object_name = 'managers'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Система мониторинга")
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role__in=['Менеджер', 'РОП'])
        else:
            return CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], town=f'{self.request.user.town}').order_by('-status', '-role')


class MonitoringManagerReportView(MyLoginMixin, DataMixin, ListView):
    model = CustomUser
    template_name = 'main/monitoring_manager_report.html'
    context_object_name = 'manager'
    pk_url_kwarg = 'manager_id'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        months = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        years = ["", 2023, 2024, 2025, 2026, 2027, 2028]
        context['get_queryset'] = ''
        context['manager_cargo_sent'] = []
        context['manager_cargo_issued'] = []

        if self.request.GET.get('month') or self.request.GET.get('year'):
            now = datetime.datetime.now()
            context['manager_cargo'] = CargoArticle.objects.filter(responsible_manager=self.kwargs['manager_id']).select_related('cargo_id')
            context['manager_reports'] = ManagersReports.objects.filter(manager_id=self.kwargs['manager_id']).select_related('manager_id')

            if 'month' in self.request.GET:
                month = self.request.GET.get('month')
                for index, m in enumerate(months):
                    if m == month:
                        month = index
                        break

                context['manager_reports'] = context['manager_reports'].filter(report_upload_date__month=month)
                context['manager_cargo_sent'] = context['manager_cargo'].filter(time_from_china__month=month)
                context['manager_cargo_issued'] = context['manager_cargo'].filter(time_cargo_release__month=month)
                now = now.replace(month=month)

            if 'year' in self.request.GET:
                year = int(self.request.GET.get('year'))
                context['manager_reports'] = context['manager_reports'].filter(report_upload_date__year=year)
                context['manager_cargo_sent'] = context['manager_cargo_sent'].filter(time_from_china__year=year)
                context['manager_cargo_issued'] = context['manager_cargo_issued'].filter(time_cargo_release__year=year)
                now = now.replace(year=year)
        else:
            now = datetime.datetime.now()
            month = now.month
            year = now.year
            context['manager_reports'] = ManagersReports.objects.filter(manager_id=self.kwargs['manager_id'], report_upload_date__month=month, report_upload_date__year=year).select_related('manager_id')
            context['manager_cargo_sent'] = CargoArticle.objects.filter(responsible_manager=self.kwargs['manager_id'], time_from_china__month=month, time_from_china__year=year).select_related('cargo_id')
            context['manager_cargo_issued'] = CargoArticle.objects.filter(responsible_manager=self.kwargs['manager_id'], time_cargo_release__month=month, time_cargo_release__year=year).select_related('cargo_id')

        context['day_reports'] = dict()
        context['warm_clients_success'] = 0

        for report in context['manager_reports']:
            if report.number_of_completed_transactions_based_on_orders:
                context['warm_clients_success'] = context['warm_clients_success'] + float(report.number_of_completed_transactions_based_on_orders.replace(" ", "").replace(",", "."))
            context['day_reports'].update({(report.report_upload_date + datetime.timedelta(hours=3)).strftime("%d.%m.%Y"): report})

        context['all_days'] = []
        context['form_day_report'] = []
        context['manager_cargo_for_every_days'] = []
        for day in range(1, calendar.monthrange(now.year, now.month)[1] + 1):
            context['all_days'].append(now.replace(day=day).strftime("%d.%m.%Y"))
            if now.replace(day=day).strftime("%d.%m.%Y") in context['day_reports']:
                context['form_day_report'].append({
                    'day': now.replace(day=day).strftime("%d.%m.%Y"),
                    'f': EditRopReportForm(instance=context['day_reports'][now.replace(day=day).strftime("%d.%m.%Y")]),
                    'report_id': context['day_reports'][now.replace(day=day).strftime("%d.%m.%Y")].pk
                })
            else:
                context['form_day_report'].append({
                    'day': now.replace(day=day).strftime("%d.%m.%Y"),
                    'f': RopReportForm(),
                    'report_id': '',
                })
            weight = 0
            volume = 0
            for cargo in context['manager_cargo_sent'].filter(time_from_china__day=day):
                weight = weight + float(cargo.weight.replace(" ", "").replace(",", "."))
                volume = volume + float(cargo.volume.replace(" ", "").replace(",", "."))
            context['manager_cargo_for_every_days'].append({'day': now.replace(day=day).strftime("%d.%m.%Y"),
                                                            'count_sent': context['manager_cargo_sent'].filter(time_from_china__day=day).count(),
                                                            'count_issued': context['manager_cargo_issued'].filter(time_cargo_release__day=day).count(),
                                                            'weight': weight,
                                                            'volume': volume})
        try:
            context['manager_plan'] = context['manager'].managerplans_set.get(month=now.month, year=now.year)
            context['manager_plan_id'] = context['manager_plan'].pk
            context['manager_plan_edit_form'] = EditManagerPlanForm(instance=context['manager_plan'])
            context['manager_plan_value'] = context['manager_plan'].manager_monthly_net_profit_plan
        except:
            context['manager_plan_add_form'] = AddManagerPlanForm()

        context['manager_cargo_sent_count'] = context['manager_cargo_sent'].count()
        context['manager_cargo_issued_count'] = context['manager_cargo_issued'].count()

        context['month_int'] = now.month
        context['month'] = months[now.month]
        context['months'] = months
        context['year'] = now.year
        context['years'] = years
        c_def = self.get_user_context(title="Мониторинг менеджера")
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        return CustomUser.objects.get(pk=self.kwargs['manager_id'])

    def get(self, request, *args, **kwargs):
        return super(MonitoringManagerReportView, self).get(request, *args, **kwargs)


class MonitoringManagerAddReportView(MyLoginMixin, DataMixin, CreateView):
    form_class = RopReportForm
    model = ManagersReports
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def form_valid(self, form):
        manager_report = form.save(commit=False)
        manager_report.report_upload_date = make_aware(datetime.datetime.strptime(self.kwargs['day'], "%d.%m.%Y"))
        manager_report.manager_id = CustomUser.objects.get(pk=self.kwargs['manager_id'])
        manager_report.save()
        return redirect(self.request.META.get('HTTP_REFERER'))


class MonitoringManagerEditReportView(MyLoginMixin, DataMixin, UpdateView):
    form_class = EditRopReportForm
    model = ManagersReports
    pk_url_kwarg = 'report_id'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def form_valid(self, form):
        manager_report = form.save(commit=False)
        manager_report.save()
        return redirect(self.request.META.get('HTTP_REFERER'))


class MonitoringManagerAddPlanView(MyLoginMixin, DataMixin, CreateView):
    form_class = AddManagerPlanForm
    model = ManagerPlans
    pk_url_kwarg = 'manager_id'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def form_valid(self, form):
        manager_plan = form.save(commit=False)
        manager_plan.month = self.kwargs['month']
        manager_plan.year = self.kwargs['year']
        manager_plan.manager_id = CustomUser.objects.get(pk=self.kwargs['manager_id'])
        manager_plan.save()
        return redirect(self.request.META.get('HTTP_REFERER'))


class MonitoringManagerEditPlanView(MyLoginMixin, DataMixin, UpdateView):
    form_class = EditManagerPlanForm
    model = ManagerPlans
    pk_url_kwarg = 'plan_id'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    # def get_initial(self):
    #     initial_base = super(MonitoringManagerEditPlanView, self).get_initial()
    #     initial_base['password'] = generate_password(12)
    #     return initial_base
    #
    # def get_object(self, queryset=None):
    #     super(MonitoringManagerEditPlanView, self).get_object()
    def form_valid(self, form):
        form.save()
        return redirect(self.request.META.get('HTTP_REFERER'))


class MonitoringLeaderboardView(MyLoginMixin, DataMixin, ListView):
    model = CustomUser
    template_name = 'main/monitoring_leaderboard.html'
    context_object_name = 'managers_all'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП', 'Логист', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        months = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        years = ["", 2023, 2024, 2025, 2026, 2027, 2028]
        now = datetime.datetime.now()
        month = now.month
        year = now.year
        if self.request.GET.get('month') or self.request.GET.get('year'):
            if 'month' in self.request.GET:
                month = self.request.GET.get('month')
                for index, m in enumerate(months):
                    if m == month:
                        month = index
                        break
                now = now.replace(month=month)
            if 'year' in self.request.GET:
                year = int(self.request.GET.get('year'))
                now = now.replace(year=year)
        context['monitoring_reports'] = ManagersReports.objects.filter(report_upload_date__month=month, report_upload_date__year=year)
        context['monitoring_cargo'] = CargoArticle.objects.filter(time_from_china__month=month, time_from_china__year=year)

        context['month'] = months[now.month]
        context['months'] = months
        context['year'] = now.year
        context['years'] = years

        context['all_data'] = dict()
        context['all_net_profit'] = 0
        if self.request.user.role == 'Супер Администратор':
            context['managers'] = CustomUser.objects.filter(role__in=['Менеджер', 'РОП'])
        else:
            context['managers'] = CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], town=f'{self.request.user.town}', status=True)
        for manager in context['managers']:
            if manager.pk != 18:

                context['all_data'][f'{manager.pk}'] = dict()
                context['all_data'][f'{manager.pk}']['fio'] = f"{manager.last_name} {manager.first_name}"
                try:
                    context['all_data'][f'{manager.pk}']['manager_monthly_net_profit_plan'] = float(manager.managerplans_set.get(month=now.month, year=now.year).manager_monthly_net_profit_plan.replace(" ", "").replace(",", "."))
                except:
                    context['all_data'][f'{manager.pk}']['manager_monthly_net_profit_plan'] = 240000
                context['all_data'][f'{manager.pk}']['net_profit'] = 0
                context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] = 0
                context['all_data'][f'{manager.pk}']['buyer_files'] = 0
                context['all_data'][f'{manager.pk}']['new_clients'] = 0
                context['all_data'][f'{manager.pk}']['sum_CP'] = 0
                context['all_data'][f'{manager.pk}']['warm_clients'] = 0
                context['all_data'][f'{manager.pk}']['warm_clients_success'] = 0
                context['all_data'][f'{manager.pk}']['sum_calls'] = 0
                context['all_data'][f'{manager.pk}']['sum_duration_calls'] = 0

                context['all_data'][f'{manager.pk}']['weight'] = 0
                context['all_data'][f'{manager.pk}']['volume'] = 0

                for cargo in context['monitoring_cargo']:
                    if cargo.responsible_manager == str(manager.pk):
                        if cargo.weight:
                            context['all_data'][f'{manager.pk}']['weight'] += float(cargo.weight.replace(" ", "").replace(",", "."))
                        if cargo.volume:
                            context['all_data'][f'{manager.pk}']['volume'] += float(cargo.volume.replace(" ", "").replace(",", "."))

                for report in context['monitoring_reports']:
                    if report.manager_id.pk == manager.pk:
                        if report.net_profit_to_the_company:
                            context['all_data'][f'{manager.pk}']['net_profit'] += float(report.net_profit_to_the_company.replace(" ", "").replace(",", "."))
                            context['all_net_profit'] += float(report.net_profit_to_the_company.replace(" ", "").replace(",", "."))
                        if report.raised_funds_to_the_company:
                            context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] += float(report.raised_funds_to_the_company.replace(" ", "").replace(",", "."))
                        if report.number_of_applications_to_buyers:
                            context['all_data'][f'{manager.pk}']['buyer_files'] += float(report.number_of_applications_to_buyers.replace(" ", "").replace(",", "."))
                        if report.number_of_new_clients_attracted:
                            context['all_data'][f'{manager.pk}']['new_clients'] += float(report.number_of_new_clients_attracted.replace(" ", "").replace(",", "."))
                        if report.amount_of_issued_CP:
                            context['all_data'][f'{manager.pk}']['sum_CP'] += float(report.amount_of_issued_CP.replace(" ", "").replace(",", "."))
                        if report.number_of_incoming_quality_applications:
                            context['all_data'][f'{manager.pk}']['warm_clients'] += float(report.number_of_incoming_quality_applications.replace(" ", "").replace(",", "."))
                        # if report.number_of_completed_transactions_based_on_orders:
                        #     context['all_data'][f'{manager.pk}']['warm_clients_success'] = context['all_data'][f'{manager.pk}']['warm_clients_success'] + float(
                        #         report.number_of_completed_transactions_based_on_orders.replace(" ", "").replace(",", "."))
                        if report.number_of_calls:
                            context['all_data'][f'{manager.pk}']['sum_calls'] += float(report.number_of_calls.replace(" ", "").replace(",", "."))
                        if report.duration_of_calls:
                            context['all_data'][f'{manager.pk}']['sum_duration_calls'] += float(report.duration_of_calls.replace(" ", "").replace(",", "."))

                context['all_data'][f'{manager.pk}']['procent_plan'] = context['all_data'][f'{manager.pk}']['net_profit'] / float(context['all_data'][f'{manager.pk}']['manager_monthly_net_profit_plan']) * 100
                try:
                    context['all_data'][f'{manager.pk}']['marga'] = context['all_data'][f'{manager.pk}']['net_profit'] / context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] * 100
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['marga'] = 0
                try:
                    context['all_data'][f'{manager.pk}']['paid_CP'] = context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] / context['all_data'][f'{manager.pk}']['sum_CP'] * 100
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['paid_CP'] = 0
                # try:
                #     context['all_data'][f'{manager.pk}']['conversion'] = context['all_data'][f'{manager.pk}']['warm_clients_success'] / context['all_data'][f'{manager.pk}']['warm_clients']
                # except ZeroDivisionError:
                #     context['all_data'][f'{manager.pk}']['conversion'] = 0
                try:
                    context['all_data'][f'{manager.pk}']['average_duration_calls'] = context['all_data'][f'{manager.pk}']['sum_duration_calls'] / context['all_data'][f'{manager.pk}']['sum_calls']
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['average_duration_calls'] = 0

                context['all_data'][f'{manager.pk}']['sum_calls_need'] = 0
                context['all_data'][f'{manager.pk}']['sum_duration_calls_need'] = 0
                context['all_data'][f'{manager.pk}']['new_clients_need'] = 0
                context['all_data'][f'{manager.pk}']['calls_need'] = 240
                context['all_data'][f'{manager.pk}']['new_clients_net_profit_need'] = 80000

                for report in context['monitoring_reports']:
                    if report.manager_id.pk == manager.pk:
                        if report.number_of_calls and make_aware(datetime.datetime(2023, 10, 15)) >= report.report_upload_date >= make_aware(datetime.datetime(2023, 10, 9)):
                            context['all_data'][f'{manager.pk}']['calls_need'] = context['all_data'][f'{manager.pk}']['calls_need'] - float(report.number_of_calls.replace(" ", "").replace(",", "."))
                        if report.net_profit_to_the_company and make_aware(datetime.datetime(2023, 10, 15)) >= report.report_upload_date >= make_aware(datetime.datetime(2023, 10, 9)):
                            context['all_data'][f'{manager.pk}']['new_clients_net_profit_need'] = context['all_data'][f'{manager.pk}']['new_clients_net_profit_need'] - float(
                                report.net_profit_to_the_company.replace(" ", "").replace(",", "."))
                        if report.number_of_new_clients_attracted and make_aware(datetime.datetime(2023, 10, 15)) >= report.report_upload_date >= make_aware(datetime.datetime(2023, 10, 9)):
                            context['all_data'][f'{manager.pk}']['new_clients_need'] = context['all_data'][f'{manager.pk}']['new_clients_need'] + float(report.number_of_new_clients_attracted.replace(" ", "").replace(",", "."))
                        if report.number_of_calls and make_aware(datetime.datetime(2023, 10, 15)) >= report.report_upload_date >= make_aware(datetime.datetime(2023, 10, 9)):
                            context['all_data'][f'{manager.pk}']['sum_calls_need'] = context['all_data'][f'{manager.pk}']['sum_calls_need'] + float(report.number_of_calls.replace(" ", "").replace(",", "."))
                        if report.duration_of_calls and make_aware(datetime.datetime(2023, 10, 15)) >= report.report_upload_date >= make_aware(datetime.datetime(2023, 10, 9)):
                            context['all_data'][f'{manager.pk}']['sum_duration_calls_need'] = context['all_data'][f'{manager.pk}']['sum_duration_calls_need'] + float(report.duration_of_calls.replace(" ", "").replace(",", "."))

                try:
                    context['all_data'][f'{manager.pk}']['calls_duration_need'] = context['all_data'][f'{manager.pk}']['sum_duration_calls_need'] / context['all_data'][f'{manager.pk}']['sum_calls_need']
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['calls_duration_need'] = 0
        context['prediction'] = context['all_net_profit']
        if year == datetime.datetime.now().year and month == datetime.datetime.now().month:
            all_days = calendar.monthcalendar(year, month)
            all_work_days = 0
            current_work_days = 0
            for week in all_days:
                for item, day in enumerate(week):
                    if item < 5 and day != 0:
                        all_work_days += 1
                    if day <= datetime.datetime.now().day and item < 5 and day != 0:
                        current_work_days += 1
            context['prediction'] = context['prediction'] / current_work_days * all_work_days
        c_def = self.get_user_context(title="Таблица результатов")
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role='Менеджер')
        else:
            return CustomUser.objects.filter(role='Менеджер', town=f'{self.request.user.town}')


class AddExchangeRatesView(MyLoginMixin, DataMixin, CreateView):
    form_class = AddExchangeRatesForm
    model = ExchangeRates
    template_name = 'main/create_exchangerates.html'
    success_url = reverse_lazy('main:exchangerates')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Установка курса валют")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_initial(self):
        initial_base = super(AddExchangeRatesView, self).get_initial()
        curs = self.get_last_currency_dollar_and_yuan()
        if curs:
            initial_base['yuan'] = curs.yuan
            initial_base['yuan_non_cash'] = curs.yuan_non_cash
            initial_base['dollar'] = curs.dollar
        return initial_base

    def form_valid(self, form):
        new_data = form.save(commit=False)
        if not form.cleaned_data['yuan'] and not form.cleaned_data['dollar']:
            form.add_error(None, f'Ошибка добавления курса')
            return super(AddExchangeRatesView, self).form_invalid(form)
        new_data.save()
        return redirect('main:exchangerates')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка добавления курса')
        return super(AddExchangeRatesView, self).form_invalid(form)


class ExchangeRatesView(MyLoginMixin, DataMixin, ListView):
    paginate_by = 16
    model = ExchangeRates
    template_name = 'main/exchangerates.html'
    context_object_name = 'currencies'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Курсы валют")
        return dict(list(context.items()) + list(c_def.items()))


class EmployeesView(MyLoginMixin, DataMixin, ListView):
    paginate_by = 8
    model = CustomUser
    template_name = 'main/employees.html'
    context_object_name = 'employees'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Сотрудники")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.all()
        else:
            return CustomUser.objects.filter(role__in=['Логист', 'Оператор', 'Менеджер', 'Закупщик'])


class AddEmployeeView(MyLoginMixin, DataMixin, CreateView):
    form_class = AddEmployeesForm
    model = CustomUser
    template_name = 'main/create_employees.html'
    success_url = reverse_lazy('main:employees')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Регистрация сотрудника")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_initial(self):
        initial_base = super(AddEmployeeView, self).get_initial()
        initial_base['password'] = generate_password(12)
        return initial_base

    def post(self, request, *args, **kwargs):
        form = AddEmployeesForm(request.POST)
        if form.is_valid():
            new_data = form.save(commit=False)
            new_data.username = ''.join(re.findall(r'\d+', form.cleaned_data['phone']))
            new_data.set_password(form.cleaned_data['password'])
            new_data.pass_no_sha = form.cleaned_data['password']
            # if new_data.role == 'Менеджер':
            #     new_data.manager_monthly_net_profit_plan = '240 000'
            new_data.save()
            return redirect('main:employees')
        form.add_error(None, f'Ошибка добавления сотрудника')
        self.object = None
        return self.form_invalid(form)


class CardEmployeesView(MyLoginMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardEmployeesForm
    template_name = 'main/card_employees.html'
    pk_url_kwarg = 'employee_id'
    success_url = reverse_lazy('main:employees')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Карточка сотрудника")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        kwargs['instance'].password = kwargs['instance'].pass_no_sha
        return kwargs

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.username = ''.join(re.findall(r'\d+', form.cleaned_data['phone']))
        new_data.set_password(form.cleaned_data['password'])
        new_data.pass_no_sha = form.cleaned_data['password']
        new_data.save()
        update_session_auth_hash(self.request, new_data)
        return redirect('main:employees')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных сотрудника')
        return super(CardEmployeesView, self).form_invalid(form)


class ClientsView(MyLoginMixin, DataMixin, ListView):
    paginate_by = 3
    model = CustomUser
    template_name = 'main/clients.html'
    context_object_name = 'all_clients'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Клиенты")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Менеджер':
            return CustomUser.objects.filter(role__in=['Клиент'], manager=self.request.user.pk).order_by('-time_create')
        elif self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role__in=['Клиент']).order_by('-time_create')


class AddClientView(MyLoginMixin, DataMixin, CreateView):
    form_class = AddClientsForm
    model = CustomUser
    template_name = 'main/create_client.html'
    success_url = reverse_lazy('main:clients')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Новый клиент")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_initial(self):
        initial_base = super(AddClientView, self).get_initial()
        initial_base['password'] = generate_password(12)
        return initial_base

    def post(self, request, *args, **kwargs):
        form = AddClientsForm(request.POST)
        if form.is_valid():
            new_data = form.save(commit=False)
            new_data.role = 'Клиент'
            new_data.manager = self.request.user.pk
            new_data.username = ''.join(re.findall(r'\d+', form.cleaned_data['phone']))
            new_data.set_password(form.cleaned_data['password'])
            new_data.pass_no_sha = form.cleaned_data['password']
            new_data.save()
            return redirect('main:clients')
        form.add_error(None, f'Ошибка добавления нового клиента')
        self.object = None
        return self.form_invalid(form)


class CardClientsView(MyLoginMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardClientsForm
    template_name = 'main/card_client.html'
    pk_url_kwarg = 'client_id'
    success_url = reverse_lazy('main:clients')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Карточка клиента")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if hasattr(self, 'object'):
            kwargs.update({'instance': self.object})
        kwargs['instance'].password = kwargs['instance'].pass_no_sha
        return kwargs

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.username = ''.join(re.findall(r'\d+', form.cleaned_data['phone']))
        new_data.set_password(form.cleaned_data['password'])
        new_data.pass_no_sha = form.cleaned_data['password']
        new_data.save()
        return redirect('main:clients')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных клиента')
        return super(CardClientsView, self).form_invalid(form)


class AppealsView(MyLoginMixin, DataMixin, ListView):
    paginate_by = 12
    model = Appeals
    template_name = 'main/appeals.html'
    context_object_name = 'all_appeals'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Заявки")
        context['status_now'] = self.request.GET.getlist('status')
        context['client_now'] = self.request.GET.getlist('client')
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Клиент':
            return Appeals.objects.filter(client=self.request.user.pk)
        elif self.request.user.role == 'Менеджер':
            if self.request.GET.getlist('client') and not self.request.GET.getlist('status'):
                return Appeals.objects.filter(Q(manager=self.request.user.pk) &
                                              Q(client__in=self.request.GET.getlist('client')))
            elif not self.request.GET.getlist('client') and self.request.GET.getlist('status'):
                return Appeals.objects.filter(Q(manager=self.request.user.pk) &
                                              Q(status__in=self.request.GET.getlist('status')))
            elif not self.request.GET.getlist('client') and self.request.GET.getlist('status'):
                return Appeals.objects.filter(Q(manager=self.request.user.pk) &
                                              Q(client__in=self.request.GET.getlist('client')) &
                                              Q(status__in=self.request.GET.getlist('status')))
            return Appeals.objects.filter(manager=self.request.user.pk)
        else:
            return Appeals.objects.all()


class AddAppealsView(MyLoginMixin, DataMixin, CreateView):
    form_class = AddAppealsForm
    model = Appeals
    template_name = 'main/create_appeal.html'
    context_object_name = 'appeals'
    success_url = reverse_lazy('main:card_appeal')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Новая заявка")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        if self.request.user.role == 'Клиент':
            new_data.client = self.request.user.pk
            new_data.manager = self.request.user.manager
            new_data.status = statuses[1]
        elif self.request.user.role == 'Менеджер':
            new_data.manager = self.request.user.pk
            new_data.status = statuses[0]
        new_data.save()
        return redirect('main:card_appeal', new_data.pk)

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка создания заявки')
        return super(AddAppealsView, self).form_invalid(form)


class CardAppealsView(MyLoginMixin, DataMixin, UpdateView):
    paginate_by = 10
    pk_url_kwarg = 'appeal_id'
    model = Appeals
    form_class = UpdateStatusAppealsForm
    form_client = UpdateAppealsClientForm
    form_manager = UpdateAppealsManagerForm
    context_object_name = 'appeal'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_template_names(self):
        if self.request.user.role == 'Клиент':
            template_name = 'main/card_appeal_client.html'
            return template_name
        elif self.request.user.role == 'Менеджер':
            template_name = 'main/card_appeal_manager.html'
            return template_name
        elif self.request.user.role == 'Супер Администратор':
            template_name = 'main/card_appeal_manager.html'
            return template_name
        elif self.request.user.role == 'Закупщик':
            template_name = 'main/card_appeal_manager.html'
            return template_name

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_goods'] = context['appeal'].goods_set.all().order_by('-time_create')
        context['goods_vycup'] = 0
        context['goods_log'] = 0
        context['goods_itog'] = 0
        for goods in context['all_goods']:
            if goods.price_rmb and goods.quantity:
                context['goods_vycup'] = context['goods_vycup'] + \
                                         float(goods.price_rmb.replace(' ', '').replace(',', '.')) * float(goods.quantity.replace(' ', '').replace(',', '.'))
            if goods.price_delivery:
                context['goods_log'] = context['goods_log'] + float(goods.price_delivery.replace(' ', '').replace(',', '.'))
            context['goods_itog'] = float(context['goods_vycup']) + float(context['goods_log'])
        if self.object.status == statuses[0]:
            manager = CustomUser.objects.get(pk=self.object.manager)
            context['manager_fio'] = f"{manager.last_name} {manager.first_name} {manager.patronymic} {manager.phone}"
        elif self.object.status == statuses[1] or self.object.status == statuses[2]:
            client, manager = CustomUser.objects.filter(pk__in=[self.object.client, self.object.manager])
            context['client_fio'] = f"{client.last_name} {client.first_name} {client.patronymic} {client.phone}"
            context['manager_fio'] = f"{manager.last_name} {manager.first_name} {manager.patronymic} {manager.phone}"
        context['edit_form_client'] = self.form_client(instance=self.object)
        context['edit_form_manager'] = self.form_manager(instance=self.object)
        c_def = self.get_user_context(title="Карточка заявки")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        current_client = None
        if self.object.client:
            current_client = self.object.client
        if self.request.user.role == 'Клиент':
            if self.request.POST.get('tag'):
                new_data = self.form_client(self.request.POST, instance=self.object)
                if new_data.is_valid():
                    new_data.save()
                else:
                    new_data.add_error(None, f'Такое название заявки уже существует')
                    return super(CardAppealsView, self).form_invalid(new_data)
                return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])
        elif self.request.user.role == 'Менеджер':
            if self.request.POST.get('tag'):
                new_data = self.form_manager(self.request.POST, instance=self.object)
                if new_data.is_valid():
                    if not self.object.client:
                        new_data.client = current_client
                    new_data.save()
                else:
                    new_data.add_error(None, new_data.errors)
                    return super(CardAppealsView, self).form_invalid(new_data)
                return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.status = statuses[2]
        new_data.save()
        return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])


class AddGoodsView(MyLoginMixin, DataMixin, CreateView):
    pk_url_kwarg = 'appeal_id'
    form_class = AddGoodsForm
    model = Goods
    template_name = 'main/create_goods.html'
    success_url = reverse_lazy('main:card_appeal')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appeal_id_form"] = self.kwargs['appeal_id']
        c_def = self.get_user_context(title="Добавление нового товара")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.appeal_id = Appeals.objects.get(pk=self.kwargs['appeal_id'])
        new_data.save()
        return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка добавления товара')
        return super(AddGoodsView, self).form_invalid(form)


class CardGoodsView(MyLoginMixin, DataMixin, UpdateView):
    model = Goods
    form_class = CardGoodsForm
    template_name = 'main/card_goods.html'
    pk_url_kwarg = 'goods_id'
    context_object_name = 'goods'
    success_url = reverse_lazy('main:card_appeal')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context["appeal_id_form"] = self.kwargs['appeal_id']
        c_def = self.get_user_context(title="Карточка товара")
        return dict(list(context.items()) + list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.appeal_id = Appeals.objects.get(pk=self.kwargs['appeal_id'])
        new_data.save()
        return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных товара')
        return super(CardGoodsView, self).form_invalid(form)


class DeleteGoodsView(MyLoginMixin, DataMixin, DeleteView):
    model = Goods
    pk_url_kwarg = 'goods_id'
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']
    success_url = reverse_lazy('main:card_appeal')

    def delete(self, request, *args, **kwargs):
        goods = self.get_object()
        goods.delete()
        return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])


class CallsView(MyLoginMixin, DataMixin, TemplateView):
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'Оператор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Звонки")
        # Получаем данные из формы
        form = CallsFilterForm(self.request.GET or None)
        selected_operator_statuses = self.request.GET.getlist('status_call')
        selected_manager_statuses = self.request.GET.getlist('status_manager')
        page_size = self.request.GET.get('page_size', 30)  # По умолчанию 30
        search_query = self.request.GET.get('search', '')
        # Получаем все звонки с использованием select_related для оптимизации
        calls_query = Calls.objects.select_related('operator', 'manager').all()
        # Фильтруем звонки по выбранным статусам
        if self.request.user.role in ['Оператор', 'Супер Администратор', 'РОП']:
            calls_query = Calls.objects.select_related('operator', 'manager').order_by('pk').all()
        elif self.request.user.role == 'Менеджер':
            calls_query = Calls.objects.filter(manager=self.request.user).select_related('operator', 'manager').order_by('pk').all()

        if selected_operator_statuses:
            calls_query = calls_query.filter(status_call__in=selected_operator_statuses)
        if selected_manager_statuses:
            calls_query = calls_query.filter(status_manager__in=selected_manager_statuses)

        # Фильтрация по запросу поиска
        if search_query:
            calls_query = calls_query.filter(
                Q(client_phone__iregex=search_query)
                |
                Q(client_name__iregex=search_query)
                |
                Q(client_location__iregex=search_query)
                |
                Q(description__iregex=search_query)
            )
        # Устанавливаем количество элементов на странице
        paginator = Paginator(calls_query, int(page_size))
        page = self.request.GET.get('page')
        try:
            calls_paginated = paginator.page(page)
        except PageNotAnInteger:
            # Если 'page' не является целым числом, показываем первую страницу
            calls_paginated = paginator.page(1)
        except EmptyPage:
            # Если 'page' больше максимального количества страниц, показываем последнюю страницу
            calls_paginated = paginator.page(paginator.num_pages)

        # Определяем диапазон страниц для отображения
        current_page = calls_paginated.number
        total_pages = paginator.num_pages
        page_range = range(max(1, current_page - 3), min(total_pages, current_page + 3) + 1)
        context['calls'] = calls_paginated
        context['paginator_'] = paginator
        context['page_range_'] = page_range
        context['form'] = form
        context['messages'] = [message for message in messages.get_messages(self.request)]
        context['selected_operator_statuses'] = selected_operator_statuses
        context['selected_manager_statuses'] = selected_manager_statuses
        context['page_size'] = page_size  # Передаем значение page_size в контекст
        context['search'] = search_query  # Передаем значение search в контекст
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'calls-table':
            return 'main/calls/calls_table.html'
        return 'main/calls/calls.html'


class LeadsView(MyLoginMixin, DataMixin, TemplateView):
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'Оператор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Звонки")
        # Получаем данные из формы
        form = CallsFilterForm(self.request.GET or None)
        selected_operator_statuses = self.request.GET.getlist('status_call')
        selected_manager_statuses = self.request.GET.getlist('status_manager')
        page_size = self.request.GET.get('page_size', 30)  # По умолчанию 30
        search_query = self.request.GET.get('search', '')
        # Получаем все звонки с использованием select_related для оптимизации
        calls_query = Calls.objects.select_related('operator', 'manager').all()
        # Фильтруем звонки по выбранным статусам
        if self.request.user.role in ['Оператор', 'Супер Администратор', 'РОП']:
            calls_query = Calls.objects.select_related('operator', 'manager').order_by('pk').all()
        elif self.request.user.role == 'Менеджер':
            calls_query = Calls.objects.filter(manager=self.request.user).select_related('operator', 'manager').order_by('pk').all()

        if selected_operator_statuses:
            calls_query = calls_query.filter(status_call__in=selected_operator_statuses)
        if selected_manager_statuses:
            calls_query = calls_query.filter(status_manager__in=selected_manager_statuses)

        # Фильтрация по запросу поиска
        if search_query:
            calls_query = calls_query.filter(
                client_phone__icontains=search_query
            ) | calls_query.filter(
                client_name__icontains=search_query
            )
        # Устанавливаем количество элементов на странице
        paginator = Paginator(calls_query, int(page_size))
        page = self.request.GET.get('page')
        try:
            calls_paginated = paginator.page(page)
        except PageNotAnInteger:
            # Если 'page' не является целым числом, показываем первую страницу
            calls_paginated = paginator.page(1)
        except EmptyPage:
            # Если 'page' больше максимального количества страниц, показываем последнюю страницу
            calls_paginated = paginator.page(paginator.num_pages)

        # Определяем диапазон страниц для отображения
        current_page = calls_paginated.number
        total_pages = paginator.num_pages
        page_range = range(max(1, current_page - 3), min(total_pages, current_page + 3) + 1)
        context['calls'] = calls_paginated
        context['paginator_'] = paginator
        context['page_range_'] = page_range
        context['form'] = form
        context['messages'] = [message for message in messages.get_messages(self.request)]
        context['selected_operator_statuses'] = selected_operator_statuses
        context['selected_manager_statuses'] = selected_manager_statuses
        context['page_size'] = page_size  # Передаем значение page_size в контекст
        context['search'] = search_query  # Передаем значение search в контекст
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'calls-table':
            return 'main/calls/calls_table.html'
        return 'main/calls/calls.html'


def find_best_matches(column_name, possible_names):
    column_name_lower = ''.join(column_name.split()).lower()
    best_match = None
    max_similarity = 0

    for possible_name in possible_names:
        possible_name_lower = ''.join(possible_name.split()).lower()
        intersection = len(set(column_name_lower) & set(possible_name_lower))
        union = len(set(column_name_lower) | set(possible_name_lower))
        if union == 0:
            continue
        similarity = intersection / union
        if similarity > max_similarity and similarity >= 0.9:
            max_similarity = similarity
            best_match = possible_name

    return best_match


def new_calls(request):
    # Получаем количество новых звонков
    badge_calls = Calls.objects.filter(manager=request.user).filter(status_manager='Новая').select_related('operator', 'manager').count()

    # Проверяем наличие изменений по сравнению с предыдущим значением
    last_badge_calls = request.session.get('last_badge_calls', 0)
    has_changes = badge_calls != last_badge_calls

    # Сохраняем текущее значение для будущего сравнения
    request.session['last_badge_calls'] = badge_calls
    return render(request, 'main/calls/new_calls.html',
                  context={'badge_calls': badge_calls,
                           'has_changes': has_changes})


def add_calls(request):
    if request.POST:
        form = CallsFileForm(request.POST, request.FILES)
        if form.is_valid():
            calls_file = form.save(commit=False)
            calls_file.user = request.user
            calls_file.save()

            # Размер пакета для batch_create
            BATCH_SIZE = 10000

            try:
                excel_file = calls_file.file

                # Чтение файла Excel с использованием pandas
                df = pd.read_excel(excel_file)

                # Определение возможных вариантов имен колонок
                column_mapping = {
                    'client_name': ['название лида', 'имя', 'фамилия', 'имя клиента', 'компания'],
                    'client_phone': ['телефон', 'номер телефона', 'контактный номер', 'рабочий телефон'],
                }

                # Нормализация имен колонок и сбор данных
                normalized_columns = {key: [] for key in column_mapping.keys()}
                for col in df.columns:
                    for key, possible_names in column_mapping.items():
                        best_match = find_best_matches(col, possible_names)
                        if best_match:
                            normalized_columns[key].append(col)
                            break

                # Проверка наличия хотя бы одной колонки для каждого поля
                required_columns = set(column_mapping.keys())
                missing_columns = []
                for key in required_columns:
                    if not normalized_columns[key]:
                        missing_columns.append(key)
                if missing_columns:
                    # logger.error(f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}.')
                    return HttpResponse(f'Отсутствуют необходимые колонки: {", ".join(missing_columns)}.')

                # Получение всех операторов и установка начального индекса
                operators = list(User.objects.filter(role='Оператор'))  # Фильтрация по роли Оператор
                current_operator_index = 0

                # Процесс создания объектов Calls
                total_rows = len(df)
                processed_rows = 0
                created_calls_count = 0
                duplicate_phone_count = 0

                # logger.info(f'Начало обработки файла {calls_file.file.name}. Всего строк: {total_rows}')

                calls_to_create = []
                existing_phones = Calls.get_existing_phones()

                for index, row in df.iterrows():
                    processed_rows += 1

                    # Выбор следующего оператора по очереди
                    if operators:
                        current_operator = operators[current_operator_index]
                        current_operator_index = (current_operator_index + 1) % len(operators)
                    else:
                        current_operator = None  # Если нет операторов, оставляем поле operator пустым

                    # Создание объекта Calls
                    call = Calls.create_from_row(row, normalized_columns, current_operator, calls_file)
                    if call:
                        if call.client_phone in existing_phones:
                            # logger.warning(f'Пропущена строка {processed_rows}: client_phone={call.client_phone} уже существует.')
                            duplicate_phone_count += 1
                            continue
                        calls_to_create.append(call)
                        existing_phones.add(call.client_phone)

                    # Массовое создание объектов Calls с пакетным созданием
                    if len(calls_to_create) >= BATCH_SIZE:
                        created_calls = Calls.objects.bulk_create(calls_to_create)
                        created_calls_count += len(created_calls)
                        # logger.info(f'Создано {created_calls_count} новых объектов Calls.')
                        calls_to_create = []

                # Создание оставшихся объектов Calls
                if calls_to_create:
                    created_calls = Calls.objects.bulk_create(calls_to_create)
                    created_calls_count += len(created_calls)
                    # logger.info(f'Создано {created_calls_count} новых объектов Calls.')

                # logger.info(f'Файл {calls_file.file.name} успешно обработан. Всего строк: {total_rows}, обработано: {processed_rows}, создано заявок: {created_calls_count}, дублирующихся номеров: {duplicate_phone_count}')
                if created_calls_count == 0:
                    messages.info(request, f'Файл {calls_file.file.name} был загружен ранее.\n Создано заявок: {created_calls_count}')
                else:
                    messages.success(request,
                                     f'Файл {calls_file.file.name} успешно обработан.\n Всего строк: {total_rows}, обработано: {processed_rows}, создано заявок: {created_calls_count}, дублирующихся номеров: {duplicate_phone_count}')
                return redirect('main:calls')
            except Exception as e:
                # logger.error(f'Ошибка при обработке файла {calls_file.file.name}: {e}')
                messages.error(request, f'Ошибка при обработке файла {calls_file.file.name}: {e}')
                return redirect('main:calls')

    else:
        form = CallsFileForm()
    return render(request, 'main/calls/add_calls.html',
                  context={'form': form})


# Функция для нахождения ближайшего совпадения по названию колонки

@login_required
def edit_calls(request, call_id):
    call = Calls.objects.get(pk=call_id)
    if request.user.role == 'Менеджер':
        form = EditCallsManager(instance=call)
    else:
        form = EditCallsOperator(instance=call)
    if request.POST:
        if request.POST.get('csrfmiddlewaretoken'):
            if request.user.role == 'Менеджер':
                form_edit = EditCallsManager(request.POST, instance=call)
            else:
                form_edit = EditCallsOperator(request.POST, instance=call)
            if form_edit.is_valid():
                form_edit.save()
                messages.success(request, f"Заявка на прозвон {call.client_name} - {call.client_phone}")
            referer = request.META.get('HTTP_REFERER', reverse('main:calls'))
            # Добавляем якорь к URL
            if referer:
                referer += f'#call_{call_id}'
            return redirect(referer)
    else:
        return render(request, 'main/calls/edit_calls.html',
                      context={'call': call,
                               'form': form})
