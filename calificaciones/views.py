from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages 
from .models import Empresa, CalificacionTributaria, Profile, PasswordResetToken
from .forms import EmpresaForm, UserCreateForm, UserManagementForm
import csv
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
import pyotp
import qrcode
import base64
from io import BytesIO
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone
import random

def send_mfa_email_code(user):
    """Genera y envía código MFA por email"""
    # Generar código de 6 dígitos
    code = str(random.randint(100000, 999999))
    
    # Guardar en el perfil
    profile = user.profile
    profile.mfa_email_code = code
    profile.mfa_email_code_expires = timezone.now() + timedelta(minutes=10)  # 10 minutos
    profile.save()
    
    # Enviar email
    try:
        send_mail(
            'Código de Verificación MFA - NUAM Capital',
            f'''
            NUAM CAPITAL - Código de Verificación

            Hola {user.first_name},

            Tu código de verificación para acceder a NUAM Capital es:

            🔒 {code}

            Este código expirará en 10 minutos.

            Si no solicitaste este código, ignora este mensaje.

            Equipo NUAM Capital
            ''',
            'NUAM Capital <noreply@nuamcapital.cl>',
            [user.email],
            fail_silently=False,
            html_message=f'''
            <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                <div style="background: #1a365d; color: white; padding: 20px; text-align: center;">
                    <h2 style="margin: 0;">NUAM CAPITAL</h2>
                </div>
                
                <div style="padding: 25px;">
                    <h3 style="color: #1a365d;">Código de Verificación</h3>
                    
                    <p>Hola <strong>{user.first_name}</strong>,</p>
                    
                    <p>Usa el siguiente código para completar tu acceso:</p>
                    
                    <div style="background: #f8f9fa; border: 2px dashed #dee2e6; padding: 20px; text-align: center; margin: 20px 0;">
                        <div style="font-size: 2rem; font-weight: bold; letter-spacing: 0.5rem; color: #1a365d;">
                            {code}
                        </div>
                        <small style="color: #6c757d;">Válido por 10 minutos</small>
                    </div>
                    
                    <p style="color: #6c757d; font-size: 0.9rem;">
                        Si no solicitaste este código, puedes ignorar este mensaje.
                    </p>
                </div>
            </div>
            '''
        )
        return True
    except Exception as e:
        print(f"Error enviando código MFA: {e}")
        return False


def es_administrador(user):
    return hasattr(user, 'profile') and user.profile.es_administrador()

@login_required
@user_passes_test(es_administrador)
def admin_users(request):
    """Vista principal de administración de usuarios"""
    usuarios = User.objects.all().select_related('profile')
    
    
    context = {
        'usuarios': usuarios,
        'total_usuarios': usuarios.count(),
        'admins': usuarios.filter(profile__rol='ADMIN').count(),
        'usuarios_normales': usuarios.filter(profile__rol='USER').count(),
        'viewers': usuarios.filter(profile__rol='VIEWER').count(),
    }
    return render(request, 'users_management.html', context)

@login_required
@user_passes_test(es_administrador)
def admin_create_user(request):
    """Vista para crear nuevo usuario"""
    if request.method == 'POST':
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Usuario {user.username} creado exitosamente')
            return redirect('calificaciones:admin_users')
    else:
        form = UserCreateForm()
    
    context = {
        'form': form,
        'titulo': 'Crear Nuevo Usuario'
    }
    return render(request, 'user_management_form.html', context)

@login_required
@user_passes_test(es_administrador)
def admin_edit_user(request, user_id):
    """Vista para editar usuario existente"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = UserManagementForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
            return redirect('calificaciones:admin_users')
    else:
        form = UserManagementForm(instance=usuario)
    
    context = {
        'form': form,
        'usuario': usuario,
        'titulo': f'Editar Usuario: {usuario.username}'
    }
    return render(request, 'user_management_form.html', context)

@login_required
@user_passes_test(es_administrador)
def admin_delete_user(request, user_id):
    """Vista para eliminar usuario"""
    usuario = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        username = usuario.username
        # No permitir eliminar el propio usuario
        if usuario == request.user:
            messages.error(request, 'No puedes eliminar tu propio usuario')
        else:
            usuario.delete()
            messages.success(request, f'Usuario {username} eliminado exitosamente')
        return redirect('calificaciones:admin_users')
    
    context = {
        'usuario': usuario,
        'titulo': 'Eliminar Usuario'
    }
    return render(request, 'confirm_delete_user.html', context)
def test_reset_view(request, token):
    """Vista temporal para probar que la URL funciona"""
    return HttpResponse(f"¡La URL funciona! Token recibido: {token}")

@login_required
def mfa_view(request):
    """Vista para configurar y verificar MFA en una sola página"""
    user = request.user
    profile = user.profile
    
    # Si ya está verificado, redirigir al dashboard
    if hasattr(profile, 'mfa_verified') and profile.mfa_verified:
        messages.info(request, "MFA ya está configurado y verificado")
        return redirect('calificaciones:dashboard')
    
    # Generar secreto si no existe
    if not profile.mfa_secret:
        secret = pyotp.random_base32()
        profile.mfa_secret = secret
        profile.save()
    else:
        secret = profile.mfa_secret

    # Generar QR
    try:
        import qrcode
        import base64
        from io import BytesIO
        
        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user.email, 
            issuer_name="NUAM Capital"
        )
        qr = qrcode.make(otp_uri)
        buffer = BytesIO()
        qr.save(buffer, format="PNG")
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return render(request, 'mfa.html', {
            'qr_base64': qr_base64, 
            'secret': secret
        })
        
    except ImportError:
        messages.error(request, "Error: No se puede generar el QR code")
        return render(request, 'mfa.html', {
            'secret': secret
        })

def verify_mfa_view(request):
    """Vista para verificar código MFA - SOLO EMAIL"""
    pending_user_id = request.session.get('pending_user_id')
    
    if not pending_user_id:
        messages.error(request, "Sesión de verificación no válida")
        return redirect('calificaciones:login')
    
    try:
        user = User.objects.get(id=pending_user_id)
    except User.DoesNotExist:
        messages.error(request, "Usuario no encontrado")
        return redirect('calificaciones:login')

    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        
        if not code:
            messages.error(request, "Por favor ingresa el código de verificación")
            return render(request, 'verify_mfa.html')
        
        # Validar código email
        profile = user.profile
        if (profile.mfa_email_code and 
            profile.mfa_email_code == code and
            profile.mfa_email_code_expires and
            profile.mfa_email_code_expires > timezone.now()):
            
            # ✅ Código correcto
            profile.mfa_email_code = None  # Limpiar código usado
            profile.mfa_email_code_expires = None
            profile.save()
            
            del request.session['pending_user_id']
            login(request, user)
            messages.success(request, f"✅ ¡Verificación exitosa! Bienvenido {user.first_name}")
            return redirect('calificaciones:dashboard')
        else:
            messages.error(request, "❌ Código incorrecto o expirado. Intenta nuevamente.")
    
    return render(request, 'verify_mfa.html')

def login_view(request):
    """
    Vista de login corregida y mejorada
    """
    # Si ya está autenticado, redirigir al dashboard
    if request.user.is_authenticated:
        return redirect('calificaciones:dashboard')
        
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        # Buscar usuario por email (username o email real)
        user = None
        
        # Intentar autenticar con username (que es el email en nuestro caso)
        user = authenticate(request, username=email, password=password)
        
        # Si no funciona, intentar buscar por email real
        if user is None:
            try:
                user_by_email = User.objects.get(email=email)
                user = authenticate(request, username=user_by_email.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            # Verificar si tiene MFA configurado
            if hasattr(user, "profile") and user.profile.mfa_secret:
                # ENVIAR CÓDIGO POR EMAIL en lugar de redirigir a app
                if send_mfa_email_code(user):
                    request.session["pending_user_id"] = user.id
                    request.session["mfa_type"] = "email"  # Indicar que es MFA por email
                    messages.info(request, "Se ha enviado un código de verificación a tu email")
                    return redirect("calificaciones:verify_mfa")
                else:
                    messages.error(request, "Error al enviar código de verificación")
                    return render(request, "login.html")
            
            # Login sin MFA
            login(request, user)
            messages.success(request, f"¡Bienvenido {user.first_name}!")
            return redirect("calificaciones:dashboard")
        else:
            messages.error(request, "Credenciales incorrectas")
    
    # Si es GET, simplemente renderizar el template
    return render(request, "login.html")

def forgot_password_view(request):
    """Vista para recuperación - CON localhost"""
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        
        try:
            user = User.objects.get(email=email)
            reset_token = PasswordResetToken.objects.create(user=user)
            
            # USAR localhost EN LUGAR DE 127.0.0.1
            reset_url = f"http://localhost:8000/reset-password/{reset_token.token}/"
            
            print(f"URL GENERADA: {reset_url}")
            
            send_mail(
                'Recuperación de Contraseña - NUAM Capital',
                f'''
                NUAM CAPITAL - Recuperación de Contraseña

                Hola {user.first_name},

                Para restablecer tu contraseña, haz clic en el siguiente enlace:

                {reset_url}

                Este enlace expirará en 24 horas.

                Equipo NUAM Capital
                ''',
                'NUAM Capital <noreply@nuamcapital.cl>',
                [user.email],
                fail_silently=False,
                html_message=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: #1a365d; color: white; padding: 20px; text-align: center;">
                        <h2 style="margin: 0;">NUAM CAPITAL</h2>
                    </div>
                    
                    <div style="padding: 25px;">
                        <p>Hola <strong>{user.first_name}</strong>,</p>
                        <p>Para restablecer tu contraseña, haz clic en el siguiente botón:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="{reset_url}" style="background: #1a365d; color: white; padding: 14px 35px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold;">
                                Restablecer Contraseña
                            </a>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; text-align: center;">
                            Este enlace expirará en 24 horas.
                        </p>
                    </div>
                </div>
                '''
            )
            
            messages.success(request, f'Se envió un enlace de recuperación a {email}. Revisa tu bandeja de entrada.')
            
        except User.DoesNotExist:
            messages.error(request, f'No existe una cuenta con el email: {email}')
        except Exception as e:
            messages.error(request, 'Error temporal al enviar el email.')
    
    return render(request, 'forgot_password.html')

def reset_password_view(request, token):
    """Vista para restablecer contraseña - CON DEBUG"""
    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        
        if reset_token.used:
            messages.error(request, "Este enlace ya fue utilizado.")
            return redirect('calificaciones:forgot_password')
        
        # Verificar expiración
        now = timezone.now()
        if timezone.is_naive(reset_token.expires_at):
            from django.conf import settings
            default_timezone = timezone.get_default_timezone()
            expires_at = timezone.make_aware(reset_token.expires_at, default_timezone)
        else:
            expires_at = reset_token.expires_at
            
        if now >= expires_at:
            messages.error(request, "El enlace ha expirado.")
            return redirect('calificaciones:forgot_password')
        
        if request.method == 'POST':
            password = request.POST.get('password')
            confirm_password = request.POST.get('confirm_password')
            
            print(f" DEBUG RESET PASSWORD:")
            print(f"   Usuario: {reset_token.user.email}")
            print(f"   Nueva contraseña recibida: {password}")
            print(f"   Confirmación: {confirm_password}")
            
            if password != confirm_password:
                messages.error(request, "Las contraseñas no coinciden.")
            elif len(password) < 6:
                messages.error(request, "La contraseña debe tener al menos 6 caracteres.")
            else:
                # Actualizar contraseña
                user = reset_token.user
                print(f"   Contraseña ANTES: {user.password[:20]}...")
                
                user.set_password(password)
                user.save()
                
                print(f"   Contraseña DESPUÉS: {user.password[:20]}...")
                print(f"   Contraseña actualizada")
                
                # Marcar token como usado
                reset_token.used = True
                reset_token.save()
                
                messages.success(request, "Contraseña actualizada correctamente. Ahora puedes iniciar sesión.")
                return redirect('calificaciones:login')
        
        return render(request, 'reset_password.html', {'token': token})
        
    except PasswordResetToken.DoesNotExist:
        messages.error(request, "El enlace de recuperación no es válido.")
        return redirect('calificaciones:forgot_password')

def logout_view(request):
    """Vista de logout - limpia mensajes y redirige"""
    # Limpiar mensajes existentes
    list(messages.get_messages(request))
    
    # Cerrar sesión
    logout(request)
    
    # Redirigir al login sin mensajes
    return redirect('calificaciones:login')

def register_view(request):
    """Vista de registro corregida con mejor manejo de errores"""
    if request.user.is_authenticated:
        return redirect('calificaciones:home')
        
    if request.method == "POST":
        nombre = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm_password")

        # Validaciones
        if password != confirm:
            messages.error(request, "Las contraseñas no coinciden")
            return render(request, "home_public.html")

        # Verificar si el usuario ya existe (por email o username)
        if User.objects.filter(email=email).exists():
            messages.error(request, "Ya existe una cuenta con este correo electrónico")
            return render(request, "home_public.html")

        if User.objects.filter(username=email).exists():
            messages.error(request, "Ya existe una cuenta con este correo electrónico")
            return render(request, "home_public.html")

        try:
            # Crear usuario
            user = User.objects.create_user(
                username=email,
                email=email,
                first_name=nombre,
                password=password
            )
            
            # Verificar si ya tiene perfil (por si acaso)
            if not hasattr(user, 'profile'):
                # Crear perfil con MFA solo si no existe
                secret = pyotp.random_base32()
                Profile.objects.create(user=user, mfa_secret=secret)
            
            messages.success(request, "Cuenta creada correctamente. Ahora puedes iniciar sesión.")
            return redirect("calificaciones:login")

        except Exception as e:
            # Manejo genérico de errores inesperados
            print(f"Error en registro: {str(e)}")  # Para debug
            messages.error(request, "Error al crear la cuenta. Por favor intenta nuevamente.")
    
    return render(request, "register.html")

def home(request):
    """Página principal - Datos DEL USUARIO ACTUAL"""
    if request.user.is_authenticated:
        # Datos para el dashboard autenticado - SOLO DEL USUARIO
        total_empresas = Empresa.objects.filter(usuario=request.user).count()
        total_calificaciones = CalificacionTributaria.objects.filter(usuario=request.user).count()
        
        # Contar usuarios con MFA habilitado (esto sigue global)
        usuarios_con_mfa = Profile.objects.filter(mfa_secret__isnull=False).count()
        
        context = {
            'page_title': 'Panel General - NUAM',
            'total_empresas': total_empresas,
            'total_calificaciones': total_calificaciones,
            'usuarios_activos': usuarios_con_mfa,
            'factores_range': range(8, 17),
        }
        return render(request, 'dashboard_authenticated.html', context)
    else:
        # Contexto para landing page
        context = {
            'page_title': 'NUAM Capital - Sistema de Gestión',
        }
        return render(request, 'home_public.html', context)
    
@login_required
def mantenedor_calificaciones(request):
    """Vista principal del mantenedor con datos DEL USUARIO ACTUAL"""
    calificaciones = CalificacionTributaria.objects.filter(usuario=request.user).select_related('empresa')
    
    # Filtros (solo sobre los datos del usuario)
    ejercicio = request.GET.get('ejercicio')
    mercado = request.GET.get('mercado')
    instrumento = request.GET.get('instrumento')
    
    if ejercicio:
        calificaciones = calificaciones.filter(ejercicio=ejercicio)
    if mercado:
        calificaciones = calificaciones.filter(mercado__icontains=mercado)
    if instrumento:
        calificaciones = calificaciones.filter(instrumento__icontains=instrumento)
    
    context = {
        'calificaciones': calificaciones,
    }
    return render(request, 'mantenedor.html', context)

@login_required
def ingresar_calificacion(request):
    """Vista para ingresar nueva calificación - ASIGNAR AL USUARIO"""
    empresas = Empresa.objects.filter(usuario=request.user)  # Solo empresas del usuario
    
    if request.method == 'POST':
        try:
            calificacion = CalificacionTributaria(
                usuario=request.user,  # ⬅️ ASIGNAR USUARIO AUTOMÁTICAMENTE
                empresa_id=request.POST.get('empresa'),
                ejercicio=request.POST.get('ejercicio'),
                mercado=request.POST.get('mercado'),
                instrumento=request.POST.get('instrumento'),
                fecha_pago=request.POST.get('fecha_pago'),
                secuencia_evento=request.POST.get('secuencia_evento'),
                tipo_sociedad=request.POST.get('tipo_sociedad'),
                valor_historico=request.POST.get('valor_historico') or None,
                descripcion_dividendo=request.POST.get('descripcion_dividendo'),
                origen=request.POST.get('origen'),
                acogido_isfut=bool(request.POST.get('acogido_isfut'))
            )
            calificacion.save()
            
            messages.success(request, f'Calificación {calificacion.instrumento} creada correctamente')
            return redirect('calificaciones:mantenedor')
            
        except Exception as e:
            messages.error(request, f'Error al crear la calificación: {str(e)}')
    
    context = {
        'titulo': 'Ingresar Nueva Calificación',
        'empresas': empresas
    }
    return render(request, 'form_calificacion.html', context)

@login_required  # Solo para usuarios autenticados
def modificar_calificacion(request, id):
    """Vista para modificar calificación existente"""
    calificacion = get_object_or_404(CalificacionTributaria, id=id)
    empresas = Empresa.objects.all()
    
    if request.method == 'POST':
        try:
            # Actualizar los campos
            calificacion.empresa_id = request.POST.get('empresa')
            calificacion.ejercicio = request.POST.get('ejercicio')
            calificacion.mercado = request.POST.get('mercado')
            calificacion.instrumento = request.POST.get('instrumento')
            calificacion.fecha_pago = request.POST.get('fecha_pago')
            calificacion.secuencia_evento = request.POST.get('secuencia_evento')
            calificacion.tipo_sociedad = request.POST.get('tipo_sociedad')
            
            # Manejar campo opcional
            valor_historico = request.POST.get('valor_historico')
            calificacion.valor_historico = valor_historico if valor_historico else None
            
            calificacion.descripcion_dividendo = request.POST.get('descripcion_dividendo')
            calificacion.origen = request.POST.get('origen')
            calificacion.acogido_isfut = 'acogido_isfut' in request.POST
            
            calificacion.save()
            messages.success(request, f'Calificación {calificacion.instrumento} actualizada correctamente')
            return redirect('calificaciones:mantenedor')
            
        except Exception as e:
            messages.error(request, f'Error al actualizar: {str(e)}')
    
    context = {
        'titulo': f'Modificar Calificación: {calificacion.instrumento}',
        'empresas': empresas,
        'calificacion': calificacion
    }
    return render(request, 'form_calificacion.html', context)

@login_required  # Solo para usuarios autenticados
def eliminar_calificacion(request, id):
    """Vista para eliminar calificación"""
    calificacion = get_object_or_404(CalificacionTributaria, id=id)
    
    if request.method == 'POST':
        instrumento = calificacion.instrumento
        calificacion.delete()
        messages.success(request, f'Calificación {instrumento} eliminada correctamente')
        return redirect('calificaciones:mantenedor')
    
    context = {
        'calificacion': calificacion,
        'titulo': 'Eliminar Calificación'
    }
    return render(request, 'confirmar_eliminar.html', context)

def carga_masiva(request):
    return render(request, 'carga_masiva.html')

@login_required
def lista_empresas(request):
    """Vista para listar empresas DEL USUARIO ACTUAL"""
    empresas = Empresa.objects.filter(usuario=request.user)
    context = {
        'empresas': empresas,
    }
    return render(request, 'empresas.html', context)

@login_required
def agregar_empresa(request):
    """Vista para agregar nueva empresa - ASIGNAR AL USUARIO"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save(commit=False)
            empresa.usuario = request.user  # ⬅️ ASIGNAR USUARIO AUTOMÁTICAMENTE
            empresa.save()
            messages.success(request, f'Empresa {empresa.nombre} creada correctamente')
            return redirect('calificaciones:empresas')
    else:
        form = EmpresaForm()
    
    context = {
        'form': form,
        'titulo': 'Agregar Nueva Empresa'
    }
    return render(request, 'form_empresa.html', context)

def buscar_calificaciones(request):
    """Vista para búsqueda específica (puede combinarse con mantenedor)"""
    return redirect('calificaciones:mantenedor')

def exportar_calificaciones(request):
    """Vista para exportar calificaciones a CSV"""

    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="calificaciones.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Ejercicio', 'Instrumento', 'Mercado', 'Fecha Pago', 'Origen'])
    
    calificaciones = CalificacionTributaria.objects.all()
    for calif in calificaciones:
        writer.writerow([
            calif.ejercicio,
            calif.instrumento,
            calif.mercado,
            calif.fecha_pago,
            calif.get_origen_display()
        ])
    
    return response

# Template para confirmar eliminación
def confirmar_eliminar(request, id):
    """Vista para confirmar eliminación"""
    calificacion = get_object_or_404(CalificacionTributaria, id=id)
    
    if request.method == 'POST':
        calificacion.delete()
        return redirect('calificaciones:mantenedor')
    
    context = {
        'calificacion': calificacion,
        'titulo': 'Confirmar Eliminación'
    }
    return render(request, 'confirmar_eliminar.html', context)

@login_required  # Solo para usuarios autenticados
def descargar_plantilla_montos(request):
    """Descargar plantilla CSV formal para carga de montos DJ1948"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="NUAM_Plantilla_Formal_Montos_DJ1948.csv"'
    
    response.write(u'\ufeff')  # BOM para UTF-8
    writer = csv.writer(response, delimiter=',', quoting=csv.QUOTE_ALL)
    
    # ===== HEADER CORPORATIVO FORMAL =====
    writer.writerow(['NUAM CAPITAL - SISTEMA INTEGRAL DE GESTIÓN TRIBUTARIA'])
    writer.writerow(['PLANTILLA FORMAL PARA CARGA MASIVA DE MONTOS - FORMULARIO DJ1948'])
    writer.writerow(['Fecha de Emisión:', datetime.now().strftime('%d de %B de %Y')])
    writer.writerow(['Código Documento:', 'NUAM-DJ1948-PLANTILLA-1.0'])
    writer.writerow(['Área Responsable:', 'Departamento de Cumplimiento Tributario'])
    writer.writerow([])
    
    # ===== INSTRUCCIONES FORMALES =====
    writer.writerow(['SECCIÓN I: INSTRUCCIONES FORMALES DE USO'])
    writer.writerow(['1. IDENTIFICACIÓN DE CAMPOS OBLIGATORIOS'])
    writer.writerow(['   - Campos marcados con (*) son de carácter obligatorio'])
    writer.writerow(['   - El incumplimiento generará rechazo en la validación'])
    writer.writerow([])
    writer.writerow(['2. ESPECIFICACIONES TÉCNICAS'])
    writer.writerow(['   - Fechas: Formato ISO 8601 (YYYY-MM-DD)'])
    writer.writerow(['   - Decimales: Separador punto (.), dos decimales para montos'])
    writer.writerow(['   - Moneda: Pesos Chilenos ($)'])
    writer.writerow(['   - Codificación: UTF-8'])
    writer.writerow([])
    writer.writerow(['3. PROCESO DE CARGA'])
    writer.writerow(['   - Complete los datos en las secciones indicadas'])
    writer.writerow(['   - Mantenga la estructura de encabezados original'])
    writer.writerow(['   - Elimine las filas de ejemplo antes de la carga productiva'])
    writer.writerow([])
    
    # ===== SECCIÓN DE DATOS - ENCABEZADOS =====
    writer.writerow(['SECCIÓN II: ESTRUCTURA DE DATOS - MONTOS TRIBUTARIOS'])
    encabezados = [
        'EJERCICIO_FISCAL (*)',
        'CODIGO_MERCADO (*)', 
        'INSTRUMENTO_FINANCIERO (*)',
        'FECHA_PAGO (*)',
        'SECUENCIA_EVENTO',
        'DESCRIPCION_EVENTO',
        'TIPO_SOCIEDAD',
        'VALOR_HISTORICO'
    ]
    
    # Montos con descripción formal
    descripciones_oficiales = {
        8: 'MONTO_CREDITO_IDPC_2017',
        9: 'MONTO_CREDITO_IDPC_2016', 
        10: 'MONTO_CREDITO_IDPC_VOLUNTARIO',
        11: 'MONTO_SIN_CREDITO_IDPC',
        12: 'MONTO_RENTAS_RAP_DIF_INICIAL',
        13: 'MONTO_OTRAS_RENTAS_SIN_PRIORIDAD',
        14: 'MONTO_EXCESO_DISTRIBUCIONES',
        15: 'MONTO_UTILIDADES_ISFUT_20780',
        16: 'MONTO_RENTAS_1983_ISFUT_21210',
        17: 'MONTO_RENTAS_EXENTAS_IGC_AFECTAS_IA',
        18: 'MONTO_RENTAS_EXENTAS_IGC_IA',
        19: 'MONTO_INGRESOS_NO_CONSTITUTIVOS_RENTA',
        # ... continuar con los 37 montos
    }
    
    for i in range(8, 38):
        nombre_oficial = descripciones_oficiales.get(i, f'MONTO_{i:02d}')
        encabezados.append(f'{nombre_oficial}')
    
    writer.writerow(encabezados)
    writer.writerow([])
    
    # ===== EJEMPLOS FORMALES COMPLETOS =====
    writer.writerow(['SECCIÓN III: EJEMPLOS FORMALES DE REGISTRO'])
    writer.writerow(['NOTA: Los siguientes ejemplos representan casos reales válidos para el sistema.'])
    writer.writerow([])
    
    # Ejemplo 1 - Acción con dividendos
    writer.writerow(['EJEMPLO 1: ACCIÓN ORDINARIA - DIVIDENDO ORDINARIO'])
    ejemplo1 = [
        2024,                           # EJERCICIO_FISCAL
        'ACN',                          # CODIGO_MERCADO
        'BANCO_SANTANDER_CHILE',        # INSTRUMENTO_FINANCIERO  
        '2024-09-15',                   # FECHA_PAGO
        10001,                          # SECUENCIA_EVENTO
        'DIVIDENDO ORDINARIO CORRESPONDIENTE AL EJERCICIO 2024',
        'A',                            # TIPO_SOCIEDAD
        '1850.75'                       # VALOR_HISTORICO
    ]
    
    # Montos de ejemplo realistas
    montos_ejemplo1 = [
        '1250000.00',   # monto_8
        '850000.00',    # monto_9  
        '0.00',         # monto_10
        '2500000.00',   # monto_11
        '0.00',         # monto_12
        '150000.00',    # monto_13
        '0.00',         # monto_14
        '0.00',         # monto_15
        '0.00',         # monto_16
        '0.00',         # monto_17
        '0.00',         # monto_18
        '0.00',         # monto_19
        # ... completar con 0.00 hasta monto_37
    ]
    
    # Rellenar los 37 montos
    while len(montos_ejemplo1) < 30:  # 37-8+1 = 30 campos
        montos_ejemplo1.append('0.00')
    
    ejemplo1.extend(montos_ejemplo1[:30])
    writer.writerow(ejemplo1)
    writer.writerow([])
    
    # Ejemplo 2 - Cuota de fondo
    writer.writerow(['EJEMPLO 2: CUOTA DE FONDO DE INVERSIÓN - DISTRIBUCIÓN SEMESTRAL'])
    ejemplo2 = [
        2024,
        'CFI',
        'FONDO_CAPITALIZACION_NUAM', 
        '2024-06-30',
        10002,
        'DISTRIBUCIÓN DE UTILIDADES SEMESTRALES FONDO DE INVERSIÓN',
        'C',
        '0.00'
    ]
    
    montos_ejemplo2 = [
        '0.00',         # monto_8
        '0.00',         # monto_9
        '0.00',         # monto_10
        '3250000.00',   # monto_11
        '0.00',         # monto_12
        '0.00',         # monto_13
        '0.00',         # monto_14
        '0.00',         # monto_15
        '0.00',         # monto_16
        '0.00',         # monto_17
        '0.00',         # monto_18
        '0.00',         # monto_19
        # ... completar con 0.00
    ]
    
    while len(montos_ejemplo2) < 30:
        montos_ejemplo2.append('0.00')
    
    ejemplo2.extend(montos_ejemplo2[:30])
    writer.writerow(ejemplo2)
    writer.writerow([])
    
    # ===== SECCIÓN DE VALIDACIONES =====
    writer.writerow(['SECCIÓN IV: NORMAS DE VALIDACIÓN'])
    writer.writerow(['ARTÍCULO 1: FORMATOS ACEPTADOS'])
    writer.writerow(['   - EJERCICIO_FISCAL: Año entre 2000 y 2030'])
    writer.writerow(['   - CODIGO_MERCADO: ACN, CFI, FONDOS, DERIVADOS'])
    writer.writerow(['   - FECHA_PAGO: Fecha válida en formato YYYY-MM-DD'])
    writer.writerow(['   - SECUENCIA_EVENTO: Número único ≥ 10000'])
    writer.writerow([])
    writer.writerow(['ARTÍCULO 2: REGLAS DE NEGOCIO'])
    writer.writerow(['   - Los montos deben ser valores numéricos positivos'])
    writer.writerow(['   - El sistema calculará factores automáticamente'])
    writer.writerow(['   - Validación: Σ(factores 8-16) ≤ 1.00000000'])
    writer.writerow([])
    
    # ===== PIE DE PÁGINA FORMAL =====
    writer.writerow(['SECCIÓN V: INFORMACIÓN INSTITUCIONAL'])
    writer.writerow(['NUAM CAPITAL LIMITADA'])
    writer.writerow(['RUT: 76.123.456-7'])
    writer.writerow(['Av. Apoquindo 3000, Las Condes, Santiago'])
    writer.writerow(['Teléfono: +56 2 2345 6789'])
    writer.writerow(['Email: cumplimiento.tributario@nuamcapital.cl'])
    writer.writerow(['Sitio Web: www.nuamcapital.cl'])
    writer.writerow([])
    writer.writerow(['DOCUMENTO DE USO INTERNO - CONFIDENCIALIDAD PROTEGIDA'])
    
    return response
@login_required
def descargar_plantilla_factores(request):
    """Descargar plantilla CSV formal para carga de factores"""
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="NUAM_Plantilla_Formal_Factores_Tributarios.csv"'
    
    response.write(u'\ufeff')  # BOM para UTF-8
    writer = csv.writer(response, delimiter=',', quoting=csv.QUOTE_ALL)
    
    # ===== HEADER CORPORATIVO FORMAL =====
    writer.writerow(['NUAM CAPITAL - SISTEMA INTEGRAL DE GESTIÓN TRIBUTARIA'])
    writer.writerow(['PLANTILLA FORMAL PARA CARGA MASIVA DE FACTORES TRIBUTARIOS'])
    writer.writerow(['Fecha de Emisión:', datetime.now().strftime('%d de %B de %Y')])
    writer.writerow(['Código Documento:', 'NUAM-FACTORES-PLANTILLA-1.0'])
    writer.writerow(['Área Responsable:', 'Departamento de Análisis Tributario'])
    writer.writerow([])
    
    # ===== INSTRUCCIONES ESPECÍFICAS FACTORES =====
    writer.writerow(['SECCIÓN I: INSTRUCCIONES ESPECIALIZADAS - FACTORES'])
    writer.writerow(['1. PRECISIÓN DECIMAL REQUERIDA'])
    writer.writerow(['   - Todos los factores deben tener 8 decimales'])
    writer.writerow(['   - Formato: 0.12345678 (nunca 0,12345678)'])
    writer.writerow(['   - Rango válido: 0.00000000 a 1.00000000'])
    writer.writerow([])
    writer.writerow(['2. RESTRICCIÓN CRÍTICA - SUMA FACTORES 8-16'])
    writer.writerow(['   - La suma de factores 8 al 16 NO debe superar 1.00000000'])
    writer.writerow(['   - Validación automática: Σ(factor_8...factor_16) ≤ 1.0'])
    writer.writerow(['   - Ejemplo válido: 0.15000000 + 0.20000000 + ... = 0.95000000'])
    writer.writerow(['   - Ejemplo inválido: 0.30000000 + 0.35000000 + ... = 1.10000000'])
    writer.writerow([])
    
    # ===== SECCIÓN DE DATOS - ENCABEZADOS FACTORES =====
    writer.writerow(['SECCIÓN II: ESTRUCTURA DE DATOS - FACTORES TRIBUTARIOS'])
    encabezados = [
        'EJERCICIO_FISCAL (*)',
        'CODIGO_MERCADO (*)',
        'INSTRUMENTO_FINANCIERO (*)', 
        'FECHA_PAGO (*)',
        'SECUENCIA_EVENTO',
        'DESCRIPCION_EVENTO'
    ]
    
    # Factores con nomenclatura oficial completa
    nomenclatura_oficial = {
        8: 'FACTOR_CREDITO_IDPC_DESDE_2017',
        9: 'FACTOR_CREDITO_IDPC_HASTA_2016',
        10: 'FACTOR_CREDITO_IDPC_VOLUNTARIO',
        11: 'FACTOR_SIN_CREDITO_IDPC',
        12: 'FACTOR_RENTAS_RAP_DIFERENCIA_INICIAL',
        13: 'FACTOR_OTRAS_RENTAS_SIN_PRIORIDAD',
        14: 'FACTOR_EXCESO_DISTRIBUCIONES_DESPROPORCIONADAS',
        15: 'FACTOR_UTILIDADES_ISFUT_LEY_20780',
        16: 'FACTOR_RENTAS_1983_ISFUT_LEY_21210',
        17: 'FACTOR_RENTAS_EXENTAS_IGC_AFECTAS_IA',
        18: 'FACTOR_RENTAS_EXENTAS_IGC_IA',
        19: 'FACTOR_INGRESOS_NO_CONSTITUTIVOS_RENTA',
        # ... continuar para los 37 factores
    }
    
    for i in range(8, 38):
        nombre_oficial = nomenclatura_oficial.get(i, f'FACTOR_{i:02d}')
        encabezados.append(f'{nombre_oficial}')
    
    writer.writerow(encabezados)
    writer.writerow([])
    
    # ===== EJEMPLOS FORMALES COMPLETOS FACTORES =====
    writer.writerow(['SECCIÓN III: EJEMPLOS FORMALES DE FACTORES VÁLIDOS'])
    writer.writerow(['NOTA: Estos ejemplos cumplen con todas las validaciones del sistema.'])
    writer.writerow([])
    
    # Ejemplo 1 - Factores que suman exactamente 1.0
    writer.writerow(['EJEMPLO 1: ACCIÓN - SUMA FACTORES 8-16 = 1.00000000'])
    ejemplo1 = [
        2024,
        'ACN', 
        'EMPRESAS_CMPC',
        '2024-12-20',
        10003,
        'DIVIDENDO FINAL EJERCICIO 2024'
    ]
    
    # Factores que suman exactamente 1.0 para 8-16
    factores_ejemplo1 = [
        '0.15000000',   # factor_8
        '0.12000000',   # factor_9
        '0.08000000',   # factor_10
        '0.18000000',   # factor_11
        '0.09000000',   # factor_12
        '0.11000000',   # factor_13
        '0.10000000',   # factor_14
        '0.09000000',   # factor_15
        '0.08000000',   # factor_16
        # Factores 17-37 en 0
    ]
    
    # Completar con ceros hasta factor_37
    while len(factores_ejemplo1) < 30:
        factores_ejemplo1.append('0.00000000')
    
    ejemplo1.extend(factores_ejemplo1[:30])
    writer.writerow(ejemplo1)
    writer.writerow([])
    
    # Ejemplo 2 - Factores que suman menos de 1.0
    writer.writerow(['EJEMPLO 2: FONDO INVERSIÓN - SUMA FACTORES 8-16 = 0.73000000'])
    ejemplo2 = [
        2024,
        'CFI',
        'FONDO_RENTA_FIJA_NUAM',
        '2024-03-31',
        10004,
        'DISTRIBUCIÓN TRIMESTRAL DE RENTAS'
    ]
    
    factores_ejemplo2 = [
        '0.10000000',   # factor_8
        '0.08000000',   # factor_9
        '0.06000000',   # factor_10
        '0.15000000',   # factor_11
        '0.07000000',   # factor_12
        '0.09000000',   # factor_13
        '0.08000000',   # factor_14
        '0.05000000',   # factor_15
        '0.04000000',   # factor_16
        # Resto en 0
    ]
    
    while len(factores_ejemplo2) < 30:
        factores_ejemplo2.append('0.00000000')
    
    ejemplo2.extend(factores_ejemplo2[:30])
    writer.writerow(ejemplo2)
    writer.writerow([])
    
    # ===== SECCIÓN DE VALIDACIONES AVANZADAS =====
    writer.writerow(['SECCIÓN IV: VALIDACIONES AVANZADAS'])
    writer.writerow(['CONTROL 1: INTEGRIDAD MATEMÁTICA'])
    writer.writerow(['   - Verificación: factor_8 + factor_9 + ... + factor_16 ≤ 1.00000000'])
    writer.writerow(['   - Tolerancia: 0.00000001 (precisión de 8 decimales)'])
    writer.writerow([])
    writer.writerow(['CONTROL 2: CONSISTENCIA TRIBUTARIA'])
    writer.writerow(['   - Factores deben representar distribución real de rentas'])
    writer.writerow(['   - Compatibilidad con normativa SII vigente'])
    writer.writerow(['   - Auditoría trail disponible por 10 años'])
    writer.writerow([])
    
    # ===== PIE DE PÁGINA FORMAL =====
    writer.writerow(['SECCIÓN V: GOBERNANZA Y CUMPLIMIENTO'])
    writer.writerow(['NUAM CAPITAL LIMITADA'])
    writer.writerow(['Registro SII: 12345-6'])
    writer.writerow(['Superintendencia de Valores y Seguros: Corredor Autorizado'])
    writer.writerow(['Política de Cumplimiento: NC-2024-001'])
    writer.writerow([])
    writer.writerow(['CONTACTO INSTITUCIONAL:'])
    writer.writerow(['Jefe Departamento Tributario: Sr. Eduardo Leiva'])
    writer.writerow(['Email: analisis.tributario@nuamcapital.cl'])
    writer.writerow(['Teléfono: +56 2 2345 6790'])
    writer.writerow([])
    writer.writerow(['DOCUMENTO CONTROLADO - VERSIÓN 1.0'])
    
    return response