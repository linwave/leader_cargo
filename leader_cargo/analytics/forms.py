from django.forms import ModelForm, TextInput, Select, FileInput

from .models import CargoFiles, CargoArticle


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


class UpdateStatusArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})

    class Meta:
        model = CargoArticle
        fields = ["status"]


class EditTableArticleForm(ModelForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment_to_the_carrier_statuses = [
            ('Оплачено', 'Оплачено'),
            ('Не оплачено', 'Не оплачено'),
        ]
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields["payment_to_the_carrier_status"].choices = payment_to_the_carrier_statuses

    class Meta:
        model = CargoArticle
        fields = ["responsible_manager", "carrier", "path_format", "prr", "tat_cost", "payment_to_the_carrier_status", "time_cargo_arrival_to_RF", "time_cargo_release"]
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
