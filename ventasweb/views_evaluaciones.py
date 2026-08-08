"""
Vistas para el sistema de evaluaciones educativas
Conforme al sistema educativo de la República Dominicana
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponse
from django.template.loader import get_template
from django.conf import settings
from django.urls import reverse
from xhtml2pdf import pisa
from datetime import date
import os
from .models import CustomUser, Materia, Curso, AnhoEscolar, EvaluacionDiagnostica, ResultadoEvaluacionDiagnostica, Matricula, Rubrica, CriterioRubrica, NivelDesempeno, EvaluacionRubrica, CalificacionCriterio, Estudiante


@login_required
def evaluaciones_diagnosticas(request):
    """
    Vista para gestionar evaluaciones diagnósticas
    Permiten identificar conocimientos previos y nivel inicial del estudiante
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Procesar formulario POST
    if request.method == 'POST':
        materia_id = request.POST.get('materia')
        periodo = request.POST.get('periodo')
        competencia = request.POST.get('competencia', '').strip()
        indicadores = request.POST.get('indicadores', '').strip()
        fecha_aplicacion = request.POST.get('fecha_aplicacion')
        instrumento = request.POST.get('instrumento')
        observaciones = request.POST.get('observaciones', '').strip()
        
        # Validar campos requeridos
        if not materia_id:
            messages.error(request, 'Debes seleccionar una materia.')
        else:
            try:
                materia = Materia.objects.get(id=materia_id)
                
                # Crear la evaluación diagnóstica
                evaluacion = EvaluacionDiagnostica.objects.create(
                    materia=materia,
                    periodo=periodo,
                    competencia=competencia if competencia else None,
                    indicadores=indicadores if indicadores else None,
                    fecha_aplicacion=fecha_aplicacion if fecha_aplicacion else None,
                    instrumento=instrumento,
                    observaciones=observaciones if observaciones else None,
                    creado_por=request.user
                )
                
                messages.success(request, f'Evaluación diagnóstica creada exitosamente para {materia.nombre}.')
                return redirect('evaluaciones_diagnosticas')
                
            except Materia.DoesNotExist:
                messages.error(request, 'La materia seleccionada no existe.')
            except Exception as e:
                messages.error(request, f'Error al crear la evaluación: {str(e)}')
    
    # Obtener materias del profesor
    materias = Materia.objects.filter(profesor=request.user)
    
    # Obtener evaluaciones diagnósticas del profesor
    evaluaciones = EvaluacionDiagnostica.objects.filter(
        materia__profesor=request.user
    ).select_related('materia', 'materia__curso', 'creado_por')
    
    context = {
        'titulo': 'Evaluaciones Diagnósticas',
        'materias': materias,
        'evaluaciones': evaluaciones,
        'descripcion': 'Evaluación inicial para identificar conocimientos previos y nivel de competencia de los estudiantes al inicio del año escolar o unidad didáctica.'
    }
    return render(request, 'evaluaciones/diagnosticas.html', context)


@login_required
def evaluar_diagnostica(request, evaluacion_id):
    """
    Vista para evaluar estudiantes en una evaluación diagnóstica específica.
    Permite registrar el nivel de logro y observaciones por estudiante.
    """
    # Obtener la evaluación
    evaluacion = get_object_or_404(EvaluacionDiagnostica, id=evaluacion_id)
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Verificar que sea el profesor de la materia o un administrador
    if request.user.rol == 'Profesor' and evaluacion.materia.profesor != request.user:
        messages.error(request, 'No tienes permiso para evaluar esta materia.')
        return redirect('evaluaciones_diagnosticas')
    
    # Procesar formulario POST (guardar evaluación de un estudiante)
    if request.method == 'POST':
        estudiante_id = request.POST.get('estudiante_id')
        nivel_logro = request.POST.get('nivel_logro')
        puntaje_obtenido = request.POST.get('puntaje_obtenido', '').strip()
        puntaje_total = request.POST.get('puntaje_total', '').strip()
        fortalezas = request.POST.get('fortalezas', '').strip()
        debilidades = request.POST.get('debilidades', '').strip()
        recomendaciones = request.POST.get('recomendaciones', '').strip()
        observaciones = request.POST.get('observaciones', '').strip()
        
        if estudiante_id and nivel_logro:
            try:
                estudiante = CustomUser.objects.get(id=estudiante_id)
                
                # Procesar puntajes
                puntaje_obtenido_val = float(puntaje_obtenido) if puntaje_obtenido else None
                puntaje_total_val = float(puntaje_total) if puntaje_total else None
                
                # Si hay puntaje obtenido pero no hay puntaje total, asumir 100
                if puntaje_obtenido_val is not None and puntaje_total_val is None:
                    puntaje_total_val = 100.0
                
                # Crear o actualizar el resultado
                resultado, created = ResultadoEvaluacionDiagnostica.objects.update_or_create(
                    evaluacion=evaluacion,
                    estudiante=estudiante,
                    defaults={
                        'nivel_logro': nivel_logro,
                        'puntaje_obtenido': puntaje_obtenido_val,
                        'puntaje_total': puntaje_total_val,
                        'fortalezas': fortalezas if fortalezas else None,
                        'debilidades': debilidades if debilidades else None,
                        'recomendaciones': recomendaciones if recomendaciones else None,
                        'observaciones': observaciones if observaciones else None,
                        'evaluado_por': request.user
                    }
                )
                
                action = 'registrada' if created else 'actualizada'
                messages.success(request, f'Evaluación {action} exitosamente para {estudiante.get_full_name()}.')
                
            except CustomUser.DoesNotExist:
                messages.error(request, 'El estudiante seleccionado no existe.')
            except Exception as e:
                messages.error(request, f'Error al guardar la evaluación: {str(e)}')
        else:
            messages.error(request, 'Debes seleccionar un estudiante y un nivel de logro.')
        
        return redirect('evaluar_diagnostica', evaluacion_id=evaluacion_id)
    
    # Obtener estudiantes matriculados en la materia
    matriculas = Matricula.objects.filter(materia=evaluacion.materia).select_related('estudiante')
    estudiantes_ids = [m.estudiante.id for m in matriculas]
    estudiantes = CustomUser.objects.filter(id__in=estudiantes_ids).order_by('first_name', 'last_name')
    
    # Obtener resultados existentes
    resultados = ResultadoEvaluacionDiagnostica.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante', 'evaluado_por')
    
    # Crear un diccionario de resultados por estudiante_id
    resultados_dict = {r.estudiante.id: r for r in resultados}
    
    # Preparar lista de estudiantes con sus resultados
    estudiantes_con_resultados = []
    for estudiante in estudiantes:
        resultado = resultados_dict.get(estudiante.id)
        estudiantes_con_resultados.append({
            'estudiante': estudiante,
            'resultado': resultado
        })
    
    context = {
        'titulo': 'Evaluar Estudiantes',
        'evaluacion': evaluacion,
        'estudiantes_con_resultados': estudiantes_con_resultados,
        'total_estudiantes': len(estudiantes),
        'evaluados': len(resultados),
        'porcentaje_completado': evaluacion.porcentaje_completado()
    }
    return render(request, 'evaluaciones/evaluar_diagnostica.html', context)


@login_required
def rubricas(request):
    """
    Vista unificada para gestionar rúbricas y evaluaciones
    Incluye: crear rúbricas, gestionar criterios, aplicar a estudiantes y ver evaluaciones
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener año escolar activo
    anho_activo = AnhoEscolar.objects.filter(activo=True).first()
    if not anho_activo:
        messages.warning(request, 'No hay un año escolar activo.')
    
    materias = Materia.objects.none()
    estudiantes_por_materia = {}
    if anho_activo:
        if request.user.rol == 'Profesor':
            materias = Materia.objects.filter(profesor=request.user, curso__anho_escolar=anho_activo)
        elif request.user.rol == 'Estudiante':
            materias = Materia.objects.filter(matriculas__estudiante=request.user, curso__anho_escolar=anho_activo).distinct()
        else:
            materias = Materia.objects.filter(curso__anho_escolar=anho_activo)
        # Diccionario de estudiantes por materia
        for materia in materias:
            estudiantes = CustomUser.objects.filter(matriculas__materia=materia, matriculas__anho_escolar=anho_activo, rol='Estudiante').distinct().order_by('last_name', 'first_name')
            estudiantes_por_materia[materia.id] = estudiantes
    
    # Variable para controlar qué tab mostrar
    active_tab = request.GET.get('tab', 'rubricas')
    
    # Procesar formularios según la acción
    if request.method == 'POST':
        action = request.POST.get('action')
        
        # CREAR NUEVA RÚBRICA
        if action == 'crear_rubrica':
            try:
                nombre = request.POST.get('nombre_rubrica')
                tipo_actividad = request.POST.get('tipo_actividad')
                descripcion = request.POST.get('descripcion', '')
                
                if not nombre:
                    messages.error(request, 'El nombre de la rúbrica es obligatorio.')
                    return redirect('rubricas')
                
                rubrica = Rubrica.objects.create(
                    nombre=nombre,
                    tipo_actividad=tipo_actividad,
                    descripcion=descripcion,
                    creado_por=request.user
                )
                
                messages.success(request, f'Rúbrica "{nombre}" creada exitosamente.')
                return redirect('rubricas')
                
            except Materia.DoesNotExist:
                messages.error(request, 'Materia no válida.')
            except Exception as e:
                messages.error(request, f'Error al crear la rúbrica: {str(e)}')
        
        # ELIMINAR RÚBRICA
        elif action == 'eliminar_rubrica':
            try:
                rubrica_id = request.POST.get('rubrica_id')
                
                if not rubrica_id:
                    messages.error(request, 'ID de rúbrica no proporcionado.')
                    return redirect('rubricas')
                
                rubrica = Rubrica.objects.get(id=rubrica_id, creado_por=request.user)
                
                # Verificar si hay evaluaciones asociadas
                evaluaciones_count = rubrica.evaluaciones.count()
                if evaluaciones_count > 0:
                    messages.error(
                        request, 
                        f'No se puede eliminar la rúbrica "{rubrica.nombre}" porque tiene {evaluaciones_count} '
                        f'evaluación(es) asociada(s). Primero debes eliminar o reasignar las evaluaciones.'
                    )
                    return redirect('rubricas')
                
                nombre_rubrica = rubrica.nombre
                rubrica.delete()
                
                messages.success(request, f'Rúbrica "{nombre_rubrica}" eliminada exitosamente.')
                return redirect('rubricas')
                
            except Rubrica.DoesNotExist:
                messages.error(request, 'Rúbrica no encontrada o no tienes permiso para eliminarla.')
            except Exception as e:
                messages.error(request, f'Error al eliminar la rúbrica: {str(e)}')
        
        # ELIMINAR EVALUACIÓN CON RÚBRICA
        elif action == 'eliminar_evaluacion':
            try:
                evaluacion_id = request.POST.get('evaluacion_id')
                
                if not evaluacion_id:
                    messages.error(request, 'ID de evaluación no proporcionado.')
                    return redirect(reverse('rubricas') + '?tab=evaluaciones')
                
                evaluacion = EvaluacionRubrica.objects.get(
                    id=evaluacion_id,
                    materia__profesor=request.user
                )
                
                titulo_evaluacion = evaluacion.titulo
                total_calificaciones = CalificacionCriterio.objects.filter(evaluacion=evaluacion).count()
                
                # Eliminar la evaluación (las calificaciones se eliminan en cascada)
                evaluacion.delete()
                
                if total_calificaciones > 0:
                    messages.success(
                        request, 
                        f'Evaluación "{titulo_evaluacion}" eliminada exitosamente. '
                        f'Se eliminaron {total_calificaciones} calificación(es) asociada(s).'
                    )
                else:
                    messages.success(request, f'Evaluación "{titulo_evaluacion}" eliminada exitosamente.')
                
                return redirect(reverse('rubricas') + '?tab=evaluaciones')
                
            except EvaluacionRubrica.DoesNotExist:
                messages.error(request, 'Evaluación no encontrada o no tienes permiso para eliminarla.')
            except Exception as e:
                messages.error(request, f'Error al eliminar la evaluación: {str(e)}')
        
        # APLICAR RÚBRICA (CREAR EVALUACIÓN)
        elif action == 'aplicar_rubrica':
            try:
                rubrica_id = request.POST.get('rubrica')
                materia_id = request.POST.get('materia')
                titulo = request.POST.get('titulo')
                descripcion = request.POST.get('descripcion', '')
                fecha_evaluacion = request.POST.get('fecha_evaluacion')
                periodo = request.POST.get('periodo')
                
                if not all([rubrica_id, materia_id, titulo, fecha_evaluacion, periodo]):
                    messages.error(request, 'Todos los campos obligatorios deben completarse.')
                    return redirect(reverse('rubricas') + '?tab=aplicar')
                
                rubrica = Rubrica.objects.get(id=rubrica_id, creado_por=request.user)
                # La materia se selecciona en el formulario
                materia = Materia.objects.get(id=materia_id, profesor=request.user)
                curso = materia.curso
                
                if rubrica.total_criterios() == 0:
                    messages.error(request, 'La rúbrica debe tener al menos un criterio antes de aplicarla.')
                    return redirect(reverse('rubricas') + '?tab=aplicar')
                
                if not rubrica.ponderacion_valida():
                    total_pond = rubrica.total_ponderacion()
                    messages.warning(
                        request, 
                        f'Advertencia: La suma de ponderaciones es {total_pond}%. '
                        f'Se recomienda que sumen exactamente 100%.'
                    )
                
                evaluacion = EvaluacionRubrica.objects.create(
                    rubrica=rubrica,
                    materia=materia,
                    curso=curso,
                    titulo=titulo,
                    descripcion=descripcion,
                    fecha_evaluacion=fecha_evaluacion,
                    periodo=periodo,
                    creada_por=request.user
                )
                
                messages.success(request, f'Evaluación "{titulo}" creada exitosamente. Ahora puedes evaluar a los estudiantes.')
                return redirect('evaluar_con_rubrica', evaluacion_id=evaluacion.id)
                
            except Rubrica.DoesNotExist:
                messages.error(request, 'Datos no válidos.')
            except Exception as e:
                messages.error(request, f'Error al crear la evaluación: {str(e)}')
    
    # Obtener rúbricas
    if anho_activo:
        if request.user.rol == 'Profesor':
            # Mostrar rúbricas creadas por el profesor (con o sin materia asignada)
            rubricas_list = Rubrica.objects.filter(
                creado_por=request.user
            ).select_related('materia', 'materia__curso', 'creado_por').order_by('-fecha_creacion')
        elif request.user.rol == 'Estudiante':
            rubricas_list = Rubrica.objects.filter(
                materia__matriculas__estudiante=request.user,
                materia__curso__anho_escolar=anho_activo
            ).select_related('materia', 'materia__curso', 'creado_por').distinct().order_by('-fecha_creacion')
        else:
            # Administradores y coordinadores ven todas del año activo
            rubricas_list = Rubrica.objects.filter(
                Q(materia__isnull=True) | Q(materia__curso__anho_escolar=anho_activo)
            ).select_related('materia', 'materia__curso', 'creado_por').order_by('-fecha_creacion')
    else:
        rubricas_list = Rubrica.objects.none()
    
    # Obtener rúbricas disponibles para aplicar (solo activas con criterios)
    rubricas_disponibles = rubricas_list.filter(activa=True)
    
    # Obtener evaluaciones
    if anho_activo:
        evaluaciones = EvaluacionRubrica.objects.filter(
            materia__profesor=request.user,
            materia__curso__anho_escolar=anho_activo
        ).select_related('rubrica', 'materia', 'curso', 'creada_por').order_by('-fecha_evaluacion')
    else:
        evaluaciones = EvaluacionRubrica.objects.none()
    
    context = {
        'titulo': 'Gestión de Rúbricas',
        'materias': materias,
        'rubricas': rubricas_list,
        'rubricas_disponibles': rubricas_disponibles,
        'evaluaciones': evaluaciones,
        'descripcion': 'Crea rúbricas, define criterios de evaluación y aplícalas a tus estudiantes.',
        'anho_activo': anho_activo,
        'estudiantes_por_materia': estudiantes_por_materia,
        'active_tab': active_tab,
    }
    return render(request, 'evaluaciones/rubricas.html', context)


@login_required
def gestionar_criterios_rubrica(request, rubrica_id):
    """
    Vista para gestionar criterios de una rúbrica específica
    Permite agregar, editar y eliminar criterios con sus niveles de desempeño
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener la rúbrica
    # Permitir acceso si fue creada por el usuario (rúbricas genéricas) 
    # o si tiene materia y el usuario es el profesor
    rubrica = get_object_or_404(
        Rubrica,
        id=rubrica_id,
        creado_por=request.user
    )
    
    # Procesar formulario de creación de criterio
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'agregar_criterio':
            try:
                nombre_criterio = request.POST.get('nombre_criterio')
                descripcion_criterio = request.POST.get('descripcion_criterio', '')
                ponderacion = request.POST.get('ponderacion', 20.0)
                
                if not nombre_criterio:
                    messages.error(request, 'El nombre del criterio es obligatorio.')
                    return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
                
                # Obtener el último orden
                ultimo_criterio = rubrica.criterios.order_by('-orden').first()
                orden = (ultimo_criterio.orden + 1) if ultimo_criterio else 1
                
                # Crear criterio
                criterio = CriterioRubrica.objects.create(
                    rubrica=rubrica,
                    nombre=nombre_criterio,
                    descripcion=descripcion_criterio,
                    ponderacion=ponderacion,
                    orden=orden
                )
                
                # Crear niveles de desempeño por defecto
                niveles_default = [
                    ('excelente', 5.0, 'Desempeño sobresaliente que excede las expectativas.'),
                    ('muy_bueno', 4.0, 'Desempeño muy bueno, cumple con las expectativas de manera efectiva.'),
                    ('bueno', 3.0, 'Desempeño satisfactorio, cumple con los requisitos básicos.'),
                    ('regular', 2.0, 'Desempeño aceptable pero con áreas que necesitan mejora.'),
                    ('necesita_mejorar', 1.0, 'Desempeño insuficiente, requiere mejora significativa.'),
                ]
                
                for nivel, puntaje, descriptor in niveles_default:
                    NivelDesempeno.objects.create(
                        criterio=criterio,
                        nivel=nivel,
                        puntaje=puntaje,
                        descriptor=descriptor
                    )
                
                messages.success(request, f'Criterio "{nombre_criterio}" agregado exitosamente con 5 niveles de desempeño.')
                return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
                
            except Exception as e:
                messages.error(request, f'Error al agregar criterio: {str(e)}')
        
        elif action == 'eliminar_criterio':
            try:
                criterio_id = request.POST.get('criterio_id')
                criterio = CriterioRubrica.objects.get(id=criterio_id, rubrica=rubrica)
                criterio_nombre = criterio.nombre
                criterio.delete()
                messages.success(request, f'Criterio "{criterio_nombre}" eliminado exitosamente.')
                return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
            except CriterioRubrica.DoesNotExist:
                messages.error(request, 'Criterio no encontrado.')
            except Exception as e:
                messages.error(request, f'Error al eliminar criterio: {str(e)}')
        
        elif action == 'actualizar_descriptor':
            try:
                nivel_id = request.POST.get('nivel_id')
                nuevo_descriptor = request.POST.get('descriptor')
                
                nivel = NivelDesempeno.objects.get(
                    id=nivel_id,
                    criterio__rubrica=rubrica
                )
                nivel.descriptor = nuevo_descriptor
                nivel.save()
                
                messages.success(request, 'Descriptor actualizado exitosamente.')
                return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
            except NivelDesempeno.DoesNotExist:
                messages.error(request, 'Nivel de desempeño no encontrado.')
            except Exception as e:
                messages.error(request, f'Error al actualizar descriptor: {str(e)}')
        
        elif action == 'actualizar_ponderacion':
            try:
                criterio_id = request.POST.get('criterio_id')
                nueva_ponderacion = request.POST.get('nueva_ponderacion')
                
                criterio = CriterioRubrica.objects.get(id=criterio_id, rubrica=rubrica)
                criterio.ponderacion = float(nueva_ponderacion)
                criterio.save()
                
                messages.success(request, f'Ponderación de "{criterio.nombre}" actualizada a {nueva_ponderacion}%.')
                return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
            except CriterioRubrica.DoesNotExist:
                messages.error(request, 'Criterio no encontrado.')
            except Exception as e:
                messages.error(request, f'Error al actualizar ponderación: {str(e)}')
        
        elif action == 'distribuir_ponderaciones':
            try:
                total_criterios = rubrica.criterios.count()
                if total_criterios == 0:
                    messages.error(request, 'No hay criterios para distribuir.')
                    return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
                
                # Distribuir equitativamente
                ponderacion_equitativa = 100.0 / total_criterios
                
                for criterio in rubrica.criterios.all():
                    criterio.ponderacion = round(ponderacion_equitativa, 2)
                    criterio.save()
                
                messages.success(
                    request, 
                    f'Ponderaciones distribuidas equitativamente: {round(ponderacion_equitativa, 2)}% cada criterio.'
                )
                return redirect('gestionar_criterios_rubrica', rubrica_id=rubrica_id)
            except Exception as e:
                messages.error(request, f'Error al distribuir ponderaciones: {str(e)}')
    
    # Obtener criterios con sus niveles
    criterios = rubrica.criterios.prefetch_related('niveles').order_by('orden')
    
    context = {
        'titulo': f'Gestionar Criterios - {rubrica.nombre}',
        'rubrica': rubrica,
        'criterios': criterios,
    }
    return render(request, 'evaluaciones/gestionar_criterios_rubrica.html', context)


@login_required
def listas_cotejo(request):
    """
    Vista para gestionar listas de cotejo
    Lista de indicadores de logro con opción Sí/No o Presente/Ausente
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    materias = Materia.objects.filter(profesor=request.user)
    
    context = {
        'titulo': 'Listas de Cotejo',
        'materias': materias,
        'descripcion': 'Instrumento de verificación que permite registrar la presencia o ausencia de indicadores de aprendizaje específicos.'
    }
    return render(request, 'evaluaciones/listas_cotejo.html', context)


@login_required
def portafolios(request):
    """
    Vista para gestionar portafolios de estudiantes
    Colección organizada de trabajos y evidencias de aprendizaje
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    materias = Materia.objects.filter(profesor=request.user)
    
    context = {
        'titulo': 'Portafolios de Estudiantes',
        'materias': materias,
        'descripcion': 'Compilación sistemática de trabajos y evidencias que documenta el progreso y logros de aprendizaje del estudiante a lo largo del tiempo.'
    }
    return render(request, 'evaluaciones/portafolios.html', context)


@login_required
def registros_anecdoticos(request):
    """
    Vista para registros anecdóticos
    Observaciones cualitativas de comportamientos y eventos significativos
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    materias = Materia.objects.filter(profesor=request.user)
    
    context = {
        'titulo': 'Registros Anecdóticos',
        'materias': materias,
        'descripcion': 'Registro narrativo de observaciones significativas sobre el comportamiento, actitudes y desarrollo del estudiante en situaciones específicas.'
    }
    return render(request, 'evaluaciones/registros_anecdoticos.html', context)


@login_required
def cuadernos_clase(request):
    """
    Vista para registrar cuadernos de clase estandarizados
    Conforme a los estándares del MINERD - República Dominicana
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    materias = Materia.objects.filter(profesor=request.user)
    
    context = {
        'titulo': 'Cuadernos de Clase',
        'materias': materias,
        'descripcion': 'Registro estandarizado de planificación diaria, asistencia, contenidos desarrollados y observaciones del proceso educativo conforme a normativas del MINERD.'
    }
    return render(request, 'evaluaciones/cuadernos_clase.html', context)


# ============================================
# Reportes PDF para Evaluaciones Diagnósticas
# ============================================

@login_required
def reporte_individual_diagnostica(request, resultado_id):
    """
    Genera reporte PDF individual de un estudiante en una evaluación diagnóstica.
    Incluye nivel de logro, puntaje, fortalezas, debilidades y recomendaciones.
    """
    resultado = get_object_or_404(
        ResultadoEvaluacionDiagnostica.objects.select_related(
            'estudiante', 'evaluacion', 'evaluacion__materia', 
            'evaluacion__materia__curso', 'evaluacion__creado_por', 'evaluado_por'
        ), 
        id=resultado_id
    )
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a este reporte.')
        return redirect('plataform')
    
    # Función para resolver rutas estáticas
    def link_callback(uri, rel):
        if os.path.isfile(uri):
            return uri
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT
        
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri
        
        if not os.path.isfile(path):
            raise Exception(f'media URI must start with {sUrl} or {mUrl}')
        return path
    
    context = {
        'resultado': resultado,
        'fecha_actual': date.today(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }
    
    # Renderizar template HTML
    template = get_template('evaluaciones/reporte_individual_diagnostica_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f'diagnostica_{resultado.estudiante.first_name}_{resultado.estudiante.last_name}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    
    return response


@login_required
def reporte_grupal_diagnostica(request, evaluacion_id):
    """
    Genera reporte PDF grupal de todos los estudiantes de una evaluación diagnóstica.
    Incluye estadísticas, gráficos y análisis general del curso.
    """
    evaluacion = get_object_or_404(
        EvaluacionDiagnostica.objects.select_related(
            'materia', 'materia__curso', 'creado_por'
        ),
        id=evaluacion_id
    )
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a este reporte.')
        return redirect('plataform')
    
    # Obtener todos los resultados de la evaluación
    resultados = ResultadoEvaluacionDiagnostica.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante', 'evaluado_por').order_by(
        'estudiante__first_name', 'estudiante__last_name'
    )
    
    # Calcular estadísticas
    total_evaluados = resultados.count()
    
    # Contar por nivel de logro
    stats = {
        'no_alcanzado': resultados.filter(nivel_logro='no_alcanzado').count(),
        'en_proceso': resultados.filter(nivel_logro='en_proceso').count(),
        'alcanzado': resultados.filter(nivel_logro='alcanzado').count(),
        'supera': resultados.filter(nivel_logro='supera').count(),
    }
    
    # Calcular porcentajes
    porcentajes = {}
    if total_evaluados > 0:
        for nivel, count in stats.items():
            porcentajes[nivel] = round((count / total_evaluados) * 100, 1)
    
    # Calcular promedio de puntajes (si aplica)
    resultados_con_puntaje = resultados.exclude(puntaje_obtenido__isnull=True)
    promedio_puntaje = None
    if resultados_con_puntaje.exists():
        suma_puntajes = sum([float(r.puntaje_obtenido) for r in resultados_con_puntaje])
        promedio_puntaje = round(suma_puntajes / resultados_con_puntaje.count(), 2)
    
    # Función para resolver rutas estáticas
    def link_callback(uri, rel):
        if os.path.isfile(uri):
            return uri
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT
        
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri
        
        if not os.path.isfile(path):
            raise Exception(f'media URI must start with {sUrl} or {mUrl}')
        return path
    
    context = {
        'evaluacion': evaluacion,
        'resultados': resultados,
        'total_evaluados': total_evaluados,
        'stats': stats,
        'porcentajes': porcentajes,
        'promedio_puntaje': promedio_puntaje,
        'fecha_actual': date.today(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }
    
    # Renderizar template HTML
    template = get_template('evaluaciones/reporte_grupal_diagnostica_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f'diagnostica_grupal_{evaluacion.materia.nombre}_{evaluacion.materia.curso.nombre}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    
    return response


@login_required
def reporte_seguimiento_diagnostica(request, estudiante_id, materia_id):
    """
    Genera reporte PDF de seguimiento comparativo de un estudiante en una materia.
    Muestra evolución a través de las evaluaciones diagnósticas realizadas.
    """
    estudiante = get_object_or_404(CustomUser, id=estudiante_id, rol='Estudiante')
    materia = get_object_or_404(Materia, id=materia_id)
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a este reporte.')
        return redirect('plataform')
    
    # Obtener todas las evaluaciones diagnósticas de esa materia
    evaluaciones = EvaluacionDiagnostica.objects.filter(
        materia=materia
    ).order_by('fecha_creacion')
    
    # Obtener los resultados del estudiante para cada evaluación
    resultados_timeline = []
    for evaluacion in evaluaciones:
        try:
            resultado = ResultadoEvaluacionDiagnostica.objects.get(
                evaluacion=evaluacion,
                estudiante=estudiante
            )
            resultados_timeline.append({
                'evaluacion': evaluacion,
                'resultado': resultado
            })
        except ResultadoEvaluacionDiagnostica.DoesNotExist:
            # Si no hay resultado para esta evaluación, marcarlo como no evaluado
            resultados_timeline.append({
                'evaluacion': evaluacion,
                'resultado': None
            })
    
    # Análisis de evolución
    evolucion = None
    if len(resultados_timeline) >= 2:
        # Comparar primera y última evaluación con resultado
        resultados_validos = [r for r in resultados_timeline if r['resultado']]
        if len(resultados_validos) >= 2:
            primer_resultado = resultados_validos[0]['resultado']
            ultimo_resultado = resultados_validos[-1]['resultado']
            
            niveles_orden = {
                'no_alcanzado': 1,
                'en_proceso': 2,
                'alcanzado': 3,
                'supera': 4
            }
            
            nivel_inicial = niveles_orden.get(primer_resultado.nivel_logro, 0)
            nivel_actual = niveles_orden.get(ultimo_resultado.nivel_logro, 0)
            
            if nivel_actual > nivel_inicial:
                evolucion = 'positiva'
            elif nivel_actual < nivel_inicial:
                evolucion = 'negativa'
            else:
                evolucion = 'estable'
    
    # Función para resolver rutas estáticas
    def link_callback(uri, rel):
        if os.path.isfile(uri):
            return uri
        sUrl = settings.STATIC_URL
        sRoot = settings.STATIC_ROOT
        mUrl = settings.MEDIA_URL
        mRoot = settings.MEDIA_ROOT
        
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri
        
        if not os.path.isfile(path):
            raise Exception(f'media URI must start with {sUrl} or {mUrl}')
        return path
    
    context = {
        'estudiante': estudiante,
        'materia': materia,
        'resultados_timeline': resultados_timeline,
        'evolucion': evolucion,
        'total_evaluaciones': len(evaluaciones),
        'evaluaciones_completadas': len([r for r in resultados_timeline if r['resultado']]),
        'fecha_actual': date.today(),
        'STATIC_ROOT': settings.STATIC_ROOT,
    }
    
    # Renderizar template HTML
    template = get_template('evaluaciones/reporte_seguimiento_diagnostica_pdf.html')
    html = template.render(context)
    
    # Crear respuesta PDF
    response = HttpResponse(content_type='application/pdf')
    filename = f'seguimiento_{estudiante.first_name}_{estudiante.last_name}_{materia.codigo}.pdf'
    response['Content-Disposition'] = f'inline; filename="{filename}"'
    
    # Generar PDF
    pisa_status = pisa.CreatePDF(html, dest=response, link_callback=link_callback)
    
    if pisa_status.err:
        return HttpResponse('Error al generar PDF')
    
    return response


@login_required
def evaluaciones_rubricas(request):
    """
    Vista redirigida a la vista unificada de rúbricas
    Mantiene compatibilidad con enlaces antiguos
    """
    # Redirigir a la pestaña de aplicar rúbricas
    return redirect(reverse('rubricas') + '?tab=aplicar')


@login_required
def evaluar_con_rubrica(request, evaluacion_id):
    """
    Vista para evaluar estudiantes usando una rúbrica específica
    Permite calificar cada criterio para cada estudiante
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener la evaluación
    evaluacion = get_object_or_404(
        EvaluacionRubrica.objects.select_related(
            'rubrica', 'materia', 'curso', 'creada_por'
        ).prefetch_related(
            'rubrica__criterios__niveles'
        ),
        id=evaluacion_id,
        materia__profesor=request.user
    )
    
    # Obtener año escolar activo
    anho_activo = AnhoEscolar.objects.filter(activo=True).first()
    if not anho_activo:
        messages.error(request, 'No hay un año escolar activo. Contacta al administrador.')
        return redirect('evaluaciones_rubricas')
    
    # Verificar que el curso de la evaluación pertenece al año activo
    if evaluacion.curso.anho_escolar != anho_activo:
        messages.warning(
            request, 
            f'Esta evaluación es del año escolar "{evaluacion.curso.anho_escolar.nombre}". '
            f'El año activo actual es "{anho_activo.nombre}".'
        )
    
    # Obtener estudiantes matriculados en la materia específica de la evaluación
    estudiantes = CustomUser.objects.filter(
        rol='Estudiante',
        matriculas__anho_escolar=evaluacion.curso.anho_escolar,
        matriculas__materia=evaluacion.materia
    ).distinct().order_by('last_name', 'first_name')
    
    # Procesar formulario de evaluación
    if request.method == 'POST':
        try:
            estudiante_id = request.POST.get('estudiante_id')
            estudiante = CustomUser.objects.get(id=estudiante_id, rol='Estudiante')
            
            # Procesar cada criterio
            criterios_evaluados = 0
            puntaje_total_estudiante = 0
            
            for criterio in evaluacion.rubrica.criterios.all():
                nivel_id = request.POST.get(f'nivel_criterio_{criterio.id}')
                observaciones = request.POST.get(f'observaciones_criterio_{criterio.id}', '')
                
                if nivel_id:
                    nivel = NivelDesempeno.objects.get(id=nivel_id, criterio=criterio)
                    
                    # Crear o actualizar calificación
                    calificacion, created = CalificacionCriterio.objects.update_or_create(
                        evaluacion=evaluacion,
                        estudiante=estudiante,
                        criterio=criterio,
                        defaults={
                            'nivel_otorgado': nivel,
                            'observaciones': observaciones
                        }
                    )
                    criterios_evaluados += 1
                    puntaje_total_estudiante += calificacion.puntaje_ponderado()
            
            if criterios_evaluados > 0:
                messages.success(
                    request,
                    f'Evaluación de {estudiante.get_full_name()} guardada exitosamente. '
                    f'{criterios_evaluados} criterios evaluados. '
                    f'Puntaje: {round(puntaje_total_estudiante, 2)}/100'
                )
            else:
                messages.warning(request, 'No se evaluó ningún criterio.')
            
            return redirect('evaluar_con_rubrica', evaluacion_id=evaluacion_id)
            
        except (CustomUser.DoesNotExist, NivelDesempeno.DoesNotExist):
            messages.error(request, 'Datos no válidos.')
        except Exception as e:
            messages.error(request, f'Error al guardar la evaluación: {str(e)}')
    
    # Obtener calificaciones existentes
    calificaciones = CalificacionCriterio.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante', 'criterio', 'nivel_otorgado')
    
    # Organizar calificaciones por estudiante
    calificaciones_por_estudiante = {}
    for cal in calificaciones:
        if cal.estudiante_id not in calificaciones_por_estudiante:
            calificaciones_por_estudiante[cal.estudiante_id] = {
                'estudiante': cal.estudiante,
                'criterios': {},
                'total': 0,
                'completado': False
            }
        calificaciones_por_estudiante[cal.estudiante_id]['criterios'][cal.criterio_id] = cal
        calificaciones_por_estudiante[cal.estudiante_id]['total'] += cal.puntaje_ponderado()
    
    # Verificar si están completos (todos los criterios evaluados)
    total_criterios = evaluacion.rubrica.criterios.count()
    for est_id in calificaciones_por_estudiante:
        criterios_evaluados = len(calificaciones_por_estudiante[est_id]['criterios'])
        calificaciones_por_estudiante[est_id]['completado'] = (criterios_evaluados == total_criterios)
    
    context = {
        'evaluacion': evaluacion,
        'estudiantes': estudiantes,
        'criterios': evaluacion.rubrica.criterios.all(),
        'calificaciones_por_estudiante': calificaciones_por_estudiante,
        'total_criterios': total_criterios,
    }
    return render(request, 'evaluaciones/evaluar_con_rubrica.html', context)


@login_required
def imprimir_rubrica(request, rubrica_id):
    """
    Vista para generar versión imprimible de una rúbrica con resultados de estudiantes
    Muestra la estructura completa con criterios, estudiantes evaluados y sus calificaciones
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener la rúbrica
    rubrica = get_object_or_404(
        Rubrica.objects.select_related('materia', 'materia__curso', 'creado_por'),
        id=rubrica_id
    )
    
    # Verificar que el usuario tenga acceso a esta rúbrica
    if request.user.rol == 'Profesor' and rubrica.materia.profesor != request.user:
        messages.error(request, 'No tienes permiso para ver esta rúbrica.')
        return redirect('rubricas')
    
    # Obtener criterios con sus niveles ordenados
    criterios = rubrica.criterios.prefetch_related('niveles').order_by('orden', 'id')
    
    # Obtener todas las evaluaciones realizadas con esta rúbrica
    evaluaciones = EvaluacionRubrica.objects.filter(
        rubrica=rubrica
    ).select_related('curso', 'materia', 'creada_por').order_by('-fecha_evaluacion')
    
    # Para cada evaluación, obtener los resultados de los estudiantes
    evaluaciones_con_resultados = []
    for evaluacion in evaluaciones:
        # Obtener todas las calificaciones de esta evaluación
        calificaciones = CalificacionCriterio.objects.filter(
            evaluacion=evaluacion
        ).select_related('estudiante', 'criterio', 'nivel_otorgado')
        
        # Organizar calificaciones por estudiante
        estudiantes_resultados = {}
        for cal in calificaciones:
            if cal.estudiante_id not in estudiantes_resultados:
                estudiantes_resultados[cal.estudiante_id] = {
                    'estudiante': cal.estudiante,
                    'criterios': {},
                    'total': 0,
                    'completado': False
                }
            estudiantes_resultados[cal.estudiante_id]['criterios'][cal.criterio_id] = {
                'nivel': cal.nivel_otorgado,
                'puntaje': cal.puntaje_ponderado(),
                'observaciones': cal.observaciones
            }
            estudiantes_resultados[cal.estudiante_id]['total'] += cal.puntaje_ponderado()
        
        # Verificar completitud
        total_criterios = criterios.count()
        for est_id in estudiantes_resultados:
            criterios_evaluados = len(estudiantes_resultados[est_id]['criterios'])
            estudiantes_resultados[est_id]['completado'] = (criterios_evaluados == total_criterios)
        
        # Convertir a lista ordenada por nombre de estudiante
        resultados_lista = sorted(
            estudiantes_resultados.values(),
            key=lambda x: (x['estudiante'].last_name, x['estudiante'].first_name)
        )
        
        # Calcular promedio del grupo
        promedio_grupo = 0
        if resultados_lista:
            suma_totales = sum(r['total'] for r in resultados_lista)
            promedio_grupo = round(suma_totales / len(resultados_lista), 2)
        
        evaluaciones_con_resultados.append({
            'evaluacion': evaluacion,
            'estudiantes': resultados_lista,
            'total_estudiantes': len(resultados_lista),
            'promedio_grupo': promedio_grupo
        })
    
    context = {
        'rubrica': rubrica,
        'criterios': criterios,
        'evaluaciones_con_resultados': evaluaciones_con_resultados,
        'fecha_actual': date.today(),
    }
    
    return render(request, 'evaluaciones/rubrica_imprimible.html', context)


@login_required
def imprimir_evaluacion_rubrica(request, evaluacion_id):
    """
    Vista para generar versión imprimible de una evaluación específica con rúbrica
    Muestra los resultados de los estudiantes evaluados en esta evaluación particular
    """
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Director', 'Administrador', 'Coordinador']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Obtener la evaluación
    evaluacion = get_object_or_404(
        EvaluacionRubrica.objects.select_related('rubrica', 'materia', 'curso', 'creada_por', 'rubrica__materia', 'rubrica__materia__curso'),
        id=evaluacion_id
    )
    
    # Verificar que el usuario tenga acceso a esta evaluación
    if request.user.rol == 'Profesor' and evaluacion.materia.profesor != request.user:
        messages.error(request, 'No tienes permiso para ver esta evaluación.')
        return redirect('evaluaciones_rubricas')
    
    # Obtener la rúbrica y sus criterios
    rubrica = evaluacion.rubrica
    criterios = rubrica.criterios.prefetch_related('niveles').order_by('orden', 'id')
    
    # Obtener todas las calificaciones de esta evaluación
    calificaciones = CalificacionCriterio.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante', 'criterio', 'nivel_otorgado')
    
    # Organizar calificaciones por estudiante
    estudiantes_resultados = {}
    for cal in calificaciones:
        if cal.estudiante_id not in estudiantes_resultados:
            estudiantes_resultados[cal.estudiante_id] = {
                'estudiante': cal.estudiante,
                'criterios': {},
                'total': 0,
                'completado': False
            }
        estudiantes_resultados[cal.estudiante_id]['criterios'][cal.criterio_id] = {
            'nivel': cal.nivel_otorgado,
            'puntaje': cal.puntaje_ponderado(),
            'observaciones': cal.observaciones
        }
        estudiantes_resultados[cal.estudiante_id]['total'] += cal.puntaje_ponderado()
    
    # Verificar completitud
    total_criterios = criterios.count()
    for est_id in estudiantes_resultados:
        criterios_evaluados = len(estudiantes_resultados[est_id]['criterios'])
        estudiantes_resultados[est_id]['completado'] = (criterios_evaluados == total_criterios)
    
    # Convertir a lista ordenada por nombre de estudiante
    resultados_lista = sorted(
        estudiantes_resultados.values(),
        key=lambda x: (x['estudiante'].last_name, x['estudiante'].first_name)
    )
    
    # Calcular promedio del grupo
    promedio_grupo = 0
    evaluaciones_completas = 0
    if resultados_lista:
        suma_totales = sum(r['total'] for r in resultados_lista)
        promedio_grupo = round(suma_totales / len(resultados_lista), 2)
        evaluaciones_completas = sum(1 for r in resultados_lista if r['completado'])
    
    context = {
        'rubrica': rubrica,
        'criterios': criterios,
        'evaluacion': evaluacion,
        'estudiantes': resultados_lista,
        'total_estudiantes': len(resultados_lista),
        'promedio_grupo': promedio_grupo,
        'evaluaciones_completas': evaluaciones_completas,
        'fecha_actual': date.today(),
    }
    
    return render(request, 'evaluaciones/evaluacion_rubrica_imprimible.html', context)
