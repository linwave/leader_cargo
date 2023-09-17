import datetime
import re
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
import string
import random

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .forms import AddEmployeesForm, AddExchangeRatesForm, AddClientsForm, CardEmployeesForm, CardClientsForm, LoginUserForm, AddAppealsForm, AddGoodsForm, CardGoodsForm
from .models import *
from .utils import DataMixin

menu = [
    # {'title': 'Главная', 'url_name': 'home'},
    # {'title': 'Авторизация', 'url_name': 'login'},
    {'title': 'Сотрудники', 'url_name': 'employees'},
    {'title': 'Курсы валют', 'url_name': 'exchangerates'},
    {'title': 'Клиенты', 'url_name': 'clients'},
    {'title': 'Заявки', 'url_name': 'appeals'},
]
statuses = [
    'Новая',
    'В работе',
    'Выкуп и доставка',
    'Доставка',
    'Завершено',
]


# Доп. функции
def generate_password(length):
    characters = string.ascii_letters + string.digits
    password = ''.join(random.choice(characters) for _ in range(length))
    return password


def last_currency():
    try:
        curs = ExchangeRates.objects.filter(time_create__contains=datetime.datetime.today().date()).order_by('-time_create')[:1][0]
        curs.yuan = str(format(float(curs.yuan), '.2f'))
        curs.dollar = str(format(float(curs.dollar), '.2f'))
        return curs
    except IndexError:
        return False


# Заглушки
def logout_user(request):
    logout(request)
    return redirect('login')


# ВЬЮХИИИИИИ КЛАССЫ
class LoginUser(DataMixin, LoginView):
    form_class = LoginUserForm
    template_name = 'main/login.html'

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Авторизация")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_success_url(self):
        if self.request.user.role == 'Супер Администратор':
            return reverse_lazy('home')
        elif self.request.user.role == 'Администратор':
            return reverse_lazy('home')
        elif self.request.user.role == 'Менеджер':
            return reverse_lazy('clients')
        else:
            return reverse_lazy('appeals')

    def form_invalid(self, form):
        login_user = authenticate(self.request, username=''.join(re.findall(r'\d+', form.cleaned_data['phone'])), password=form.cleaned_data['password'])
        if login_user and login_user.status:
            login(self.request, login_user)
            if self.request.user.role == 'Супер Администратор':
                return redirect('home')
            elif self.request.user.role == 'Администратор':
                return redirect('home')
            elif self.request.user.role == 'Менеджер':
                return redirect('clients')
            else:
                return redirect('appeals')
        else:
            form.add_error(None, f'Ошибка авторизации')
            return super(LoginUser, self).form_invalid(form)


class AddExchangeRatesView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddExchangeRatesForm
    model = ExchangeRates
    template_name = 'main/create_exchangerates.html'
    success_url = reverse_lazy('exchangerates')
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Администратор']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Установка курса валют")
        return dict(list(super().get_context_data(**kwargs).items()) + list(c_def.items()))

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка добавления курса')
        return super(AddExchangeRatesView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class ExchangeRatesView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 3
    model = ExchangeRates
    template_name = 'main/exchangerates.html'
    context_object_name = 'currencies'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Администратор']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Курсы валют")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        return ExchangeRates.objects.order_by('-time_create')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            elif request.user.role == 'Клиент':
                return redirect('appeals')
            elif request.user.role == 'Менеджер':
                return redirect('clients')
            elif request.user.role == 'Закупщик':
                return self.handle_no_permission()


class EmployeesView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 3
    model = CustomUser
    template_name = 'main/employees.html'
    context_object_name = 'employees'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Администратор']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Сотрудники")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        return CustomUser.objects.filter(role__in=['Менеджер', 'Закупщик']).order_by('-time_create')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class AddEmployeeView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddEmployeesForm
    model = CustomUser
    template_name = 'main/create_employees.html'
    success_url = reverse_lazy('employees')
    login_url = reverse_lazy('login')
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
            new_data.save()
            return redirect('employees')
        form.add_error(None, f'Ошибка добавления сотрудника')
        self.object = None
        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class CardEmployeesView(LoginRequiredMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardEmployeesForm
    template_name = 'main/card_employees.html'
    pk_url_kwarg = 'employee_id'
    success_url = reverse_lazy('employees')
    login_url = reverse_lazy('login')
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
        return redirect('employees')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных сотрудника')
        return super(CardEmployeesView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class ClientsView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 3
    model = CustomUser
    template_name = 'main/clients.html'
    context_object_name = 'all_clients'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Клиенты")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        return CustomUser.objects.filter(role__in=['Клиент']).order_by('-time_create')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class AddClientView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddClientsForm
    model = CustomUser
    template_name = 'main/create_client.html'
    success_url = reverse_lazy('clients')
    login_url = reverse_lazy('login')
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
            return redirect('clients')
        form.add_error(None, f'Ошибка добавления нового клиента')
        self.object = None
        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class CardClientsView(LoginRequiredMixin, DataMixin, UpdateView):
    model = CustomUser
    form_class = CardClientsForm
    template_name = 'main/card_client.html'
    pk_url_kwarg = 'client_id'
    success_url = reverse_lazy('clients')
    login_url = reverse_lazy('login')
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
        return redirect('clients')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных клиента')
        return super(CardClientsView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class AppealsView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 10
    model = Appeals
    template_name = 'main/appeals.html'
    context_object_name = 'all_appeals'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Заявки")
        return dict(list(context.items()) + list(c_def.items()))

    def get_queryset(self):
        return Appeals.objects.filter(client=self.request.user.pk).order_by('-time_create')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class AddAppealsView(LoginRequiredMixin, DataMixin, CreateView):
    form_class = AddAppealsForm
    model = Appeals
    template_name = 'main/create_appeal.html'
    context_object_name = 'appeals'
    success_url = reverse_lazy('card_appeal')
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Новая заявка")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        if self.request.user.role == 'Клиент':
            new_data.client = self.request.user.pk
            new_data.manager = self.request.user.manager
        new_data.status = statuses[0]
        new_data.save()
        return redirect('appeals')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка создания заявки')
        return super(AddAppealsView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class CardAppealsView(LoginRequiredMixin, DataMixin, DetailView):
    paginate_by = 10
    pk_url_kwarg = 'appeal_id'
    model = Appeals
    context_object_name = 'appeal'
    template_name = 'main/card_appeal.html'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client_fio'] = self.request.user
        context['all_goods'] = context['appeal'].goods_set.all().order_by('-time_create')
        context['goods_vycup'] = 0
        context['goods_log'] = 0
        context['goods_itog'] = 0
        for goods in context['all_goods']:
            context['goods_vycup'] = context['goods_vycup'] + float(goods.price_rmb*goods.quantity)
            if goods.price_delivery:
                context['goods_log'] = context['goods_log'] + float(goods.price_delivery)
            context['goods_itog'] = float(context['goods_vycup']) + float(context['goods_log'])
        client, manager = CustomUser.objects.filter(pk__in=[context['appeal'].client, context['appeal'].manager])
        context['client_fio'] = f"{client.last_name} {client.first_name} {client.patronymic} {client.phone}"
        context['manager_fio'] = f"{manager.last_name} {manager.first_name} {manager.patronymic} {manager.phone}"
        c_def = self.get_user_context(title="Карточка заявки")
        return dict(list(context.items()) + list(c_def.items()))

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class AddGoodsView(LoginRequiredMixin, DataMixin, CreateView):
    pk_url_kwarg = 'appeal_id'
    form_class = AddGoodsForm
    model = Goods
    template_name = 'main/create_goods.html'
    success_url = reverse_lazy('card_appeal')
    login_url = reverse_lazy('login')
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
        return redirect('card_appeal', appeal_id=self.kwargs['appeal_id'])

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка добавления товара')
        return super(AddGoodsView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()


class CardGoodsView(LoginRequiredMixin, DataMixin, UpdateView):
    model = Goods
    form_class = CardGoodsForm
    template_name = 'main/card_goods.html'
    pk_url_kwarg = 'goods_id'
    context_object_name = 'goods'
    success_url = reverse_lazy('card_appeal')
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Карточка товара")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def form_valid(self, form):
        new_data = form.save(commit=False)
        new_data.appeal_id = Appeals.objects.get(pk=form.cleaned_data['password'])
        new_data.save()
        return redirect('card_appeal')

    def form_invalid(self, form):
        form.add_error(None, f'Ошибка изменения данных товара')
        return super(CardGoodsView, self).form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()