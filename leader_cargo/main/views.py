import calendar
import re

from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import redirect
import string
import random

from django.urls import reverse_lazy
from django.utils.timezone import make_aware
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import AddEmployeesForm, AddExchangeRatesForm, AddClientsForm, CardEmployeesForm, CardClientsForm, LoginUserForm, AddAppealsForm, AddGoodsForm, CardGoodsForm, UpdateStatusAppealsForm, UpdateAppealsClientForm, \
    UpdateAppealsManagerForm, RopReportForm, EditRopReportForm, EditManagerPlanForm, AddManagerPlanForm
from .models import *
from .utils import DataMixin

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
        return dict(list(context.items())+list(c_def.items()))

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


class ProfileUser(LoginRequiredMixin, DataMixin, TemplateView):
    template_name = 'main/profile.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Профиль пользователя")
        return dict(list(context.items()) + list(c_def.items()))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringSystemView(LoginRequiredMixin, DataMixin, ListView):
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
            return CustomUser.objects.filter(role='Менеджер')
        else:
            return CustomUser.objects.filter(role='Менеджер', town=f'{self.request.user.town}')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringManagerReportView(LoginRequiredMixin, DataMixin, ListView):
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
        if self.request.GET.get('month') or self.request.GET.get('year'):
            now = datetime.datetime.now()
            context['manager_reports'] = ManagersReports.objects.filter(manager_id=self.kwargs['manager_id'])
            if 'month' in self.request.GET:
                month = self.request.GET.get('month')
                for index, m in enumerate(months):
                    if m == month:
                        month = index
                        break
                context['manager_reports'].filter(report_upload_date__month=month)
                now = now.replace(month=month)
            if 'year' in self.request.GET:
                year = int(self.request.GET.get('year'))
                context['manager_reports'].filter(report_upload_date__year=year)
                now = now.replace(year=year)
        else:
            now = datetime.datetime.now()
            month = now.month
            year = now.year
            context['manager_reports'] = ManagersReports.objects.filter(manager_id=self.kwargs['manager_id'], report_upload_date__month=month, report_upload_date__year=year)

        context['day_reports'] = dict()
        for report in context['manager_reports']:
            context['day_reports'].update({(report.report_upload_date+datetime.timedelta(hours=3)).strftime("%d.%m.%Y"): report})

        context['all_days'] = []
        context['form_day_report'] = []
        for day in range(1, calendar.monthrange(now.year, now.month)[1]+1):
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
        try:
            context['manager_plan'] = context['manager'].managerplans_set.get(month=now.month, year=now.year)
            context['manager_plan_id'] = context['manager_plan'].pk
            context['manager_plan_edit_form'] = EditManagerPlanForm(instance=context['manager_plan'])
            context['manager_plan_value'] = context['manager_plan'].manager_monthly_net_profit_plan
            print(context['manager_plan'])
        except:
            context['manager_plan_add_form'] = AddManagerPlanForm()
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringManagerAddReportView(LoginRequiredMixin, DataMixin, CreateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringManagerEditReportView(LoginRequiredMixin, DataMixin, UpdateView):
    form_class = EditRopReportForm
    model = ManagersReports
    pk_url_kwarg = 'report_id'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'РОП']

    def form_valid(self, form):
        manager_report = form.save(commit=False)
        manager_report.save()
        return redirect(self.request.META.get('HTTP_REFERER'))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringManagerAddPlanView(LoginRequiredMixin, DataMixin, CreateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringManagerEditPlanView(LoginRequiredMixin, DataMixin, UpdateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class MonitoringLeaderboardView(LoginRequiredMixin, DataMixin, ListView):
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
        context['month'] = months[now.month]
        context['months'] = months
        context['year'] = now.year
        context['years'] = years

        context['all_data'] = dict()
        if self.request.user.role == 'Супер Администратор':
            context['managers'] = CustomUser.objects.filter(role='Менеджер')
        else:
            context['managers'] = CustomUser.objects.filter(role='Менеджер', town=f'{self.request.user.town}', status=True)
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

                for report in context['monitoring_reports']:
                    if report.manager_id.pk == manager.pk:
                        if report.net_profit_to_the_company:
                            context['all_data'][f'{manager.pk}']['net_profit'] = context['all_data'][f'{manager.pk}']['net_profit'] + float(report.net_profit_to_the_company.replace(" ", "").replace(",", "."))
                        if report.raised_funds_to_the_company:
                            context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] = context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] + float(report.raised_funds_to_the_company.replace(" ", "").replace(",", "."))
                        if report.number_of_applications_to_buyers:
                            context['all_data'][f'{manager.pk}']['buyer_files'] = context['all_data'][f'{manager.pk}']['buyer_files'] + float(report.number_of_applications_to_buyers.replace(" ", "").replace(",", "."))
                        if report.number_of_new_clients_attracted:
                            context['all_data'][f'{manager.pk}']['new_clients'] = context['all_data'][f'{manager.pk}']['new_clients'] + float(report.number_of_new_clients_attracted.replace(" ", "").replace(",", "."))
                        if report.amount_of_issued_CP:
                            context['all_data'][f'{manager.pk}']['sum_CP'] = context['all_data'][f'{manager.pk}']['sum_CP'] + float(report.amount_of_issued_CP.replace(" ", "").replace(",", "."))
                        if report.number_of_incoming_quality_applications:
                            context['all_data'][f'{manager.pk}']['warm_clients'] = context['all_data'][f'{manager.pk}']['warm_clients'] + float(report.number_of_incoming_quality_applications.replace(" ", "").replace(",", "."))
                        if report.number_of_completed_transactions_based_on_orders:
                            context['all_data'][f'{manager.pk}']['warm_clients_success'] = context['all_data'][f'{manager.pk}']['warm_clients_success'] + float(report.number_of_completed_transactions_based_on_orders.replace(" ", "").replace(",", "."))
                        if report.number_of_calls:
                            context['all_data'][f'{manager.pk}']['sum_calls'] = context['all_data'][f'{manager.pk}']['sum_calls'] + float(report.number_of_calls.replace(" ", "").replace(",", "."))
                        if report.duration_of_calls:
                            context['all_data'][f'{manager.pk}']['sum_duration_calls'] = context['all_data'][f'{manager.pk}']['sum_duration_calls'] + float(report.duration_of_calls.replace(" ", "").replace(",", "."))

                context['all_data'][f'{manager.pk}']['procent_plan'] = context['all_data'][f'{manager.pk}']['net_profit'] / float(context['all_data'][f'{manager.pk}']['manager_monthly_net_profit_plan']) * 100
                try:
                    context['all_data'][f'{manager.pk}']['marga'] = context['all_data'][f'{manager.pk}']['net_profit'] / context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] * 100
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['marga'] = 0
                try:
                    context['all_data'][f'{manager.pk}']['paid_CP'] = context['all_data'][f'{manager.pk}']['amount_of_accepted_funds'] / context['all_data'][f'{manager.pk}']['sum_CP'] * 100
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['paid_CP'] = 0
                try:
                    context['all_data'][f'{manager.pk}']['conversion'] = context['all_data'][f'{manager.pk}']['warm_clients_success'] / context['all_data'][f'{manager.pk}']['warm_clients']
                except ZeroDivisionError:
                    context['all_data'][f'{manager.pk}']['conversion'] = 0
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
                            context['all_data'][f'{manager.pk}']['new_clients_net_profit_need'] = context['all_data'][f'{manager.pk}']['new_clients_net_profit_need'] - float(report.net_profit_to_the_company.replace(" ", "").replace(",", "."))
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
        c_def = self.get_user_context(title="Таблица результатов")
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role='Менеджер')
        else:
            return CustomUser.objects.filter(role='Менеджер', town=f'{self.request.user.town}')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AddExchangeRatesView(LoginRequiredMixin, DataMixin, CreateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class ExchangeRatesView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 16
    model = ExchangeRates
    template_name = 'main/exchangerates.html'
    context_object_name = 'currencies'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор', 'Логист']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Курсы валют")
        return dict(list(context.items())+list(c_def.items()))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class EmployeesView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 8
    model = CustomUser
    template_name = 'main/employees.html'
    context_object_name = 'employees'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Сотрудники")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role__in=['Менеджер', 'Закупщик', 'РОП', 'Администратор'])
        else:
            return CustomUser.objects.filter(role__in=['Менеджер', 'Закупщик'])

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AddEmployeeView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddEmployeesForm
    model = CustomUser
    template_name = 'main/create_employees.html'
    success_url = reverse_lazy('main:employees')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор']

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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class CardEmployeesView(LoginRequiredMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardEmployeesForm
    template_name = 'main/card_employees.html'
    pk_url_kwarg = 'employee_id'
    success_url = reverse_lazy('main:employees')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Администратор']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Карточка сотрудника")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

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
        return redirect('main:employees')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных сотрудника')
        return super(CardEmployeesView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class ClientsView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 3
    model = CustomUser
    template_name = 'main/clients.html'
    context_object_name = 'all_clients'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Клиенты")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        if self.request.user.role == 'Менеджер':
            return CustomUser.objects.filter(role__in=['Клиент'], manager=self.request.user.pk).order_by('-time_create')
        elif self.request.user.role == 'Супер Администратор':
            return CustomUser.objects.filter(role__in=['Клиент']).order_by('-time_create')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AddClientView(LoginRequiredMixin, DataMixin, CreateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class CardClientsView(LoginRequiredMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardClientsForm
    template_name = 'main/card_client.html'
    pk_url_kwarg = 'client_id'
    success_url = reverse_lazy('main:clients')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Карточка клиента")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AppealsView(LoginRequiredMixin, DataMixin, ListView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AddAppealsView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddAppealsForm
    model = Appeals
    template_name = 'main/create_appeal.html'
    context_object_name = 'appeals'
    success_url = reverse_lazy('main:card_appeal')
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Новая заявка")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class CardAppealsView(LoginRequiredMixin, DataMixin, UpdateView):
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
                                         float(goods.price_rmb.replace(' ', '').replace(',', '.'))*float(goods.quantity.replace(' ', '').replace(',', '.'))
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
                    print(self.object.client)
                    if not self.object.client:
                        new_data.client = current_client
                        print(new_data.client)
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class AddGoodsView(LoginRequiredMixin, DataMixin, CreateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class CardGoodsView(LoginRequiredMixin, DataMixin, UpdateView):
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

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))


class DeleteGoodsView(LoginRequiredMixin, DataMixin, DeleteView):
    model = Goods
    pk_url_kwarg = 'goods_id'
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']
    success_url = reverse_lazy('main:card_appeal')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()
        return redirect('main:card_appeal', appeal_id=self.kwargs['appeal_id'])

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return redirect(self.get_redirect_url_for_user(role=self.request.user.role))
