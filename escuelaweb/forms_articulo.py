from django import forms
from .models import Articulo

class ArticuloForm(forms.ModelForm):
    class Meta:
        model = Articulo
        fields = '__all__'
        widgets = {
            'codigo_barras': forms.TextInput(attrs={'class': 'form-control'}),
            # ...otros widgets...
        }

    def clean_codigo_barras(self):
        codigo = self.cleaned_data.get('codigo_barras')
        if codigo:
            if Articulo.objects.filter(codigo_barras=codigo).exists():
                raise forms.ValidationError('Ya existe un artículo con ese código de barras.')
        return codigo
