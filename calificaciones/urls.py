from django.urls import path
from . import views

app_name = 'calificaciones'

urlpatterns = [
    # Página principal / mantenedor
    path('', views.mantenedor_calificaciones, name='mantenedor'),
    
    # Gestión de calificaciones
    path('ingresar/', views.ingresar_calificacion, name='ingresar'),
    path('modificar/<int:id>/', views.modificar_calificacion, name='modificar'),
    path('eliminar/<int:id>/', views.eliminar_calificacion, name='eliminar'),
    
    # Carga de archivos (solo una vista por ahora)
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    
    # Búsqueda y reportes
    path('buscar/', views.buscar_calificaciones, name='buscar'),
    path('exportar/', views.exportar_calificaciones, name='exportar'),
    
    # Gestión de empresas
    path('empresas/', views.lista_empresas, name='empresas'),
    path('empresas/agregar/', views.agregar_empresa, name='agregar_empresa'),

    
     # Descarga de plantillas
    path('descargar-plantilla-montos/', views.descargar_plantilla_montos, name='descargar_plantilla_montos'),
    path('descargar-plantilla-factores/', views.descargar_plantilla_factores, name='descargar_plantilla_factores'),
]

