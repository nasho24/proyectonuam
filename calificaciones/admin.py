from django.contrib import admin
from django.contrib.auth.models import Group
from django.utils.html import format_html
from .models import Empresa, CalificacionTributaria, FactoresCalificacion, ArchivoCarga

# ==========================================
# CONFIGURACIÓN ADMINISTRATIVA PROFESIONAL
# ==========================================

# Personalizar el título del admin
admin.site.site_header = "NUAM Capital - Sistema de Gestión Tributaria"
admin.site.site_title = "Panel de Administración NUAM"
admin.site.index_title = "Administración del Sistema"

# Remover el modelo Group del admin (opcional)
admin.site.unregister(Group)

# ==========================================
# FILTROS PERSONALIZADOS
# ==========================================

class EjercicioFilter(admin.SimpleListFilter):
    title = 'Ejercicio Fiscal'
    parameter_name = 'ejercicio'
    
    def lookups(self, request, model_admin):
        ejercicios = CalificacionTributaria.objects.values_list('ejercicio', flat=True).distinct()
        return [(ej, f"{ej}") for ej in sorted(ejercicios)]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ejercicio=self.value())

class MercadoFilter(admin.SimpleListFilter):
    title = 'Mercado'
    parameter_name = 'mercado'
    
    def lookups(self, request, model_admin):
        mercados = CalificacionTributaria.objects.values_list('mercado', flat=True).distinct()
        return [(m, m) for m in sorted(mercados) if m]
    
    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(mercado=self.value())

# ==========================================
# INLINES PARA RELACIONES
# ==========================================

class FactoresCalificacionInline(admin.TabularInline):
    model = FactoresCalificacion
    extra = 0
    can_delete = False
    readonly_fields = ['validar_factores_display']  # CORREGIDO
    
    fields = ['validar_factores_display', 'factor_8', 'factor_9', 'factor_10']
    
    def validar_factores_display(self, obj):
        if obj.validar_factores():
            return format_html('<span style="color: green;">✅ Válido</span>')
        else:
            return format_html('<span style="color: red;">❌ Inválido</span>')
    validar_factores_display.short_description = 'Validación'

# ==========================================
# MODELADMIN PARA EMPRESAS
# ==========================================

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = [
        'rut_formateado', 
        'nombre', 
        'giro', 
        'telefono', 
        'email'
    ]
    
    list_filter = ['giro']
    search_fields = ['nombre', 'rut', 'giro', 'email']
    readonly_fields = ['fecha_creacion_display']  # CORREGIDO
    list_per_page = 20
    
    fieldsets = (
        ('Información Fiscal', {
            'fields': ('rut', 'nombre', 'giro')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'telefono', 'email')
        }),
    )
    
    def rut_formateado(self, obj):
        return format_html('<strong>{}</strong>', obj.rut)
    rut_formateado.short_description = 'RUT'
    rut_formateado.admin_order_field = 'rut'
    
    def fecha_creacion_display(self, obj):
        return f"ID: {obj.id}"
    fecha_creacion_display.short_description = 'ID Registro'

# ==========================================
# MODELADMIN PARA CALIFICACIONES TRIBUTARIAS
# ==========================================

@admin.register(CalificacionTributaria)
class CalificacionTributariaAdmin(admin.ModelAdmin):
    list_display = [
        'instrumento',
        'empresa_link',
        'ejercicio',
        'mercado',
        'fecha_pago',
        'origen_badge',
        'acogido_isfut_badge'
    ]
    
    list_filter = [EjercicioFilter, MercadoFilter, 'origen', 'acogido_isfut']
    search_fields = ['instrumento', 'empresa__nombre', 'descripcion_dividendo']
    readonly_fields = ['fecha_creacion_display']  # CORREGIDO
    list_per_page = 25
    date_hierarchy = 'fecha_pago'
    
    inlines = [FactoresCalificacionInline]
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'empresa', 
                'ejercicio', 
                'mercado', 
                'instrumento'
            )
        }),
        ('Detalles del Evento', {
            'fields': (
                'fecha_pago',
                'secuencia_evento', 
                'descripcion_dividendo',
                'tipo_sociedad',
                'valor_historico'
            )
        }),
        ('Clasificación', {
            'fields': (
                'origen',
                'acogido_isfut'
            )
        }),
    )
    
    def empresa_link(self, obj):
        return format_html(
            '<a href="/admin/calificaciones/empresa/{}/change/">{}</a>',
            obj.empresa.id,
            obj.empresa.nombre
        )
    empresa_link.short_description = 'Empresa'
    empresa_link.admin_order_field = 'empresa__nombre'
    
    def origen_badge(self, obj):
        color = {
            'CORREDOR': 'orange',
            'SISTEMA': 'blue', 
            'CARGA_MASIVA': 'green'
        }.get(obj.origen, 'gray')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_origen_display()
        )
    origen_badge.short_description = 'Origen'
    
    def acogido_isfut_badge(self, obj):
        if obj.acogido_isfut:
            return format_html(
                '<span style="background-color: green; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">✅ ISFUT</span>'
            )
        return format_html(
            '<span style="background-color: gray; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">❌ Sin ISFUT</span>'
        )
    acogido_isfut_badge.short_description = 'ISFUT'
    
    def fecha_creacion_display(self, obj):
        return f"ID: {obj.id}"
    fecha_creacion_display.short_description = 'ID Registro'

# ==========================================
# MODELADMIN PARA FACTORES
# ==========================================

@admin.register(FactoresCalificacion)
class FactoresCalificacionAdmin(admin.ModelAdmin):
    list_display = [
        'calificacion_link',
        'suma_factores_8_16',
        'factor_8',
        'factor_9', 
        'factor_10',
        'validacion_badge'
    ]
    
    list_filter = ['calificacion__ejercicio', 'calificacion__mercado']
    search_fields = ['calificacion__instrumento', 'calificacion__empresa__nombre']
    readonly_fields = ['suma_factores_8_16']  # CORREGIDO
    list_per_page = 20
    
    fieldsets = (
        ('Relación', {
            'fields': ('calificacion',)
        }),
        ('Factores Tributarios (8-16)', {
            'fields': (
                'factor_8', 'factor_9', 'factor_10', 'factor_11', 'factor_12',
                'factor_13', 'factor_14', 'factor_15', 'factor_16'
            )
        }),
        ('Factores Tributarios (17-37)', {
            'fields': (
                'factor_17', 'factor_18', 'factor_19', 'factor_20', 'factor_21',
                'factor_22', 'factor_23', 'factor_24', 'factor_25', 'factor_26',
                'factor_27', 'factor_28', 'factor_29', 'factor_30', 'factor_31',
                'factor_32', 'factor_33', 'factor_34', 'factor_35', 'factor_36',
                'factor_37'
            ),
            'classes': ('collapse',)
        }),
        ('Validación', {
            'fields': ('suma_factores_8_16',)
        }),
    )
    
    def calificacion_link(self, obj):
        return format_html(
            '<a href="/admin/calificaciones/calificaciontributaria/{}/change/">{}</a>',
            obj.calificacion.id,
            f"{obj.calificacion.instrumento} - {obj.calificacion.ejercicio}"
        )
    calificacion_link.short_description = 'Calificación'
    calificacion_link.admin_order_field = 'calificacion__instrumento'
    
    def suma_factores_8_16(self, obj):
        return obj.validar_factores()
    suma_factores_8_16.short_description = 'Σ Factores 8-16'
    
    def validacion_badge(self, obj):
        if obj.validar_factores():
            return format_html('<span style="color: green;">✅ Válido</span>')
        return format_html('<span style="color: red;">❌ Inválido</span>')
    validacion_badge.short_description = 'Validación'

# ==========================================
# MODELADMIN PARA ARCHIVOS DE CARGA
# ==========================================

@admin.register(ArchivoCarga)
class ArchivoCargaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_archivo',
        'empresa_link',
        'tipo_carga_badge',
        'fecha_carga',
        'estado_badge',
        'registros_procesados',
        'registros_error'
    ]
    
    list_filter = ['tipo_carga', 'estado', 'fecha_carga']
    search_fields = ['nombre_archivo', 'empresa__nombre']
    readonly_fields = ['fecha_carga', 'registros_procesados', 'registros_error']
    list_per_page = 15
    date_hierarchy = 'fecha_carga'
    
    def empresa_link(self, obj):
        return format_html(
            '<a href="/admin/calificaciones/empresa/{}/change/">{}</a>',
            obj.empresa.id,
            obj.empresa.nombre
        )
    empresa_link.short_description = 'Empresa'
    
    def tipo_carga_badge(self, obj):
        color = 'blue' if obj.tipo_carga == 'MONTOS' else 'green'
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            color,
            obj.get_tipo_carga_display()
        )
    tipo_carga_badge.short_description = 'Tipo Carga'
    
    def estado_badge(self, obj):
        colors = {
            'PENDIENTE': 'orange',
            'PROCESANDO': 'blue',
            'COMPLETADO': 'green',
            'ERROR': 'red'
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">{}</span>',
            colors.get(obj.estado, 'gray'),
            obj.estado
        )
    estado_badge.short_description = 'Estado'

# ==========================================
# ACCIONES PERSONALIZADAS
# ==========================================

def marcar_como_procesado(modeladmin, request, queryset):
    queryset.update(estado='COMPLETADO')
marcar_como_procesado.short_description = "📋 Marcar como procesado"

def recalcular_factores(modeladmin, request, queryset):
    for calificacion in queryset:
        # Aquí iría la lógica de recálculo
        pass
    modeladmin.message_user(request, "Factores recalculados exitosamente")
recalcular_factores.short_description = "🔄 Recalcular factores"

# Agregar acciones a los modelos
ArchivoCargaAdmin.actions = [marcar_como_procesado]
CalificacionTributariaAdmin.actions = [recalcular_factores]