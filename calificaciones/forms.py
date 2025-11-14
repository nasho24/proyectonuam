from django import forms
from django.contrib.auth.models import User
from .models import Empresa, CalificacionTributaria, Profile

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

class UserManagementForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label='Nombre')
    last_name = forms.CharField(required=True, label='Apellido')
    rol = forms.ChoiceField(choices=Profile.USER_ROLES, label='Rol')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and hasattr(self.instance, 'profile'):
            self.fields['rol'].initial = self.instance.profile.rol
    
    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            profile, created = Profile.objects.get_or_create(user=user)
            profile.rol = self.cleaned_data['rol']
            profile.save()
        return user

class UserCreateForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True, label='Nombre')
    last_name = forms.CharField(required=True, label='Apellido')
    password = forms.CharField(widget=forms.PasswordInput, label='Contraseña')
    rol = forms.ChoiceField(choices=Profile.USER_ROLES, label='Rol')
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        
        if commit:
            user.save()
            # VERIFICAR si ya existe un perfil antes de crear uno nuevo
            profile, created = Profile.objects.get_or_create(
                user=user,
                defaults={'rol': self.cleaned_data['rol']}
            )
            if not created:
                # Si ya existe, actualizar el rol
                profile.rol = self.cleaned_data['rol']
                profile.save()
        
        return user