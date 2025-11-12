from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
# ==========================================
# MODELOS PRINCIPALES
# ==========================================


def clean(self):
    if not self.validar_factores():
        raise ValidationError("La suma de los factores del 8 al 16 no puede ser mayor que 1.")
    
def save(self, *args, **kwargs):
    self.clean()
    super().save(*args, **kwargs)

class Empresa(models.Model):
    rut = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    giro = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    class Meta:
        verbose_name = "Empresa"
        verbose_name_plural = "Empresas"
    
    def __str__(self):
        return f"{self.nombre} ({self.rut})"

class CalificacionTributaria(models.Model):
    TIPO_ORIGEN = [
        ('CORREDOR', 'Corredor'),
        ('SISTEMA', 'Sistema'),
        ('CARGA_MASIVA', 'Carga Masiva'),
    ]
    
    TIPO_SOCIEDAD = [
        ('A', 'Abierta'),
        ('C', 'Cerrada'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    ejercicio = models.IntegerField()
    mercado = models.CharField(max_length=10)
    instrumento = models.CharField(max_length=100)
    fecha_pago = models.DateField()
    descripcion_dividendo = models.TextField(blank=True, null=True)
    secuencia_evento = models.IntegerField()
    acogido_isfut = models.BooleanField(default=False)
    origen = models.CharField(max_length=50, choices=TIPO_ORIGEN)
    tipo_sociedad = models.CharField(max_length=1, choices=TIPO_SOCIEDAD, blank=True, null=True)
    valor_historico = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.instrumento} - {self.ejercicio}"

class FactoresCalificacion(models.Model):
    calificacion = models.OneToOneField(CalificacionTributaria, on_delete=models.CASCADE)
    
    # Factores del 8 al 37
    factor_8 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_9 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_10 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_11 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_12 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_13 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_14 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_15 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_16 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_17 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_18 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_19 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_20 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_21 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_22 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_23 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_24 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_25 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_26 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_27 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_28 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_29 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_30 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_31 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_32 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_33 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_34 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_35 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_36 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    factor_37 = models.DecimalField(max_digits=9, decimal_places=8, blank=True, null=True)
    
    def validar_factores(self):
        """Valida que la suma de factores 8-16 sea <= 1"""
        factores = [self.factor_8, self.factor_9, self.factor_10, self.factor_11, 
                   self.factor_12, self.factor_13, self.factor_14, self.factor_15, self.factor_16]
        suma = sum(factor for factor in factores if factor is not None)
        return suma <= 1

    def __str__(self):
        return f"Factores para {self.calificacion.instrumento}"

class ArchivoCarga(models.Model):
    TIPO_CARGA = [
        ('MONTOS', 'Montos'),
        ('FACTORES', 'Factores'),
    ]
    
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE)
    nombre_archivo = models.CharField(max_length=255)
    tipo_carga = models.CharField(max_length=20, choices=TIPO_CARGA)
    fecha_carga = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, default='PENDIENTE')
    registros_procesados = models.IntegerField(default=0)
    registros_error = models.IntegerField(default=0)
    
    def __str__(self):
        return f"{self.nombre_archivo} - {self.fecha_carga}"

# ==========================================
# MODELO USERPROFILE (NUEVO)
# ==========================================

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, null=True, blank=True)
    
    ROLES = [
        ('ADMIN', 'Administrador'),
        ('EMPRESA', 'Usuario Empresa'),
        ('CONSULTA', 'Usuario Consulta'),
    ]
    rol = models.CharField(max_length=20, choices=ROLES, default='EMPRESA')
    
    def __str__(self):
        return f"{self.user.username} - {self.empresa.nombre if self.empresa else 'Sin empresa'}"

# ==========================================
# SEÑALES PARA CREAR PERFIL AUTOMÁTICO
# ==========================================
        
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    mfa_secret = models.CharField(max_length=32, blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    empresa = models.ForeignKey('Empresa', on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Perfil de {self.user.username}"
    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()

class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(48)
        if not self.expires_at:
            # Siempre crear con timezone aware
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)
    
    def is_valid(self):
        """Verifica si el token es válido - compatible con naive y aware"""
        if self.used:
            return False
        
        now = timezone.now()
        
        # CONVERTIR expires_at a timezone aware si es naive
        if timezone.is_naive(self.expires_at):
            # Si expires_at es naive, asumir que está en la timezone por defecto
            from django.conf import settings
            default_timezone = timezone.get_default_timezone()
            expires_at_aware = timezone.make_aware(self.expires_at, default_timezone)
        else:
            expires_at_aware = self.expires_at
        
        return now < expires_at_aware
    
    def __str__(self):
        return f"Token for {self.user.email} - {'Valid' if self.is_valid() else 'Expired'}"


        