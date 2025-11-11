from django import forms
from .models import Empresa, CalificacionTributaria

class EmpresaForm(forms.ModelForm):
    class Meta:
        model = Empresa
        fields = ['rut', 'nombre', 'giro', 'direccion', 'telefono', 'email']
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12.345.678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de la empresa'}),
            'giro': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Giro comercial'}),
            'direccion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Dirección completa'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+56 9 1234 5678'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'empresa@ejemplo.com'}),
        }
class CalificacionForm(forms.ModelForm):
    class Meta:
        model = CalificacionTributaria
        fields = [
            'empresa', 'ejercicio', 'mercado', 'instrumento', 'fecha_pago',
            'descripcion_dividendo', 'secuencia_evento', 'acogido_isfut',
            'origen', 'tipo_sociedad', 'valor_historico'
        ]
        widgets = {
            'fecha_pago': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'ejercicio': forms.NumberInput(attrs={'class': 'form-control'}),
            'mercado': forms.TextInput(attrs={'class': 'form-control'}),
            'instrumento': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion_dividendo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'secuencia_evento': forms.NumberInput(attrs={'class': 'form-control'}),
            'valor_historico': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }