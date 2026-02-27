from django.urls import path
from . import views

urlpatterns = [
    # ... existing urls ...
    # Reporte general PDF (notas por curso)
    path('reporte-general/<int:curso_id>/pdf/', views.reporte_general_pdf, name='reporte_general_pdf'),
    path('register/', views.register_user, name='register'),
    
    path("activate/<uidb64>/<token>/", views.activate, name="activate"),

    path('users/', views.user_list, name='user_list'),
    path('users/create/', views.user_create, name='create_user'),
    
    path('users/<int:user_id>/update/', views.user_update, name='update_user'),
    path('users/<int:user_id>/delete/', views.user_delete, name='delete_user'),
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


    # URLs para Matr�culas
    
    path('matriculas/', views.lista_matriculas, name='lista_matriculas'),
    path('matriculas/agregar/', views.agregar_matricula, name='agregar_matricula'),
    path('matriculas/editar/<int:pk>/', views.editar_matricula, name='editar_matricula'),
    path('matriculas/eliminar/<int:pk>/', views.eliminar_matricula, name='eliminar_matricula'),
    path('matriculas/confirmar-eliminar/<int:pk>/', views.confirmar_eliminar_matricula, name='confirmar_eliminar_matricula'),
    path('matriculas/<int:matricula_id>/eliminar/', views.eliminar_matricula, name='eliminar_matricula'),
    path('matriculas/<int:matricula_id>/actualizar-notas/', views.actualizar_notas, name='actualizar_notas'),
    path('estudiante/<int:estudiante_id>/reporte-notas/', views.reporte_notas_estudiante, name='reporte_notas_estudiante'),
    
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
] 
