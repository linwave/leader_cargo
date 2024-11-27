from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, UpdateView

from .forms import AddClientsForm, AddRequisitesClientsForm, AddEntityForm, AddRequisitesEntityForm, AddBillsForm
from .models import Clients, RequisitesClients, Bills, Entity, RequisitesEntity
from main.utils import DataMixin, MyLoginMixin


def add_row_to_bill(request):
    template_name = 'bills/partial/add_row_to_bill.html'
    return render(request, template_name)


class BillsView(MyLoginMixin, DataMixin, TemplateView):
    template_name = 'bills/bills.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bills'] = Bills.objects.all()
        if self.request.user.role == 'Менеджер' or self.request.user.role == 'Логист':
            context['bills'] = context['bills'].filter(manager=self.request.user)
        c_def = self.get_user_context(title="Счета")
        return dict(list(context.items()) + list(c_def.items()))


class BillsAddView(MyLoginMixin, DataMixin, CreateView):
    model = Bills
    form_class = AddBillsForm
    template_name = 'bills/partial/add_bills.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Clients.objects.all()
        if self.request.user.role == 'Менеджер' or self.request.user.role == 'Логист':
            context['clients'] = context['clients'].filter(manager=self.request.user)
        context['entities'] = Entity.objects.all()
        c_def = self.get_user_context(title="Создание запроса счета")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        entity = Bills.objects.create(
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            inn=int(request.POST.get('inn')),
            cpp=request.POST.get('cpp'),
            ogrnip=request.POST.get('ogrnip'),
            ur_address=request.POST.get('ur_address'),
            fact_address=request.POST.get('fact_address'),
            phone=int(request.POST.get('phone').replace(' ', '').replace('+', '').replace('(', '').replace(')', '').replace('-', '')),
            name_job=request.POST.get('name_job'),
            fio=request.POST.get('fio'),
            based_charter=request.POST.get('based_charter'),
            nds_status=request.POST.get('nds_status')
        )
        entity.requisites.create(
            name=request.POST.get('requisites-name'),
            rs=request.POST.get('rs'),
            bic=request.POST.get('bic'),
            ks=request.POST.get('ks'),
            name_bank=request.POST.get('name_bank')
        )
        return redirect('bills:entity')


class EntityView(MyLoginMixin, DataMixin, TemplateView):
    template_name = 'bills/entity.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entities'] = Entity.objects.all()
        c_def = self.get_user_context(title="Наши счета")
        return dict(list(context.items()) + list(c_def.items()))


class EntityAddView(MyLoginMixin, DataMixin, CreateView):
    model = Entity
    form_class = AddEntityForm
    template_name = 'bills/partial/add_entity.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Добавление нашего Юр. лица")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        entity = Entity.objects.create(
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            inn=int(request.POST.get('inn')),
            cpp=request.POST.get('cpp'),
            ogrnip=request.POST.get('ogrnip'),
            ur_address=request.POST.get('ur_address'),
            fact_address=request.POST.get('fact_address'),
            phone=int(request.POST.get('phone').replace(' ', '').replace('+', '').replace('(', '').replace(')', '').replace('-', '')),
            name_job=request.POST.get('name_job'),
            fio=request.POST.get('fio'),
            based_charter=request.POST.get('based_charter'),
            nds_status=request.POST.get('nds_status')
        )
        entity.requisites.create(
            name=request.POST.get('requisites-name'),
            rs=request.POST.get('rs'),
            bic=request.POST.get('bic'),
            ks=request.POST.get('ks'),
            name_bank=request.POST.get('name_bank')
        )
        return redirect('bills:entity')


class EntityEditView(MyLoginMixin, DataMixin, UpdateView):
    model = Entity
    form_class = AddEntityForm
    pk_url_kwarg = 'entity_id'
    context_object_name = 'entity'
    template_name = 'bills/entity_edit.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requisites'] = self.get_object().requisites.all()
        c_def = self.get_user_context(title="Изменение данных нашего Юр. лица")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        entity = self.get_object()
        entity.name = request.POST.get('name')
        entity.type = request.POST.get('type')
        entity.inn = int(request.POST.get('inn'))
        entity.cpp = request.POST.get('cpp')
        entity.ogrnip = request.POST.get('ogrnip')
        entity.ur_address = request.POST.get('ur_address')
        entity.fact_address = request.POST.get('fact_address')
        entity.phone = int(request.POST.get('phone').replace(' ', '').replace('+', '').replace('(', '').replace(')', '').replace('-', ''))
        entity.name_job = request.POST.get('name_job')
        entity.fio = request.POST.get('fio')
        entity.based_charter = request.POST.get('based_charter')
        entity.nds_status = request.POST.get('nds_status')
        entity.save()
        return redirect('bills:entity_edit', entity.pk)


class ClientsView(MyLoginMixin, DataMixin, TemplateView):
    template_name = 'bills/clients.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['clients'] = Clients.objects.all()
        if self.request.user.role == 'Менеджер' or self.request.user.role == 'Логист':
            context['clients'] = context['clients'].filter(manager=self.request.user)
        c_def = self.get_user_context(title="Клиенты")
        return dict(list(context.items()) + list(c_def.items()))


class ClientsAddView(MyLoginMixin, DataMixin, CreateView):
    model = Clients
    form_class = AddClientsForm
    template_name = 'bills/partial/add_clients.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        c_def = self.get_user_context(title="Добавление клиентов")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        client = Clients.objects.create(
            manager=self.request.user,
            name=request.POST.get('name'),
            type=request.POST.get('type'),
            inn=int(request.POST.get('inn')),
            cpp=request.POST.get('cpp'),
            ogrnip=request.POST.get('ogrnip'),
            ur_address=request.POST.get('ur_address'),
            fact_address=request.POST.get('fact_address'),
            phone=int(request.POST.get('phone').replace(' ', '').replace('+', '').replace('(', '').replace(')', '').replace('-', '')),
            name_job=request.POST.get('name_job'),
            fio=request.POST.get('fio'),
            based_charter=request.POST.get('based_charter'),
            nds_status=request.POST.get('nds_status')
        )
        client.requisites.create(
            name=request.POST.get('requisites-name'),
            rs=request.POST.get('rs'),
            bic=request.POST.get('bic'),
            ks=request.POST.get('ks'),
            name_bank=request.POST.get('name_bank')
        )
        return redirect('bills:clients')


class ClientsEditView(MyLoginMixin, DataMixin, UpdateView):
    model = Clients
    form_class = AddClientsForm
    pk_url_kwarg = 'client_id'
    context_object_name = 'client'
    template_name = 'bills/clients_edit.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requisites'] = self.get_object().requisites.all()
        c_def = self.get_user_context(title="Изменение данных клиентов")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        client = self.get_object()
        client.name = request.POST.get('name')
        client.type = request.POST.get('type')
        client.inn = int(request.POST.get('inn'))
        client.cpp = request.POST.get('cpp')
        client.ogrnip = request.POST.get('ogrnip')
        client.ur_address = request.POST.get('ur_address')
        client.fact_address = request.POST.get('fact_address')
        client.phone = int(request.POST.get('phone').replace(' ', '').replace('+', '').replace('(', '').replace(')', '').replace('-', ''))
        client.name_job = request.POST.get('name_job')
        client.fio = request.POST.get('fio')
        client.based_charter = request.POST.get('based_charter')
        client.nds_status = request.POST.get('nds_status')
        client.save()
        return redirect('bills:clients_edit', client.pk)


class RequisitesClientsAddView(MyLoginMixin, DataMixin, CreateView):
    model = RequisitesClients
    form_class = AddRequisitesClientsForm
    template_name = 'bills/partial/add_req.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['client'] = Clients.objects.get(pk=self.request.GET['client'])
        c_def = self.get_user_context(title="Добавление реквизитов")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        client = Clients.objects.get(pk=kwargs['client_id'])
        client.requisites.create(
            name=request.POST.get('requisites-name'),
            rs=request.POST.get('rs'),
            bic=request.POST.get('bic'),
            ks=request.POST.get('ks'),
            name_bank=request.POST.get('name_bank')
        )
        return redirect('bills:clients_edit', client.pk)


class RequisitesClientsEditView(MyLoginMixin, DataMixin, CreateView):
    model = RequisitesClients
    form_class = AddRequisitesClientsForm
    pk_url_kwarg = 'requisite_id'
    context_object_name = 'requisite'
    template_name = 'bills/partial/edit_req.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requisite'] = self.get_object()
        context['client'] = context['requisite'].client
        c_def = self.get_user_context(title="Редактирование реквизитов")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        requisite = self.get_object()
        requisite.name=request.POST.get('requisites-name')
        requisite.rs=request.POST.get('rs')
        requisite.bic=request.POST.get('bic')
        requisite.ks=request.POST.get('ks')
        requisite.name_bank=request.POST.get('name_bank')
        requisite.save()
        return redirect('bills:clients_edit', requisite.client.pk)


class RequisitesEntityAddView(MyLoginMixin, DataMixin, CreateView):
    model = RequisitesEntity
    form_class = AddRequisitesEntityForm
    template_name = 'bills/partial/add_req_entity.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entity'] = Entity.objects.get(pk=self.request.GET['entity'])
        c_def = self.get_user_context(title="Добавление реквизитов наших Юр.лиц")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        entity = Entity.objects.get(pk=kwargs['entity_id'])
        entity.requisites.create(
            name=request.POST.get('requisites-name'),
            rs=request.POST.get('rs'),
            bic=request.POST.get('bic'),
            ks=request.POST.get('ks'),
            name_bank=request.POST.get('name_bank')
        )
        return redirect('bills:entity_edit', entity.pk)


class RequisitesEntityEditView(MyLoginMixin, DataMixin, CreateView):
    model = RequisitesEntity
    form_class = AddRequisitesEntityForm
    pk_url_kwarg = 'requisite_id'
    context_object_name = 'requisite'
    template_name = 'bills/partial/edit_req_entity.html'
    login_url = reverse_lazy('main:login')
    role_have_perm = ['Супер Администратор', 'Логист', 'РОП', 'Менеджер']

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super().get_context_data(**kwargs)
        context['requisite'] = self.get_object()
        context['entity'] = context['requisite'].entity
        c_def = self.get_user_context(title="Редактирование реквизитов наших Юр.лиц")
        return dict(list(context.items()) + list(c_def.items()))

    def post(self, request, *args, **kwargs):
        requisite = self.get_object()
        requisite.name=request.POST.get('requisites-name')
        requisite.rs=request.POST.get('rs')
        requisite.bic=request.POST.get('bic')
        requisite.ks=request.POST.get('ks')
        requisite.name_bank=request.POST.get('name_bank')
        requisite.save()
        return redirect('bills:entity_edit', requisite.entity.pk)

