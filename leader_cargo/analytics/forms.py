import django.forms
from django import forms
from django.forms import ModelForm, TextInput, Select, FileInput, NumberInput, DateInput, ClearableFileInput, FileField

from .models import CargoFiles, CargoArticle, CarriersList, RoadsList, RequestsForLogisticsCalculations, RequestsForLogisticsGoods, CarriersRoadParameters


class AddBidRequestLogisticsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsGoods
        fields = []


class UpdateRequestForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsCalculations
        fields = []


class NewStatusRequestForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsGoods
        fields = []


class AddGoodsRequestLogisticsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsGoods
        fields = []


class EditGoodsRequestLogisticsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsGoods
        fields = []


class AddRequestsForLogisticsCalculationsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsCalculations
        fields = ["name"]
        widgets = {
            "name": TextInput(attrs={
                'placeholder': 'Введите предварительное название запроса на просчет',
            }),
        }


class EditRequestsForLogisticsCalculationsForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RequestsForLogisticsCalculations
        fields = ["name"]
        widgets = {
            "name": TextInput(attrs={
                'placeholder': 'Введите название запроса на просчет',
            }),
        }


class AddRoadToCarriersForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['road'].empty_label = 'Дорога не выбрана'

    class Meta:
        model = CarriersRoadParameters
        fields = ["road", "min_transportation_time", "max_transportation_time"]
        widgets = {
            "road": Select(attrs={
                'empty_label': 'Дорога не выбрана',
                'class': 'form-select',
                'placeholder': 'Выберете дорогу',
            }),
            "min_transportation_time": NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите минимальное время доставки в Днях',
            }),
            "max_transportation_time": NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите максимальное время доставки в Днях',
            }),
        }


class EditRoadToCarriersForm(ModelForm):

    class Meta:
        model = CarriersRoadParameters
        fields = ["min_transportation_time", "max_transportation_time"]
        widgets = {
            "min_transportation_time": NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите минимальное время доставки в Днях',
            }),
            "max_transportation_time": NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Выберите максимальное время доставки в Днях',
            }),
        }


class DeleteRoadToCarriersForm(ModelForm):
    class Meta:
        model = CarriersRoadParameters
        fields = []


class AddRoadForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RoadsList
        fields = ["name"]
        widgets = {
            "name": TextInput(attrs={
                'placeholder': 'Введите название дороги',
            })
        }


class EditRoadForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = RoadsList
        fields = ["name", "activity"]
        widgets = {
            "carrier_name": TextInput(attrs={
                'placeholder': 'Введите название дороги',
            }),
        }


class DeleteRoadForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CarriersList
        fields = []


class AddCarriersListForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CarriersList
        fields = ["name"]
        widgets = {
            "name": TextInput(attrs={
                'placeholder': 'Введите название перевозчика',
            }),
        }


class EditCarriersListForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CarriersList
        fields = ["name", "activity"]
        widgets = {
            "carrier_name": TextInput(attrs={
                'placeholder': 'Введите название перевозчика',
            }),
        }


class DeleteCarriersListForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CarriersList
        fields = []


class AddCargo(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == 'time_from_china':
                continue
            self.fields[field].widget.attrs.update({'class': 'form-control'})
            if field in ['weight', 'volume', 'number_of_seats', 'cost_goods', 'insurance_cost', 'packaging_cost']:
                self.fields[field].widget.attrs.update({'class': 'form-control imask_float'})

    def clean_volume(self):
        value = self.cleaned_data.get('volume')
        if isinstance(value, str):
            value = value.replace(',', '.')
        try:
            return float(value)
        except (ValueError, TypeError):
            raise forms.ValidationError("Введите корректное значение объема.")

    class Meta:
        model = CargoArticle
        fields = [
            "article", "responsible_manager", "carrier", "path_format", "status",
            "name_goods", "number_of_seats", "weight", "volume", "transportation_tariff",
            "cost_goods", "insurance_cost", "packaging_cost", "time_from_china", "total_cost"
        ]
        widgets = {
            "time_from_china": forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }
class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class AddCarrierFilesForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CargoFiles
        fields = ["name_carrier", "file_path"]
        widgets = {
            "name_carrier": Select(attrs={
                'class': 'form-control',
                'id': 'name_carrier',
            }),
        }
    file_path = MultipleFileField()
class UpdateStatusArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CargoArticle
        fields = ["status"]


class EditTransportationTariffForClients(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CargoArticle
        fields = ["transportation_tariff_for_clients"]


class EditTableArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment_to_the_carrier_statuses = [
            ('Оплачено', 'Оплачено'),
            ('Не оплачено', 'Не оплачено'),
        ]
        paid_by_the_client_statuses = [
            ('Оплачено полностью', 'Оплачено полностью'),
            ('Оплачено частично', 'Оплачено частично'),
            ('Не оплачено', 'Не оплачено'),
        ]
        statuses = [
            ('В пути', 'В пути'),
            ('Прибыл в РФ', 'Прибыл в РФ')
        ]
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        # self.fields["paid_by_the_client_status"].choices = paid_by_the_client_statuses
        self.fields["payment_to_the_carrier_status"].choices = payment_to_the_carrier_statuses
        self.fields["status"].choices = statuses

    class Meta:
        model = CargoArticle
        fields = ["responsible_manager", "carrier", "path_format", "status", "prr", "tat_cost", "payment_to_the_carrier_status", "time_cargo_arrival_to_RF", "time_cargo_release"]
        widgets = {
            "prr": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': '00,00',
            }),
            "tat_cost": TextInput(attrs={
                'class': 'form-control',
                'type': 'text',
                'placeholder': '00,00',
            }),
            "time_cargo_arrival_to_RF": TextInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            "time_cargo_release": TextInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class EditTableManagerArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        paid_by_the_client_statuses = [
            ('Оплачено полностью', 'Оплачено полностью'),
            ('Оплачено частично', 'Оплачено частично'),
            ('Не оплачено', 'Не оплачено'),
        ]
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields["paid_by_the_client_status"].choices = paid_by_the_client_statuses

    class Meta:
        model = CargoArticle
        fields = ["paid_by_the_client_status"]


class EditPaidByTheClientArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        paid_by_the_client_statuses = [
            ('Оплачено полностью', 'Оплачено полностью'),
            ('Оплачено частично', 'Оплачено частично'),
            ('Не оплачено', 'Не оплачено'),
        ]
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields["paid_by_the_client_status"].choices = paid_by_the_client_statuses

    class Meta:
        model = CargoArticle
        fields = ["paid_by_the_client_status"]
