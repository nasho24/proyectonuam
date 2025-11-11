from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages 
from .models import Empresa, CalificacionTributaria
from .forms import CalificacionForm, EmpresaForm
import csv
from datetime import datetime

def mantenedor_calificaciones(request):
    """Vista principal del mantenedor con datos reales"""
    calificaciones = CalificacionTributaria.objects.all().select_related('empresa')
    
    # Filtros
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

def ingresar_calificacion(request):
    """Vista para ingresar nueva calificación"""
    empresas = Empresa.objects.all()  # Obtener empresas para el dropdown
    
    if request.method == 'POST':
        try:
            # Crear calificación manualmente con los datos del formulario
            calificacion = CalificacionTributaria(
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

def lista_empresas(request):
    """Vista para listar empresas"""
    empresas = Empresa.objects.all()
    context = {
        'empresas': empresas,
    }
    return render(request, 'empresas.html', context)

def agregar_empresa(request):
    """Vista para agregar nueva empresa"""
    if request.method == 'POST':
        form = EmpresaForm(request.POST)
        if form.is_valid():
            empresa = form.save()
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