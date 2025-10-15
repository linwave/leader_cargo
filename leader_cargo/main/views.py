import calendar
import datetime
import datetime as dt
import json
import re
import uuid
from decimal import Decimal

import pandas as pd
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, When, Case, IntegerField, Sum
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from django.shortcuts import redirect, render, get_object_or_404
import string
import random

from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views import View
from django.views.decorators.http import require_POST, require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from telegram_bot.models import TelegramProfile
from telegram_bot.utils import send_telegram_message
from .forms import AddEmployeesForm, AddExchangeRatesForm, AddClientsForm, CardEmployeesForm, CardClientsForm, LoginUserForm, AddAppealsForm, AddGoodsForm, CardGoodsForm, UpdateStatusAppealsForm, UpdateAppealsClientForm, \
    UpdateAppealsManagerForm, RopReportForm, EditRopReportForm, EditManagerPlanForm, AddManagerPlanForm, EditCallsOperator, CallsFileForm, CallsFilterForm, EditCallsRop, LeadsFilterForm, EditLeadsManager, EditLeadsRop, CRMCallForm, \
    ExpenseForm
from .models import *
from .utils import DataMixin, MyLoginMixin, PaginationMixin
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

        # Генерация ссылки для привязки Telegram
        user = self.request.user
        telegram_profile, created = TelegramProfile.objects.get_or_create(user=user)

        if not telegram_profile.is_verified:
            # Генерация уникального токена
            if not telegram_profile.token:
                telegram_profile.generate_token()

            # Формируем ссылку
            bot_username = settings.TELEGRAM_BOT_USERNAME
            telegram_link = f"https://t.me/{bot_username}?start={telegram_profile.token}"
            context['telegram_link'] = telegram_link
        else:
            context['telegram_link'] = None  # Telegram уже привязан

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
        context['monitoring_reports'] = ManagersReports.objects.filter(report_upload_date__month=month, report_upload_date__year=year).select_related('manager_id')
        context['monitoring_cargo'] = CargoArticle.objects.filter(time_from_china__month=month, time_from_china__year=year).select_related('responsible_manager')

        context['month'] = months[now.month]
        context['months'] = months
        context['year'] = now.year
        context['years'] = years

        context['all_data'] = dict()
        context['all_net_profit'] = 0
        if self.request.user.role == 'Супер Администратор':
            context['managers'] = CustomUser.objects.filter(role__in=['Менеджер', 'РОП']).prefetch_related('plans')
        else:
            context['managers'] = CustomUser.objects.filter(role__in=['Менеджер', 'РОП'], town=f'{self.request.user.town}', status=True).prefetch_related('plans')
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
            try:
                context['prediction'] = context['prediction'] / current_work_days * all_work_days
            except ZeroDivisionError:
                context['prediction'] = 0
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


class CallsView(MyLoginMixin, DataMixin, PaginationMixin, TemplateView):
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'Оператор', 'РОП']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Звонки")
        # if self.request.user.role == 'Супер Администратор':
        #     leads = Calls.create_old_leads()
        #     print(leads)
        # Получаем данные из формы
        form = CallsFilterForm(self.request.GET or None)
        selected_managers = self.request.GET.getlist('managers')
        selected_operator_statuses = self.request.GET.getlist('status_call')
        selected_crms = self.request.GET.getlist('crm')
        page_size = self.request.GET.get('page_size', 30)  # По умолчанию 30
        search_query = self.request.GET.get('search', '')
        order_by = self.request.GET.get('order_by', 'time_create')
        order_dir = self.request.GET.get('order_dir', 'desc')

        # Применение сортировки:
        ordering = f'-{order_by}' if order_dir == 'desc' else order_by

        allowed_fields = ['time_create', 'client_name', 'client_phone', 'status_call', 'work_years']
        if order_by not in allowed_fields:
            order_by = 'time_create'

        # Получаем все звонки с использованием метода модели
        calls_query = Calls.filter_by_status(user=self.request.user,
                                             selected_operator_statuses=selected_operator_statuses,
                                             selected_managers=selected_managers,
                                             selected_crms=selected_crms)
        calls_query = calls_query.order_by(ordering)

        # Фильтрация по запросу поиска
        if search_query:
            calls_query = Calls.search(search_query, calls_query)

        # Счётчики ДО пагинации
        filtered_total = calls_query.count()

        managers_with_calls = CustomUser.get_new_in_work_leads_count_for_all_managers()
        context['managers_with_calls'] = json.dumps([
            {
                'first_name': manager.first_name,
                'patronymic': manager.patronymic,
                'last_name': manager.last_name,
                'new_calls_count': manager.new_calls_count,
                'in_progress_calls_count': manager.in_progress_calls_count
            }
            for manager in managers_with_calls
        ])

        # Пагинация
        pagination_context = self.paginate_queryset(calls_query, page_size, 'calls')
        context.update(pagination_context)

        # Сколько на текущей странице (с учётом пагинации)
        pq = context.get('paginated_queryset')
        page_current = len(pq.object_list) if pq else 0
        context.update({
            'filtered_total': filtered_total,  # всего после фильтров (до пагинации)
            'page_current': page_current,  # на текущей странице
        })
        context['form'] = form
        context['messages'] = [message for message in messages.get_messages(self.request)]
        context['managers'] = CustomUser.get_managers_and_operators()
        context['selected_manager'] = selected_managers
        context['selected_operator_statuses'] = selected_operator_statuses
        context['selected_crms'] = selected_crms
        context['page_size'] = str(page_size)  # Передаем значение page_size в контекст
        context['search'] = search_query  # Передаем значение search в контекст
        context['order_by'] = order_by
        context['order_dir'] = order_dir
        context['calls_done'] = Calls.all_calls_done()
        context['leads_with_managers'] = Leads.objects.exclude(manager=None).count()
        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'calls-table':
            return 'main/calls/calls_table.html'
        return 'main/calls/calls.html'


class LeadsView(MyLoginMixin, DataMixin, PaginationMixin, TemplateView):
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'РОП']

    def _parse_dates(self, request):
        tz = timezone.get_current_timezone()

        date_from_str = request.GET.get('date_from')  # 'YYYY-MM-DD'
        date_to_str = request.GET.get('date_to')
        period = request.GET.get('period')  # today|yesterday|week|month|''

        def to_date(s):
            if not s:
                return None
            try:
                return dt.datetime.strptime(s, "%Y-%m-%d").date()
            except ValueError:
                return None

        df = to_date(date_from_str)
        dt_ = to_date(date_to_str)  # переименовал чтобы не перекрывать модуль dt

        today = timezone.localdate()
        if period == 'today':
            df = dt_ = today
        elif period == 'yesterday':
            df = dt_ = today - dt.timedelta(days=1)
        elif period == 'week':
            df, dt_ = today - dt.timedelta(days=6), today
        elif period == 'month':
            df, dt_ = today - dt.timedelta(days=29), today

        if df and not dt_:
            dt_ = df
        if dt_ and not df:
            df = dt_
        if df and dt_ and df > dt_:
            df, dt_ = dt_, df

        def start_of_day(d):
            naive = dt.datetime.combine(d, dt.time.min)
            return timezone.make_aware(naive, tz) if settings.USE_TZ else naive

        def end_of_day(d):
            naive = dt.datetime.combine(d, dt.time.max)
            return timezone.make_aware(naive, tz) if settings.USE_TZ else naive

        df_dt = start_of_day(df) if df else None
        dt_dt = end_of_day(dt_) if dt_ else None

        return df_dt, dt_dt, (df.isoformat() if df else ''), (dt_.isoformat() if dt_ else ''), (period or '')

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Лиды")
        form = LeadsFilterForm(self.request.GET or None)

        selected_manager_statuses = self.request.GET.getlist('status_manager')
        selected_managers_raw = self.request.GET.getlist('managers')
        selected_crms = self.request.GET.getlist('crm')
        page_size = self.request.GET.get('page_size', 30)
        search_query = self.request.GET.get('search', '')

        # NEW: какое поле даты использовать
        date_field = self.request.GET.get('date_field', 'time_new')  # time_new|time_create|time_in_work|date_next_call_manager

        selected_managers_ids = []
        for mid in selected_managers_raw:
            try:
                selected_managers_ids.append(int(mid))
            except (TypeError, ValueError):
                pass
        selected_managers_str = [str(x) for x in selected_managers_ids]

        # Даты
        date_from_dt, date_to_dt, date_from_str, date_to_str, period = self._parse_dates(self.request)

        leads_query = Leads.filter_by_status(
            self.request.user, selected_manager_statuses, selected_managers_ids
        ).order_by('-time_new')

        if search_query:
            leads_query = Leads.search(search_query, leads_query)

        if selected_crms:
            leads_query = leads_query.filter(
                Q(call__crm__in=selected_crms) | Q(call__call_file__crm__in=selected_crms)
            ).distinct()

        # NEW: диапазон по выбранному полю даты + фолбэк на time_create только для time_new
        def range_q(field, gte_dt, lte_dt):
            q = Q()
            if gte_dt: q &= Q(**{f"{field}__gte": gte_dt})
            if lte_dt: q &= Q(**{f"{field}__lte": lte_dt})
            return q

        if date_from_dt or date_to_dt:
            if date_field == 'time_new':
                base = range_q('time_new', date_from_dt, date_to_dt)
                fallback = range_q('time_create', date_from_dt, date_to_dt) & Q(time_new__isnull=True)
                leads_query = leads_query.filter(base | fallback)
            elif date_field == 'time_create':
                leads_query = leads_query.filter(range_q('time_create', date_from_dt, date_to_dt))
            elif date_field == 'time_in_work':
                leads_query = leads_query.filter(range_q('time_in_work', date_from_dt, date_to_dt))
            elif date_field == 'date_next_call_manager':
                leads_query = leads_query.filter(range_q('date_next_call_manager', date_from_dt, date_to_dt))

        # === ГРАФИК: считаем из leads_query надёжно ===
        status_pairs = list(Leads.statuses_manager)  # [(value, label), ...]
        status_labels = [label for _, label in status_pairs]  # подписи в легенде
        status_keys = [f"st_{i}" for i in range(len(status_pairs))]  # безопасные алиасы

        sum_cases = {
            status_keys[i]: Sum(
                Case(
                    When(status_manager=code, then=1),
                    default=0,
                    output_field=IntegerField(),
                )
            )
            for i, (code, _label) in enumerate(status_pairs)
        }

        chart_qs = (
            leads_query
            .order_by()  # сброс сортировки перед GROUP BY
            .values('manager_id',
                    'manager__first_name', 'manager__patronymic', 'manager__last_name')
            .annotate(**sum_cases)
        )

        managers_with_calls = []
        for r in chart_qs:
            name = f"{(r.get('manager__first_name') or '')} {(r.get('manager__patronymic') or '')} {(r.get('manager__last_name') or '')}".strip() or '—'
            row = {'name': name}
            for k in status_keys:
                row[k] = int(r.get(k, 0) or 0)
            managers_with_calls.append(row)

        context['managers_with_calls'] = json.dumps(managers_with_calls, ensure_ascii=False)
        context['status_labels'] = json.dumps(status_labels, ensure_ascii=False)
        context['status_keys'] = json.dumps(status_keys, ensure_ascii=False)

        try:
            page_size = int(page_size)
        except (TypeError, ValueError):
            page_size = 30

        filtered_total = leads_query.count()
        pagination_context = self.paginate_queryset(leads_query, page_size, 'leads')
        context.update(pagination_context)
        pq = context.get('paginated_queryset')
        page_current = len(pq.object_list) if pq else 0

        context.update({
            'form': form,
            'messages': [m for m in messages.get_messages(self.request)],
            'page_size': str(page_size),
            'selected_manager_statuses': selected_manager_statuses,
            'selected_managers': selected_managers_str,
            'selected_crms': selected_crms,
            'crm_choices': CRM_CHOICES,
            'search': search_query,

            # даты + выбранное поле
            'date_from': date_from_str,
            'date_to': date_to_str,
            'period': period,
            'date_field': date_field,

            'filtered_total': filtered_total,
            'page_current': page_current,
        })

        return dict(list(context.items()) + list(c_def.items()))

    def get_template_names(self):
        if self.request.htmx.target == 'leads-table':
            return 'main/leads/leads_table.html'
        return 'main/leads/leads.html'


@login_required
def edit_leads(request, lead_id):
    lead = Leads.objects.get(pk=lead_id)
    form = EditLeadsManager(instance=lead)
    if request.user.role in ['Супер Администратор', 'РОП']:
        form = EditLeadsRop(instance=lead)
    if request.POST:
        if request.POST.get('csrfmiddlewaretoken'):
            form_edit = EditLeadsManager(request.POST, instance=lead)
            if request.user.role in ['Супер Администратор', 'РОП']:
                form_edit = EditLeadsRop(request.POST, instance=lead)
            if form_edit.is_valid():
                form_edit.save()
                messages.success(request, f"Лид обновлен: {lead}")
            else:
                if 'client_phone' in form_edit.errors:
                    messages.info(request, f"Измените/напишите Контактный номер клиента из всех перечисленных")
                else:
                    messages.error(request, f"{form_edit.errors}")
            referer = request.META.get('HTTP_REFERER', reverse('main:leads'))
            # Добавляем якорь к URL
            if referer:
                referer += f'#lead_{lead_id}'
            return redirect(referer)
    else:
        return render(request, 'main/leads/edit_leads.html',
                      context={'lead': lead,
                               'form': form})


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
    if not request.user.is_authenticated:
        badge_calls = 0
    else:
        # Получаем количество новых звонков
        badge_calls = Calls.get_new_calls(operator=request.user)
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

            try:
                result = calls_file.parse_and_generate_calls(request.user)

                if result['created'] == 0:
                    messages.info(request, f'Файл {calls_file.file.name} был загружен ранее.\nСоздано заявок: {result["created"]}')
                else:
                    messages.success(request,
                                     f'Файл {calls_file.file.name} успешно обработан.\nВсего строк: {result["total"]}, создано: {result["created"]}, дубликатов: {result["duplicates"]}')
                return redirect('main:calls')
            except Exception as e:
                messages.error(request, f'Ошибка при обработке файла {calls_file.file.name}: {e}')
                return redirect('main:calls')

    else:
        form = CallsFileForm()
    return render(request, 'main/calls/add_calls.html', context={'form': form})


# Функция для нахождения ближайшего совпадения по названию колонки

@login_required
def edit_calls(request, call_id):
    call = Calls.objects.get(pk=call_id)
    form = EditCallsOperator(instance=call)
    if request.user.role in ['Супер Администратор', 'РОП']:
        form = EditCallsRop(instance=call)
    if request.POST:
        if request.POST.get('csrfmiddlewaretoken'):
            form_edit = EditCallsOperator(request.POST, instance=call)
            if request.user.role in ['Супер Администратор', 'РОП']:
                form_edit = EditCallsRop(request.POST, instance=call)
            if form_edit.is_valid():
                form_edit.save()
                lead = call.create_or_get_lead()
                if lead:
                    messages.success(request, f"Заявка на прозвон {call.client_name} - {call.client_phone}.\n {lead}")
                    if lead.manager:
                        telegram_profile, created = TelegramProfile.objects.get_or_create(user=lead.manager)
                        if telegram_profile.is_verified:
                            send_telegram_message(lead.manager.telegram_profile.chat_id,
                                                  f"{lead.manager}\n{lead.pk} - ({lead.call.pk}) - Новый лид:\n Имя клиента: {lead.client_name}\n"
                                                  f"Номер телефона: {lead.client_phone}"
                                                  f"Лояльность: {lead.loyalty}"
                                                  f"Коментарий от оператора: {lead.call.description}", settings.TELEGRAM_BOT_TOKEN)
                else:
                    messages.success(request, f"Заявка на прозвон {call.client_name} - {call.client_phone} изменена")
            else:
                messages.error(request, f"ОШИБКА: {form_edit.errors}")
            referer = request.META.get('HTTP_REFERER', reverse('main:calls'))
            # Добавляем якорь к URL
            if referer:
                referer += f'#call_{call_id}'
            return redirect(referer)
    else:
        return render(request, 'main/calls/edit_calls.html',
                      context={'call': call,
                               'form': form})


# для наглядности можно оставить константой
CRM_SOURCE_ALPHA = 'Колл-центр Альфа'

class CRMCallView(DataMixin, View):
    template_name = 'main/calls/crm_form.html'
    role_have_perm = ['ALL']

    def get(self, request, **kwargs):
        form = CRMCallForm()
        context = self.get_user_context(title="CRM форма")
        # передадим в шаблон подпись источника
        context.update({
            'form': form,
            'crm_display': CRM_SOURCE_ALPHA
        })
        return render(request, self.template_name, context)

    @transaction.atomic
    def post(self, request):
        form = CRMCallForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {
                'form': form,
                'crm_display': CRM_SOURCE_ALPHA,
            })

        manager = User.objects.filter(pk=getattr(settings, 'CRM_DEFAULT_MANAGER_ID', 40)).first()

        phone = form.cleaned_data['client_phone']
        name = form.cleaned_data.get('client_name') or ''
        city = form.cleaned_data.get('client_location') or ''
        descr = form.cleaned_data.get('description') or ''
        now = timezone.now()

        call = Calls.objects.filter(client_phone=phone).first()
        created = False

        if call is None:
            call = Calls.objects.create(
                client_name=name or None,
                client_phone=phone,
                client_location=city or None,
                description=descr or None,
                status_call='Не обработано',
                loyalty=None,
                operator=None,                      # оператор пустой
                date_to_manager=None,
                crm=CRM_SOURCE_ALPHA,               # <— важное место
            )
            created = True
        else:
            # обновляем существующую по этому телефону
            if name and not call.client_name:
                call.client_name = name
            if city:
                call.client_location = city
            if descr:
                stamp = now.strftime('%Y-%m-%d %H:%M')
                addon = f"[{stamp}] {descr}"
                call.description = (call.description + "\n" + addon) if call.description else addon

            call.status_call = 'Не обработано'
            call.crm = CRM_SOURCE_ALPHA           # <— перезапишем источник для консистентности
            if manager:
                call.manager = manager
                call.date_to_manager = now
                call.status_manager = 'Новая'
            call.save()

        # Telegram уведомление менеджеру (ты при желании допишешь текст под себя)
        if manager:
            prof = TelegramProfile.objects.filter(user=manager, is_verified=True).first()
            if prof and prof.chat_id:
                text = (
                    f"Новая заявка из {CRM_SOURCE_ALPHA}{'' if created else ' (обновл.)'}\n"
                    f"ID: {call.pk}\n"
                    f"Клиент: {call.client_name or '—'}\n"
                    f"Телефон: {call.client_phone}\n"
                    f"Комментарий: {(descr or '—') if created else 'обновление/см. карточку'}"
                )
                try:
                    send_telegram_message(prof.chat_id, text, settings.TELEGRAM_BOT_TOKEN)
                except Exception as e:
                    print(f"TG notify error: {e}")

        messages.success(
            request,
            f"{'Создана новая' if created else 'Обновлена существующая'} заявка №{call.pk} "
            f"(Источник: Колл-центр). "
            f"{'Менеджеру отправлено уведомление.' if manager else ''}"
        )
        # остаёмся на том же URL (/crm/alpha/), чтобы делать заявки одну за другой
        return redirect(request.path)



ROLE_ALLOWED_EXPENSES = ['Супер Администратор', 'РОП']


def _parse_period(request):
    """Возвращает (date_from: date|None, date_to: date|None, date_from_str, date_to_str, period_str)."""

    def to_date(s):
        if not s:
            return None
        try:
            return dt.datetime.strptime(s, "%Y-%m-%d").date()
        except ValueError:
            return None

    period = request.GET.get("period", "")
    df = to_date(request.GET.get("date_from"))
    dt_ = to_date(request.GET.get("date_to"))

    today = timezone.localdate()

    if period == "today":
        df = dt_ = today
    elif period == "yesterday":
        df = dt_ = today - dt.timedelta(days=1)
    elif period == "week":
        df, dt_ = today - dt.timedelta(days=6), today
    elif period == "month":
        df, dt_ = today.replace(day=1), today

    # если введена только одна дата
    if df and not dt_:
        dt_ = df
    if dt_ and not df:
        df = dt_
    # нормализуем порядок
    if df and dt_ and df > dt_:
        df, dt_ = dt_, df

    # по умолчанию — текущий месяц
    if not period and not df and not dt_:
        df, dt_, period = today.replace(day=1), today, "month"

    return df, dt_, (df.isoformat() if df else ""), (dt_.isoformat() if dt_ else ""), period


def _leads_count_by_source(date_from=None, date_to=None, date_field='time_new'):
    """
    Считает количество лидов по источнику CRM за период.
    По умолчанию — по time_new (дата передачи менеджеру) c фолбэком на time_create, как мы делали.
    """
    qs = Leads.objects.select_related('call', 'call__call_file')

    # фильтр по дате
    def range_q(field, gte_d, lte_d):
        q = Q()
        if gte_d: q &= Q(**{f"{field}__date__gte": gte_d})
        if lte_d: q &= Q(**{f"{field}__date__lte": lte_d})
        return q

    if date_from or date_to:
        if date_field == 'time_new':
            base = range_q('time_new', date_from, date_to)
            fallback = range_q('time_create', date_from, date_to) & Q(time_new__isnull=True)
            qs = qs.filter(base | fallback)
        elif date_field == 'time_create':
            qs = qs.filter(range_q('time_create', date_from, date_to))
        elif date_field == 'time_in_work':
            qs = qs.filter(range_q('time_in_work', date_from, date_to))
        elif date_field == 'date_next_call_manager':
            qs = qs.filter(range_q('date_next_call_manager', date_from, date_to))

    # источник берём из call.crm, если пуст — из call.call_file.crm
    # считаем по списку CRM_CHOICES
    result = {label: 0 for (label, _) in CRM_CHOICES}  # если CRM_CHOICES = [('Биг-дата','Биг-дата'), ...]
    # иногда CRM_CHOICES как (value,label) = одинаковые; используем value
    result = {value: 0 for (value, _label) in CRM_CHOICES}

    # соберём counts по обоим местам
    rows1 = qs.filter(call__crm__isnull=False).values('call__crm').annotate(c=models.Count('id'))
    for r in rows1:
        result[r['call__crm']] = result.get(r['call__crm'], 0) + r['c']

    rows2 = qs.filter(call__crm__isnull=True, call__call_file__crm__isnull=False)\
              .values('call__call_file__crm').annotate(c=models.Count('id'))
    for r in rows2:
        result[r['call__call_file__crm']] = result.get(r['call__call_file__crm'], 0) + r['c']

    return result


def _expenses_sum_by_source(date_from=None, date_to=None):
    qs = Expense.objects.all()
    if date_from:
        qs = qs.filter(date_payment__gte=date_from)
    if date_to:
        qs = qs.filter(date_payment__lte=date_to)
    rows = qs.values('source').annotate(total=Sum('amount'))
    return {r['source']: (r['total'] or Decimal('0')) for r in rows}


class ExpensesView(MyLoginMixin, DataMixin, PaginationMixin, TemplateView):
    login_url = reverse_lazy('main:login')
    template_name = "main/expenses/expenses.html"
    role_have_perm = ROLE_ALLOWED_EXPENSES

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="База расходов")

        # период
        date_from, date_to, df_str, dt_str, period = _parse_period(self.request)

        # фильтры
        selected_sources = self.request.GET.getlist("source")  # multiple
        page_size = self.request.GET.get("page_size", 30)

        # список расходов с фильтрами
        qs = Expense.objects.select_related("created_by").order_by("-date_payment", "-created_at")
        if date_from:
            qs = qs.filter(date_payment__gte=date_from)
        if date_to:
            qs = qs.filter(date_payment__lte=date_to)
        if selected_sources:
            qs = qs.filter(source__in=selected_sources)

        # суммы и CPL
        # по умолчанию считаем CPL по лидам с датой time_new (как на вкладке Лиды)
        date_field = self.request.GET.get('date_field', 'time_new')
        sum_total = qs.aggregate(total=Sum("amount"))["total"] or Decimal("0")
        leads_by_source = _leads_count_by_source(date_from, date_to, date_field=date_field)
        expenses_by_source = _expenses_sum_by_source(date_from, date_to)

        # сводка по источникам: [{source, leads, expense, cpl}]
        sources_list = [value for (value, _label) in CRM_CHOICES]
        summary_rows = []
        total_leads = 0
        for s in sources_list:
            leads_cnt = int(leads_by_source.get(s, 0) or 0)
            exp_sum = expenses_by_source.get(s, Decimal("0")) or Decimal("0")
            total_leads += leads_cnt
            cpl = (exp_sum / leads_cnt) if leads_cnt > 0 else None
            summary_rows.append({
                "source": s,
                "leads": leads_cnt,
                "expense": exp_sum,
                "cpl": cpl,
            })

        overall_cpl = (sum_total / total_leads) if total_leads > 0 else None

        # пагинация
        try:
            page_size = int(page_size)
        except (TypeError, ValueError):
            page_size = 30
        pagination = self.paginate_queryset(qs, page_size, 'expenses')
        context.update(pagination)

        context.update({
            "crm_choices": CRM_CHOICES,
            "selected_sources": selected_sources,
            "page_size": str(page_size),

            "date_from": df_str,
            "date_to": dt_str,
            "period": period,
            "date_field": date_field,

            "sum_total": sum_total,
            "overall_cpl": overall_cpl,
            "summary_rows": summary_rows,
        })
        chart_by_source_labels = []
        chart_by_source_data = []
        for row in summary_rows:
            if row["expense"] and row["expense"] > 0:
                chart_by_source_labels.append(row["source"])
                chart_by_source_data.append(float(row["expense"]))

        # ----- данные для графика "по дням"
        by_day = (
            qs.values("date_payment")
            .annotate(total=Sum("amount"))
            .order_by("date_payment")
        )
        chart_by_day_labels = [d["date_payment"].strftime("%d.%m.%Y") for d in by_day]
        chart_by_day_data = [float(d["total"] or 0) for d in by_day]

        context.update({
            "chart_by_source": {"labels": chart_by_source_labels, "data": chart_by_source_data},
            "chart_by_day": {"labels": chart_by_day_labels, "data": chart_by_day_data},
        })
        return dict(list(context.items()) + list(c_def.items()))

    def render_to_response(self, context, **response_kwargs):
        request = self.request
        if request.headers.get('HX-Request'):
            # при HTMX возвращаем только таблицу
            return render(request, "main/expenses/_table.html", context)
        return super().render_to_response(context, **response_kwargs)
@login_required
@require_http_methods(["GET", "POST"])
def expense_create(request):
    if getattr(request.user, "role", "") not in ROLE_ALLOWED_EXPENSES:
        return HttpResponseBadRequest("Недостаточно прав")

    if request.method == "GET":
        form = ExpenseForm()
        return render(request, "main/expenses/_form.html", {
            "form": form,
            "action_url": reverse("main:expense_create"),
            "title": "Добавить расход",
        })

    form = ExpenseForm(request.POST, request.FILES)
    if form.is_valid():
        exp = form.save(commit=False)
        exp.created_by = request.user
        exp.save()
        # Обновим таблицу и закроем модалку
        view = ExpensesView(); view.request = request
        ctx = view.get_context_data()
        html = render(request, "main/expenses/_table.html", ctx)
        resp = HttpResponse(html)
        resp["HX-Trigger"] = "closeModalAndRefresh"
        return resp

    return render(request, "main/expenses/_form.html", {
        "form": form, "action_url": reverse("main:expense_create"), "title": "Добавить расход",
    }, status=422)



@login_required
@require_http_methods(["GET", "POST"])
def expense_edit(request, pk):
    if getattr(request.user, "role", "") not in ROLE_ALLOWED_EXPENSES:
        return HttpResponseBadRequest("Недостаточно прав")
    exp = get_object_or_404(Expense, pk=pk)

    if request.method == "GET":
        form = ExpenseForm(instance=exp)
        return render(request, "main/expenses/_form.html", {
            "form": form,
            "action_url": reverse("main:expense_edit", args=[exp.pk]),
            "title": "Редактировать расход",
            "existing_file": exp.receipt_file,
        })

    if request.method == "POST":
        form = ExpenseForm(request.POST, request.FILES, instance=exp)
        if form.is_valid():
            obj = form.save(commit=False)
            clear_flag = request.POST.get('receipt_file-clear') == '1'
            # если очистка запрошена и новый файл не пришёл — удаляем старый
            if clear_flag and not request.FILES.get('receipt_file'):
                if obj.receipt_file:
                    obj.receipt_file.delete(save=False)
                obj.receipt_file = None
            obj.save()

            view = ExpensesView();
            view.request = request
            ctx = view.get_context_data()
            html = render(request, "main/expenses/_table.html", ctx)
            resp = HttpResponse(html)
            resp["HX-Trigger"] = "closeModalAndRefresh"
            return resp

    form = ExpenseForm(request.POST, request.FILES, instance=exp)
    if form.is_valid():
        form.save()
        view = ExpensesView(); view.request = request
        ctx = view.get_context_data()
        html = render(request, "main/expenses/_table.html", ctx)
        resp = HttpResponse(html)
        resp["HX-Trigger"] = "closeModalAndRefresh"
        return resp

    return render(request, "main/expenses/_form.html", {
        "form": form,
        "action_url": reverse("main:expense_edit", args=[exp.pk]),
        "title": "Редактировать расход",
        "existing_file": exp.receipt_file,
    }, status=422)


# delete (POST вернёт триггер закрытия)
@login_required
@require_http_methods(["GET", "POST"])
def expense_delete_confirm(request, pk):
    if getattr(request.user, "role", "") not in ROLE_ALLOWED_EXPENSES:
        return HttpResponseBadRequest("Недостаточно прав")
    exp = get_object_or_404(Expense, pk=pk)

    if request.method == "GET":
        return render(request, "main/expenses/_confirm_delete.html", {"expense": exp})

    exp.delete()
    view = ExpensesView(); view.request = request
    ctx = view.get_context_data()
    html = render(request, "main/expenses/_table.html", ctx)
    resp = HttpResponse(html)
    resp["HX-Trigger"] = "closeModalAndRefresh"
    return resp