import datetime
import re
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.http import HttpResponse
from django.shortcuts import redirect
import string
import random

from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView

from .forms import AddEmployeesForm, AddExchangeRatesForm, AddClientsForm, CardEmployeesForm, CardClientsForm, LoginUserForm
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
@login_required
def new_appeal(request):
    return HttpResponse("Создание заявки")


@login_required
def card_appeal(request):
    return HttpResponse("Карточка заявки")


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


class AppealsManagerView(LoginRequiredMixin, DataMixin, ListView):
    paginate_by = 3
    model = Appeals
    template_name = 'main/appeals.html'
    context_object_name = 'appeals'
    login_url = reverse_lazy('login')
    role_have_perm = ['Супер Администратор', 'Закупщик', 'Менеджер', 'Клиент']

    def get_context_data(self, *, object_list=None, **kwargs):
        c_def = self.get_user_context(title="Заявки")
        return dict(list(super().get_context_data(**kwargs).items())+list(c_def.items()))

    def get_queryset(self):
        return Appeals.objects.all().order_by('pk')

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        else:
            if request.user.role in self.role_have_perm:
                return super().dispatch(request, *args, **kwargs)
            return self.handle_no_permission()
