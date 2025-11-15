from django.urls import path
from . import views

app_name = 'calificaciones'

urlpatterns = [
    # admins urls
    path('gestion-usuarios/', views.admin_users, name='admin_users'),
    path('gestion-usuarios/crear/', views.admin_create_user, name='admin_create_user'),
    path('gestion-usuarios/editar/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    path('gestion-usuarios/eliminar/<int:user_id>/', views.admin_delete_user, name='admin_delete_user'),
    path('gestion-empresas/', views.admin_empresas, name='admin_empresas'),
    path('gestion-calificaciones/', views.admin_calificaciones, name='admin_calificaciones'),
    path('gestion-archivos/', views.admin_archivos_carga, name='admin_archivos'),
    # === DASHBOARDS ===
    path('', views.home, name='home'),
    # === REDIRECCIÓN OPCIONAL ===
    path('dashboard/', views.home, name='dashboard'),
    # === AUTENTICACIÓN ===
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    # === MFA ===
    path('mfa/', views.mfa_view, name='mfa'),
    path('verify-mfa/', views.verify_mfa_view, name='verify_mfa'),
    path('reset-password/<str:token>/', views.reset_password_view, name='reset_password'),
    # Vista general del mantenedor
    path('mantenedor/', views.mantenedor_calificaciones, name='mantenedor'),
    path('ingresar/', views.ingresar_calificacion, name='ingresar'),
    path('modificar/<int:id>/', views.modificar_calificacion, name='modificar'),
    path('eliminar/<int:id>/', views.eliminar_calificacion, name='eliminar'),
    path('empresas/', views.lista_empresas, name='empresas'),
    path('empresas/agregar/', views.agregar_empresa, name='agregar_empresa'),
    path('carga-masiva/', views.carga_masiva, name='carga_masiva'),
    path('descargar-plantilla-montos/', views.descargar_plantilla_montos, name='descargar_plantilla_montos'),
    path('descargar-plantilla-factores/', views.descargar_plantilla_factores, name='descargar_plantilla_factores'),
]