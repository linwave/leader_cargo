from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import ExchangeRates, CustomUser
from django.forms import ModelForm, TextInput, Select, CharField, Textarea


class LoginUserForm(AuthenticationForm):
    phone = CharField(label='Телефон', max_length=50, widget=TextInput(attrs={'class': 'form-control',
                                                                              'id': 'phone-mask',
                                                                              'type': 'text',
                                                                              'placeholder': '+7 (___) ___-__-__'}))
    password = CharField(label='Пароль', max_length=50, widget=TextInput(attrs={'class': 'form-control',
                                                                                'placeholder': "Введите пароль",
                                                                                "type": "password",
                                                                                "id": "inputPassword5"}))


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


class AddExchangeRatesForm(ModelForm):
    class Meta:
        model = ExchangeRates
        fields = ["yuan", "dollar"]
        widgets = {
            "yuan": TextInput(attrs={
                'class': 'form-control',
                'id': 'yuan',
                'type': 'text',
                'placeholder': "Введите курс юаня 00,00",
            }),
            "dollar": TextInput(attrs={
                'class': 'form-control',
                'id': 'dollar',
                'type': 'text',
                'placeholder': "Введите курс доллара 000,00",
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


class CardEmployeesForm(ModelForm):
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