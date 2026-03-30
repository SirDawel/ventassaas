"""
Vistas para el sistema de Listas de Cotejo
Permite crear, gestionar y evaluar listas de cotejo personalizadas
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg, Sum, Prefetch
from django.http import JsonResponse, HttpResponse
from django.db import transaction
from django.utils import timezone
from datetime import datetime, date

from .models import (
    ListaCotejo, CriterioListaCotejo, EvaluacionListaCotejo,
    CalificacionCotejo, ResumenEvaluacionCotejo,
    Materia, Curso, CustomUser, Matricula, AnhoEscolar
)
from .forms import (
    ListaCotejoForm, CriterioListaCotejoForm, CriterioFormSet,
    EvaluacionListaCotejoForm, CalificacionCotejoForm,
    BuscarListaCotejoForm
)
from django.forms import inlineformset_factory


# ====================================================================
#  GESTIÓN DE LISTAS DE COTEJO (PLANTILLAS)
# ====================================================================

@login_required
def listas_cotejo_lista(request):
    """Vista para listar todas las listas de cotejo"""
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    # Filtros
    form = BuscarListaCotejoForm(request.GET, user=request.user)
    
    listas = ListaCotejo.objects.all()
    
    # Filtrar por usuario si es profesor
    if request.user.rol == 'Profesor':
        listas = listas.filter(creador=request.user)
    
    # Aplicar filtros del formulario
    if form.is_valid():
        buscar = form.cleaned_data.get('buscar')
        if buscar:
            listas = listas.filter(
                Q(nombre__icontains=buscar) |
                Q(descripcion__icontains=buscar)
            )
        
        tipo_evaluacion = form.cleaned_data.get('tipo_evaluacion')
        if tipo_evaluacion:
            listas = listas.filter(tipo_evaluacion=tipo_evaluacion)
        
        materia = form.cleaned_data.get('materia')
        if materia:
            listas = listas.filter(materia=materia)
        
        solo_plantillas = form.cleaned_data.get('solo_plantillas')
        if solo_plantillas:
            listas = listas.filter(es_plantilla=True)
    
    # Agregar conteo de criterios y evaluaciones
    listas = listas.annotate(
        num_criterios=Count('criterios'),
        num_evaluaciones=Count('evaluaciones')
    ).order_by('-fecha_creacion')
    
    context = {
        'listas': listas,
        'form': form,
        'titulo': 'Listas de Cotejo',
    }
    return render(request, 'listas_cotejo/lista.html', context)


@login_required
def lista_cotejo_crear(request):
    """Vista para crear una nueva lista de cotejo con sus criterios"""
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    if request.method == 'POST':
        form = ListaCotejoForm(request.POST)
        formset = CriterioFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                # Crear la lista
                lista = form.save(commit=False)
                lista.creador = request.user
                lista.save()
                
                # Crear los criterios
                formset.instance = lista
                formset.save()
                
                messages.success(request, f'Lista de cotejo "{lista.nombre}" creada exitosamente.')
                return redirect('lista_cotejo_detalle', pk=lista.id)
        else:
            # Mensajes de error más específicos
            error_msgs = []
            if form.errors:
                error_msgs.append('Hay errores en los datos generales de la lista.')
            if formset.errors:
                # Contar cuántos formularios tienen errores
                forms_with_errors = sum(1 for f in formset.errors if f)
                if forms_with_errors > 0:
                    error_msgs.append(f'Hay errores en {forms_with_errors} criterio(s).')
            if formset.non_form_errors():
                error_msgs.append('Hay errores generales en los criterios.')
            
            if error_msgs:
                messages.error(request, ' '.join(error_msgs) + ' Revisa los detalles marcados en rojo abajo.')
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ListaCotejoForm()
        formset = CriterioFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'titulo': 'Crear Lista de Cotejo',
        'accion': 'Crear',
    }
    return render(request, 'listas_cotejo/formulario.html', context)


@login_required
def lista_cotejo_editar(request, pk):
    """Vista para editar una lista de cotejo y sus criterios"""
    lista = get_object_or_404(ListaCotejo, pk=pk)
    
    # Verificar permisos
    if request.user.rol != 'Administrador' and lista.creador != request.user:
        messages.error(request, 'No tienes permiso para editar esta lista.')
        return redirect('listas_cotejo_lista')
    
    # Crear formset específico para edición con extra=0
    CriterioFormSetEdit = inlineformset_factory(
        ListaCotejo,
        CriterioListaCotejo,
        form=CriterioListaCotejoForm,
        extra=0,  # No agregar formularios vacíos al editar
        can_delete=True,
        min_num=1,
        validate_min=True,
    )
    
    if request.method == 'POST':
        form = ListaCotejoForm(request.POST, instance=lista)
        formset = CriterioFormSetEdit(request.POST, instance=lista)
        
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                form.save()
                formset.save()
                
                messages.success(request, f'Lista de cotejo "{lista.nombre}" actualizada exitosamente.')
                return redirect('lista_cotejo_detalle', pk=lista.id)
        else:
            # Mensajes de error más específicos
            error_msgs = []
            if form.errors:
                error_msgs.append('Hay errores en los datos generales de la lista.')
            if formset.errors:
                # Contar cuántos formularios tienen errores
                forms_with_errors = sum(1 for f in formset.errors if f)
                if forms_with_errors > 0:
                    error_msgs.append(f'Hay errores en {forms_with_errors} criterio(s).')
            if formset.non_form_errors():
                error_msgs.append('Hay errores generales en los criterios.')
            
            if error_msgs:
                messages.error(request, ' '.join(error_msgs) + ' Revisa los detalles marcados en rojo abajo.')
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = ListaCotejoForm(instance=lista)
        formset = CriterioFormSetEdit(instance=lista)
    
    context = {
        'form': form,
        'formset': formset,
        'lista': lista,
        'titulo': f'Editar: {lista.nombre}',
        'accion': 'Actualizar',
    }
    return render(request, 'listas_cotejo/formulario.html', context)


@login_required
def lista_cotejo_detalle(request, pk):
    """Vista para ver el detalle de una lista de cotejo"""
    lista = get_object_or_404(
        ListaCotejo.objects.annotate(
            num_criterios=Count('criterios'),
            num_evaluaciones=Count('evaluaciones')
        ),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.rol == 'Profesor' and lista.creador != request.user:
        messages.error(request, 'No tienes permiso para ver esta lista.')
        return redirect('listas_cotejo_lista')
    
    criterios = lista.criterios.filter(activo=True).order_by('orden')
    evaluaciones = lista.evaluaciones.all().order_by('-fecha_evaluacion')[:10]
    
    # Calcular estadísticas
    suma_puntajes = sum([c.puntaje_maximo for c in criterios])
    puntajes_validos = suma_puntajes == float(lista.puntaje_total)
    
    context = {
        'lista': lista,
        'criterios': criterios,
        'evaluaciones': evaluaciones,
        'suma_puntajes': suma_puntajes,
        'puntajes_validos': puntajes_validos,
        'titulo': lista.nombre,
    }
    return render(request, 'listas_cotejo/detalle.html', context)


@login_required
def lista_cotejo_eliminar(request, pk):
    """Vista para eliminar una lista de cotejo"""
    lista = get_object_or_404(ListaCotejo, pk=pk)
    
    # Verificar permisos
    if request.user.rol != 'Administrador' and lista.creador != request.user:
        messages.error(request, 'No tienes permiso para eliminar esta lista.')
        return redirect('listas_cotejo_lista')
    
    # Verificar si tiene evaluaciones asociadas
    if lista.evaluaciones.exists():
        messages.error(request, 'No se puede eliminar esta lista porque tiene evaluaciones asociadas.')
        return redirect('lista_cotejo_detalle', pk=lista.id)
    
    if request.method == 'POST':
        nombre = lista.nombre
        lista.delete()
        messages.success(request, f'Lista de cotejo "{nombre}" eliminada exitosamente.')
        return redirect('listas_cotejo_lista')
    
    context = {
        'lista': lista,
        'titulo': 'Eliminar Lista de Cotejo',
    }
    return render(request, 'listas_cotejo/eliminar.html', context)


# ====================================================================
#  GESTIÓN DE EVALUACIONES CON LISTAS DE COTEJO
# ====================================================================

@login_required
def evaluacion_cotejo_crear(request):
    """Vista para crear una nueva evaluación con lista de cotejo"""
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    # Pre-seleccionar lista si viene del parámetro
    lista_id = request.GET.get('lista_id')
    initial = {}
    if lista_id:
        try:
            lista = ListaCotejo.objects.get(pk=lista_id)
            initial['lista_cotejo'] = lista
            if lista.materia:
                initial['materia'] = lista.materia
        except ListaCotejo.DoesNotExist:
            pass
    
    if request.method == 'POST':
        form = EvaluacionListaCotejoForm(request.POST)
        
        # Aplicar filtros antes de validar
        if request.user.rol == 'Profesor':
            form.fields['lista_cotejo'].queryset = ListaCotejo.objects.filter(
                Q(creador=request.user) | Q(es_plantilla=True),
                activa=True
            )
            form.fields['materia'].queryset = Materia.objects.filter(profesor=request.user)
            
            anho_activo = AnhoEscolar.objects.filter(activo=True).first()
            if anho_activo:
                form.fields['curso'].queryset = Curso.objects.filter(
                    Q(profesor=request.user) | Q(materias__profesor=request.user),
                    anho_escolar=anho_activo
                ).distinct()
            else:
                form.fields['curso'].queryset = Curso.objects.filter(
                    Q(profesor=request.user) | Q(materias__profesor=request.user)
                ).distinct()
        else:
            anho_activo = AnhoEscolar.objects.filter(activo=True).first()
            if anho_activo:
                form.fields['curso'].queryset = Curso.objects.filter(anho_escolar=anho_activo)
        
        if form.is_valid():
            evaluacion = form.save(commit=False)
            evaluacion.evaluador = request.user
            evaluacion.save()
            
            messages.success(request, f'Evaluación "{evaluacion.nombre}" creada exitosamente.')
            return redirect('evaluacion_cotejo_calificar', pk=evaluacion.id)
        else:
            # Mensajes de error más específicos
            error_msgs = []
            if form.errors:
                for field, errors in form.errors.items():
                    if field == '__all__':
                        error_msgs.append(f"Error general: {', '.join(errors)}")
                    else:
                        field_label = form.fields[field].label or field
                        error_msgs.append(f"{field_label}: {', '.join(errors)}")
            
            if error_msgs:
                messages.error(request, 'Errores encontrados: ' + ' | '.join(error_msgs))
            else:
                messages.error(request, 'Por favor corrige los errores en el formulario.')
    else:
        form = EvaluacionListaCotejoForm(initial=initial)
    
    # Filtrar listas activas
    if request.user.rol == 'Profesor':
        form.fields['lista_cotejo'].queryset = ListaCotejo.objects.filter(
            Q(creador=request.user) | Q(es_plantilla=True),
            activa=True
        )
        form.fields['materia'].queryset = Materia.objects.filter(profesor=request.user)
        
        # Filtrar cursos: solo los del año activo donde el profesor imparte clases
        anho_activo = AnhoEscolar.objects.filter(activo=True).first()
        if anho_activo:
            # Cursos donde el profesor es el titular O tiene materias asignadas
            form.fields['curso'].queryset = Curso.objects.filter(
                Q(profesor=request.user) | Q(materias__profesor=request.user),
                anho_escolar=anho_activo
            ).distinct()
        else:
            # Si no hay año activo, mostrar cursos donde el profesor tiene materias
            form.fields['curso'].queryset = Curso.objects.filter(
                Q(profesor=request.user) | Q(materias__profesor=request.user)
            ).distinct()
    else:
        # Administrador: filtrar solo por año activo
        anho_activo = AnhoEscolar.objects.filter(activo=True).first()
        if anho_activo:
            form.fields['curso'].queryset = Curso.objects.filter(anho_escolar=anho_activo)
    
    context = {
        'form': form,
        'titulo': 'Crear Evaluación con Lista de Cotejo',
    }
    return render(request, 'listas_cotejo/evaluacion_formulario.html', context)


@login_required
def evaluacion_cotejo_lista(request):
    """Vista para listar todas las evaluaciones"""
    if request.user.rol not in ['Profesor', 'Administrador', 'Director', 'Estudiante']:
        messages.error(request, 'No tienes permiso para acceder a esta página.')
        return redirect('plataform')
    
    evaluaciones = EvaluacionListaCotejo.objects.select_related(
        'lista_cotejo', 'materia', 'curso', 'evaluador'
    ).prefetch_related('calificaciones')
    
    # Filtrar por rol
    if request.user.rol == 'Profesor':
        evaluaciones = evaluaciones.filter(evaluador=request.user)
    elif request.user.rol == 'Estudiante':
        # Solo ver evaluaciones publicadas de sus cursos
        evaluaciones = evaluaciones.filter(
            estado='publicada',
            curso__in=Matricula.objects.filter(
                estudiante=request.user
            ).values_list('materia__curso', flat=True)
        )
    
    # Filtros
    materia_id = request.GET.get('materia')
    if materia_id:
        evaluaciones = evaluaciones.filter(materia_id=materia_id)
    
    estado = request.GET.get('estado')
    if estado:
        evaluaciones = evaluaciones.filter(estado=estado)
    
    evaluaciones = evaluaciones.order_by('-fecha_evaluacion')
    
    context = {
        'evaluaciones': evaluaciones,
        'titulo': 'Evaluaciones con Lista de Cotejo',
    }
    return render(request, 'listas_cotejo/evaluacion_lista.html', context)


@login_required
def evaluacion_cotejo_detalle(request, pk):
    """Vista para ver el detalle de una evaluación"""
    evaluacion = get_object_or_404(
        EvaluacionListaCotejo.objects.select_related(
            'lista_cotejo', 'materia', 'curso', 'evaluador'
        ),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.rol == 'Profesor' and evaluacion.evaluador != request.user:
        messages.error(request, 'No tienes permiso para ver esta evaluación.')
        return redirect('evaluacion_cotejo_lista')
    
    # Obtener resúmenes de estudiantes
    resumenes = ResumenEvaluacionCotejo.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante').order_by(
        'estudiante__first_name', 'estudiante__last_name'
    )
    
    # Calcular estadísticas
    total_estudiantes = evaluacion.total_estudiantes()
    estudiantes_evaluados = evaluacion.estudiantes_evaluados()
    porcentaje_completado = evaluacion.porcentaje_completado()
    
    if resumenes.exists():
        promedio_curso = resumenes.aggregate(Avg('puntaje_obtenido'))['puntaje_obtenido__avg']
    else:
        promedio_curso = 0
    
    context = {
        'evaluacion': evaluacion,
        'resumenes': resumenes,
        'total_estudiantes': total_estudiantes,
        'estudiantes_evaluados': estudiantes_evaluados,
        'porcentaje_completado': porcentaje_completado,
        'promedio_curso': promedio_curso,
        'titulo': evaluacion.nombre,
    }
    return render(request, 'listas_cotejo/evaluacion_detalle.html', context)


# ====================================================================
#  CALIFICACIÓN MASIVA (TABLA INTERACTIVA)
# ====================================================================

@login_required
def evaluacion_cotejo_calificar(request, pk):
    """Vista principal para calificar estudiantes de forma masiva (tipo tabla)"""
    evaluacion = get_object_or_404(
        EvaluacionListaCotejo.objects.select_related(
            'lista_cotejo', 'materia', 'curso'
        ).prefetch_related('lista_cotejo__criterios'),
        pk=pk
    )
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para calificar.')
        return redirect('evaluacion_cotejo_detalle', pk=pk)
    
    if request.user.rol == 'Profesor' and evaluacion.evaluador != request.user:
        messages.error(request, 'No eres el evaluador de esta evaluación.')
        return redirect('evaluacion_cotejo_lista')
    
    # Obtener estudiantes del curso
    estudiantes = CustomUser.objects.filter(
        rol='Estudiante',
        matriculas__materia__curso=evaluacion.curso,
        is_active=True
    ).distinct().order_by('first_name', 'last_name')
    
    # Obtener criterios activos ordenados
    criterios = evaluacion.lista_cotejo.criterios.filter(activo=True).order_by('orden')
    
    # Obtener calificaciones existentes
    calificaciones_existentes = CalificacionCotejo.objects.filter(
        evaluacion=evaluacion
    ).select_related('estudiante', 'criterio')
    
    # Organizar calificaciones en diccionario [estudiante_id][criterio_id]
    calificaciones_dict = {}
    for calif in calificaciones_existentes:
        if calif.estudiante_id not in calificaciones_dict:
            calificaciones_dict[calif.estudiante_id] = {}
        calificaciones_dict[calif.estudiante_id][calif.criterio_id] = calif
    
    # Preparar contexto con matriz de calificaciones
    matriz = []
    for estudiante in estudiantes:
        fila = {
            'estudiante': estudiante,
            'calificaciones': []
        }
        for criterio in criterios:
            calif = calificaciones_dict.get(estudiante.id, {}).get(criterio.id)
            fila['calificaciones'].append({
                'criterio': criterio,
                'calificacion': calif,
            })
        matriz.append(fila)
    
    context = {
        'evaluacion': evaluacion,
        'criterios': criterios,
        'matriz': matriz,
        'titulo': f'Calificar: {evaluacion.nombre}',
    }
    return render(request, 'listas_cotejo/calificar.html', context)


@login_required
def evaluacion_cotejo_guardar_calificacion(request, pk):
    """Vista AJAX para guardar calificaciones individuales"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)
    
    evaluacion = get_object_or_404(EvaluacionListaCotejo, pk=pk)
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        return JsonResponse({'error': 'Sin permisos'}, status=403)
    
    try:
        estudiante_id = request.POST.get('estudiante_id')
        criterio_id = request.POST.get('criterio_id')
        valor = request.POST.get('valor')
        observacion = request.POST.get('observacion', '')
        
        estudiante = CustomUser.objects.get(id=estudiante_id)
        criterio = CriterioListaCotejo.objects.get(id=criterio_id)
        
        # Crear o actualizar calificación
        calif, created = CalificacionCotejo.objects.update_or_create(
            evaluacion=evaluacion,
            estudiante=estudiante,
            criterio=criterio,
            defaults={
                'valor': float(valor) if valor else None,
                'observacion': observacion,
                'calificado_por': request.user,
            }
        )
        
        # Recalcular resumen del estudiante
        resumen, _ = ResumenEvaluacionCotejo.objects.get_or_create(
            evaluacion=evaluacion,
            estudiante=estudiante
        )
        puntaje = resumen.calcular_puntaje()
        
        return JsonResponse({
            'success': True,
            'puntaje_obtenido': float(calif.puntaje_obtenido()),
            'resumen_puntaje': float(resumen.puntaje_obtenido),
            'resumen_porcentaje': float(resumen.porcentaje),
            'esta_completo': resumen.esta_completo,
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


# ====================================================================
#  REPORTES Y VISUALIZACIÓN
# ====================================================================

@login_required
def evaluacion_cotejo_reporte(request, pk):
    """Vista para reporte detallado de evaluación (para imprimir)"""
    evaluacion = get_object_or_404(
        EvaluacionListaCotejo.objects.select_related(
            'lista_cotejo', 'materia', 'curso', 'evaluador'
        ),
        pk=pk
    )
    
    # Obtener todas las calificaciones organizadas
    estudiantes = CustomUser.objects.filter(
        calificaciones_cotejo__evaluacion=evaluacion
    ).distinct().order_by('first_name', 'last_name')
    
    criterios = evaluacion.lista_cotejo.criterios.filter(activo=True).order_by('orden')
    
    # Construir matriz completa
    matriz = []
    for estudiante in estudiantes:
        calificaciones = CalificacionCotejo.objects.filter(
            evaluacion=evaluacion,
            estudiante=estudiante
        ).select_related('criterio')
        
        calif_dict = {c.criterio_id: c for c in calificaciones}
        
        fila = {
            'estudiante': estudiante,
            'calificaciones': [calif_dict.get(crit.id) for crit in criterios],
            'resumen': ResumenEvaluacionCotejo.objects.filter(
                evaluacion=evaluacion,
                estudiante=estudiante
            ).first()
        }
        matriz.append(fila)
    
    context = {
        'evaluacion': evaluacion,
        'criterios': criterios,
        'matriz': matriz,
        'fecha_reporte': timezone.now(),
        'titulo': f'Reporte: {evaluacion.nombre}',
    }
    return render(request, 'listas_cotejo/reporte.html', context)


@login_required
def estudiante_ver_evaluacion(request, pk):
    """Vista para que el estudiante vea su evaluación"""
    evaluacion = get_object_or_404(EvaluacionListaCotejo, pk=pk)
    
    # Solo estudiantes pueden ver esta vista
    if request.user.rol != 'Estudiante':
        messages.error(request, 'Esta vista es solo para estudiantes.')
        return redirect('evaluacion_cotejo_detalle', pk=pk)
    
    # Verificar que la evaluación esté publicada
    if evaluacion.estado != 'publicada':
        messages.error(request, 'Esta evaluación aún no está disponible.')
        return redirect('plataform')
    
    # Obtener calificaciones del estudiante
    calificaciones = CalificacionCotejo.objects.filter(
        evaluacion=evaluacion,
        estudiante=request.user
    ).select_related('criterio').order_by('criterio__orden')
    
    # Obtener resumen
    try:
        resumen = ResumenEvaluacionCotejo.objects.get(
            evaluacion=evaluacion,
            estudiante=request.user
        )
    except ResumenEvaluacionCotejo.DoesNotExist:
        resumen = None
    
    context = {
        'evaluacion': evaluacion,
        'calificaciones': calificaciones,
        'resumen': resumen,
        'titulo': f'Mi Evaluación: {evaluacion.nombre}',
    }
    return render(request, 'listas_cotejo/estudiante_vista.html', context)


@login_required
def evaluacion_cotejo_cambiar_estado(request, pk):
    """Vista para cambiar el estado de una evaluación"""
    evaluacion = get_object_or_404(EvaluacionListaCotejo, pk=pk)
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    if request.user.rol == 'Profesor' and evaluacion.evaluador != request.user:
        messages.error(request, 'No tienes permiso para modificar esta evaluación.')
        return redirect('evaluacion_cotejo_lista')
    
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        
        estados_validos = ['borrador', 'en_progreso', 'finalizada', 'publicada']
        if nuevo_estado in estados_validos:
            estado_anterior = evaluacion.get_estado_display()
            evaluacion.estado = nuevo_estado
            evaluacion.save()
            
            messages.success(
                request,
                f'Estado cambiado de "{estado_anterior}" a "{evaluacion.get_estado_display()}"'
            )
        else:
            messages.error(request, 'Estado no válido.')
    
    # Redirigir de vuelta a calificar
    return redirect('evaluacion_cotejo_calificar', pk=pk)


@login_required
def evaluacion_cotejo_eliminar(request, pk):
    """Vista para eliminar una evaluación y todas sus calificaciones"""
    evaluacion = get_object_or_404(EvaluacionListaCotejo, pk=pk)
    
    # Verificar permisos
    if request.user.rol not in ['Profesor', 'Administrador', 'Director']:
        messages.error(request, 'No tienes permiso para realizar esta acción.')
        return redirect('plataform')
    
    if request.user.rol == 'Profesor' and evaluacion.evaluador != request.user:
        messages.error(request, 'No tienes permiso para eliminar esta evaluación.')
        return redirect('evaluacion_cotejo_lista')
    
    if request.method == 'POST':
        nombre = evaluacion.nombre
        
        # Django eliminará automáticamente las calificaciones relacionadas
        # gracias a on_delete=CASCADE en los ForeignKeys
        evaluacion.delete()
        
        messages.success(
            request,
            f'Evaluación "{nombre}" eliminada exitosamente junto con todas sus calificaciones.'
        )
        return redirect('evaluacion_cotejo_lista')
    
    # Si no es POST, redirigir a la lista (no debería llegar aquí normalmente)
    return redirect('evaluacion_cotejo_lista')
