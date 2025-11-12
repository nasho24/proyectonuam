import os
import django
import sys
from django.contrib.auth.models import User
from calificaciones.models import Profile
import pyotp

# Agregar el directorio del proyecto al path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nuam_project.settings')
django.setup()

def complete_user_profiles():
    """Completar perfiles de usuarios existentes con MFA"""
    
    print("Completando perfiles de usuarios existentes...")
    
    updated_count = 0
    
    # Procesar todos los usuarios
    for user in User.objects.all():
        try:
            # Verificar si ya tiene perfil
            if hasattr(user, 'profile'):
                profile = user.profile
                if not profile.mfa_secret:
                    # Generar MFA si no tiene
                    profile.mfa_secret = pyotp.random_base32()
                    profile.save()
                    print(f"MFA agregado a usuario existente: {user.email}")
                    updated_count += 1
                else:
                    print(f"Usuario ya tiene MFA: {user.email}")
            else:
                # Crear perfil si no existe
                secret = pyotp.random_base32()
                Profile.objects.create(user=user, mfa_secret=secret)
                print(f"Perfil creado para: {user.email}")
                print(f"MFA Secret: {secret}")
                updated_count += 1
                
        except Exception as e:
            print(f"Error procesando {user.email}: {str(e)}")
    
    print(f"\nRESUMEN: Se actualizaron {updated_count} perfiles")
    
    # Mostrar estado final
    print("\nESTADO FINAL DE USUARIOS:")
    users = User.objects.all().order_by('email')
    for user in users:
        profile = getattr(user, 'profile', None)
        mfa_status = "CON MFA" if profile and profile.mfa_secret else "SIN MFA"
        staff_status = "STAFF" if user.is_staff else "USER"
        print(f"   {staff_status} {user.email} - {user.get_full_name()} - {mfa_status}")

if __name__ == "__main__":
    complete_user_profiles()
    print("\nAhora todos los usuarios tienen MFA configurado!")