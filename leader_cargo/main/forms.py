from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import ExchangeRates, CustomUser, Appeals, Goods, ManagersReports, ManagerPlans, Calls, CallsFile
from django.forms import ModelForm, TextInput, Select, CharField, Textarea, ImageField, FloatField, FileInput, ClearableFileInput


class RopReportForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'type': 'text'})

    class Meta:
        model = ManagersReports
        fields = ["net_profit_to_the_company", "raised_funds_to_the_company", "number_of_new_clients_attracted", "number_of_applications_to_buyers",
                  "amount_of_issued_CP", "number_of_incoming_quality_applications", "number_of_completed_transactions_based_on_orders", "number_of_calls", "duration_of_calls"]


class EditRopReportForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'type': 'text'})

    class Meta:
        model = ManagersReports
        fields = ["net_profit_to_the_company", "raised_funds_to_the_company", "number_of_new_clients_attracted", "number_of_applications_to_buyers",
                  "amount_of_issued_CP", "number_of_incoming_quality_applications", "number_of_completed_transactions_based_on_orders", "number_of_calls", "duration_of_calls"]


class AddManagerPlanForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'type': 'text'})

    class Meta:
        model = ManagerPlans
        fields = ["manager_monthly_net_profit_plan"]


class EditManagerPlanForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control', 'type': 'text'})

    class Meta:
        model = ManagerPlans
        fields = ["manager_monthly_net_profit_plan"]


class LoginUserForm(AuthenticationForm):
    phone = CharField(label='Телефон', max_length=50, widget=TextInput(attrs={
        'id': 'phone-mask',
        'type': 'text',
    }))
    password = CharField(label='Пароль', max_length=50, widget=TextInput(attrs={

        "type": "password",
        "id": "inputPassword5"}))


class AddAppealsForm(ModelForm):
    class Meta:
        model = Appeals
        fields = ["tag"]
        widgets = {
            "tag": TextInput(attrs={
                'class': 'form-control',
                'id': 'tag',
                'type': 'text',
                'placeholder': 'Введите название заявки',
            }),
        }


class UpdateStatusAppealsForm(ModelForm):
    class Meta:
        model = Appeals
        fields = ["status"]


class UpdateAppealsClientForm(ModelForm):
    class Meta:
        model = Appeals
        fields = ["tag"]
        widgets = {
            "tag": TextInput(attrs={
                'class': 'form-control',
                'id': 'tag',
                'type': 'text',
                'placeholder': 'Редактирование имени заявки',
                'style': "font-size: 1em;"
            }),
        }


class UpdateAppealsManagerForm(ModelForm):
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     clients = [
    #         (12, 'Менеджер'),
    #         (12, 'Закупщик'),
    #     ]
    #     self.fields["client"].widget.attrs.update({"class": 'form-control'})
    #     self.fields["client"].choices = clients

    class Meta:
        model = Appeals
        fields = ["tag", "logistic_price", "insurance_price", "packaging_price", "prr_price", "client"]
        widgets = {
            "tag": TextInput(attrs={
                'class': 'form-control',
                'id': 'tag',
                'type': 'text',
                'placeholder': 'Редактирование имени заявки',
                'style': "font-size: 1em;background-color: #f8f9fa;"
            }),
            "logistic_price": TextInput(attrs={
                'class': 'form-control',
                'id': 'logistic_price',
                'type': 'text',
                'placeholder': '-',
                # 'style': 'background-color: #f8f9fa;border: 0px;',
                # 'style': 'border: 0px;'
            }),
            "insurance_price": TextInput(attrs={
                'class': 'form-control',
                'id': 'insurance_price',
                'type': 'text',
                'placeholder': '-',
            }),
            "packaging_price": TextInput(attrs={
                'class': 'form-control',
                'id': 'packaging_price',
                'type': 'text',
                'placeholder': '-',
            }),
            "prr_price": TextInput(attrs={
                'class': 'form-control',
                'id': 'prr_price',
                'type': 'text',
                'placeholder': '-',
            }),
            "client": TextInput(attrs={
                'class': 'form-control',
                'id': 'client',
                'type': 'text',
                'placeholder': '-',
            }),
        }


class AddGoodsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Goods
        fields = "__all__"
        widgets = {
            "name": TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
                'type': 'text',
                'placeholder': 'Введите наименование товара',
            }),
            "link_url": TextInput(attrs={
                'class': 'form-control',
                'id': 'link_url',
                'type': 'text',
                'placeholder': 'Ссылка на товар',
            }),
            # "photo_good": ImageField(attrs={
            #     'class': 'form-control',
            #     'id': 'photo_good',
            #     'type': 'text',
            #     'placeholder': 'Ссылка на товар',
            # }),
            "quantity": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'quantity',
                'placeholder': 'Количество товара',
            }),
            "price_rmb": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_rmb',
                'placeholder': 'Цена за шт. в ¥ 00,00',
            }),
            "price_delivery": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery',
                'placeholder': 'Цена доставки по Китаю в ¥ 00,00',
            }),
            "product_description": Textarea(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'product_description',
                'placeholder': 'Дать ключевые характеристики - описание/требования',
            }),
            "price_purchase": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_purchase',
                'placeholder': 'Цена за шт Себестоимость - ¥',
            }),
            "price_site": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_site',
                'placeholder': 'Цена за шт На сайте - ¥',
            }),
            "price_delivery_real": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_real',
                'placeholder': 'Доставка по Китаю Себестоимость - ¥',
            }),
            "price_delivery_rf": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_rf',
                'placeholder': 'Доставка в РФ - $',
            }),
            "price_delivery_rf_real": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_rf_real',
                'placeholder': 'Доставка Себестоимость - $',
            }),
        }


class CardGoodsForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = Goods
        fields = "__all__"
        widgets = {
            "name": TextInput(attrs={
                'class': 'form-control',
                'id': 'name',
                'type': 'text',
                'placeholder': 'Введите наименование товара',
            }),
            "link_url": TextInput(attrs={
                'class': 'form-control',
                'id': 'link_url',
                'type': 'text',
                'placeholder': 'Ссылка на товар',
            }),
            "photo_good": ClearableFileInput(attrs={
                'class': 'form-control',
                'id': 'photo_good',
                'initial_text': 'lol',
            }),
            "quantity": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'quantity',
                'placeholder': 'Количество товара',
            }),
            "price_rmb": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_rmb',
                'placeholder': 'Цена за шт. в юанях 00,00',
            }),
            "price_delivery": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery',
                'placeholder': 'Цена доставки по Китаю 00,00',
            }),
            "product_description": Textarea(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'product_description',
                'placeholder': 'Дать ключевые характеристики - описание/требования',
            }),
            "price_purchase": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_purchase',
                'placeholder': 'Цена за шт Себестоимость - ¥',
            }),
            "price_site": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_site',
                'placeholder': 'Цена за шт На сайте - ¥',
            }),
            "price_delivery_real": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_real',
                'placeholder': 'Доставка по Китаю Себестоимость - ¥',
            }),
            "price_delivery_rf": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_rf',
                'placeholder': 'Доставка в РФ - $',
            }),
            "price_delivery_rf_real": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'id': 'price_delivery_rf_real',
                'placeholder': 'Доставка Себестоимость - $',
            }),
        }


class AddClientsForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ["phone", "first_name", "description", "password"]
        widgets = {
            "phone": TextInput(attrs={
                'class': 'form-control',
                'id': 'phone-mask',
                'type': 'text',
                'placeholder': "+7 (___) ___-__-__",
            }),
            "first_name": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': "ФИО",
            }),
            "description": Textarea(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': "Описание",
                # 'cols': 60,
                # 'rows': 10,
            }),
            "password": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': "Пароль",
                'id': 'pass-for-copy-client'
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if len(phone) != 18:
            raise ValidationError('Короткий номер телефона')
        return phone


class CardClientsForm(ModelForm):
    class Meta:
        model = CustomUser
        fields = ["phone", "first_name", "description", "password"]
        widgets = {
            "phone": TextInput(attrs={
                'class': 'form-control required',
                'id': 'phone-mask',
                'type': 'text',
                'placeholder': '+7 (___) ___-__-__',
            }),
            "first_name": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Имя"
            }),
            "description": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Описание"
            }),
            "password": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Введите пароль",
                "type": "password",
                "id": "inputPassword5",
                "position": "relative",
            }),
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if len(phone) != 18:
            raise ValidationError('Короткий номер телефона')
        return phone


class AddExchangeRatesForm(ModelForm):
    class Meta:
        model = ExchangeRates
        fields = ["yuan_cash_M", "yuan_cash_K", "yuan", "yuan_non_cash", "dollar"]
        widgets = {
            "yuan_cash_M": TextInput(attrs={
                'class': 'form-control',
                'id': 'yuan_cash_M',
                'type': 'text',
                'placeholder': "Курс юаня по наличке Москва",
            }),
            "yuan_cash_K": TextInput(attrs={
                'class': 'form-control',
                'id': 'yuan_cash_K',
                'type': 'text',
                'placeholder': "Курс юаня по наличке Краснодар",
            }),
            "yuan": TextInput(attrs={
                'class': 'form-control',
                'id': 'yuan',
                'type': 'text',
                'placeholder': "Курс юаня по карте",
            }),
            "yuan_non_cash": TextInput(attrs={
                'class': 'form-control',
                'id': 'yuan_non_cash',
                'type': 'text',
                'placeholder': "Курс юаня по безналу",
            }),
            "dollar": TextInput(attrs={
                'class': 'form-control',
                'id': 'dollar',
                'type': 'text',
                'placeholder': "Курс доллара 000,00",
            }),
        }


class AddEmployeesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        roles = [
            ('Менеджер', 'Менеджер'),
            ('Закупщик', 'Закупщик'),
        ]
        self.fields["role"].widget.attrs.update({"class": 'form-control'})
        self.fields["role"].choices = roles

    class Meta:
        model = CustomUser
        fields = ["phone", "password", "role", "last_name", "first_name", "patronymic", "town"]
        widgets = {
            "phone": TextInput(attrs={
                'class': 'form-control',
                'id': 'phone-mask',
                'type': 'text',
                'placeholder': '+7 (___) ___-__-__',
            }),
            "password": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Введите пароль",
                "type": "password",
                "id": "inputPassword5",
                # "width": 60,
                "position": "relative",
            }),
            # "role": Select(attrs={
            #     'class': 'form-control'
            # }),
            "last_name": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Фамилия"
            }),
            "first_name": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Имя"
            }),
            "patronymic": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Отчество"
            }),
            "town": Select(attrs={
                'class': 'form-control',
            })
        }

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if len(phone) != 18:
            raise ValidationError('Короткий номер телефона')
        return phone


class CardEmployeesForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        roles = [
            ('РОП', 'РОП'),
            ('Менеджер', 'Менеджер'),
            ('Оператор', 'Оператор'),
        ]
        self.fields["role"].widget.attrs.update({"class": 'form-control'})
        self.fields["role"].choices = roles

    class Meta:
        model = CustomUser
        fields = ["phone", "password", "role", "last_name", "first_name", "patronymic", "town", "status"]
        widgets = {
            "phone": TextInput(attrs={
                'class': 'form-control',
                'id': 'phone-mask',
                'type': 'text',
                'placeholder': '+7 (___) ___-__-__',
            }),
            "password": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Введите пароль",
                "type": "password",
                "id": "inputPassword5",
                # "width": 60,
                "position": "relative",
            }),
            "role": Select(attrs={
                'class': 'form-control'
            }),
            "last_name": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Фамилия"
            }),
            "first_name": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Имя"
            }),
            "patronymic": TextInput(attrs={
                'class': 'form-control',
                'placeholder': "Отчество"
            }),
            "town": Select(attrs={
                'class': 'form-control',
            }),
            "status": Select(attrs={
                'class': 'form-control',
            })
        }


class EditCallsOperator(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем менеджеров по ролям "РОП" и "Менеджер"
        self.fields['manager'].queryset = CustomUser.objects.filter(role__in=['РОП', 'Менеджер'])
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            # if field == 'weight':
            #     self.fields[field].widget.attrs.update({'class': 'form-control imask_float'})

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('manager') and not instance.date_to_manager:
            # Устанавливаем текущую дату и время, если выбран менеджер и date_to_manager пустой
            instance.date_to_manager = timezone.now()
        if self.cleaned_data.get('manager') != instance.manager:
            # Устанавливаем текущую дату и время, если выбран менеджер и date_to_manager пустой
            instance.date_to_manager = timezone.now()
        if not self.cleaned_data.get('manager'):
            instance.date_to_manager = None
        if commit:
            instance.save()
        return instance

    class Meta:
        model = Calls
        fields = ["status_call", "date_call", "client_name", "client_phone", "client_location", "description", 'date_next_call', 'manager']
        widgets = {
            "date_call": TextInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            "date_next_call": TextInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            "client_phone": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'autocomplete': 'off',
            }),
            "description": Textarea(attrs={
                'class': 'form-control',
                'maxlength': 250,
            }),
        }

class EditCallsManager(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем менеджеров по ролям "РОП" и "Менеджер"
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

        if 'description' in self.fields:
            self.fields['description'].widget.attrs['readonly'] = True

    class Meta:
        model = Calls
        fields = ["status_manager", "client_name", "client_phone", "client_location", "description", "description_manager", 'date_next_call_manager']
        widgets = {
            "date_next_call_manager": TextInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }),
            "client_phone": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'autocomplete': 'off',
            }),
            "description": Textarea(attrs={
                'class': 'form-control',
                'maxlength': 250,
            }),
            "description_manager": Textarea(attrs={
                'class': 'form-control',
                'maxlength': 250,
            }),
        }
class CallsFileForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CallsFile
        fields = ['crm', 'file']
        widgets = {
            'file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class CallsFilterForm(forms.Form):

    STATUS_OPERATOR_CHOICES = [
        ('Не обработано', 'Не обработано'),
        ('Не дозвонились', 'Не дозвонились'),
        ('Не заинтересован', 'Не заинтересован'),
        ('Заинтересован', 'Заинтересован'),
        ('Перезвонить позже', 'Перезвонить позже')
    ]

    STATUS_MANAGER_CHOICES = [
        ('Новая', 'Новая'),
        ('В работе', 'В работе'),
        ('Утверждена', 'Утверждена'),
        ('Отказ', 'Отказ')
    ]

    status_call = forms.MultipleChoiceField(
        choices=STATUS_OPERATOR_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Статус заявки'
    )

    status_manager = forms.MultipleChoiceField(
        choices=STATUS_MANAGER_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False,
        label='Статус заявки менеджера'
    )
# class AddCalls(ModelForm):
#
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for field in self.fields:
#             self.fields[field].widget.attrs.update({'class': 'form-control'})
#
#     class Meta:
#         model = Calls
#         fields = ["name_carrier", "file_path"]
#         widgets = {
#             "name_carrier": Select(attrs={
#                 'class': 'form-control',
#                 'id': 'name_carrier',
#             }),
#         }