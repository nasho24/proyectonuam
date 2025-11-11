from django.db import models
from django.contrib.auth.models import User

class Empresa(models.Model):
    rut = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=255)
    giro = models.CharField(max_length=255, blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    
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
    # ... continuar con todos los factores hasta el 37
    
    def validar_factores(self):
        """Valida que la suma de factores 8-16 sea <= 1"""
        factores = [self.factor_8, self.factor_9, self.factor_10, self.factor_11, 
                   self.factor_12, self.factor_13, self.factor_14, self.factor_15, self.factor_16]
        suma = sum(factor for factor in factores if factor is not None)
        return suma <= 1

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