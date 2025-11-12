# test_email.py - VERSIÓN CORREGIDA
import os
import django
import sys
from pathlib import Path

# Cargar variables de entorno ANTES de Django
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
project_root = Path(__file__).parent
load_dotenv(project_root / '.env')

print("🔧 CARGANDO VARIABLES DE ENTORNO...")
print(f"   EMAIL_HOST_USER: {os.getenv('EMAIL_HOST_USER', 'NO ENCONTRADO')}")
print(f"   EMAIL_HOST_PASSWORD: {'*' * len(os.getenv('EMAIL_HOST_PASSWORD', '')) if os.getenv('EMAIL_HOST_PASSWORD') else 'NO ENCONTRADO'}")

# Configurar Django
sys.path.append(str(project_root))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuam_project.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

print("🧪 PROBANDO CONFIGURACIÓN DE EMAIL...")
print("=" * 50)

# Mostrar configuración actual de Django
print(f"📧 EMAIL_HOST: {settings.EMAIL_HOST}")
print(f"🔌 EMAIL_PORT: {settings.EMAIL_PORT}")
print(f"🔐 EMAIL_USE_TLS: {settings.EMAIL_USE_TLS}")
print(f"👤 EMAIL_HOST_USER: {settings.EMAIL_HOST_USER}")

email_password = settings.EMAIL_HOST_PASSWORD
if email_password:
    print(f"🔑 EMAIL_HOST_PASSWORD: {'*' * len(email_password)} ({len(email_password)} caracteres)")
else:
    print(f"🔑 EMAIL_HOST_PASSWORD: NO CONFIGURADO")

print("=" * 50)

try:
    print("🚀 ENVIANDO EMAIL DE PRUEBA...")
    
    send_mail(
        '✅ Prueba de Email - NUAM Capital',
        '''
        ¡Felicidades! 🎉
        
        Este es un email de prueba desde Django. 
        Si lo recibes, la configuración de email funciona correctamente.
        
        Saludos,
        Equipo NUAM Capital
        ''',
        settings.EMAIL_HOST_USER,
        [settings.EMAIL_HOST_USER],  # Enviar a ti mismo
        fail_silently=False,
        html_message='''
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #1a365d;">✅ NUAM Capital - Prueba Exitosa</h2>
            <p>¡Felicidades! 🎉</p>
            <p>Este es un email de prueba desde Django.</p>
            <p>Si lo recibes, la configuración de email funciona correctamente.</p>
            <div style="background: #f0fff4; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <strong>✅ Configuración de email: OPERATIVA</strong>
            </div>
            <hr>
            <p style="color: #718096;">
                Saludos,<br>
                Equipo NUAM Capital
            </p>
        </div>
        '''
    )
    
    print("✅ ✅ ✅ EMAIL ENVIADO CORRECTAMENTE!")
    print("💌 Revisa tu bandeja de Gmail (y spam)")
    
except Exception as e:
    print(f"❌ ❌ ❌ ERROR AL ENVIAR EMAIL:")
    print(f"   Tipo: {type(e).__name__}")
    print(f"   Mensaje: {str(e)}")
    
    # Debug adicional
    print("=" * 50)
    print("🔧 INFORMACIÓN ADICIONAL:")
    print(f"   EMAIL_HOST_USER from env: {os.getenv('EMAIL_HOST_USER')}")
    print(f"   EMAIL_HOST_PASSWORD length: {len(os.getenv('EMAIL_HOST_PASSWORD', ''))}")
    
    # Si es error de autenticación
    if "535" in str(e) or "Authentication" in str(e):
        print("🔐 PROBLEMA DE AUTENTICACIÓN:")
        print("   1. Verifica que la CONTRASEÑA DE APLICACIÓN sea correcta")
        print("   2. No uses tu contraseña normal de Gmail")
        print("   3. La contraseña debe tener 16 caracteres SIN espacios")
        print("   4. Ejemplo: 'vzpq focz zpih lhbd' → usar 'vzpqfoczzpihlhbd'")