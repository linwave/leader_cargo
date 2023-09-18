from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import ExchangeRates, CustomUser, Appeals, Goods
from django.forms import ModelForm, TextInput, Select, CharField, Textarea, ImageField, FloatField, FileInput, ClearableFileInput


class LoginUserForm(AuthenticationForm):
    phone = CharField(label='Телефон', max_length=50, widget=TextInput(attrs={'class': 'form-control',
                                                                              'id': 'phone-mask',
                                                                              'type': 'text',
                                                                              'placeholder': '+7 (___) ___-__-__'}))
    password = CharField(label='Пароль', max_length=50, widget=TextInput(attrs={'class': 'form-control',
                                                                                'placeholder': "Введите пароль",
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
        fields = ["client"]


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

    def clean_phone(self):
        phone = self.cleaned_data['phone']
        if len(phone) != 18:
            raise ValidationError('Короткий номер телефона')
        return phone


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


