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
