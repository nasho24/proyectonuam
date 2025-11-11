from django.core.management.base import BaseCommand
from calificaciones.models import Empresa

class Command(BaseCommand):
    help = 'Crea una empresa de prueba para el sistema'
    
    def handle(self, *args, **options):
        # Verificar si ya existe
        if Empresa.objects.filter(rut="76.123.456-7").exists():
            self.stdout.write(
                self.style.WARNING('⚠️ La empresa de prueba ya existe')
            )
            return
        
        # Crear empresa
        empresa = Empresa(
            rut="76.123.456-7",
            nombre="NUAM Capital",
            giro="Servicios Financieros y Inversiones",
            direccion="Av. Apoquindo 3000, Las Condes, Santiago",
            telefono="+56 2 2345 6789",
            email="contacto@nuamcapital.cl"
        )
        empresa.save()
        
        self.stdout.write(
            self.style.SUCCESS('✅ Empresa de prueba creada exitosamente!')
        )
        self.stdout.write(f'   Nombre: {empresa.nombre}')
        self.stdout.write(f'   RUT: {empresa.rut}')