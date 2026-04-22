from django.urls import path
from . import views
from . import views_familias
from . import views_evaluaciones
from . import views_listas_cotejo
from . import views_pagos_estudiante as views_pagos
from . import views_pos

urlpatterns = [
    # ... existing urls ...
    # Reporte general PDF (notas por curso)
    path('reporte-general/<int:curso_id>/pdf/', views.reporte_general_pdf, name='reporte_general_pdf'),
    path('register/', views.register_user, name='register'),
    
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),

    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='user_create'),
    path('users/<int:user_id>/update/', views.user_update, name='user_update'),
    path('users/<int:user_id>/delete/', views.user_delete, name='user_delete'),
    path('users/<int:user_id>/reactivate/', views.user_reactivate, name='user_reactivate'),
    path('users/profile/<int:user_id>/', views.user_profile, name='user_profile'),
    path('users/log-eliminados/', views.log_usuarios_eliminados, name='log_usuarios_eliminados'),
    path('profile/picture/update/', views.update_profile_picture, name='update_profile_picture'),
    # URLs para A�o Escolar
    path('anhos-escolares/', views.lista_anhos_escolares, name='lista_anhos_escolares'),
    path('anhos-escolares/agregar/', views.agregar_anho_escolar, name='agregar_anho_escolar'),
    path('anhos-escolares/editar/<int:pk>/', views.editar_anho_escolar, name='editar_anho_escolar'),
    path('anhos-escolares/eliminar/<int:pk>/', views.eliminar_anho_escolar, name='eliminar_anho_escolar'),
    # URLs para Cursos
    path('cursos/', views.lista_cursos, name='lista_cursos'),
    path('cursos/agregar/', views.agregar_curso, name='agregar_curso'),
    path('cursos/editar/<int:pk>/', views.editar_curso, name='editar_curso'),
    path('cursos/eliminar/<int:pk>/', views.eliminar_curso, name='eliminar_curso'),
    path('cursos/<int:pk>/inscribir-estudiante/', views.inscribir_estudiante_curso, name='inscribir_estudiante_curso'),
    path('cursos/<int:pk>/desinscribir-estudiante/', views.desinscribir_estudiante_curso, name='desinscribir_estudiante_curso'),
    path('grupos/', views.lista_grupos, name='lista_grupos'),
    path('grupos/crear/', views.crear_grupo, name='crear_grupo'),
    path('grupos/crear-por-usuarios/', views.crear_grupo_por_usuarios, name='crear_grupo_por_usuarios'),
    path('grupos/<int:pk>/', views.ver_grupo, name='ver_grupo'),
    path('grupos/<int:pk>/agregar-estudiantes/', views.agregar_estudiantes_grupo, name='agregar_estudiantes_grupo'),
    path('grupos/<int:pk>/inscribir-en-curso/', views.inscribir_grupo_en_curso, name='inscribir_grupo_en_curso'),
    path('grupos/<int:pk>/eliminar/', views.eliminar_grupo, name='confirmar_eliminar_grupo'),
    path('cursos/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_curso, name='confirmar_eliminar_curso'),
    # URLs para Asistencia Personal con Código de Barras
    path('asistencia-personal/ponchar-api/', views.ponchar_asistencia_api, name='ponchar_asistencia_api'),
    
    # URLs para Materias
   
    #path('materias/agregar/<int:curso_id>/', views.agregar_materia, name='agregar_materia'),


    path('materias/', views.lista_materias, name='lista_materias'),
    #path('materias/agregar/', views.agregar_materia, name='agregar_materia'),
    path('materias/editar/<int:pk>/', views.editar_materia, name='editar_materia'),
    path('materias/eliminar/<int:pk>/', views.eliminar_materia, name='eliminar_materia'),
    path('materias/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_materia, name='confirmar_eliminar_materia'),
    path('materias/<int:id>/matriculas/', views.matriculas_materia, name='matriculas_materia'),
    path('materias/<int:materia_id>/gestionar-matriculas/', views.gestionar_matriculas, name='gestionar_matriculas'),
    path('materias/<int:materia_id>/agregar-notas/', views.agregar_notas, name='agregar_notas'),
    path('materias/<int:materia_id>/agregar-notas-modular/', views.agregar_notas_modular, name='agregar_notas_modular'),
    #lista estudiantes x materia
    path('materias/<int:materia_id>/estudiantes/', views.lista_estudiantes_materia, name='lista_estudiantes_materia'),
    path('materias/<int:materia_id>/hoja-calificaciones/', views.hoja_calificaciones_materia, name='hoja_calificaciones_materia'),

    # URLs para listas de estudiantes por curso
    path('cursos/estudiantes/info/', views.lista_estudiantes_curso_info, name='lista_estudiantes_curso_info'),
    path('cursos/estudiantes/promedios/', views.lista_estudiantes_curso_promedios, name='lista_estudiantes_curso_promedios'),    path('cursos/estudiantes/info/pdf/', views.lista_estudiantes_curso_info_pdf, name='lista_estudiantes_curso_info_pdf'),
    path('cursos/estudiantes/promedios/pdf/', views.lista_estudiantes_curso_promedios_pdf, name='lista_estudiantes_curso_promedios_pdf'),
    # URLs para Matr�culas
    
    path('matriculas/', views.lista_matriculas, name='lista_matriculas'),
    path('matriculas/agregar/', views.agregar_matricula, name='agregar_matricula'),
    path('matriculas/editar/<int:pk>/', views.editar_matricula, name='editar_matricula'),
    path('matriculas/eliminar/<int:pk>/', views.eliminar_matricula, name='eliminar_matricula'),
    path('matriculas/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_matricula, name='confirmar_eliminar_matricula'),
    path('matriculas/<int:matricula_id>/eliminar/', views.eliminar_matricula, name='eliminar_matricula'),
    path('matriculas/<int:matricula_id>/actualizar-notas/', views.actualizar_notas, name='actualizar_notas'),
    path('estudiante/<int:estudiante_id>/reporte-notas/', views.reporte_notas_estudiante, name='reporte_notas_estudiante'),
    path('estudiante/<int:estudiante_id>/record-calificaciones-pdf/', views.record_calificaciones_pdf, name='record_calificaciones_pdf'),
    path('estudiante/<int:estudiante_id>/record-calificaciones-completo-pdf/', views.record_calificaciones_completo_pdf, name='record_calificaciones_completo_pdf'),
    
    # URLs para Asistencia (Pasar Lista)
    path('asistencia/seleccionar-materia/', views.seleccionar_materia_asistencia, name='seleccionar_materia_asistencia'),
    path('asistencia/pasar-lista/<int:materia_id>/', views.pasar_lista, name='pasar_lista'),
    path('asistencia/historial/', views.historial_asistencia, name='historial_asistencia'),
    
    # URLs para Asistencia Personal (Profesores/Staff)
    path('asistencia-personal/pasar-lista/', views.pasar_lista_personal, name='pasar_lista_personal'),
    path('asistencia-personal/ponchar/', views.ponchar_asistencia_view, name='ponchar_asistencia'),
    path('asistencia-personal/ponchar-api/', views.ponchar_asistencia_api, name='ponchar_asistencia_api'),
    path('asistencia-personal/historial/', views.historial_asistencia_personal, name='historial_asistencia_personal'),
    path('asistencia-personal/codigos-barras/', views.generar_codigos_barras, name='generar_codigos_barras'),
    path('asistencia-general/estadisticas/', views.historial_asistencia_general, name='historial_asistencia_general'),
    path('asistencia-personal/historial/', views.historial_asistencia_personal, name='historial_asistencia_personal'),
    
    # URLs para Sistema de Cobros
    path('cobros/', views.cobros_dashboard, name='cobros_dashboard'),
    path('cobros/buscar-estudiante/', views.buscar_estudiante_cobro, name='buscar_estudiante_cobro'),
    # Sistema de pago simple removido - usar facturas en su lugar
    
    # URLs para Sistema de Pagos de Estudiantes
    path('estudiante-pagos/', views_pagos.estudiante_pagos, name='estudiante_pagos'),
    path('estudiante-pagos/procesar/', views_pagos.procesar_pago_estudiante, name='procesar_pago_estudiante'),
    path('generar-facturas-automatico/', views_pagos.generar_facturas_mensuales_automatico, name='generar_facturas_automatico'),
    
    # URLs para Sistema de Facturación
    path('facturas/', views.facturas_list, name='facturas_list'),
    path('facturas/nueva/', views.factura_crear_nueva, name='factura_crear_nueva'),
    path('facturas/buscar-articulo-barras/', views.buscar_articulo_barras, name='buscar_articulo_barras'),
    path('facturas/buscar-articulo-nombre/', views.buscar_articulo_nombre, name='buscar_articulo_nombre'),
    path('facturas/tarifa-estudiante/', views.tarifa_estudiante_api, name='tarifa_estudiante_api'),
    path('facturas/crear/<int:estudiante_id>/', views.factura_crear, name='factura_crear'),
    path('facturas/<int:factura_id>/', views.factura_detalle, name='factura_detalle'),
    path('facturas/<int:factura_id>/recibo/', views.factura_recibo_pos, name='factura_recibo_pos'),
    path('facturas/<int:factura_id>/registrar-pago/', views.factura_registrar_pago, name='factura_registrar_pago'),
    path('facturas/estudiante/<int:estudiante_id>/', views.facturas_estudiante, name='facturas_estudiante'),
    path('facturas/<int:factura_id>/anular/', views.factura_anular, name='factura_anular'),
    path('codigo-anulacion/', views.codigo_anulacion_ver, name='codigo_anulacion_ver'),
    # TarifaEstudiante CRUD
    
    path('tarifas/', views.tarifas_list, name='tarifas_list'),
    path('tarifas/crear/', views.tarifa_create, name='tarifa_create'),
    path('tarifas/editar/<int:pk>/', views.tarifa_edit, name='tarifa_edit'),
    path('tarifas/eliminar/<int:pk>/', views.tarifa_delete, name='tarifa_delete'),
    path('tarifas/concepto/<int:concepto_id>/monto/', views.obtener_concepto_monto, name='obtener_concepto_monto'),
    # ConceptoPago (Tarifas Estándar) CRUD - Solo Administrador
    path('conceptos/', views.conceptos_list, name='conceptos_list'),
    path('conceptos/crear/', views.concepto_create, name='concepto_create'),
    path('conceptos/editar/<int:pk>/', views.concepto_edit, name='concepto_edit'),
    path('conceptos/eliminar/<int:pk>/', views.concepto_delete, name='concepto_delete'),
    
    # URLs para Sistema de Inventario
    path('inventario/validar_codigo_barras/', views.buscar_articulo_barras, name='validar_codigo_barras'),
    
    path('inventario/', views.inventario_dashboard, name='inventario_dashboard'),
    path('inventario/lista-completa/', views.inventario_lista_completa, name='inventario_lista_completa'),
    path('inventario/articulos-pdf/', views.inventario_articulos_pdf, name='inventario_articulos_pdf'),
    path('inventario/servicios-pdf/', views.inventario_servicios_pdf, name='inventario_servicios_pdf'),
    path('inventario/articulos/', views.articulos_list, name='articulos_list'),
    path('inventario/articulos/crear/', views.articulo_crear, name='articulo_crear'),
    path('inventario/articulos/<int:articulo_id>/editar/', views.articulo_editar, name='articulo_editar'),
    path('inventario/articulos/<int:articulo_id>/eliminar/', views.articulo_eliminar, name='articulo_eliminar'),
    path('inventario/articulos/<int:articulo_id>/', views.articulo_detalle, name='articulo_detalle'),
    path('inventario/categorias/', views.categorias_list, name='categorias_list'),
    path('inventario/categorias/crear/', views.categoria_crear, name='categoria_crear'),
    path('inventario/categorias/<int:categoria_id>/editar/', views.categoria_editar, name='categoria_editar'),
    path('inventario/categorias/<int:categoria_id>/eliminar/', views.categoria_eliminar, name='categoria_eliminar'),
    
    # URLs para Reportes de Ventas
    path('reportes/ventas/', views.reportes_ventas, name='reportes_ventas'),
    
    # URLs para Grupos Familiares
    path('familias/', views_familias.grupos_familiares_lista, name='grupos_familiares_lista'),
    path('familias/crear/', views_familias.grupo_familiar_crear, name='grupo_familiar_crear'),
    path('familias/<int:grupo_id>/', views_familias.grupo_familiar_detalle, name='grupo_familiar_detalle'),
    path('familias/<int:grupo_id>/editar/', views_familias.grupo_familiar_editar, name='grupo_familiar_editar'),
    path('familias/<int:grupo_id>/asignar-estudiante/', views_familias.grupo_familiar_asignar_estudiante, name='grupo_familiar_asignar_estudiante'),
    path('familias/<int:grupo_id>/remover-estudiante/<int:estudiante_id>/', views_familias.grupo_familiar_remover_estudiante, name='grupo_familiar_remover_estudiante'),
    path('familias/<int:grupo_id>/facturar/', views_familias.grupo_familiar_facturar, name='grupo_familiar_facturar'),
    
    # ============================================
    # URLs para CONTABILIDAD - Plan de Cuentas
    # ============================================
    path('contabilidad/plan-cuentas/', views.plan_cuentas_list, name='plan_cuentas_list'),
    path('contabilidad/plan-cuentas/crear/', views.plan_cuentas_crear, name='plan_cuentas_crear'),
    path('contabilidad/plan-cuentas/<int:pk>/', views.plan_cuentas_detalle, name='plan_cuentas_detalle'),
    path('contabilidad/plan-cuentas/<int:pk>/editar/', views.plan_cuentas_editar, name='plan_cuentas_editar'),
    path('contabilidad/plan-cuentas/<int:pk>/eliminar/', views.plan_cuentas_eliminar, name='plan_cuentas_eliminar'),
    path('contabilidad/plan-cuentas/<int:pk>/toggle-activo/', views.plan_cuentas_toggle_activo, name='plan_cuentas_toggle_activo'),
    
    # APIs para Plan de Cuentas
    path('contabilidad/api/plan-cuentas/<int:pk>/subcuentas/', views.plan_cuentas_obtener_subcuentas, name='plan_cuentas_obtener_subcuentas'),
    path('contabilidad/api/plan-cuentas/estructura/', views.plan_cuentas_estructura_json, name='plan_cuentas_estructura_json'),
    
    # ============================================
    # URLs para Asientos Contables
    # ============================================
    path('contabilidad/asientos/', views.asientos_list, name='asientos_list'),
    path('contabilidad/asientos/crear/', views.asiento_crear, name='asiento_crear'),
    path('contabilidad/asientos/<int:pk>/', views.asiento_detalle, name='asiento_detalle'),
    path('contabilidad/asientos/<int:pk>/contabilizar/', views.asiento_contabilizar, name='asiento_contabilizar'),
    path('contabilidad/asientos/<int:pk>/anular/', views.asiento_anular, name='asiento_anular'),
    path('contabilidad/asientos/<int:pk>/eliminar/', views.asiento_eliminar, name='asiento_eliminar'),
    path('contabilidad/asientos/<int:pk>/imprimir/', views.asiento_imprimir, name='asiento_imprimir'),
    
    # ============================================
    # URLs para Reportes Contables
    # ============================================
    path('contabilidad/dashboard/', views.contabilidad_dashboard, name='contabilidad_dashboard'),
    path('contabilidad/reportes/libro-diario/', views.libro_diario, name='libro_diario'),
    path('contabilidad/reportes/libro-mayor/', views.libro_mayor, name='libro_mayor'),
    path('contabilidad/reportes/balance-comprobacion/', views.balance_comprobacion, name='balance_comprobacion'),
    path('contabilidad/reportes/estado-resultados/', views.estado_resultados, name='estado_resultados'),
    path('contabilidad/reportes/balance-general/', views.balance_general, name='balance_general'),
    path('contabilidad/cuentas/<int:pk>/consulta/', views.consulta_cuenta, name='consulta_cuenta'),
    
    # ============================================
    # URLs para Sistema de Evaluaciones Educativas
    # ============================================
    path('evaluaciones/diagnosticas/', views_evaluaciones.evaluaciones_diagnosticas, name='evaluaciones_diagnosticas'),
    path('evaluaciones/diagnosticas/<int:evaluacion_id>/evaluar/', views_evaluaciones.evaluar_diagnostica, name='evaluar_diagnostica'),
    path('evaluaciones/diagnosticas/reporte/individual/<int:resultado_id>/', views_evaluaciones.reporte_individual_diagnostica, name='reporte_individual_diagnostica'),
    path('evaluaciones/diagnosticas/reporte/grupal/<int:evaluacion_id>/', views_evaluaciones.reporte_grupal_diagnostica, name='reporte_grupal_diagnostica'),
    path('evaluaciones/diagnosticas/reporte/seguimiento/<int:estudiante_id>/<int:materia_id>/', views_evaluaciones.reporte_seguimiento_diagnostica, name='reporte_seguimiento_diagnostica'),
    path('evaluaciones/rubricas/', views_evaluaciones.rubricas, name='rubricas'),
    path('evaluaciones/rubricas/<int:rubrica_id>/criterios/', views_evaluaciones.gestionar_criterios_rubrica, name='gestionar_criterios_rubrica'),
    path('evaluaciones/aplicar-rubricas/', views_evaluaciones.evaluaciones_rubricas, name='evaluaciones_rubricas'),
    path('evaluaciones/aplicar-rubricas/<int:evaluacion_id>/imprimir/', views_evaluaciones.imprimir_evaluacion_rubrica, name='imprimir_evaluacion_rubrica'),
    path('evaluaciones/aplicar-rubricas/<int:evaluacion_id>/evaluar/', views_evaluaciones.evaluar_con_rubrica, name='evaluar_con_rubrica'),
    path('evaluaciones/portafolios/', views_evaluaciones.portafolios, name='portafolios'),
    path('evaluaciones/registros-anecdoticos/', views_evaluaciones.registros_anecdoticos, name='registros_anecdoticos'),
    path('evaluaciones/cuadernos-clase/', views_evaluaciones.cuadernos_clase, name='cuadernos_clase'),
    
    # ============================================
    # URLs para Sistema de Listas de Cotejo
    # ============================================
    # Gestión de Listas de Cotejo (Plantillas)
    path('listas-cotejo/', views_listas_cotejo.listas_cotejo_lista, name='listas_cotejo_lista'),
    path('listas-cotejo/crear/', views_listas_cotejo.lista_cotejo_crear, name='lista_cotejo_crear'),
    path('listas-cotejo/<int:pk>/', views_listas_cotejo.lista_cotejo_detalle, name='lista_cotejo_detalle'),
    path('listas-cotejo/<int:pk>/editar/', views_listas_cotejo.lista_cotejo_editar, name='lista_cotejo_editar'),
    path('listas-cotejo/<int:pk>/eliminar/', views_listas_cotejo.lista_cotejo_eliminar, name='lista_cotejo_eliminar'),
    
    # Gestión de Evaluaciones con Lista de Cotejo
    path('evaluaciones-cotejo/', views_listas_cotejo.evaluacion_cotejo_lista, name='evaluacion_cotejo_lista'),
    path('evaluaciones-cotejo/crear/', views_listas_cotejo.evaluacion_cotejo_crear, name='evaluacion_cotejo_crear'),
    path('evaluaciones-cotejo/<int:pk>/', views_listas_cotejo.evaluacion_cotejo_detalle, name='evaluacion_cotejo_detalle'),
    path('evaluaciones-cotejo/<int:pk>/eliminar/', views_listas_cotejo.evaluacion_cotejo_eliminar, name='evaluacion_cotejo_eliminar'),
    
    # Calificación Masiva
    path('evaluaciones-cotejo/<int:pk>/calificar/', views_listas_cotejo.evaluacion_cotejo_calificar, name='evaluacion_cotejo_calificar'),
    path('evaluaciones-cotejo/<int:pk>/guardar-calificacion/', views_listas_cotejo.evaluacion_cotejo_guardar_calificacion, name='evaluacion_cotejo_guardar_calificacion'),
    path('evaluaciones-cotejo/<int:pk>/cambiar-estado/', views_listas_cotejo.evaluacion_cotejo_cambiar_estado, name='evaluacion_cotejo_cambiar_estado'),
    
    # Reportes y Visualización
    path('evaluaciones-cotejo/<int:pk>/reporte/', views_listas_cotejo.evaluacion_cotejo_reporte, name='evaluacion_cotejo_reporte'),
    path('evaluaciones-cotejo/<int:pk>/mi-evaluacion/', views_listas_cotejo.estudiante_ver_evaluacion, name='estudiante_ver_evaluacion'),
    
    # ============================================
    # WEBHOOKS PARA POS FÍSICOS (Cardnet, Azul)
    # ============================================
    path('webhooks/pos/cardnet/', views_pos.webhook_cardnet, name='webhook_cardnet'),
    path('webhooks/pos/azul/', views_pos.webhook_azul, name='webhook_azul'),
    path('webhooks/pos/consultar/<str:transaction_id>/', views_pos.consultar_transaccion_pos, name='consultar_transaccion_pos'),
] 
