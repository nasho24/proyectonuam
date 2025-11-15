from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from .models import Empresa, CalificacionTributaria, FactoresCalificacion, ArchivoCarga, Profile, PasswordResetToken

# ==========================================
# CONFIGURACIÓN ADMINISTRATIVA PROFESIONAL
# ==========================================

admin.site.site_header = "NUAM Capital - Sistema de Gestión Tributaria"
admin.site.site_title = "Panel de Administración NUAM"
admin.site.index_title = "Administración del Sistema"
admin.site.unregister(Group)

# ==========================================
# INLINES PARA RELACIONES
# ==========================================

class FactoresCalificacionInline(admin.TabularInline):
    model = FactoresCalificacion
    extra = 0
    can_delete = False
    readonly_fields = ['validar_factores_display']
    
    fields = ['validar_factores_display', 'factor_8', 'factor_9', 'factor_10']
    
    def validar_factores_display(self, obj):
        if obj.validar_factores():
            return format_html('<span style="color: green;">✅ Válido</span>')
        else:
            return format_html('<span style="color: red;">❌ Inválido</span>')
    validar_factores_display.short_description = 'Validación'

# ==========================================
# INLINE PARA PERFILES DE USUARIO
# ==========================================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Perfil'
    fk_name = 'user'

# ==========================================
# USER ADMIN PERSONALIZADO
# ==========================================

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_rol', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'profile__rol')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    def get_rol(self, obj):
        return obj.profile.rol if hasattr(obj, 'profile') else 'Sin perfil'
    get_rol.short_description = 'Rol'

# ==========================================
# MODELADMIN PARA EMPRESAS (MODIFICADO)
# ==========================================

@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = [
        'rut_formateado', 
        'nombre', 
        'usuario',
        'giro', 
        'telefono', 
        'email'
    ]
    
    list_filter = ['giro', 'usuario']
    search_fields = ['nombre', 'rut', 'giro', 'email', 'usuario__username']
    readonly_fields = ['fecha_creacion_display']
    list_per_page = 20
    
    # ✅ MOSTRAR TODAS LAS EMPRESAS DE TODOS LOS USUARIOS
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario')
    
    fieldsets = (
        ('Información Fiscal', {
            'fields': ('rut', 'nombre', 'giro', 'usuario')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'telefono', 'email')
        }),
    )
    
    def rut_formateado(self, obj):
        return format_html('<strong>{}</strong>', obj.rut)
    rut_formateado.short_description = 'RUT'
    
    def fecha_creacion_display(self, obj):
        return f"ID: {obj.id}"
    fecha_creacion_display.short_description = 'ID Registro'

# ==========================================
# MODELADMIN PARA CALIFICACIONES TRIBUTARIAS (MODIFICADO)
# ==========================================

@admin.register(CalificacionTributaria)
class CalificacionTributariaAdmin(admin.ModelAdmin):
    list_display = [
        'instrumento',
        'empresa_link',
        'usuario',
        'ejercicio',
        'mercado',
        'fecha_pago',
        'origen_badge',
        'acogido_isfut_badge'
    ]
    
    list_filter = ['ejercicio', 'mercado', 'origen', 'acogido_isfut', 'usuario']
    search_fields = ['instrumento', 'empresa__nombre', 'descripcion_dividendo', 'usuario__username']
    readonly_fields = ['fecha_creacion_display']
    list_per_page = 25
    date_hierarchy = 'fecha_pago'
    
    inlines = [FactoresCalificacionInline]
    
    # ✅ MOSTRAR TODAS LAS CALIFICACIONES DE TODOS LOS USUARIOS
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('usuario', 'empresa')
    
    fieldsets = (
        ('Información Básica', {
            'fields': (
                'empresa', 
                'usuario',
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
            return format_html('<span style="color: green;">✅ ISFUT</span>')
        return format_html('<span style="color: gray;">❌ Sin ISFUT</span>')
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
    
    list_filter = ['calificacion__ejercicio', 'calificacion__mercado', 'calificacion__usuario']
    search_fields = ['calificacion__instrumento', 'calificacion__empresa__nombre', 'calificacion__usuario__username']
    readonly_fields = ['suma_factores_8_16']
    list_per_page = 20
    
    # ✅ MOSTRAR TODOS LOS FACTORES DE TODOS LOS USUARIOS
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('calificacion__usuario', 'calificacion__empresa')
    
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
    
    def suma_factores_8_16(self, obj):
        return obj.validar_factores()
    suma_factores_8_16.short_description = 'Σ Factores 8-16'
    
    def validacion_badge(self, obj):
        if obj.validar_factores():
            return format_html('<span style="color: green;">✅ Válido</span>')
        return format_html('<span style="color: red;">❌ Inválido</span>')
    validacion_badge.short_description = 'Validación'

# ==========================================
# MODELADMIN PARA ARCHIVOS DE CARGA (MODIFICADO)
# ==========================================

@admin.register(ArchivoCarga)
class ArchivoCargaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_archivo',
        'empresa_link',
        'usuario',
        'tipo_carga_badge',
        'fecha_carga',
        'estado_badge',
        'registros_procesados',
        'registros_error'
    ]
    
    list_filter = ['tipo_carga', 'estado', 'fecha_carga', 'empresa__usuario']
    search_fields = ['nombre_archivo', 'empresa__nombre', 'empresa__usuario__username']
    readonly_fields = ['fecha_carga', 'registros_procesados', 'registros_error']
    list_per_page = 15
    date_hierarchy = 'fecha_carga'
    
    # ✅ MOSTRAR TODOS LOS ARCHIVOS DE TODOS LOS USUARIOS
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('empresa__usuario')
    
    def empresa_link(self, obj):
        return format_html(
            '<a href="/admin/calificaciones/empresa/{}/change/">{}</a>',
            obj.empresa.id,
            obj.empresa.nombre
        )
    empresa_link.short_description = 'Empresa'
    
    def usuario(self, obj):
        return obj.empresa.usuario if obj.empresa.usuario else 'Sin usuario'
    usuario.short_description = 'Usuario'
    
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
# ADMIN PARA TOKENS DE PASSWORD RESET
# ==========================================

@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'created_at', 'expires_at', 'used', 'is_valid']
    list_filter = ['used', 'created_at']
    search_fields = ['user__username', 'user__email', 'token']
    readonly_fields = ['created_at', 'expires_at']
    
    def is_valid(self, obj):
        return obj.is_valid()
    is_valid.boolean = True
    is_valid.short_description = 'Válido'

# ==========================================
# REGISTRAR USER ADMIN PERSONALIZADO
# ==========================================

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# ==========================================
# ACCIONES PERSONALIZADAS
# ==========================================

def marcar_como_procesado(modeladmin, request, queryset):
    queryset.update(estado='COMPLETADO')
marcar_como_procesado.short_description = "📋 Marcar como procesado"

ArchivoCargaAdmin.actions = [marcar_como_procesado]